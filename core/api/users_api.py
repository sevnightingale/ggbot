"""
Demo User Management API
Handles email signup and UUID generation for hackathon demo
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime
from psycopg2.extras import RealDictCursor
from core.common.db import get_db_connection
from core.common.logger import logger

router = APIRouter()

class DemoSignupRequest(BaseModel):
    email: EmailStr

class DemoSignupResponse(BaseModel):
    user_id: str
    email: str
    is_new_user: bool
    message: str

@router.post("/api/users/demo-signup", response_model=DemoSignupResponse)
async def demo_signup(request: DemoSignupRequest):
    """
    Create or retrieve demo user by email
    Returns UUID for existing users or creates new user
    """
    try:
        email = request.email.lower().strip()
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if user already exists
                cur.execute(
                    "SELECT user_id, email FROM users WHERE email = %s",
                    (email,)
                )
                existing_user = cur.fetchone()
                
                if existing_user:
                    logger.info(f"Returning existing demo user: {email}")
                    return DemoSignupResponse(
                        user_id=str(existing_user['user_id']),
                        email=existing_user['email'],
                        is_new_user=False,
                        message="Welcome back! Your trading account has been restored."
                    )
                
                # Create new user
                new_user_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO users (user_id, email, demo_access, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (new_user_id, email, True, datetime.now())
                )
                conn.commit()
                
                logger.info(f"Created new demo user: {email} -> {new_user_id}")
                
                return DemoSignupResponse(
                    user_id=new_user_id,
                    email=email,
                    is_new_user=True,
                    message="Welcome to ggBot! Your demo account has been created."
                )
                
    except psycopg2.IntegrityError as e:
        logger.error(f"Database integrity error during signup: {e}")
        raise HTTPException(
            status_code=400, 
            detail="Email already registered or database constraint violation"
        )
    except Exception as e:
        logger.error(f"Error during demo signup: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create demo account. Please try again."
        )

@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user information by UUID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT user_id, email, demo_access, created_at FROM users WHERE user_id = %s",
                    (user_id,)
                )
                user = cur.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {
                    "user_id": str(user['user_id']),
                    "email": user['email'],
                    "demo_access": user['demo_access'],
                    "created_at": user['created_at'].isoformat() if user['created_at'] else None
                }
                
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user")

# No main section needed for router