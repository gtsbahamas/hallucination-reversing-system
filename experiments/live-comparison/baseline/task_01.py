import functools
import time
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


class JWTConfig:
    """Configuration for JWT middleware."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
        token_header: str = "Authorization",
        token_prefix: str = "Bearer",
        refresh_token_header: str = "X-Refresh-Token"
    ):
        """
        Initialize JWT configuration.
        
        Args:
            secret_key: Secret key for encoding/decoding tokens
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
            token_header: Header name for access token
            token_prefix: Token prefix (e.g., Bearer)
            refresh_token_header: Header name for refresh token
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.token_header = token_header
        self.token_prefix = token_prefix
        self.refresh_token_header = refresh_token_header


class UserContext:
    """User context attached to requests."""
    
    def __init__(self, user_id: str, username: str, roles: list[str], metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize user context.
        
        Args:
            user_id: Unique user identifier
            username: Username
            roles: List of user roles
            metadata: Additional user metadata
        """
        self.user_id = user_id
        self.username = username
        self.roles = roles
        self.metadata = metadata or {}
        self.authenticated_at = datetime.utcnow()
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user context to dictionary.
        
        Returns:
            Dictionary representation of user context
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "roles": self.roles,
            "metadata": self.metadata,
            "authenticated_at": self.authenticated_at.isoformat()
        }


class JWTMiddleware:
    """Middleware for JWT token validation and user context management."""
    
    def __init__(self, config: JWTConfig):
        """
        Initialize JWT middleware.
        
        Args:
            config: JWT configuration
        """
        self.config = config
    
    def create_access_token(self, user_id: str, username: str, roles: list[str], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create an access token.
        
        Args:
            user_id: User identifier
            username: Username
            roles: User roles
            metadata: Additional metadata
            
        Returns:
            Encoded JWT access token
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles,
            "metadata": metadata or {},
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp())
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Create a refresh token.
        
        Args:
            user_id: User identifier
            
        Returns:
            Encoded JWT refresh token
        """
        now = datetime.utcnow()
        expires = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp())
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            ExpiredSignatureError: If token has expired
            InvalidTokenError: If token is invalid
        """
        return jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
    
    def extract_token_from_header(self, header_value: Optional[str]) -> Optional[str]:
        """
        Extract token from authorization header.
        
        Args:
            header_value: Authorization header value
            
        Returns:
            Extracted token or None
        """
        if not header_value:
            return None
        
        parts = header_value.split()
        if len(parts) != 2 or parts[0] != self.config.token_prefix:
            return None
        
        return parts[1]
    
    def validate_access_token(self, token: str) -> UserContext:
        """
        Validate access token and create user context.
        
        Args:
            token: Access token to validate
            
        Returns:
            User context
            
        Raises:
            ExpiredSignatureError: If token has expired
            InvalidTokenError: If token is invalid or not an access token
        """
        payload = self.decode_token(token)
        
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        return UserContext(
            user_id=payload["user_id"],
            username=payload["username"],
            roles=payload["roles"],
            metadata=payload.get("metadata", {})
        )
    
    def validate_refresh_token(self, token: str) -> str:
        """
        Validate refresh token.
        
        Args:
            token: Refresh token to validate
            
        Returns:
            User ID from the token
            
        Raises:
            ExpiredSignatureError: If token has expired
            InvalidTokenError: If token is invalid or not a refresh token
        """
        payload = self.decode_token(token)
        
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")
        
        return payload["user_id"]
    
    def refresh_access_token(self, refresh_token: str, username: str, roles: list[str], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            username: Username for new access token
            roles: User roles for new access token
            metadata: Additional metadata
            
        Returns:
            New access token
            
        Raises:
            ExpiredSignatureError: If refresh token has expired
            InvalidTokenError: If refresh token is invalid
        """
        user_id = self.validate_refresh_token(refresh_token)
        return self.create_access_token(user_id, username, roles, metadata)


class Request:
    """Mock request object for demonstration."""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """Initialize request with headers."""
        self.headers = headers or {}
        self.user: Optional[UserContext] = None


class Response:
    """Mock response object for demonstration."""
    
    def __init__(self, status_code: int, body: Dict[str, Any]):
        """Initialize response with status code and body."""
        self.status_code = status_code
        self.body = body


def jwt_required(middleware: JWTMiddleware, optional: bool = False) -> Callable:
    """
    Decorator to enforce JWT authentication on endpoints.
    
    Args:
        middleware: JWT middleware instance
        optional: If True, authentication is optional
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: Request, *args: Any, **kwargs: Any) -> Union[Response, Any]:
            auth_header = request.headers.get(middleware.config.token_header)
            token = middleware.extract_token_from_header(auth_header)
            
            if not token:
                if optional:
                    return func(request, *args, **kwargs)
                return Response(401, {"error": "Missing authentication token"})
            
            try:
                user_context = middleware.validate_access_token(token)
                request.user = user_context
                return func(request, *args, **kwargs)
            
            except ExpiredSignatureError:
                refresh_token = request.headers.get(middleware.config.refresh_token_header)
                
                if not refresh_token:
                    return Response(401, {"error": "Token expired", "code": "TOKEN_EXPIRED"})
                
                try:
                    user_id = middleware.validate_refresh_token(refresh_token)
                    return Response(
                        401,
                        {
                            "error": "Token expired",
                            "code": "TOKEN_EXPIRED",
                            "user_id": user_id,
                            "message": "Use refresh token to obtain new access token"
                        }
                    )
                except (ExpiredSignatureError, InvalidTokenError):
                    return Response(
                        401,
                        {"error": "Invalid or expired refresh token", "code": "REFRESH_TOKEN_INVALID"}
                    )
            
            except InvalidTokenError as e:
                if optional:
                    return func(request, *args, **kwargs)
                return Response(401, {"error": f"Invalid token: {str(e)}"})
        
        return wrapper
    return decorator


def require_roles(*required_roles: str) -> Callable:
    """
    Decorator to enforce role-based access control.
    
    Args:
        required_roles: Required roles for access
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: Request, *args: Any, **kwargs: Any) -> Union[Response, Any]:
            if not hasattr(request, 'user') or request.user is None:
                return Response(401, {"error": "Authentication required"})
            
            user_context: UserContext = request.user
            
            if not any(user_context.has_role(role) for role in required_roles):
                return Response(
                    403,
                    {
                        "error": "Insufficient permissions",
                        "required_roles": list(required_roles),
                        "user_roles": user_context.roles
                    }
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class JWTMiddlewareWSGI:
    """WSGI middleware for JWT authentication."""
    
    def __init__(self, app: Callable, jwt_middleware: JWTMiddleware, excluded_paths: Optional[list[str]] = None):
        """
        Initialize WSGI middleware.
        
        Args:
            app: WSGI application
            jwt_middleware: JWT middleware instance
            excluded_paths: Paths to exclude from authentication
        """
        self.app = app
        self.jwt_middleware = jwt_middleware
        self.excluded_paths = excluded_paths or []
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Any:
        """
        WSGI application entry point.
        
        Args:
            environ: WSGI environment
            start_response: Start response callable
            
        Returns:
            Response iterable
        """
        path = environ.get('PATH_INFO', '')
        
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return self.app(environ, start_response)
        
        auth_header = environ.get('HTTP_AUTHORIZATION')
        token = self.jwt_middleware.extract_token_from_header(auth_header)
        
        if not token:
            start_response('401 Unauthorized', [('Content-Type', 'application/json')])
            return [b'{"error": "Missing authentication token"}']
        
        try:
            user_context = self.jwt_middleware.validate_access_token(token)
            environ['jwt.user'] = user_context
            return self.app(environ, start_response)
        
        except ExpiredSignatureError:
            start_response('401 Unauthorized', [('Content-Type', 'application/json')])
            return [b'{"error": "Token expired", "code": "TOKEN_EXPIRED"}']
        
        except InvalidTokenError as e:
            start_response('401 Unauthorized', [('Content-Type', 'application/json')])
            return [f'{{"error": "Invalid token: {str(e)}"}}'.encode()]


def create_token_pair(middleware: JWTMiddleware, user_id: str, username: str, roles: list[str], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Create both access and refresh tokens.
    
    Args:
        middleware: JWT middleware instance
        user_id: User identifier
        username: Username
        roles: User roles
        metadata: Additional metadata
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    access_token = middleware.create_access_token(user_id, username, roles, metadata)
    refresh_token = middleware.create_refresh_token(user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": middleware.config.access_token_expire_minutes * 60
    }