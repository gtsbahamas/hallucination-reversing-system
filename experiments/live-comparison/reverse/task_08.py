import json
import logging
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class MaxRetriesExceeded(Exception):
    """Exception raised when all retry attempts are exhausted."""
    def __init__(self, attempt_count: int, last_status_code: Optional[int], 
                 last_error_message: str, total_duration: float):
        self.attempt_count = attempt_count
        self.last_status_code = last_status_code
        self.last_error_message = last_error_message
        self.total_duration = total_duration
        super().__init__(
            f"Max retries exceeded after {attempt_count} attempts. "
            f"Last status: {last_status_code}, Error: {last_error_message}, "
            f"Total duration: {total_duration:.2f}s"
        )


class ResponseTooLargeError(Exception):
    """Exception raised when response exceeds max size."""
    pass


class SecurityError(Exception):
    """Exception raised for security violations."""
    pass


class RedirectLoopError(Exception):
    """Exception raised when redirect loop is detected."""
    pass


@dataclass
class Response:
    """HTTP Response object."""
    status_code: int
    headers: Dict[str, str]
    body: Union[str, bytes]
    
    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300
    
    def json(self) -> Any:
        """Parse response body as JSON."""
        body_str = self.body.decode('utf-8') if isinstance(self.body, bytes) else self.body
        return json.loads(body_str)


class HttpClient:
    """HTTP client with retry, circuit breaker, timeout, and logging."""
    
    RETRYABLE_STATUS_CODES: Set[int] = {500, 502, 503, 504}
    SENSITIVE_HEADERS: Set[str] = {'authorization', 'x-api-key', 'cookie', 'proxy-authorization'}
    SENSITIVE_BODY_FIELDS: Set[str] = {'password', 'token', 'secret', 'api_key'}
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        exponential_base: float = 2.0,
        max_backoff: float = 60.0,
        jitter_factor: float = 0.2,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        timeout: Optional[float] = None,
        max_response_size: int = 10 * 1024 * 1024,  # 10MB
        max_redirects: int = 10,
        retry_on_timeout: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize HTTP client with configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            exponential_base: Base for exponential calculation
            max_backoff: Maximum backoff delay in seconds
            jitter_factor: Random jitter factor (±20% by default)
            failure_threshold: Number of failures before circuit opens
            recovery_timeout: Seconds before attempting recovery from open state
            timeout: Default timeout for requests in seconds
            max_response_size: Maximum response size in bytes
            max_redirects: Maximum number of redirects to follow
            retry_on_timeout: Whether to retry on timeout errors
            logger: Logger instance for request/response logging
        """
        if not isinstance(max_retries, int):
            raise TypeError('max_retries must be int')
        if max_retries < 0:
            raise ValueError('max_retries must be non-negative')
        
        if not isinstance(failure_threshold, int):
            raise TypeError('failure_threshold must be int')
        if failure_threshold < 0:
            raise ValueError('failure_threshold must be non-negative')
        
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_base = exponential_base
        self.max_backoff = max_backoff
        self.jitter_factor = jitter_factor
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.timeout = timeout
        self.max_response_size = max_response_size
        self.max_redirects = max_redirects
        self.retry_on_timeout = retry_on_timeout
        
        self.logger = logger or logging.getLogger(__name__)
        
        # Circuit breaker state
        self.state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.opened_at: Optional[float] = None
        
        # Session for connection pooling
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _validate_url(self, url: str) -> None:
        """Validate URL format and scheme."""
        if not isinstance(url, str):
            raise TypeError(f'URL must be string, got {type(url).__name__}')
        
        # Check for CRLF injection
        if '\r' in url or '\n' in url:
            raise ValueError('CRLF injection attempt detected')
        
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ['http', 'https']:
            raise ValueError(f'Invalid URL: {url}')
    
    def _validate_timeout(self, timeout: Optional[float]) -> None:
        """Validate timeout parameter."""
        if timeout is not None:
            if not isinstance(timeout, (int, float)):
                raise TypeError(f'Timeout must be numeric or None, got {type(timeout).__name__}')
            if timeout <= 0:
                raise ValueError('Timeout must be positive number or None')
    
    def _validate_headers(self, headers: Optional[Dict[str, str]]) -> None:
        """Validate headers parameter."""
        if headers is not None:
            if not isinstance(headers, dict):
                raise TypeError('Headers must be dict')
            for key, value in headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError('Header keys and values must be strings')
                # Check for CRLF injection
                if '\r' in key or '\n' in key or '\r' in value or '\n' in value:
                    raise ValueError('CRLF injection attempt detected in headers')
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Redact sensitive header values for logging."""
        return {
            k: '[REDACTED]' if k.lower() in self.SENSITIVE_HEADERS else v
            for k, v in headers.items()
        }
    
    def _redact_sensitive_fields(self, data: Any, depth: int = 0) -> Any:
        """Recursively redact sensitive fields in data structures."""
        if depth > 10:  # Prevent infinite recursion
            return data
        
        if isinstance(data, dict):
            return {
                k: '[REDACTED]' if k.lower() in self.SENSITIVE_BODY_FIELDS else 
                   self._redact_sensitive_fields(v, depth + 1)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._redact_sensitive_fields(item, depth + 1) for item in data]
        else:
            return data
    
    def _sanitize_body(self, body: Any) -> str:
        """Sanitize request body for logging."""
        if body is None:
            return ''
        
        try:
            if isinstance(body, (dict, list)):
                sanitized = self._redact_sensitive_fields(body)
                return json.dumps(sanitized)
            elif isinstance(body, bytes):
                try:
                    body_dict = json.loads(body.decode('utf-8'))
                    sanitized = self._redact_sensitive_fields(body_dict)
                    return json.dumps(sanitized)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return '<binary data>'
            else:
                return str(body)
        except Exception:
            return '<unparseable data>'
    
    def _truncate_body_for_log(self, body: Union[str, bytes]) -> str:
        """Truncate response body for logging."""
        if isinstance(body, bytes):
            try:
                body_str = body.decode('utf-8')
            except UnicodeDecodeError:
                body_str = '<binary data>'
        else:
            body_str = body
        
        if len(body_str) > 1000:
            remaining = len(body_str) - 1000
            return f"{body_str[:1000]}... (truncated {remaining} bytes)"
        return body_str
    
    def _log_request(self, method: str, url: str, headers: Dict[str, str], 
                     body: Any = None) -> None:
        """Log request details."""
        try:
            log_data = {
                'method': method,
                'url': url,
                'headers': self._sanitize_headers(headers),
                'timestamp': datetime.utcnow().isoformat()
            }
            if body is not None:
                log_data['body'] = self._sanitize_body(body)
            self.logger.info(f"Request: {json.dumps(log_data)}")
        except Exception as e:
            print(f'Logging failed: {e}', file=sys.stderr)
    
    def _log_response(self, status_code: int, headers: Dict[str, str], 
                      body: Union[str, bytes], duration_ms: float) -> None:
        """Log response details."""
        try:
            log_data = {
                'status_code': status_code,
                'headers': dict(headers),
                'body': self._truncate_body_for_log(body),
                'duration_ms': duration_ms
            }
            self.logger.info(f"Response: {json.dumps(log_data)}")
        except Exception as e:
            print(f'Logging failed: {e}', file=sys.stderr)
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset to half-open."""
        if self.state == CircuitBreakerState.OPEN and self.opened_at is not None:
            if (time.time() - self.opened_at) >= self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
        return False
    
    def _check_circuit_breaker(self) -> None:
        """Check circuit breaker state before making request."""
        if self.failure_threshold == 0:
            return  # Circuit breaker disabled
        
        if self.state == CircuitBreakerState.OPEN:
            if not self._should_attempt_reset():
                raise CircuitBreakerOpenError('Circuit breaker is open')
    
    def _handle_success(self) -> None:
        """Handle successful request for circuit breaker."""
        if self.failure_threshold == 0:
            return
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.consecutive_failures = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.consecutive_failures = 0
    
    def _handle_failure(self) -> None:
        """Handle failed request for circuit breaker."""
        if self.failure_threshold == 0:
            return
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = time.time()
        elif self.state == CircuitBreakerState.CLOSED:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.opened_at = time.time()
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_backoff)
        jittered_delay = delay * (1 + random.uniform(-self.jitter_factor, self.jitter_factor))
        return max(0, jittered_delay)
    
    def _build_url_with_params(self, url: str, params: Optional[Dict[str, Any]]) -> str:
        """Build URL with query parameters."""
        if not params:
            return url
        
        parsed = urlparse(url)
        existing_params = parse_qs(parsed.query)
        
        # Merge params
        for key, value in params.items():
            existing_params[key] = [str(value)]
        
        # Encode
        encoded_params = urlencode(params, doseq=True)
        
        # Rebuild URL
        new_parsed = parsed._replace(query=encoded_params)
        return urlunparse(new_parsed)
    
    def _validate_json_serializable(self, json_body: Any) -> str:
        """Validate and serialize JSON body."""
        try:
            return json.dumps(json_body)
        except TypeError as e:
            raise TypeError(f'JSON body not serializable: {e}')
    
    def _check_response_size(self, response: requests.Response) -> None:
        """Check if response size exceeds limit."""
        content_length = response.headers.get('Content-Length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_response_size:
                    response.close()
                    raise ResponseTooLargeError(
                        f'Response size {size} exceeds maximum {self.max_response_size}'
                    )
            except (ValueError, TypeError):
                pass
    
    def _follow_redirects(self, response: requests.Response, 
                          visited_urls: Set[str]) -> requests.Response:
        """Follow redirects manually with validation."""
        redirect_count = 0
        current_response = response
        
        while redirect_count < self.max_redirects:
            if current_response.status_code not in (301, 302, 303, 307, 308):
                break
            
            location = current_response.headers.get('Location')
            if not location:
                break
            
            # Validate redirect URL scheme
            parsed_location = urlparse(location)
            if parsed_location.scheme and parsed_location.scheme not in ['http', 'https']:
                raise SecurityError(f'Invalid redirect scheme: {parsed_location.scheme}')
            
            # Check for redirect loop
            if location in visited_urls:
                raise RedirectLoopError(f'Redirect loop detected at: {location}')
            
            visited_urls.add(location)
            redirect_count += 1
            
            # Make redirected request
            current_response = self.session.get(
                location,
                allow_redirects=False,
                timeout=self.timeout
            )
        
        if redirect_count >= self.max_redirects:
            raise RedirectLoopError(f'Max redirects ({self.max_redirects}) exceeded')
        
        return current_response
    
    def _make_request(self, method: str, url: str, 
                      headers: Optional[Dict[str, str]] = None,
                      json_body: Any = None,
                      timeout: Optional[float] = None) -> Response:
        """Make a single HTTP request attempt."""
        self._check_circuit_breaker()
        
        effective_timeout = timeout if timeout is not None else self.timeout
        self._validate_timeout(effective_timeout)
        
        request_headers = headers or {}
        self._log_request(method, url, request_headers, json_body)
        
        start_time = time.time()
        
        try:
            kwargs = {
                'timeout': effective_timeout,
                'allow_redirects': False
            }
            
            if json_body is not None:
                self._validate_json_serializable(json_body)
                kwargs['json'] = json_body
            
            if headers:
                kwargs['headers'] = headers
            
            response = self.session.request(method, url, **kwargs)
            
            # Check response size
            self._check_response_size(response)
            
            # Follow redirects with validation
            visited_urls = {url}
            response = self._follow_redirects(response, visited_urls)
            
            # Read body
            body = response.content if response.content else b''
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            self._log_response(
                response.status_code,
                dict(response.headers),
                body,
                duration_ms
            )
            
            result = Response(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=body
            )
            
            if response.ok:
                self._handle_success()
            else:
                self._handle_failure()
            
            return result
            
        except requests.Timeout as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            self._handle_failure()
            raise TimeoutError(f'Request timeout after {duration_ms:.2f}ms: {str(e)}')
        
        except requests.ConnectionError as e:
            self._handle_failure()
            raise ConnectionError(f'Connection failed: {str(e)}')
        
        except Exception as e:
            self._handle_failure()
            raise
    
    def _should_retry(self, exception: Exception, status_code: Optional[int]) -> bool:
        """Determine if request should be retried."""
        if isinstance(exception, TimeoutError):
            return self.retry_on_timeout
        
        if isinstance(exception, (ConnectionError, requests.ConnectionError)):
            return True
        
        if status_code and status_code in self.RETRYABLE_STATUS_CODES:
            return True
        
        return False
    
    def _request(self, method: str, url: str, 
                 headers: Optional[Dict[str, str]] = None,
                 json: Any = None,
                 params: Optional[Dict[str, Any]] = None,
                 timeout: Optional[float] = None) -> Response:
        """Make HTTP request with retry logic."""
        self._validate_url(url)
        self._validate_headers(headers)
        
        # Build URL with params
        final_url = self._build_url_with_params(url, params)
        
        if self.max_retries == 0:
            return self._make_request(method, final_url, headers, json, timeout)
        
        total_start_time = time.time()
        last_exception: Optional[Exception] = None
        last_status_code: Optional[int] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_request(method, final_url, headers, json, timeout)
                
                if response.ok or response.status_code not in self.RETRYABLE_STATUS_CODES:
                    return response
                
                last_status_code = response.status_code
                
                if attempt < self.max_retries:
                    delay = self._calculate_backoff(attempt)
                    time.sleep(delay)
                
            except Exception as e:
                last_exception = e
                
                should_retry = self._should_retry(e, last_status_code)
                
                if attempt < self.max_retries and should_retry:
                    delay = self._calculate_backoff(attempt)
                    time.sleep(delay)
                else:
                    total_duration = time.time() - total_start_time
                    raise MaxRetriesExceeded(
                        attempt_count=attempt + 1,
                        last_status_code=last_status_code,
                        last_error_message=str(e),
                        total_duration=total_duration
                    )
        
        # If we get here, all retries exhausted
        total_duration = time.time() - total_start_time
        raise MaxRetriesExceeded(
            attempt_count=self.max_retries + 1,
            last_status_code=last_status_code,
            last_error_message=str(last_exception) if last_exception else 'All retries failed',
            total_duration=total_duration
        )
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None) -> Response:
        """Make GET request."""
        return self._request('GET', url, headers=headers, params=params, timeout=timeout)
    
    def post(self, url: str, json: Any = None, 
             headers: Optional[Dict[str, str]] = None,
             params: Optional[Dict[str, Any]] = None,
             timeout: Optional[float] = None) -> Response:
        """Make POST request."""
        return self._request('POST', url, headers=headers, json=json, 
                           params=params, timeout=timeout)
    
    def put(self, url: str, json: Any = None,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None) -> Response:
        """Make PUT request."""
        return self._request('PUT', url, headers=headers, json=json,
                           params=params, timeout=timeout)
    
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None,
               params: Optional[Dict[str, Any]] = None,
               timeout: Optional[float] = None) -> Response:
        """Make DELETE request."""
        return self._request('DELETE', url, headers=headers, params=params, 
                           timeout=timeout)
    
    def close(self) -> None:
        """Close the session and cleanup resources."""
        self.session.close()
    
    def __enter__(self) -> 'HttpClient':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()