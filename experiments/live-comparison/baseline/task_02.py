import time
from typing import Optional, Protocol, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class StorageBackend(Protocol):
    """Protocol defining the storage backend interface for rate limiting."""
    
    def zadd(self, key: str, score: float, member: str) -> int:
        """Add a member with score to a sorted set."""
        ...
    
    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove members from sorted set within score range."""
        ...
    
    def zcard(self, key: str) -> int:
        """Get the number of members in a sorted set."""
        ...
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time on a key."""
        ...
    
    def pipeline(self) -> "Pipeline":
        """Create a pipeline for batch operations."""
        ...


class Pipeline(Protocol):
    """Protocol for Redis pipeline operations."""
    
    def zadd(self, key: str, score: float, member: str) -> "Pipeline":
        ...
    
    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> "Pipeline":
        ...
    
    def zcard(self, key: str) -> "Pipeline":
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
    """
    
    def __init__(
        self,
        storage: StorageBackend,
        key_prefix: str = "ratelimit",
        default_limits: Optional[Dict[LimitType, RateLimit]] = None
    ) -> None:
        """
        Initialize the rate limiter.
        
        Args:
            storage: Redis-compatible storage backend
            key_prefix: Prefix for all Redis keys
            default_limits: Default rate limits by type
        """
        self.storage = storage
        self.key_prefix = key_prefix
        self.default_limits = default_limits or {}
        self.endpoint_limits: Dict[str, RateLimit] = {}
        self.user_limits: Dict[str, RateLimit] = {}
        self.user_endpoint_limits: Dict[Tuple[str, str], RateLimit] = {}
    
    def set_endpoint_limit(self, endpoint: str, limit: RateLimit) -> None:
        """
        Set rate limit for a specific endpoint.
        
        Args:
            endpoint: Endpoint identifier
            limit: Rate limit configuration
        """
        self.endpoint_limits[endpoint] = limit
    
    def set_user_limit(self, user_id: str, limit: RateLimit) -> None:
        """
        Set rate limit for a specific user.
        
        Args:
            user_id: User identifier
            limit: Rate limit configuration
        """
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
            user_id: User identifier
            endpoint: Endpoint identifier
            limit: Rate limit configuration
        """
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
    
    def _check_limit(
        self,
        key: str,
        limit: RateLimit,
        current_time: float
    ) -> RateLimitResult:
        """
        Check if request is within rate limit for a specific key.
        
        Args:
            key: Redis key for the limit
            limit: Rate limit configuration
            current_time: Current timestamp
        
        Returns:
            Result of rate limit check
        """
        window_start = current_time - limit.window_seconds
        request_id = f"{current_time}:{id(self)}"
        
        pipe = self.storage.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, current_time, request_id)
        pipe.expire(key, limit.window_seconds + 1)
        
        results = pipe.execute()
        current_count = results[1]
        
        allowed = current_count < limit.max_requests
        
        retry_after = None
        if not allowed:
            pipe = self.storage.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.execute()
            
            retry_after = limit.window_seconds
        
        return RateLimitResult(
            allowed=allowed,
            current_count=current_count + (1 if allowed else 0),
            limit=limit.max_requests,
            window_seconds=limit.window_seconds,
            retry_after=retry_after
        )
    
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
        """
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
        
        for key, limit in checks:
            result = self._check_limit(key, limit, current_time)
            if not result.allowed:
                return result
        
        return result
    
    def reset_limit(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> int:
        """
        Reset rate limit counters for specified identifiers.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier
        
        Returns:
            Number of keys deleted
        """
        keys_to_delete = []
        
        if user_id and endpoint:
            keys_to_delete.append(
                self._get_key(LimitType.USER_ENDPOINT, user_id, endpoint)
            )
        
        if endpoint:
            keys_to_delete.append(self._get_key(LimitType.ENDPOINT, endpoint))
        
        if user_id:
            keys_to_delete.append(self._get_key(LimitType.USER, user_id))
        
        deleted = 0
        for key in keys_to_delete:
            try:
                self.storage.zremrangebyscore(key, 0, float('inf'))
                deleted += 1
            except Exception:
                pass
        
        return deleted
    
    def get_current_usage(
        self,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> Dict[str, Tuple[int, int]]:
        """
        Get current usage statistics for specified identifiers.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier
            current_time: Current timestamp (defaults to time.time())
        
        Returns:
            Dictionary mapping limit type to (current_count, max_requests)
        """
        if current_time is None:
            current_time = time.time()
        
        usage = {}
        
        if user_id and endpoint:
            limit = self._get_limit(LimitType.USER_ENDPOINT, user_id, endpoint)
            if limit:
                key = self._get_key(LimitType.USER_ENDPOINT, user_id, endpoint)
                window_start = current_time - limit.window_seconds
                self.storage.zremrangebyscore(key, 0, window_start)
                count = self.storage.zcard(key)
                usage["user_endpoint"] = (count, limit.max_requests)
        
        if endpoint:
            limit = self._get_limit(LimitType.ENDPOINT, endpoint=endpoint)
            if limit:
                key = self._get_key(LimitType.ENDPOINT, endpoint)
                window_start = current_time - limit.window_seconds
                self.storage.zremrangebyscore(key, 0, window_start)
                count = self.storage.zcard(key)
                usage["endpoint"] = (count, limit.max_requests)
        
        if user_id:
            limit = self._get_limit(LimitType.USER, user_id=user_id)
            if limit:
                key = self._get_key(LimitType.USER, user_id)
                window_start = current_time - limit.window_seconds
                self.storage.zremrangebyscore(key, 0, window_start)
                count = self.storage.zcard(key)
                usage["user"] = (count, limit.max_requests)
        
        return usage