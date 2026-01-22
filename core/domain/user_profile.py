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
    """Available subscription tiers for the business model."""
    FREE = "free"                # Free tier: Can browse, cannot activate bots
    PREPAID = "prepaid"          # Prepaid tier: Credit pack users, hard-block on depletion
    USAGE_BASED = "usage_based"  # Usage tier: Pay per LLM call, metered billing
    PRO = "pro"                  # Premium tier: $29/month + usage + agent access


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
    def is_pro_tier(self) -> bool:
        """Check if user has pro subscription."""
        return self.subscription_tier == SubscriptionTier.PRO

    @property
    def is_prepaid_tier(self) -> bool:
        """Check if user is on prepaid (credit pack) tier."""
        return self.subscription_tier == SubscriptionTier.PREPAID

    @property
    def requires_credit_check(self) -> bool:
        """
        Check if user requires hard credit balance check before LLM calls.

        Prepaid users MUST have credits available before any LLM call.
        Usage-based users are billed for overage, so no hard check needed.
        """
        return self.subscription_tier == SubscriptionTier.PREPAID

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

    # =========================================================================
    # SIMPLIFIED PERMISSION MODEL
    # Single source of truth: can_activate_bots
    # All paid features available to USAGE_BASED and PRO tiers
    # =========================================================================

    @property
    def can_activate_bots(self) -> bool:
        """
        MASTER PERMISSION: Check if user can activate/run bots.

        This is the single source of truth for all paid features.
        True for PREPAID, USAGE_BASED, and PRO tiers with active subscriptions.
        """
        return (
            self.subscription_tier in [
                SubscriptionTier.PREPAID,
                SubscriptionTier.USAGE_BASED,
                SubscriptionTier.PRO
            ] and
            self.has_active_subscription and
            not self.subscription_expired
        )

    @property
    def can_use_agents(self) -> bool:
        """Check if user can create and use agents (PRO tier only)."""
        return self.subscription_tier == SubscriptionTier.PRO and self.can_activate_bots

    # =========================================================================
    # LEGACY PROPERTIES - All delegate to can_activate_bots
    # Kept for backward compatibility, will be phased out
    # =========================================================================

    @property
    def is_premium_user(self) -> bool:
        """DEPRECATED: Use can_activate_bots instead."""
        return self.can_activate_bots

    @property
    def can_use_premium_features(self) -> bool:
        """DEPRECATED: Use can_activate_bots instead."""
        return self.can_activate_bots

    @property
    def requires_own_llm_keys(self) -> bool:
        """DEPRECATED: Platform provides LLM keys for all paid users."""
        return not self.can_activate_bots

    @property
    def can_publish_telegram_signals(self) -> bool:
        """DEPRECATED: Use can_activate_bots instead."""
        return self.can_activate_bots

    @property
    def can_use_signal_validation(self) -> bool:
        """DEPRECATED: Use can_activate_bots instead."""
        return self.can_activate_bots

    @property
    def can_use_live_trading(self) -> bool:
        """DEPRECATED: Use can_activate_bots instead."""
        return self.can_activate_bots

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
    
    def upgrade_to_pro_tier(
        self,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        expires_at: Optional[datetime] = None
    ) -> None:
        """Upgrade user to Pro tier with Stripe integration."""
        self.subscription_tier = SubscriptionTier.PRO
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