"""
Supabase Authentication Utilities

Provides backend authentication helpers for JWT token verification and user management.
Enhanced for V2 orchestrator with FastAPI dependency injection.
"""

import os
import jwt
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Request, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from core.common.logger import logger

def create_supabase_client() -> Client:
    """Create and return a Supabase client for backend operations."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")
    
    return create_client(url, key)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a Supabase JWT token.
    
    Args:
        token: The JWT token from the Authorization header
        
    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        # Get JWT secret from environment
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            raise ValueError("SUPABASE_JWT_SECRET environment variable is required")
        
        # Decode and verify the token
        payload = jwt.decode(
            token, 
            jwt_secret, 
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        return payload
    except jwt.InvalidTokenError as e:
        print(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        print(f"Error verifying JWT token: {e}")
        return None

def get_current_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from request Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID if authenticated, None if not authenticated
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt_token(token)
    
    if payload:
        return payload.get("sub")  # 'sub' contains the user ID in Supabase JWTs
    
    return None

def require_auth(f):
    """
    Decorator to require authentication for API endpoints.
    
    Usage:
        @app.get("/protected")
        @require_auth
        async def protected_endpoint(request: Request):
            user_id = get_current_user_id(request)
            return {"user_id": user_id}
    """
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # Find the request object in args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(status_code=500, detail="Request object not found")
        
        user_id = get_current_user_id(request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        return await f(*args, **kwargs)
    
    return decorated_function

def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Get full user information from a JWT token using Supabase client.
    
    Args:
        token: The JWT token
        
    Returns:
        User information if valid, None if invalid
    """
    payload = verify_jwt_token(token)
    if not payload:
        return None
    
    try:
        supabase = create_supabase_client()
        user_id = payload.get("sub")
        
        # Get user information from Supabase Auth
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            return {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "created_at": user_response.user.created_at,
                "last_sign_in_at": user_response.user.last_sign_in_at,
                "user_metadata": user_response.user.user_metadata
            }
    except Exception as e:
        print(f"Error getting user from token: {e}")
    
    return None

# V2 FastAPI Security Scheme
security = HTTPBearer()

class AuthenticatedUser:
    """User context extracted from Supabase JWT token for V2 orchestrator."""
    
    def __init__(self, user_id: str, email: str, claims: Dict[str, Any]):
        self.user_id = user_id
        self.email = email
        self.claims = claims
        self._profile = None
    
    async def load_profile(self):
        """Load user profile from database."""
        if self._profile is None:
            from core.services.user_service import UserService
            user_service = UserService()
            self._profile = await user_service.get_or_create_profile(self.user_id, self.email)
        return self._profile
    
    async def is_premium_user(self) -> bool:
        """Check if user has premium subscription."""
        profile = await self.load_profile()
        return profile.can_use_premium_features if profile else False
    
    async def can_use_indicator(self, indicator_name: str) -> bool:
        """Check if user can access specific indicator."""
        from core.services.indicator_service import IndicatorService
        return await IndicatorService.check_indicator_access(self.user_id, indicator_name)

async def get_current_user_v2(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuthenticatedUser:
    """
    FastAPI dependency to get current authenticated user for V2 orchestrator.
    
    Args:
        credentials: HTTP Bearer token from request
        
    Returns:
        AuthenticatedUser instance with user context
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify token and extract claims
    claims = verify_jwt_token(credentials.credentials)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Validate required claims
    user_id = claims.get("sub")
    email = claims.get("email")
    
    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token: missing required claims")
    
    # Create authenticated user context
    user = AuthenticatedUser(
        user_id=user_id,
        email=email,
        claims=claims
    )
    
    logger.bind(user_id=user.user_id).debug("User authenticated successfully (V2)")
    return user

async def require_premium_user_v2(
    current_user: AuthenticatedUser = Depends(get_current_user_v2)
) -> AuthenticatedUser:
    """
    FastAPI dependency to require premium subscription.
    """
    is_premium = await current_user.is_premium_user()
    if not is_premium:
        raise HTTPException(
            status_code=403, 
            detail="Premium subscription required for this feature"
        )
    return current_user

# Middleware helper for extracting user context (Legacy - kept for V1 compatibility)
class AuthMiddleware:
    """Middleware class for handling authentication in FastAPI apps."""
    
    @staticmethod
    def get_user_context(request: Request) -> Dict[str, Any]:
        """
        Get user context from request for use in business logic.
        
        Returns:
            Dictionary with user_id and is_authenticated flags
        """
        user_id = get_current_user_id(request)
        return {
            "user_id": user_id,
            "is_authenticated": user_id is not None
        }
    
    @staticmethod
    def require_user_id(request: Request) -> str:
        """
        Get user ID from request, raising HTTPException if not authenticated.
        
        Returns:
            User ID string
            
        Raises:
            HTTPException: If user is not authenticated
        """
        user_id = get_current_user_id(request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user_id

    @staticmethod
    async def authenticate_request(authorization: str) -> AuthenticatedUser:
        """
        Manually authenticate a request with Bearer token for V2.
        
        Args:
            authorization: Authorization header value
            
        Returns:
            AuthenticatedUser instance
            
        Raises:
            HTTPException: If authentication fails
        """
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ", 1)[1]
        claims = verify_jwt_token(token)
        
        if not claims:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = claims.get("sub")
        email = claims.get("email")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token claims")
        
        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            claims=claims
        )