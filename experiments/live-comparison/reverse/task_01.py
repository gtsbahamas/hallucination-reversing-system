import jwt
import hmac
import hashlib
import time
import json
import base64
import logging
from typing import Optional, Dict, Any, List, Callable, Union, TypedDict
from dataclasses import dataclass
from functools import wraps
from datetime import datetime, timezone
import fnmatch


logger = logging.getLogger(__name__)


class UserContext(TypedDict, total=False):
    user_id: str
    email: Optional[str]
    role: str
    permissions: Optional[List[str]]


@dataclass
class JWTConfig:
    secret_key: str
    algorithm: str = 'HS256'
    access_token_lifetime: int = 900  # 15 minutes
    refresh_token_lifetime: int = 604800  # 7 days
    clock_skew: int = 60  # 60 seconds tolerance
    expected_issuer: Optional[str] = None
    expected_audience: Optional[str] = None
    public_key: Optional[str] = None
    json_errors: bool = True
    excluded_paths: List[str] = None
    enable_revocation_check: bool = False
    revocation_list: set = None
    max_token_size: int = 10240  # 10KB
    enable_token_caching: bool = False
    token_cache_ttl: int = 5  # 5 seconds
    
    def __post_init__(self):
        if self.excluded_paths is None:
            self.excluded_paths = []
        if self.revocation_list is None:
            self.revocation_list = set()


class TokenCache:
    def __init__(self, ttl: int = 5):
        self.cache: Dict[str, tuple[Dict[str, Any], float]] = {}
        self.ttl = ttl
    
    def get(self, token_hash: str) -> Optional[Dict[str, Any]]:
        if token_hash in self.cache:
            payload, cached_time = self.cache[token_hash]
            if time.time() - cached_time < self.ttl:
                return payload
            else:
                del self.cache[token_hash]
        return None
    
    def set(self, token_hash: str, payload: Dict[str, Any]):
        self.cache[token_hash] = (payload, time.time())
    
    def clear_expired(self):
        current_time = time.time()
        expired_keys = [
            k for k, (_, cached_time) in self.cache.items()
            if current_time - cached_time >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]


class JWTMiddleware:
    def __init__(self, config: JWTConfig):
        self.config = config
        self.token_cache = TokenCache(config.token_cache_ttl) if config.enable_token_caching else None
        
        # Validate required configuration
        if not self.config.secret_key and not self.config.public_key:
            raise ValueError("Either secret_key or public_key must be configured")
    
    def _get_token_hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _should_skip_authentication(self, path: str) -> bool:
        for pattern in self.config.excluded_paths:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False
    
    def _extract_token_from_request(self, request) -> Optional[str]:
        # Check Authorization header first
        auth_header = request.headers.get('Authorization')
        
        if auth_header is not None:
            if not isinstance(auth_header, str):
                return None
            
            # Handle Bearer scheme (case-insensitive)
            parts = auth_header.split(' ', 1)
            if len(parts) == 2:
                scheme, token = parts
                if scheme.lower() == 'bearer':
                    return token.strip()
        
        # Check cookies if header not present
        if hasattr(request, 'cookies'):
            cookie_token = request.cookies.get('access_token')
            if cookie_token:
                return cookie_token
        
        return None
    
    def _validate_token_structure(self, token: str) -> bool:
        if not token or not isinstance(token, str):
            return False
        
        # Check token size
        if len(token) > self.config.max_token_size:
            return False
        
        # Check JWT structure (three segments)
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        return True
    
    def _decode_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        # Check cache first if enabled
        if self.token_cache and token_type == 'access':
            token_hash = self._get_token_hash(token)
            cached_payload = self.token_cache.get(token_hash)
            if cached_payload:
                return cached_payload
        
        # Determine key and algorithms
        if self.config.algorithm.startswith('RS'):
            key = self.config.public_key if self.config.public_key else self.config.secret_key
            algorithms = ['RS256', 'RS384', 'RS512']
        else:
            key = self.config.secret_key
            algorithms = ['HS256', 'HS384', 'HS512']
        
        # Decode options
        decode_options = {
            'verify_signature': True,
            'verify_exp': True,
            'verify_nbf': True,
            'verify_iat': True,
            'verify_aud': self.config.expected_audience is not None,
            'verify_iss': self.config.expected_issuer is not None,
            'require_exp': True,
            'require_iat': False,
        }
        
        try:
            # Decode with configured parameters
            payload = jwt.decode(
                token,
                key,
                algorithms=algorithms,
                options=decode_options,
                leeway=self.config.clock_skew,
                audience=self.config.expected_audience,
                issuer=self.config.expected_issuer
            )
            
            # Validate exp is numeric
            if 'exp' not in payload:
                raise jwt.InvalidTokenError('missing required claim: exp')
            
            if not isinstance(payload.get('exp'), (int, float)):
                raise jwt.InvalidTokenError('invalid expiration format')
            
            # Check token type if present
            if 'type' in payload and payload['type'] != token_type:
                if token_type == 'access' and payload['type'] == 'refresh':
                    raise jwt.InvalidTokenError('refresh token cannot be used for API access')
                raise jwt.InvalidTokenError(f'invalid token type: expected {token_type}, got {payload["type"]}')
            
            # Check revocation if enabled
            if self.config.enable_revocation_check and 'jti' in payload:
                if payload['jti'] in self.config.revocation_list:
                    raise jwt.InvalidTokenError('token has been revoked')
            
            # Cache valid payload if caching enabled
            if self.token_cache and token_type == 'access':
                token_hash = self._get_token_hash(token)
                self.token_cache.set(token_hash, payload)
            
            return payload
            
        except jwt.ExpiredSignatureError:
            if token_type == 'refresh':
                raise jwt.InvalidTokenError('refresh token expired')
            raise jwt.InvalidTokenError('token expired')
        except jwt.InvalidTokenError as e:
            # Handle various JWT errors
            error_msg = str(e).lower()
            if 'algorithm' in error_msg or 'none' in error_msg:
                raise jwt.InvalidTokenError('unsupported algorithm')
            if 'issuer' in error_msg:
                raise jwt.InvalidTokenError('invalid issuer')
            if 'audience' in error_msg:
                raise jwt.InvalidTokenError('invalid audience')
            if 'not yet valid' in error_msg or 'nbf' in error_msg:
                raise jwt.InvalidTokenError('token not yet valid')
            if 'signature' in error_msg:
                raise jwt.InvalidTokenError('invalid signature')
            raise
        except (ValueError, json.JSONDecodeError, base64.binascii.Error):
            raise jwt.InvalidTokenError('malformed token')
    
    def _create_access_token(self, user_id: str, additional_claims: Dict[str, Any] = None) -> str:
        current_time = int(time.time())
        exp = current_time + self.config.access_token_lifetime
        
        payload = {
            'user_id': user_id,
            'exp': exp,
            'iat': current_time,
            'type': 'access'
        }
        
        if self.config.expected_issuer:
            payload['iss'] = self.config.expected_issuer
        
        if self.config.expected_audience:
            payload['aud'] = self.config.expected_audience
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def _create_error_response(self, status_code: int, error: str, message: str) -> tuple:
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'Cache-Control': 'no-store'
        }
        
        if self.config.json_errors:
            body = json.dumps({'error': error, 'message': message})
            headers['Content-Type'] = 'application/json'
        else:
            body = message
            headers['Content-Type'] = 'text/plain'
        
        return status_code, body, headers
    
    def _log_auth_failure(self, request, reason: str):
        remote_addr = getattr(request, 'remote_addr', 'unknown')
        path = getattr(request, 'path', 'unknown')
        logger.warning(f'Auth failed: {reason} from {remote_addr} to {path}')
    
    def validate_request(self, request):
        # Preserve original request attributes
        original_path = request.path
        original_method = request.method
        
        # Check if path should skip authentication
        if self._should_skip_authentication(original_path):
            return None
        
        # Extract token
        token = self._extract_token_from_request(request)
        
        if not token:
            self._log_auth_failure(request, 'missing authorization header')
            return self._create_error_response(
                401,
                'unauthorized',
                'Authorization header required'
            )
        
        # Validate token structure
        if not self._validate_token_structure(token):
            if len(token) > self.config.max_token_size:
                self._log_auth_failure(request, 'token too large')
                return self._create_error_response(
                    400,
                    'bad_request',
                    'token too large'
                )
            self._log_auth_failure(request, 'malformed token')
            return self._create_error_response(
                401,
                'unauthorized',
                'malformed token'
            )
        
        try:
            # Decode and validate token
            payload = self._decode_token(token, token_type='access')
            
            # Attach user context to request
            request.user = payload
            
            return None  # Success, no error response
            
        except jwt.InvalidTokenError as e:
            error_msg = str(e)
            self._log_auth_failure(request, error_msg)
            
            # Determine appropriate status code
            if 'refresh token cannot be used' in error_msg:
                status_code = 403
            else:
                status_code = 401
            
            return self._create_error_response(
                status_code,
                'unauthorized',
                error_msg
            )
        except Exception as e:
            self._log_auth_failure(request, 'unexpected error')
            logger.error(f'Unexpected error during token validation: {type(e).__name__}')
            return self._create_error_response(
                401,
                'unauthorized',
                'authentication failed'
            )
    
    def handle_refresh_token(self, request) -> tuple:
        # Validate request body
        if not hasattr(request, 'json') or not request.json:
            return self._create_error_response(
                400,
                'bad_request',
                'refresh token required'
            )
        
        refresh_token = request.json.get('refresh_token')
        
        if not refresh_token or not isinstance(refresh_token, str):
            return self._create_error_response(
                400,
                'bad_request',
                'refresh token required'
            )
        
        # Validate token structure
        if not self._validate_token_structure(refresh_token):
            if len(refresh_token) > self.config.max_token_size:
                return self._create_error_response(
                    400,
                    'bad_request',
                    'token too large'
                )
            return self._create_error_response(
                401,
                'unauthorized',
                'malformed token'
            )
        
        try:
            # Decode refresh token
            payload = self._decode_token(refresh_token, token_type='refresh')
            
            # Extract user info
            user_id = payload.get('user_id')
            if not user_id:
                return self._create_error_response(
                    401,
                    'unauthorized',
                    'invalid token: missing user_id'
                )
            
            # Create new access token
            additional_claims = {k: v for k, v in payload.items() 
                               if k not in ('exp', 'iat', 'type', 'nbf', 'jti')}
            new_access_token = self._create_access_token(user_id, additional_claims)
            
            # Return success response
            headers = {
                'Content-Type': 'application/json',
                'X-Content-Type-Options': 'nosniff',
                'Cache-Control': 'no-store'
            }
            
            body = json.dumps({
                'access_token': new_access_token
            })
            
            return 200, body, headers
            
        except jwt.InvalidTokenError as e:
            error_msg = str(e)
            self._log_auth_failure(request, f'refresh token: {error_msg}')
            return self._create_error_response(
                401,
                'unauthorized',
                error_msg
            )
        except Exception as e:
            logger.error(f'Unexpected error during token refresh: {type(e).__name__}')
            return self._create_error_response(
                401,
                'unauthorized',
                'token refresh failed'
            )


class MockRequest:
    def __init__(self, path: str = '/api/data', method: str = 'GET', 
                 headers: Dict[str, str] = None, cookies: Dict[str, str] = None,
                 json_data: Dict[str, Any] = None, remote_addr: str = '127.0.0.1'):
        self.path = path
        self.method = method
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.json = json_data
        self.remote_addr = remote_addr
        self.user = None


def create_test_token(secret_key: str, payload: Dict[str, Any], algorithm: str = 'HS256') -> str:
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def main():
    # Example usage
    config = JWTConfig(
        secret_key='test_secret',
        algorithm='HS256',
        access_token_lifetime=900,
        clock_skew=60,
        json_errors=True,
        excluded_paths=['/health', '/public/*'],
        enable_revocation_check=False
    )
    
    middleware = JWTMiddleware(config)
    
    # Test 1: Valid token
    current_time = int(time.time())
    valid_payload = {
        'user_id': '123',
        'exp': current_time + 600,
        'role': 'user',
        'type': 'access'
    }
    valid_token = create_test_token(config.secret_key, valid_payload)
    
    request = MockRequest(
        path='/api/data',
        headers={'Authorization': f'Bearer {valid_token}'}
    )
    
    error = middleware.validate_request(request)
    if error:
        print(f"Error: {error}")
    else:
        print(f"Success! User context: {request.user}")
    
    # Test 2: Missing Authorization header
    request = MockRequest(path='/api/data')
    error = middleware.validate_request(request)
    print(f"Missing auth test: {error[0]} - {error[1]}")
    
    # Test 3: Expired token
    expired_payload = {
        'user_id': '123',
        'exp': current_time - 3600,
        'type': 'access'
    }
    expired_token = create_test_token(config.secret_key, expired_payload)
    request = MockRequest(
        path='/api/data',
        headers={'Authorization': f'Bearer {expired_token}'}
    )
    error = middleware.validate_request(request)
    print(f"Expired token test: {error[0]} - {error[1]}")
    
    # Test 4: Refresh token endpoint
    refresh_payload = {
        'user_id': '456',
        'exp': current_time + 604800,
        'type': 'refresh',
        'role': 'admin'
    }
    refresh_token = create_test_token(config.secret_key, refresh_payload)
    request = MockRequest(
        path='/refresh',
        method='POST',
        json_data={'refresh_token': refresh_token}
    )
    status, body, headers = middleware.handle_refresh_token(request)
    print(f"Refresh token test: {status} - {body}")
    
    # Test 5: Public endpoint (excluded path)
    request = MockRequest(path='/health')
    error = middleware.validate_request(request)
    print(f"Public endpoint test: {'Skipped authentication' if error is None else 'Failed'}")


if __name__ == '__main__':
    main()