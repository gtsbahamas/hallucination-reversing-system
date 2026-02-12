import functools
import time
from typing import Any, Callable, Dict, Optional, Union, Set, List
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, InvalidAlgorithmError
import threading
from abc import ABC, abstractmethod


class TokenBlacklist(ABC):
    """Abstract base class for token blacklist storage."""
    
    @abstractmethod
    def add(self, jti: str, exp: int) -> None:
        """Add token to blacklist."""
        pass
    
    @abstractmethod
    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> None:
        """Remove expired tokens from blacklist."""
        pass


class InMemoryTokenBlacklist(TokenBlacklist):
    """Thread-safe in-memory token blacklist implementation."""
    
    def __init__(self):
        self._blacklist: Dict[str, int] = {}
        self._lock = threading.RLock()
    
    def add(self, jti: str, exp: int) -> None:
        with self._lock:
            self._blacklist[jti] = exp
    
    def is_blacklisted(self, jti: str) -> bool:
        with self._lock:
            return jti in self._blacklist
    
    def cleanup_expired(self) -> None:
        current_time = int(time.time())
        with self._lock:
            expired = [jti for jti, exp in self._blacklist.items() if exp < current_time]
            for jti in expired:
                del self._blacklist[jti]


class UserDataProvider(ABC):
    """Abstract base class for fetching user data."""
    
    @abstractmethod
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user data from authoritative source.
        
        Returns:
            Dict with keys: username, roles, metadata or None if user not found
        """
        pass


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
        refresh_token_header: str = "X-Refresh-Token",
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        leeway: int = 0,
        refresh_token_rotation: bool = True,
        allowed_algorithms: Optional[List[str]] = None
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
            issuer: Token issuer claim
            audience: Token audience claim
            leeway: Clock skew tolerance in seconds
            refresh_token_rotation: Enable refresh token rotation
            allowed_algorithms: Whitelist of allowed algorithms
        """
        if not secret_key:
            raise ValueError("secret_key cannot be empty")
        
        if access_token_expire_minutes <= 0:
            raise ValueError("access_token_expire_minutes must be positive")
        
        if refresh_token_expire_days <= 0:
            raise ValueError("refresh_token_expire_days must be positive")
        
        if leeway < 0:
            raise ValueError("leeway cannot be negative")
        
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.token_header = token_header
        self.token_prefix = token_prefix
        self.refresh_token_header = refresh_token_header
        self.issuer = issuer
        self.audience = audience
        self.leeway = leeway
        self.refresh_token_rotation = refresh_token_rotation
        self.allowed_algorithms = allowed_algorithms or [algorithm]


class UserContext:
    """User context attached to requests."""
    
    def __init__(
        self, 
        user_id: str, 
        username: str, 
        roles: List[str], 
        metadata: Optional[Dict[str, Any]] = None,
        jti: Optional[str] = None
    ):
        """
        Initialize user context.
        
        Args:
            user_id: Unique user identifier
            username: Username
            roles: List of user roles
            metadata: Additional user metadata
            jti: JWT ID from token
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not username:
            raise ValueError("username cannot be empty")
        if not isinstance(roles, list):
            raise ValueError("roles must be a list")
        
        self.user_id = user_id
        self.username = username
        self.roles = roles
        self.metadata = metadata or {}
        self.jti = jti
        self.authenticated_at = datetime.utcnow()
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        if not role:
            return False
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """
        Check if user has any of the specified roles.
        
        Args:
            roles: List of roles to check
            
        Returns:
            True if user has any of the roles, False otherwise
        """
        if not roles:
            return False
        return any(self.has_role(role) for role in roles)
    
    def has_all_roles(self, roles: List[str]) -> bool:
        """
        Check if user has all of the specified roles.
        
        Args:
            roles: List of roles to check
            
        Returns:
            True if user has all roles, False otherwise
        """
        if not roles:
            return True
        return all(self.has_role(role) for role in roles)
    
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
    
    def __init__(
        self, 
        config: JWTConfig,
        blacklist: Optional[TokenBlacklist] = None,
        user_data_provider: Optional[UserDataProvider] = None
    ):
        """
        Initialize JWT middleware.
        
        Args:
            config: JWT configuration
            blacklist: Token blacklist implementation
            user_data_provider: Provider for fetching user data
        """
        if not config:
            raise ValueError("config cannot be None")
        
        self.config = config
        self.blacklist = blacklist or InMemoryTokenBlacklist()
        self.user_data_provider = user_data_provider
        self._lock = threading.RLock()
    
    def _generate_jti(self) -> str:
        """Generate unique JWT ID."""
        import uuid
        return str(uuid.uuid4())
    
    def create_access_token(
        self, 
        user_id: str, 
        username: str, 
        roles: List[str], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an access token.
        
        Args:
            user_id: User identifier
            username: Username
            roles: User roles
            metadata: Additional metadata
            
        Returns:
            Encoded JWT access token
            
        Raises:
            ValueError: If required parameters are invalid
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not username:
            raise ValueError("username cannot be empty")
        if not isinstance(roles, list):
            raise ValueError("roles must be a list")
        
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles,
            "metadata": metadata or {},
            "type": "access",
            "jti": self._generate_jti(),
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "nbf": int(now.timestamp())
        }
        
        if self.config.issuer:
            payload["iss"] = self.config.issuer
        
        if self.config.audience:
            payload["aud"] = self.config.audience
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, user_id: str, access_token_jti: Optional[str] = None) -> str:
        """
        Create a refresh token.
        
        Args:
            user_id: User identifier
            access_token_jti: JTI of associated access token for binding
            
        Returns:
            Encoded JWT refresh token
            
        Raises:
            ValueError: If user_id is invalid
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        now = datetime.utcnow()
        expires = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "jti": self._generate_jti(),
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "nbf": int(now.timestamp())
        }
        
        if access_token_jti:
            payload["ati"] = access_token_jti
        
        if self.config.issuer:
            payload["iss"] = self.config.issuer
        
        if self.config.audience:
            payload["aud"] = self.config.audience
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def decode_token(self, token: str, verify: bool = True) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            verify: Whether to verify signature and expiration
            
        Returns:
            Decoded token payload
            
        Raises:
            ExpiredSignatureError: If token has expired
            InvalidTokenError: If token is invalid
            InvalidAlgorithmError: If algorithm is not allowed
        """
        if not token:
            raise InvalidTokenError("Token cannot be empty")
        
        options = {}
        if not verify:
            options = {
                "verify_signature": False,
                "verify_exp": False,
                "verify_nbf": False,
                "verify_iat": False,
                "verify_aud": False,
                "verify_iss": False
            }
        
        decode_params = {
            "jwt": token,
            "key": self.config.secret_key,
            "algorithms": self.config.allowed_algorithms,
            "options": options,
            "leeway": self.config.leeway
        }
        
        if verify and self.config.issuer:
            decode_params["issuer"] = self.config.issuer
        
        if verify and self.config.audience:
            decode_params["audience"] = self.config.audience
        
        try:
            payload = jwt.decode(**decode_params)
        except ExpiredSignatureError:
            raise
        except InvalidAlgorithmError:
            raise InvalidTokenError("Invalid or disallowed algorithm")
        except Exception as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
        
        if verify and "jti" in payload:
            if self.blacklist.is_blacklisted(payload["jti"]):
                raise InvalidTokenError("Token has been revoked")
        
        return payload
    
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
        
        if not isinstance(header_value, str):
            return None
        
        parts = header_value.split()
        if len(parts) != 2:
            return None
        
        if parts[0] != self.config.token_prefix:
            return None
        
        token = parts[1].strip()
        if not token:
            return None
        
        return token
    
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
        if not token:
            raise InvalidTokenError("Token cannot be empty")
        
        payload = self.decode_token(token)
        
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        required_fields = ["user_id", "username", "roles"]
        for field in required_fields:
            if field not in payload:
                raise InvalidTokenError(f"Missing required field: {field}")
        
        if not isinstance(payload["roles"], list):
            raise InvalidTokenError("Roles must be a list")
        
        return UserContext(
            user_id=payload["user_id"],
            username=payload["username"],
            roles=payload["roles"],
            metadata=payload.get("metadata", {}),
            jti=payload.get("jti")
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
        if not token:
            raise InvalidTokenError("Token cannot be empty")
        
        payload = self.decode_token(token)
        
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")
        
        if "user_id" not in payload:
            raise InvalidTokenError("Missing user_id in token")
        
        return payload["user_id"]
    
    def refresh_access_token(self, refresh_token: str) -> Union[str, Dict[str, str]]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token or dict with access_token and new refresh_token if rotation enabled
            
        Raises:
            ExpiredSignatureError: If refresh token has expired
            InvalidTokenError: If refresh token is invalid
            ValueError: If user data provider not configured or user not found
        """
        if not refresh_token:
            raise InvalidTokenError("Refresh token cannot be empty")
        
        if not self.user_data_provider:
            raise ValueError("User data provider not configured")
        
        user_id = self.validate_refresh_token(refresh_token)
        
        user_data = self.user_data_provider.get_user_data(user_id)
        if not user_data:
            raise InvalidTokenError("User not found or invalid")
        
        if "username" not in user_data or "roles" not in user_data:
            raise ValueError("Invalid user data format")
        
        access_token = self.create_access_token(
            user_id=user_id,
            username=user_data["username"],
            roles=user_data["roles"],
            metadata=user_data.get("metadata")
        )
        
        if self.config.refresh_token_rotation:
            refresh_payload = self.decode_token(refresh_token, verify=False)
            if "jti" in refresh_payload:
                self.revoke_token(refresh_payload["jti"], refresh_payload.get("exp", 0))
            
            new_refresh_token = self.create_refresh_token(user_id)
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token
            }
        
        return access_token
    
    def revoke_token(self, jti: str, exp: int) -> None:
        """
        Revoke a token by adding it to blacklist.
        
        Args:
            jti: JWT ID to revoke
            exp: Token expiration timestamp
        """
        if not jti:
            raise ValueError("jti cannot be empty")
        
        self.blacklist.add(jti, exp)
    
    def cleanup_blacklist(self) -> None:
        """Remove expired tokens from blacklist."""
        self.blacklist.cleanup_expired()


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
                return Response(
                    401,
                    {
                        "error": "Token expired",
                        "code": "TOKEN_EXPIRED"
                    }
                )
            
            except InvalidTokenError as e:
                if optional:
                    return func(request, *args, **kwargs)
                return Response(401, {"error": f"Invalid token: {str(e)}"})
            
            except Exception as e:
                return Response(500, {"error": "Authentication error"})
        
        return wrapper
    return decorator


def require_roles(*required_roles: str, require_all: bool = False) -> Callable:
    """
    Decorator to enforce role-based access control.
    
    Args:
        required_roles: Required roles for access
        require_all: If True, user must have all roles. If False, any role is sufficient.
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: Request, *args: Any, **kwargs: Any) -> Union[Response, Any]:
            if not hasattr(request, 'user') or request.user is None:
                return Response(401, {"error": "Authentication required"})
            
            user_context: UserContext = request.user
            
            if not required_roles:
                return func(request, *args, **kwargs)
            
            has_access = False
            if require_all:
                has_access = user_context.has_all_roles(list(required_roles))
            else:
                has_access = user_context.has_any_role(list(required_roles))
            
            if not has_access:
                return Response(
                    403,
                    {
                        "error": "Insufficient permissions",
                        "required_roles": list(required_roles)
                    }
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class JWTMiddlewareWSGI:
    """WSGI middleware for JWT authentication."""
    
    def __init__(
        self, 
        app: Callable, 
        jwt_middleware: JWTMiddleware, 
        excluded_paths: Optional[List[str]] = None
    ):
        """
        Initialize WSGI middleware.
        
        Args:
            app: WSGI application
            jwt_middleware: JWT middleware instance
            excluded_paths: Paths to exclude from authentication
        """
        if not app:
            raise ValueError("app cannot be None")
        if not jwt_middleware:
            raise ValueError("jwt_middleware cannot be None")
        
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
        
        except InvalidTokenError:
            start_response('401 Unauthorized', [('Content-Type', 'application/json')])
            return [b'{"error": "Invalid token"}']
        
        except Exception:
            start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
            return [b'{"error": "Authentication error"}']


def create_token_pair(
    middleware: JWTMiddleware, 
    user_id: str, 
    username: str, 
    roles: List[str], 
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
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
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not middleware:
        raise ValueError("middleware cannot be None")
    if not user_id:
        raise ValueError("user_id cannot be empty")
    if not username:
        raise ValueError("username cannot be empty")
    if not isinstance(roles, list):
        raise ValueError("roles must be a list")
    
    access_token = middleware.create_access_token(user_id, username, roles, metadata)
    
    access_payload = middleware.decode_token(access_token, verify=False)
    access_jti = access_payload.get("jti")
    
    refresh_token = middleware.create_refresh_token(user_id, access_jti)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": middleware.config.access_token_expire_minutes * 60
    }