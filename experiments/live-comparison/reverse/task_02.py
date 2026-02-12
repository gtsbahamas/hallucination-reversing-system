import re
import time
import logging
import urllib.parse
from typing import Dict, Optional, Any
import uuid

try:
    import redis
except ImportError:
    raise ImportError("redis package is required. Install with: pip install redis")

logger = logging.getLogger(__name__)


class RateLimiterError(Exception):
    """Custom exception for rate limiter errors."""
    pass


class RateLimiter:
    """Sliding window rate limiter with Redis storage supporting per-user and per-endpoint limits."""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        limit: str,
        key_prefix: str = "ratelimit:",
        fail_open: bool = False,
        endpoint_limiting: bool = False
    ):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance
            limit: Rate limit in format "N/unit" where unit is s/m/h/d
            key_prefix: Prefix for Redis keys for namespace isolation
            fail_open: If True, allow requests when Redis is unavailable; if False, reject
            endpoint_limiting: If True, enforce per-endpoint limits
        
        Raises:
            ValueError: If limit format is invalid
            TypeError: If limit is not a string
        """
        if not isinstance(limit, str):
            raise TypeError(f"limit must be string in format N/unit, got {type(limit).__name__}")
        
        self._validate_limit_format(limit)
        self.redis_client = redis_client
        self.limit_str = limit
        self.key_prefix = key_prefix
        self.fail_open = fail_open
        self.endpoint_limiting = endpoint_limiting
        
        self.limit_count, self.window_seconds = self._parse_limit(limit)
        
        self._lua_script = self.redis_client.register_script("""
            local key = KEYS[1]
            local window_start = tonumber(ARGV[1])
            local current_time = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            local ttl = tonumber(ARGV[4])
            local request_id = ARGV[5]
            
            redis.call('ZREMRANGEBYSCORE', key, '-inf', '(' .. window_start)
            
            local current_count = redis.call('ZCARD', key)
            
            local allowed = 0
            local remaining = 0
            local reset_after = 0
            
            if current_count < limit then
                redis.call('ZADD', key, current_time, request_id)
                redis.call('EXPIRE', key, ttl)
                allowed = 1
                remaining = limit - current_count - 1
            else
                allowed = 0
                remaining = 0
            end
            
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            if #oldest > 0 then
                local oldest_time = tonumber(oldest[2])
                reset_after = oldest_time + (current_time - window_start) - current_time
                if reset_after < 0 then
                    reset_after = 0
                end
            else
                reset_after = 0
            end
            
            return {allowed, remaining, reset_after}
        """)
    
    def _validate_limit_format(self, limit_str: str) -> None:
        """
        Validate limit format using regex.
        
        Args:
            limit_str: Limit string to validate
            
        Raises:
            ValueError: If format is invalid
        """
        if not re.match(r'^\d+(\.\d+)?/[smhd]$', limit_str):
            raise ValueError(f"Invalid limit format: {limit_str}, expected N/unit")
    
    def _parse_limit(self, limit_str: str) -> tuple[int, float]:
        """
        Parse limit string into count and window duration in seconds.
        
        Args:
            limit_str: Limit string in format "N/unit"
            
        Returns:
            Tuple of (limit_count, window_seconds)
            
        Raises:
            ValueError: If time unit is unsupported or count is invalid
        """
        parts = limit_str.split('/')
        limit_value = float(parts[0])
        time_unit = parts[1]
        
        valid_units = {'s', 'm', 'h', 'd'}
        if time_unit not in valid_units:
            raise ValueError(f"Unsupported time unit: {time_unit}, must be s/m/h/d")
        
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        if limit_value < 1:
            window_seconds = units[time_unit] / limit_value
            limit_count = 1
        else:
            if limit_value != int(limit_value):
                raise ValueError("Limit count must be positive integer when >= 1")
            limit_count = int(limit_value)
            if limit_count <= 0:
                raise ValueError("Limit count must be positive integer")
            window_seconds = units[time_unit]
        
        return limit_count, float(window_seconds)
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize user ID or endpoint to prevent Redis key injection.
        
        Args:
            identifier: User ID or endpoint string
            
        Returns:
            Sanitized identifier safe for use in Redis keys
        """
        return urllib.parse.quote(identifier, safe='')
    
    def _make_key(self, user_id: str, endpoint: Optional[str] = None) -> str:
        """
        Generate Redis key for user-endpoint combination.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier (optional)
            
        Returns:
            Redis key string
        """
        safe_user = self._sanitize_identifier(user_id)
        
        if endpoint and self.endpoint_limiting:
            from urllib.parse import urlparse
            endpoint_path = urlparse(endpoint).path
            safe_endpoint = self._sanitize_identifier(endpoint_path)
            return f"{self.key_prefix}user:{safe_user}:endpoint:{safe_endpoint}"
        else:
            return f"{self.key_prefix}user:{safe_user}"
    
    def _validate_identifiers(self, user_id: Any, endpoint: Optional[Any] = None) -> None:
        """
        Validate user_id and endpoint parameters.
        
        Args:
            user_id: User identifier to validate
            endpoint: Endpoint identifier to validate
            
        Raises:
            ValueError: If identifiers are invalid
            TypeError: If types are incorrect
        """
        if not isinstance(user_id, str):
            raise TypeError(f"user_id must be string, got {type(user_id).__name__}")
        
        if not user_id:
            raise ValueError("user_id is required and must be non-empty string")
        
        if len(user_id) > 256:
            raise ValueError("user_id and endpoint must not exceed 256 characters")
        
        if self.endpoint_limiting:
            if endpoint is not None:
                if not isinstance(endpoint, str):
                    raise TypeError(f"endpoint must be string, got {type(endpoint).__name__}")
                if not endpoint:
                    raise ValueError("endpoint is required for endpoint-based limiting")
                if len(endpoint) > 256:
                    raise ValueError("user_id and endpoint must not exceed 256 characters")
    
    def check(self, user_id: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit and record it if allowed.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier (optional, required if endpoint_limiting is True)
            
        Returns:
            Dict with keys:
                - allowed (bool): Whether request is allowed
                - remaining (int): Remaining quota in current window
                - reset_after (float): Seconds until quota resets
                
        Raises:
            ValueError: If identifiers are invalid
            TypeError: If parameter types are incorrect
            RateLimiterError: If Redis operation fails and fail_open is False
        """
        self._validate_identifiers(user_id, endpoint)
        
        key = self._make_key(user_id, endpoint)
        current_time = time.time()
        window_start = current_time - self.window_seconds
        ttl_seconds = int(self.window_seconds + 60)
        request_id = str(uuid.uuid4())
        
        try:
            result = self._lua_script(
                keys=[key],
                args=[
                    window_start,
                    current_time,
                    self.limit_count,
                    ttl_seconds,
                    request_id
                ]
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            reset_after = float(result[2])
            
            return {
                'allowed': allowed,
                'remaining': max(0, remaining),
                'reset_after': max(0.0, reset_after)
            }
            
        except redis.ConnectionError as e:
            if self.fail_open:
                logger.warning(f"Redis unavailable, allowing request: {type(e).__name__}")
                return {
                    'allowed': True,
                    'remaining': self.limit_count,
                    'reset_after': 0.0
                }
            raise RateLimiterError(f"Rate limiter unavailable: Redis connection failed") from e
        
        except redis.TimeoutError as e:
            if self.fail_open:
                logger.warning(f"Redis timeout, allowing request: {type(e).__name__}")
                return {
                    'allowed': True,
                    'remaining': self.limit_count,
                    'reset_after': 0.0
                }
            raise RateLimiterError(f"Rate limiter unavailable: Redis timeout") from e
        
        except redis.ResponseError as e:
            logger.error(f"Redis error during rate limiting for user {user_id}")
            raise RateLimiterError(f"Redis error during rate limiting: {type(e).__name__}") from e
        
        except (ValueError, TypeError) as e:
            logger.warning(f"Corrupted data for user {user_id}, resetting")
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
            return {
                'allowed': True,
                'remaining': self.limit_count - 1,
                'reset_after': self.window_seconds
            }
        
        except Exception as e:
            logger.error(f"Unexpected error during rate limiting for user {user_id}: {type(e).__name__}")
            raise RateLimiterError(f"Unexpected error during rate limiting: {type(e).__name__}") from e
    
    def get_current_usage(self, user_id: str, endpoint: Optional[str] = None) -> int:
        """
        Get current request count in window without incrementing.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier (optional)
            
        Returns:
            Current request count in window
            
        Raises:
            ValueError: If identifiers are invalid
            RateLimiterError: If Redis operation fails
        """
        self._validate_identifiers(user_id, endpoint)
        
        key = self._make_key(user_id, endpoint)
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            self.redis_client.zremrangebyscore(key, '-inf', f'({window_start}')
            count = self.redis_client.zcard(key)
            return int(count)
        
        except redis.ConnectionError as e:
            raise RateLimiterError(f"Rate limiter unavailable: Redis connection failed") from e
        except redis.ResponseError as e:
            raise RateLimiterError(f"Redis error during rate limiting: {type(e).__name__}") from e
        except Exception as e:
            raise RateLimiterError(f"Unexpected error: {type(e).__name__}") from e
    
    def reset(self, user_id: str, endpoint: Optional[str] = None) -> None:
        """
        Reset rate limit for user-endpoint combination.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier (optional)
            
        Raises:
            ValueError: If identifiers are invalid
            RateLimiterError: If Redis operation fails
        """
        self._validate_identifiers(user_id, endpoint)
        
        key = self._make_key(user_id, endpoint)
        
        try:
            self.redis_client.delete(key)
        except redis.ConnectionError as e:
            raise RateLimiterError(f"Rate limiter unavailable: Redis connection failed") from e
        except redis.ResponseError as e:
            raise RateLimiterError(f"Redis error during rate limiting: {type(e).__name__}") from e
        except Exception as e:
            raise RateLimiterError(f"Unexpected error: {type(e).__name__}") from e