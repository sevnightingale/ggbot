"""
User Service for V2 Orchestrator

Handles user profile management and subscription-related operations.
"""

from typing import Optional
from datetime import datetime
from core.common.db import get_db_connection
from core.common.logger import logger
from core.domain import UserProfile, SubscriptionTier, SubscriptionStatus


class UserService:
    """Service for managing user profiles and subscriptions."""
    
    def __init__(self):
        self._log = logger.bind(component="user_service")
    
    async def get_or_create_profile(
        self,
        user_id: str,
        email: str
    ) -> UserProfile:
        """
        Get existing user profile or create a new one.
        
        Args:
            user_id: User ID from Supabase auth
            email: User email from JWT token
            
        Returns:
            UserProfile instance
        """
        try:
            # Try to get existing profile
            profile = await self.get_profile(user_id)
            if profile:
                return profile
            
            # Create new profile with free tier
            profile = UserProfile.create_free_user(user_id)
            
            # Store in database
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_profiles 
                        (user_id, subscription_tier, subscription_status, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (user_id) DO NOTHING
                    """, (
                        user_id,
                        profile.subscription_tier.value,
                        profile.subscription_status.value
                    ))
                conn.commit()
            
            self._log.info(f"Created new user profile for {user_id}")

            # Send welcome email and sync to Resend (async, don't block on failure)
            try:
                from core.services.resend_service import resend_service

                # Sync user to Resend audience
                resend_service.sync_user_to_resend(user_id, email)

                # Send welcome email
                resend_service.send_welcome_email(email)

                self._log.info(f"Sent welcome email to {email}")
            except Exception as email_error:
                # Don't fail user creation if email fails
                self._log.warning(f"Failed to send welcome email to {email}: {email_error}")

            return profile
            
        except Exception as e:
            self._log.error(f"Failed to get/create profile for {user_id}: {e}")
            # Return default free user profile as fallback
            return UserProfile.create_free_user(user_id)
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID with retry logic for SSL errors.

        Args:
            user_id: User ID

        Returns:
            UserProfile instance if found, None otherwise
        """
        import time

        # Retry up to 3 times for SSL errors
        max_retries = 3
        retry_delay = 0.1  # 100ms between retries

        for attempt in range(max_retries):
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT subscription_tier, subscription_status, subscription_expires_at,
                                   stripe_customer_id, stripe_subscription_id,
                                   telegram_user_id, telegram_username, telegram_chat_id,
                                   monthly_signal_count, paid_data_points, created_at, updated_at
                            FROM user_profiles
                            WHERE user_id = %s
                        """, (user_id,))

                        result = cur.fetchone()
                        if not result:
                            return None

                        return UserProfile(
                            user_id=user_id,
                            subscription_tier=SubscriptionTier(result[0]),
                            subscription_status=SubscriptionStatus(result[1]),
                            subscription_expires_at=result[2],
                            stripe_customer_id=result[3],
                            stripe_subscription_id=result[4],
                            telegram_user_id=result[5],
                            telegram_username=result[6],
                            telegram_chat_id=result[7],
                            monthly_signal_count=result[8] or 0,
                            paid_data_points=result[9] or [],
                            created_at=result[10],
                            updated_at=result[11]
                        )

            except Exception as e:
                # Check if it's an SSL error
                error_msg = str(e)
                is_ssl_error = 'SSL' in error_msg or 'connection' in error_msg.lower()

                if is_ssl_error and attempt < max_retries - 1:
                    self._log.warning(f"SSL error on attempt {attempt + 1}/{max_retries} for {user_id}, retrying...")
                    time.sleep(retry_delay)
                    continue
                else:
                    self._log.error(f"Failed to get profile for {user_id}: {e}")
                    return None

        return None
    
    async def update_profile(self, profile: UserProfile) -> bool:
        """
        Update user profile in database.
        
        Args:
            profile: UserProfile instance to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_profiles
                        SET subscription_tier = %s,
                            subscription_status = %s,
                            subscription_expires_at = %s,
                            stripe_customer_id = %s,
                            stripe_subscription_id = %s,
                            telegram_user_id = %s,
                            telegram_username = %s,
                            telegram_chat_id = %s,
                            monthly_signal_count = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (
                        profile.subscription_tier.value,
                        profile.subscription_status.value,
                        profile.subscription_expires_at,
                        profile.stripe_customer_id,
                        profile.stripe_subscription_id,
                        profile.telegram_user_id,
                        profile.telegram_username,
                        profile.telegram_chat_id,
                        profile.monthly_signal_count,
                        profile.user_id
                    ))
                    
                    success = cur.rowcount > 0
                    if success:
                        conn.commit()
                        self._log.info(f"Updated profile for user {profile.user_id}")
                    
                    return success
                    
        except Exception as e:
            self._log.error(f"Failed to update profile for {profile.user_id}: {e}")
            return False


# Convenience instance
user_service = UserService()