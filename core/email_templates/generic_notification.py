"""
Generic notification email template.

Used for various system notifications and updates.
"""

from .base_template import render_email
from typing import Optional


def create_generic_notification_email(
    title: str,
    message: str,
    action_text: Optional[str] = None,
    action_url: Optional[str] = None,
    notification_type: str = "info"
) -> tuple[str, str]:
    """
    Create generic notification email HTML.

    Args:
        title: Notification title/heading
        message: Main notification message (can include HTML)
        action_text: Optional button text
        action_url: Optional button URL
        notification_type: Type of notification ("info", "success", "warning", "error")

    Returns:
        Tuple of (subject, html_content)
    """
    # Map notification type to emoji
    emoji_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }

    emoji = emoji_map.get(notification_type, "📬")

    # Create action button if provided
    action_button = ""
    if action_text and action_url:
        action_button = f"""
        <center>
            <a href="{action_url}" class="button">
                {action_text}
            </a>
        </center>
        """

    content = f"""
        <h2>{title} {emoji}</h2>
        <div style="margin: 20px 0;">
            {message}
        </div>

        {action_button}

        <p style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px;">
            If you have any questions or need assistance, please don't hesitate to contact our support team.
        </p>
    """

    subject = title

    return subject, render_email(content, subject)
