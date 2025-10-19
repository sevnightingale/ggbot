"""
Resend Email Service for ggbots

Handles email operations including:
- Contact syncing between Supabase and Resend
- Welcome email automation
- Notification emails (trades, signals, alerts)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import resend

from core.common.logger import logger
from core.common.db import get_db_connection


class ResendService:
    """Service for managing email contacts and sending automated emails via Resend."""

    def __init__(self):
        """Initialize Resend service with API key from environment."""
        self.api_key = os.getenv("RESEND_API_KEY")
        if not self.api_key:
            raise ValueError("RESEND_API_KEY not found in environment variables")

        resend.api_key = self.api_key
        self._log = logger.bind(component="resend_service")

        # Default audience ID (will be configurable)
        self.default_audience_id = os.getenv("RESEND_AUDIENCE_ID")

    # ===========================
    # Audience Management
    # ===========================

    def create_audience(self, name: str) -> Optional[str]:
        """
        Create a new audience in Resend.

        Args:
            name: Name for the audience (e.g., "ggbots Users")

        Returns:
            Audience ID if successful, None otherwise
        """
        try:
            params: resend.Audiences.CreateParams = {
                "name": name
            }
            result = resend.Audiences.create(params)
            audience_id = result.get("id")

            self._log.info(f"Created Resend audience: {name} (ID: {audience_id})")
            return audience_id

        except Exception as e:
            self._log.error(f"Failed to create audience '{name}': {e}")
            return None

    def get_audience(self, audience_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve audience details.

        Args:
            audience_id: Resend audience ID

        Returns:
            Audience data if found, None otherwise
        """
        try:
            result = resend.Audiences.get(audience_id)
            return result
        except Exception as e:
            self._log.error(f"Failed to get audience {audience_id}: {e}")
            return None

    def list_audiences(self) -> List[Dict[str, Any]]:
        """
        List all audiences.

        Returns:
            List of audience data dictionaries
        """
        try:
            result = resend.Audiences.list()
            return result.get("data", [])
        except Exception as e:
            self._log.error(f"Failed to list audiences: {e}")
            return []

    # ===========================
    # Contact Management
    # ===========================

    def add_contact(
        self,
        email: str,
        audience_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        unsubscribed: bool = False
    ) -> bool:
        """
        Add a contact to Resend audience.

        Args:
            email: Contact email address
            audience_id: Target audience ID (uses default if not provided)
            first_name: Contact first name
            last_name: Contact last name
            unsubscribed: Whether contact is unsubscribed

        Returns:
            True if successful, False otherwise
        """
        audience_id = audience_id or self.default_audience_id
        if not audience_id:
            self._log.error("No audience_id provided and no default set")
            return False

        try:
            params: resend.Contacts.CreateParams = {
                "email": email,
                "audience_id": audience_id,
                "unsubscribed": unsubscribed,
            }

            if first_name:
                params["first_name"] = first_name
            if last_name:
                params["last_name"] = last_name

            resend.Contacts.create(params)
            self._log.info(f"Added contact to Resend: {email}")
            return True

        except Exception as e:
            self._log.error(f"Failed to add contact {email}: {e}")
            return False

    def get_contact(
        self,
        email: str,
        audience_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve contact by email.

        Args:
            email: Contact email address
            audience_id: Audience ID to search in

        Returns:
            Contact data if found, None otherwise
        """
        audience_id = audience_id or self.default_audience_id
        if not audience_id:
            self._log.error("No audience_id provided and no default set")
            return None

        try:
            result = resend.Contacts.get(
                email=email,
                audience_id=audience_id
            )
            return result
        except Exception as e:
            # Contact not found is expected in some cases
            self._log.debug(f"Contact not found: {email} - {e}")
            return None

    def update_contact(
        self,
        email: str,
        audience_id: Optional[str] = None,
        unsubscribed: Optional[bool] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> bool:
        """
        Update an existing contact.

        Args:
            email: Contact email address
            audience_id: Audience ID
            unsubscribed: Update subscription status
            first_name: Update first name
            last_name: Update last name

        Returns:
            True if successful, False otherwise
        """
        audience_id = audience_id or self.default_audience_id
        if not audience_id:
            self._log.error("No audience_id provided and no default set")
            return False

        try:
            params: resend.Contacts.UpdateParams = {
                "email": email,
                "audience_id": audience_id,
            }

            if unsubscribed is not None:
                params["unsubscribed"] = unsubscribed
            if first_name:
                params["first_name"] = first_name
            if last_name:
                params["last_name"] = last_name

            resend.Contacts.update(params)
            self._log.info(f"Updated contact: {email}")
            return True

        except Exception as e:
            self._log.error(f"Failed to update contact {email}: {e}")
            return False

    def remove_contact(
        self,
        email: str,
        audience_id: Optional[str] = None
    ) -> bool:
        """
        Remove a contact from audience.

        Args:
            email: Contact email address
            audience_id: Audience ID

        Returns:
            True if successful, False otherwise
        """
        audience_id = audience_id or self.default_audience_id
        if not audience_id:
            self._log.error("No audience_id provided and no default set")
            return False

        try:
            resend.Contacts.remove(
                email=email,
                audience_id=audience_id
            )
            self._log.info(f"Removed contact: {email}")
            return True

        except Exception as e:
            self._log.error(f"Failed to remove contact {email}: {e}")
            return False

    def list_contacts(
        self,
        audience_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all contacts in an audience.

        Args:
            audience_id: Audience ID to list contacts from

        Returns:
            List of contact dictionaries
        """
        audience_id = audience_id or self.default_audience_id
        if not audience_id:
            self._log.error("No audience_id provided and no default set")
            return []

        try:
            result = resend.Contacts.list(audience_id=audience_id)
            return result.get("data", [])
        except Exception as e:
            self._log.error(f"Failed to list contacts: {e}")
            return []

    # ===========================
    # User Sync Operations
    # ===========================

    def sync_user_to_resend(
        self,
        user_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> bool:
        """
        Sync a single user from Supabase to Resend.
        Creates new contact if doesn't exist, updates if exists.

        Args:
            user_id: Supabase user ID
            email: User email
            first_name: User first name
            last_name: User last name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if contact exists
            existing = self.get_contact(email)

            if existing:
                # Update existing contact
                return self.update_contact(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
            else:
                # Create new contact
                return self.add_contact(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )

        except Exception as e:
            self._log.error(f"Failed to sync user {user_id} to Resend: {e}")
            return False

    def sync_all_users_to_resend(self) -> Dict[str, int]:
        """
        Sync all active users from Supabase to Resend.

        Returns:
            Dictionary with sync statistics (success_count, error_count, total)
        """
        stats = {
            "success_count": 0,
            "error_count": 0,
            "total": 0
        }

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get all active users
                    cur.execute("""
                        SELECT id, email
                        FROM auth.users
                        WHERE deleted_at IS NULL
                        AND email IS NOT NULL
                    """)

                    users = cur.fetchall()
                    stats["total"] = len(users)

                    self._log.info(f"Starting sync of {stats['total']} users to Resend")

                    for user_id, email in users:
                        success = self.sync_user_to_resend(
                            user_id=str(user_id),
                            email=email
                        )

                        if success:
                            stats["success_count"] += 1
                        else:
                            stats["error_count"] += 1

            self._log.info(
                f"Sync complete: {stats['success_count']}/{stats['total']} successful, "
                f"{stats['error_count']} errors"
            )

            return stats

        except Exception as e:
            self._log.error(f"Failed to sync users: {e}")
            return stats

    # ===========================
    # Email Sending
    # ===========================

    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        from_email: str = "noreply@message.ggbots.ai"
    ) -> bool:
        """
        Send an email via Resend.

        Args:
            to: Recipient email
            subject: Email subject
            html: HTML email content
            from_email: Sender email (must be verified domain)

        Returns:
            True if successful, False otherwise
        """
        try:
            params = {
                "from": from_email,
                "to": [to],
                "subject": subject,
                "html": html
            }

            resend.Emails.send(params)
            self._log.info(f"Sent email to {to}: {subject}")
            return True

        except Exception as e:
            self._log.error(f"Failed to send email to {to}: {e}")
            return False

    # ===========================
    # Template-Based Email Methods
    # ===========================

    def send_welcome_email(
        self,
        user_email: str,
        first_name: Optional[str] = None
    ) -> bool:
        """
        Send welcome email to new user.

        Args:
            user_email: User's email address
            first_name: User's first name (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            from core.email_templates.welcome_email import create_welcome_email

            subject, html = create_welcome_email(user_email, first_name)
            return self.send_email(user_email, subject, html)

        except Exception as e:
            self._log.error(f"Failed to send welcome email to {user_email}: {e}")
            return False

    def send_trade_notification(
        self,
        user_email: str,
        trade_data: Dict[str, Any]
    ) -> bool:
        """
        Send trade execution notification.

        Args:
            user_email: User's email address
            trade_data: Dictionary with trade details (symbol, side, size, price, confidence, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            from core.email_templates.trade_notification import create_trade_notification_email

            subject, html = create_trade_notification_email(trade_data)
            return self.send_email(user_email, subject, html)

        except Exception as e:
            self._log.error(f"Failed to send trade notification to {user_email}: {e}")
            return False

    def send_signal_alert(
        self,
        user_email: str,
        signal_data: Dict[str, Any]
    ) -> bool:
        """
        Send signal alert notification.

        Args:
            user_email: User's email address
            signal_data: Dictionary with signal details (symbol, direction, confidence, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            from core.email_templates.signal_alert import create_signal_alert_email

            subject, html = create_signal_alert_email(signal_data)
            return self.send_email(user_email, subject, html)

        except Exception as e:
            self._log.error(f"Failed to send signal alert to {user_email}: {e}")
            return False

    def send_generic_notification(
        self,
        user_email: str,
        title: str,
        message: str,
        action_text: Optional[str] = None,
        action_url: Optional[str] = None,
        notification_type: str = "info"
    ) -> bool:
        """
        Send generic notification email.

        Args:
            user_email: User's email address
            title: Notification title
            message: Notification message
            action_text: Optional button text
            action_url: Optional button URL
            notification_type: Type ("info", "success", "warning", "error")

        Returns:
            True if successful, False otherwise
        """
        try:
            from core.email_templates.generic_notification import create_generic_notification_email

            subject, html = create_generic_notification_email(
                title, message, action_text, action_url, notification_type
            )
            return self.send_email(user_email, subject, html)

        except Exception as e:
            self._log.error(f"Failed to send notification to {user_email}: {e}")
            return False


# Convenience instance
resend_service = ResendService()
