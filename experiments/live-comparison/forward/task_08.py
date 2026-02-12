import time
import logging
import asyncio
import random
from typing import Optional, Dict, Any, Callable, List, Set
from dataclasses import dataclass, field
from enum import Enum
import httpx


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
    excluded_exceptions: List[type] = field(default_factory=lambda: [])


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
        self.last_failure_time: Optional[float] = None
        self._lock: asyncio.Lock = asyncio.Lock()
    
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
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                await self._on_success_locked()
                return result
            except Exception as e:
                if not any(isinstance(e, exc) for exc in self.config.excluded_exceptions):
                    await self._on_failure_locked()
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True
        return (time.monotonic() - self.last_failure_time) >= self.config.timeout_duration
    
    async def _on_success_locked(self) -> None:
        """Handle successful call. Must be called with lock held."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker transitioned to CLOSED")
    
    async def _on_failure_locked(self) -> None:
        """Handle failed call. Must be called with lock held."""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        
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
        log_responses: bool = True,
        max_connections: int = 100,
        max_keepalive_connections: int = 20
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
            max_connections: Maximum number of connections in pool
            max_keepalive_connections: Maximum keepalive connections
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        
        cb_config = circuit_breaker_config or CircuitBreakerConfig()
        if httpx.TimeoutException not in cb_config.excluded_exceptions:
            cb_config.excluded_exceptions.append(httpx.TimeoutException)
        
        self.circuit_breaker = CircuitBreaker(cb_config)
        self.default_headers = default_headers or {}
        self.log_requests = log_requests
        self.log_responses = log_responses
        self._in_flight_requests: Set[asyncio.Task] = set()
        self._closed = False
        
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections
        )
        
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=self.default_headers,
            limits=limits
        )
    
    async def close(self) -> None:
        """Close the HTTP client gracefully."""
        if self._closed:
            return
        
        self._closed = True
        
        if self._in_flight_requests:
            logger.info(f"Waiting for {len(self._in_flight_requests)} in-flight requests to complete")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._in_flight_requests, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for in-flight requests to complete")
        
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
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def _sanitize_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Sanitize headers by masking sensitive values."""
        if not headers:
            return {}
        
        sensitive_headers = {'authorization', 'cookie', 'x-api-key', 'x-api-token', 'x-auth-token'}
        return {
            k: '***REDACTED***' if k.lower() in sensitive_headers else v
            for k, v in headers.items()
        }
    
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
            "headers": self._sanitize_headers(headers),
            "params": params
        }
        
        if data:
            data_str = str(data)
            if len(data_str) < 1000:
                log_data["data"] = data
            else:
                log_data["data_size"] = len(data_str)
        
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
            "headers": self._sanitize_headers(dict(response.headers))
        }
        
        try:
            content = response.text
            if len(content) < 1000:
                log_data["content"] = content
            else:
                log_data["content_size"] = len(content)
        except Exception as e:
            logger.debug(f"Could not log response content: {e}")
        
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
            if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError)):
                return True
            if isinstance(exception, httpx.HTTPStatusError):
                response = exception.response
            else:
                return False
        
        if response:
            status_code = response.status_code
            if 400 <= status_code < 500:
                return status_code in [408, 429]
            return status_code in [500, 502, 503, 504]
        
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
        if self._closed:
            raise RuntimeError("Client is closed")
        
        headers = {**self.default_headers, **(kwargs.pop("headers", {}))}
        params = kwargs.pop("params", None)
        data = kwargs.pop("data", None)
        json_data = kwargs.pop("json", None)
        
        self._log_request(method, url, headers, params, data or json_data)
        
        async def _make_request() -> httpx.Response:
            """Internal function to make HTTP request."""
            start_time = time.monotonic()
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                **kwargs
            )
            duration = time.monotonic() - start_time
            self._log_response(response, duration)
            response.raise_for_status()
            return response
        
        last_exception: Optional[Exception] = None
        last_response: Optional[httpx.Response] = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self.circuit_breaker.call(_make_request)
                return response
            except httpx.HTTPStatusError as e:
                last_exception = e
                last_response = e.response
                
                if not self._should_retry(last_response, e):
                    raise
                
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                        f"Retrying in {delay:.2f}s. Status: {e.response.status_code}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Request failed after {self.retry_config.max_retries + 1} attempts. "
                        f"Status: {e.response.status_code}"
                    )
                    raise
            except Exception as e:
                last_exception = e
                
                if not self._should_retry(None, e):
                    raise
                
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.retry_config.max_retries + 1}). "
                        f"Retrying in {delay:.2f}s. Error: {type(e).__name__}: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Request failed after {self.retry_config.max_retries + 1} attempts. "
                        f"Error: {type(e).__name__}: {str(e)}"
                    )
                    raise
        
        raise last_exception
    
    async def _track_request(self, coro):
        """Track in-flight requests for graceful shutdown."""
        task = asyncio.current_task()
        if task:
            self._in_flight_requests.add(task)
        try:
            return await coro
        finally:
            if task:
                self._in_flight_requests.discard(task)
    
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
        return await self._track_request(
            self._execute_request("GET", url, params=params, headers=headers, **kwargs)
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
        return await self._track_request(
            self._execute_request("POST", url, data=data, json=json, headers=headers, **kwargs)
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
        return await self._track_request(
            self._execute_request("PUT", url, data=data, json=json, headers=headers, **kwargs)
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
        return await self._track_request(
            self._execute_request("PATCH", url, data=data, json=json, headers=headers, **kwargs)
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
        return await self._track_request(
            self._execute_request("DELETE", url, headers=headers, **kwargs)
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
        return await self._track_request(
            self._execute_request("HEAD", url, headers=headers, **kwargs)
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
        return await self._track_request(
            self._execute_request("OPTIONS", url, headers=headers, **kwargs)
        )