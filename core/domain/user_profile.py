"""
User Profile Domain Model

Represents user subscription management and business model integration.
Extends Supabase auth.users with subscription tiers and premium features.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class SubscriptionTier(Enum):
    """Available subscription tiers for the freemium business model."""
    FREE = "free"      # Free tier: paper trading with user's LLM keys
    GGBASE = "ggbase"  # Paid tier: hosted LLM + Telegram signal publishing


class SubscriptionStatus(Enum):
    """Subscription status for managing billing and access."""
    ACTIVE = "active"        # Subscription active and in good standing
    CANCELLED = "cancelled"  # Subscription cancelled, access until expiry
    PAST_DUE = "past_due"   # Payment failed, limited access


@dataclass
class UserProfile:
    """
    User profile entity extending Supabase authentication with business model.
    
    Manages subscription tiers, Stripe integration, and premium feature access.
    """
    
    user_id: str  # References Supabase auth.users(id)
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Optional subscription management
    subscription_expires_at: Optional[datetime] = None
    
    # Stripe integration
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Telegram integration  
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_chat_id: Optional[int] = None
    
    # Usage tracking
    monthly_signal_count: int = 0
    
    # Premium data point access
    paid_data_points: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate user profile after initialization."""
        if not self.user_id:
            raise ValueError("user_id is required")
    
    @property
    def is_free_tier(self) -> bool:
        """Check if user is on free tier."""
        return self.subscription_tier == SubscriptionTier.FREE
    
    @property
    def is_ggbase_tier(self) -> bool:
        """Check if user has ggbase subscription."""
        return self.subscription_tier == SubscriptionTier.GGBASE
    
    @property
    def is_premium_user(self) -> bool:
        """Check if user has any premium subscription."""
        return self.subscription_tier in [SubscriptionTier.GGBASE]
    
    @property
    def has_active_subscription(self) -> bool:
        """Check if user has active subscription."""
        return (
            self.subscription_status == SubscriptionStatus.ACTIVE and
            (self.subscription_expires_at is None or
             self.subscription_expires_at > datetime.now(timezone.utc))
        )
    
    @property
    def subscription_expired(self) -> bool:
        """Check if subscription has expired."""
        return (
            self.subscription_expires_at is not None and
            self.subscription_expires_at <= datetime.now(timezone.utc)
        )
    
    @property
    def can_use_premium_features(self) -> bool:
        """Check if user can access premium features."""
        return (
            self.is_premium_user and 
            self.has_active_subscription and
            not self.subscription_expired
        )
    
    @property
    def requires_own_llm_keys(self) -> bool:
        """Check if user must provide their own LLM API keys."""
        return self.is_free_tier or not self.can_use_premium_features
    
    @property
    def can_publish_telegram_signals(self) -> bool:
        """Check if user can publish signals to Telegram."""
        return self.can_use_premium_features
    
    @property
    def can_use_signal_validation(self) -> bool:
        """Check if user can use signal validation mode."""
        return self.can_use_premium_features

    @property
    def can_use_live_trading(self) -> bool:
        """Check if user can use Symphony live trading."""
        return self.can_use_premium_features

    def has_data_point_access(self, data_point_name: str) -> bool:
        """Check if user has access to specific premium data point."""
        return data_point_name in self.paid_data_points
    
    def grant_data_point_access(self, data_point_name: str) -> None:
        """Grant access to premium data point."""
        if data_point_name not in self.paid_data_points:
            self.paid_data_points.append(data_point_name)
            self.updated_at = datetime.now()
    
    def revoke_data_point_access(self, data_point_name: str) -> None:
        """Revoke access to premium data point."""
        if data_point_name in self.paid_data_points:
            self.paid_data_points.remove(data_point_name)
            self.updated_at = datetime.now()
    
    def grant_multiple_data_points(self, data_point_names: list[str]) -> None:
        """Grant access to multiple premium data points."""
        for name in data_point_names:
            if name not in self.paid_data_points:
                self.paid_data_points.append(name)
        self.updated_at = datetime.now()
    
    @property
    def has_telegram_integration(self) -> bool:
        """Check if user has Telegram integration configured."""
        return self.telegram_user_id is not None
    
    @property
    def has_stripe_integration(self) -> bool:
        """Check if user has Stripe customer record."""
        return self.stripe_customer_id is not None
    
    def upgrade_to_signals_tier(
        self,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        expires_at: Optional[datetime] = None
    ) -> None:
        """Upgrade user to signals tier with Stripe integration."""
        self.subscription_tier = SubscriptionTier.GGBASE
        self.subscription_status = SubscriptionStatus.ACTIVE
        self.stripe_customer_id = stripe_customer_id
        self.stripe_subscription_id = stripe_subscription_id
        self.subscription_expires_at = expires_at
        self.updated_at = datetime.now()
    
    def cancel_subscription(self, expires_at: datetime) -> None:
        """Cancel subscription with access until expiry."""
        self.subscription_status = SubscriptionStatus.CANCELLED
        self.subscription_expires_at = expires_at
        self.updated_at = datetime.now()
    
    def mark_payment_past_due(self) -> None:
        """Mark subscription as past due (failed payment)."""
        self.subscription_status = SubscriptionStatus.PAST_DUE
        self.updated_at = datetime.now()
    
    def reactivate_subscription(self) -> None:
        """Reactivate subscription after payment resolution."""
        self.subscription_status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def set_telegram_integration(
        self,
        telegram_user_id: int,
        telegram_username: Optional[str] = None,
        telegram_chat_id: Optional[int] = None
    ) -> None:
        """Configure Telegram integration for signal publishing."""
        self.telegram_user_id = telegram_user_id
        self.telegram_username = telegram_username
        self.telegram_chat_id = telegram_chat_id
        self.updated_at = datetime.now()
    
    def increment_signal_count(self, count: int = 1) -> None:
        """Increment monthly signal usage counter."""
        self.monthly_signal_count += count
        self.updated_at = datetime.now()
    
    def reset_monthly_counters(self) -> None:
        """Reset monthly usage counters (called at month rollover)."""
        self.monthly_signal_count = 0
        self.updated_at = datetime.now()
    
    @classmethod
    def create_free_user(cls, user_id: str) -> 'UserProfile':
        """Factory method to create new free tier user."""
        return cls(
            user_id=user_id,
            subscription_tier=SubscriptionTier.FREE,
            subscription_status=SubscriptionStatus.ACTIVE
        )