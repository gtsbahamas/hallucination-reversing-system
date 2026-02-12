import time
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import httpx
from functools import wraps


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_duration: float = 60.0
    excluded_exceptions: List[type] = field(default_factory=list)


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: When circuit is open
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            if not any(isinstance(e, exc) for exc in self.config.excluded_exceptions):
                await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.timeout_duration
    
    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info("Circuit breaker transitioned to CLOSED")
    
    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning("Circuit breaker transitioned to OPEN from HALF_OPEN")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker transitioned to OPEN after {self.failure_count} failures")


class HTTPClientWrapper:
    """
    HTTP client wrapper with exponential backoff retry, circuit breaker,
    timeout handling, and request/response logging.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        default_headers: Optional[Dict[str, str]] = None,
        log_requests: bool = True,
        log_responses: bool = True
    ):
        """
        Initialize HTTP client wrapper.
        
        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
            default_headers: Default headers for all requests
            log_requests: Whether to log requests
            log_responses: Whether to log responses
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig()
        )
        self.default_headers = default_headers or {}
        self.log_requests = log_requests
        self.log_responses = log_responses
        
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=self.default_headers
        )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self) -> "HTTPClientWrapper":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with optional jitter.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.retry_config.initial_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        if self.retry_config.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def _log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None
    ) -> None:
        """Log HTTP request details."""
        if not self.log_requests:
            return
        
        log_data = {
            "method": method,
            "url": url,
            "headers": {k: v for k, v in (headers or {}).items() if k.lower() not in ["authorization"]},
            "params": params
        }
        
        if data and len(str(data)) < 1000:
            log_data["data"] = data
        
        logger.info(f"HTTP Request: {log_data}")
    
    def _log_response(
        self,
        response: httpx.Response,
        duration: float
    ) -> None:
        """Log HTTP response details."""
        if not self.log_responses:
            return
        
        log_data = {
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "url": str(response.url),
            "headers": dict(response.headers)
        }
        
        try:
            content = response.text
            if len(content) < 1000:
                log_data["content"] = content
        except Exception:
            pass
        
        logger.info(f"HTTP Response: {log_data}")
    
    def _should_retry(self, response: Optional[httpx.Response], exception: Optional[Exception]) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            response: HTTP response if available
            exception: Exception if raised
            
        Returns:
            True if should retry
        """
        if exception:
            if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError)):
                return True
            return False
        
        if response:
            return response.status_code in [408, 429, 500, 502, 503, 504]
        
        return False
    
    async def _execute_request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Execute HTTP request with retry and circuit breaker.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
            
        Raises:
            CircuitBreakerError: When circuit breaker is open
            httpx.HTTPError: On HTTP errors after all retries
        """
        headers = kwargs.pop("headers", {})
        params = kwargs.pop("params", None)
        data = kwargs.pop("data", None)
        json_data = kwargs.pop("json", None)
        
        self._log_request(method, url, headers, params, data or json_data)
        
        async def _make_request() -> httpx.Response:
            """Internal function to make HTTP request."""
            start_time = time.time()
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                **kwargs
            )
            duration = time.time() - start_time
            self._log_response(response, duration)
            response.raise_for_status()
            return response
        
        last_exception: Optional[Exception] = None
        last_response: Optional[httpx.Response] = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self.circuit_breaker.call(_make_request)
                return response
            except Exception as e:
                last_exception = e
                last_response = getattr(e, "response", None)
                
                if not self._should_retry(last_response, e):
                    raise
                
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                        f"Retrying in {delay:.2f}s. Error: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Request failed after {self.retry_config.max_retries + 1} attempts. "
                        f"Error: {str(e)}"
                    )
                    raise
        
        if last_exception:
            raise last_exception
        raise Exception("Request failed with unknown error")
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform GET request.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "GET",
            url,
            params=params,
            headers=headers,
            **kwargs
        )
    
    async def post(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform POST request.
        
        Args:
            url: Request URL
            data: Request body data
            json: JSON request body
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "POST",
            url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
    
    async def put(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform PUT request.
        
        Args:
            url: Request URL
            data: Request body data
            json: JSON request body
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "PUT",
            url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
    
    async def patch(
        self,
        url: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform PATCH request.
        
        Args:
            url: Request URL
            data: Request body data
            json: JSON request body
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "PATCH",
            url,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )
    
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform DELETE request.
        
        Args:
            url: Request URL
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "DELETE",
            url,
            headers=headers,
            **kwargs
        )
    
    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform HEAD request.
        
        Args:
            url: Request URL
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "HEAD",
            url,
            headers=headers,
            **kwargs
        )
    
    async def options(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """
        Perform OPTIONS request.
        
        Args:
            url: Request URL
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        return await self._execute_request(
            "OPTIONS",
            url,
            headers=headers,
            **kwargs
        )