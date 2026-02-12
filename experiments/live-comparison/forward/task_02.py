import time
import uuid
import os
import threading
from typing import Optional, Protocol, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class StorageBackend(Protocol):
    """Protocol defining the storage backend interface for rate limiting."""
    
    def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add members with scores to a sorted set."""
        ...
    
    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove members from sorted set within score range."""
        ...
    
    def zcard(self, key: str) -> int:
        """Get the number of members in a sorted set."""
        ...
    
    def zcount(self, key: str, min_score: float, max_score: float) -> int:
        """Count members in sorted set within score range."""
        ...
    
    def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> list:
        """Get members from sorted set by index range."""
        ...
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time on a key."""
        ...
    
    def eval(self, script: str, numkeys: int, *keys_and_args: Any) -> Any:
        """Execute a Lua script."""
        ...
    
    def pipeline(self) -> "Pipeline":
        """Create a pipeline for batch operations."""
        ...


class Pipeline(Protocol):
    """Protocol for Redis pipeline operations."""
    
    def zadd(self, key: str, mapping: Dict[str, float]) -> "Pipeline":
        ...
    
    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> "Pipeline":
        ...
    
    def zcard(self, key: str) -> "Pipeline":
        ...
    
    def zcount(self, key: str, min_score: float, max_score: float) -> "Pipeline":
        ...
    
    def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> "Pipeline":
        ...
    
    def expire(self, key: str, seconds: int) -> "Pipeline":
        ...
    
    def execute(self) -> list:
        ...


class LimitType(Enum):
    """Types of rate limits."""
    USER = "user"
    ENDPOINT = "endpoint"
    USER_ENDPOINT = "user_endpoint"


@dataclass
class RateLimit:
    """Configuration for a rate limit."""
    max_requests: int
    window_seconds: int
    
    def __post_init__(self) -> None:
        if self.max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    current_count: int
    limit: int
    window_seconds: int
    retry_after: Optional[float] = None
    
    @property
    def remaining(self) -> int:
        """Get remaining requests in current window."""
        return max(0, self.limit - self.current_count)


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter supporting per-user and per-endpoint limits.
    
    Uses Redis sorted sets to track request timestamps within sliding time windows.
    Supports multiple limit types and hierarchical limit checking.
    Uses Lua scripts for atomic operations to prevent race conditions.
    """
    
    # Lua script for atomic rate limit check and increment
    RATE_LIMIT_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    local request_id = ARGV[4]
    local expiry = tonumber(ARGV[5])
    
    local window_start = now - window
    
    redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
    
    local current = redis.call('ZCARD', key)
    
    if current < limit then
        redis.call('ZADD', key, now, request_id)
        redis.call('EXPIRE', key, expiry)
        return {1, current + 1, -1}
    else
        local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        local oldest_score = -1
        if #oldest > 0 then
            oldest_score = tonumber(oldest[2])
        end
        return {0, current, oldest_score}
    end
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        key_prefix: str = "ratelimit",
        default_limits: Optional[Dict[LimitType, RateLimit]] = None,
        fail_open: bool = False
    ) -> None:
        """
        Initialize the rate limiter.
        
        Args:
            storage: Redis-compatible storage backend
            key_prefix: Prefix for all Redis keys
            default_limits: Default rate limits by type
            fail_open: If True, allow requests on storage errors; if False, deny them
        """
        self.storage = storage
        self.key_prefix = key_prefix
        self.default_limits = default_limits or {}
        self.endpoint_limits: Dict[str, RateLimit] = {}
        self.user_limits: Dict[str, RateLimit] = {}
        self.user_endpoint_limits: Dict[Tuple[str, str], RateLimit] = {}
        self.fail_open = fail_open
        self._process_id = os.getpid()
    
    def set_endpoint_limit(self, endpoint: str, limit: RateLimit) -> None:
        """
        Set rate limit for a specific endpoint.
        
        Args:
            endpoint: Endpoint identifier (must be non-empty)
            limit: Rate limit configuration
        
        Raises:
            ValueError: If endpoint is empty
        """
        if not endpoint:
            raise ValueError("endpoint cannot be empty")
        self.endpoint_limits[endpoint] = limit
    
    def set_user_limit(self, user_id: str, limit: RateLimit) -> None:
        """
        Set rate limit for a specific user.
        
        Args:
            user_id: User identifier (must be non-empty)
            limit: Rate limit configuration
        
        Raises:
            ValueError: If user_id is empty
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        self.user_limits[user_id] = limit
    
    def set_user_endpoint_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: RateLimit
    ) -> None:
        """
        Set rate limit for a specific user-endpoint combination.
        
        Args:
            user_id: User identifier (must be non-empty)
            endpoint: Endpoint identifier (must be non-empty)
            limit: Rate limit configuration
        
        Raises:
            ValueError: If user_id or endpoint is empty
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not endpoint:
            raise ValueError("endpoint cannot be empty")
        self.user_endpoint_limits[(user_id, endpoint)] = limit
    
    def _get_key(self, limit_type: LimitType, *identifiers: str) -> str:
        """
        Generate Redis key for a limit.
        
        Args:
            limit_type: Type of limit
            identifiers: Additional identifiers (user_id, endpoint, etc.)
        
        Returns:
            Redis key string
        """
        parts = [self.key_prefix, limit_type.value] + list(identifiers)
        return ":".join(parts)
    
    def _get_limit(
        self,
        limit_type: LimitType,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Optional[RateLimit]:
        """
        Get applicable rate limit for the given parameters.
        
        Args:
            limit_type: Type of limit to retrieve
            user_id: User identifier
            endpoint: Endpoint identifier
        
        Returns:
            RateLimit if configured, None otherwise
        """
        if limit_type == LimitType.USER_ENDPOINT and user_id and endpoint:
            return self.user_endpoint_limits.get((user_id, endpoint))
        elif limit_type == LimitType.USER and user_id:
            return self.user_limits.get(user_id)
        elif limit_type == LimitType.ENDPOINT and endpoint:
            return self.endpoint_limits.get(endpoint)
        
        return self.default_limits.get(limit_type)
    
    def _generate_request_id(self, current_time: float) -> str:
        """
        Generate a unique request ID.
        
        Args:
            current_time: Current timestamp
        
        Returns:
            Unique request identifier
        """
        thread_id = threading.get_ident()
        unique_id = uuid.uuid4().hex
        return f"{current_time}:{self._process_id}:{thread_id}:{unique_id}"
    
    def _check_limit(
        self,
        key: str,
        limit: RateLimit,
        current_time: float
    ) -> RateLimitResult:
        """
        Check if request is within rate limit for a specific key.
        
        Uses Lua script for atomic check-and-increment operation.
        
        Args:
            key: Redis key for the limit
            limit: Rate limit configuration
            current_time: Current timestamp
        
        Returns:
            Result of rate limit check
        
        Raises:
            Exception: Re-raises storage errors based on fail_open setting
        """
        request_id = self._generate_request_id(current_time)
        expiry = limit.window_seconds * 2
        
        try:
            result = self.storage.eval(
                self.RATE_LIMIT_SCRIPT,
                1,
                key,
                int(current_time * 1000),
                limit.window_seconds * 1000,
                limit.max_requests,
                request_id,
                expiry
            )
            
            if not isinstance(result, list) or len(result) != 3:
                raise ValueError(f"Unexpected script result format: {result}")
            
            allowed = bool(result[0])
            current_count = int(result[1])
            oldest_score = float(result[2]) if result[2] != -1 else -1
            
            retry_after = None
            if not allowed and oldest_score > 0:
                retry_after = max(0.0, (oldest_score / 1000.0 + limit.window_seconds) - current_time)
            elif not allowed:
                retry_after = float(limit.window_seconds)
            
            return RateLimitResult(
                allowed=allowed,
                current_count=current_count,
                limit=limit.max_requests,
                window_seconds=limit.window_seconds,
                retry_after=retry_after
            )
        except Exception as e:
            if self.fail_open:
                return RateLimitResult(
                    allowed=True,
                    current_count=0,
                    limit=limit.max_requests,
                    window_seconds=limit.window_seconds,
                    retry_after=None
                )
            else:
                raise
    
    def check_rate_limit(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> RateLimitResult:
        """
        Check if request should be allowed based on all applicable rate limits.
        
        Checks limits in order of specificity:
        1. User-endpoint combination (most specific)
        2. Endpoint limit
        3. User limit (least specific)
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier
            current_time: Current timestamp (defaults to time.time())
        
        Returns:
            Result indicating if request is allowed
        
        Raises:
            ValueError: If user_id or endpoint is empty string
        """
        if user_id is not None and not user_id:
            raise ValueError("user_id cannot be empty string")
        if endpoint is not None and not endpoint:
            raise ValueError("endpoint cannot be empty string")
        
        if current_time is None:
            current_time = time.time()
        
        checks = []
        
        if user_id and endpoint:
            limit = self._get_limit(LimitType.USER_ENDPOINT, user_id, endpoint)
            if limit:
                key = self._get_key(LimitType.USER_ENDPOINT, user_id, endpoint)
                checks.append((key, limit))
        
        if endpoint:
            limit = self._get_limit(LimitType.ENDPOINT, endpoint=endpoint)
            if limit:
                key = self._get_key(LimitType.ENDPOINT, endpoint)
                checks.append((key, limit))
        
        if user_id:
            limit = self._get_limit(LimitType.USER, user_id=user_id)
            if limit:
                key = self._get_key(LimitType.USER, user_id)
                checks.append((key, limit))
        
        if not checks:
            return RateLimitResult(
                allowed=True,
                current_count=0,
                limit=0,
                window_seconds=0
            )
        
        result = None
        for key, limit in checks:
            result = self._check_limit(key, limit, current_time)
            if not result.allowed:
                return result
        
        return result if result is not None else RateLimitResult(
            allowed=True,
            current_count=0,
            limit=0,
            window_seconds=0
        )
    
    def reset_limit(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Reset rate limit counters for specified identifiers.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier
        
        Returns:
            Dictionary mapping key to success status
        """
        if user_id is not None and not user_id:
            raise ValueError("user_id cannot be empty string")
        if endpoint is not None and not endpoint:
            raise ValueError("endpoint cannot be empty string")
        
        keys_to_delete = []
        
        if user_id and endpoint:
            keys_to_delete.append(
                self._get_key(LimitType.USER_ENDPOINT, user_id, endpoint)
            )
        
        if endpoint:
            keys_to_delete.append(self._get_key(LimitType.ENDPOINT, endpoint))
        
        if user_id:
            keys_to_delete.append(self._get_key(LimitType.USER, user_id))
        
        results = {}
        for key in keys_to_delete:
            try:
                self.storage.zremrangebyscore(key, 0, float('inf'))
                results[key] = True
            except Exception:
                results[key] = False
        
        return results
    
    def get_current_usage(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> Dict[str, Tuple[int, int]]:
        """
        Get current usage statistics for specified identifiers.
        
        This is a read-only operation that does not modify data.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier
            current_time: Current timestamp (defaults to time.time())
        
        Returns:
            Dictionary mapping limit type to (current_count, max_requests)
        """
        if user_id is not None and not user_id:
            raise ValueError("user_id cannot be empty string")
        if endpoint is not None and not endpoint:
            raise ValueError("endpoint cannot be empty string")
        
        if current_time is None:
            current_time = time.time()
        
        current_time_ms = int(current_time * 1000)
        usage = {}
        
        try:
            if user_id and endpoint:
                limit = self._get_limit(LimitType.USER_ENDPOINT, user_id, endpoint)
                if limit:
                    key = self._get_key(LimitType.USER_ENDPOINT, user_id, endpoint)
                    window_start_ms = current_time_ms - (limit.window_seconds * 1000)
                    count = self.storage.zcount(key, window_start_ms, float('inf'))
                    usage["user_endpoint"] = (count, limit.max_requests)
            
            if endpoint:
                limit = self._get_limit(LimitType.ENDPOINT, endpoint=endpoint)
                if limit:
                    key = self._get_key(LimitType.ENDPOINT, endpoint)
                    window_start_ms = current_time_ms - (limit.window_seconds * 1000)
                    count = self.storage.zcount(key, window_start_ms, float('inf'))
                    usage["endpoint"] = (count, limit.max_requests)
            
            if user_id:
                limit = self._get_limit(LimitType.USER, user_id=user_id)
                if limit:
                    key = self._get_key(LimitType.USER, user_id)
                    window_start_ms = current_time_ms - (limit.window_seconds * 1000)
                    count = self.storage.zcount(key, window_start_ms, float('inf'))
                    usage["user"] = (count, limit.max_requests)
        except Exception:
            pass
        
        return usage
    
    def get_all_limits(self) -> Dict[str, RateLimit]:
        """
        Get all configured rate limits.
        
        Returns:
            Dictionary mapping limit identifier to RateLimit configuration
        """
        limits = {}
        
        for limit_type, limit in self.default_limits.items():
            limits[f"default:{limit_type.value}"] = limit
        
        for endpoint, limit in self.endpoint_limits.items():
            limits[f"endpoint:{endpoint}"] = limit
        
        for user_id, limit in self.user_limits.items():
            limits[f"user:{user_id}"] = limit
        
        for (user_id, endpoint), limit in self.user_endpoint_limits.items():
            limits[f"user_endpoint:{user_id}:{endpoint}"] = limit
        
        return limits