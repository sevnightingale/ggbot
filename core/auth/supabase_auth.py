"""
Supabase Authentication Utilities

Provides backend authentication helpers for JWT token verification and user management.
"""

import os
import jwt
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Request
from supabase import create_client, Client

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

# Middleware helper for extracting user context
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