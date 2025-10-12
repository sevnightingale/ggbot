"""
Welcome email template for new ggbots users.

Sent when a user first signs up or creates their account.
"""

from .base_template import render_email


def create_welcome_email(
    user_email: str,
    first_name: str = None
) -> tuple[str, str]:
    """
    Create welcome email HTML.

    Args:
        user_email: User's email address
        first_name: User's first name (optional)

    Returns:
        Tuple of (subject, html_content)
    """
    greeting = f"Hey {first_name}" if first_name else "Hey there"

    content = f"""
        <h2>Welcome to ggbots! 🚀</h2>
        <p>{greeting},</p>
        <p>
            Thanks for joining <strong>ggbots</strong> - the autonomous AI trading platform
            that combines advanced reasoning models with sophisticated execution engines.
        </p>

        <div class="stats">
            <p style="margin: 0 0 10px 0; font-weight: 600;">What's next?</p>
            <ol style="margin: 0; padding-left: 20px;">
                <li style="margin: 8px 0;">Configure your first trading bot in the dashboard</li>
                <li style="margin: 8px 0;">Customize your AI decision agent with your trading style</li>
                <li style="margin: 8px 0;">Start with paper trading to test strategies risk-free</li>
                <li style="margin: 8px 0;">Monitor real-time signals and market analysis</li>
            </ol>
        </div>

        <center>
            <a href="https://app.ggbots.ai/dashboard" class="button">
                Go to Dashboard
            </a>
        </center>

        <p style="margin-top: 25px;">
            <strong>Need help getting started?</strong><br>
            Check out our <a href="https://docs.ggbots.ai" style="color: #667eea;">documentation</a>
            or reach out to our support team.
        </p>

        <p style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px;">
            <strong>Pro tip:</strong> Start by exploring the extraction agent to see how we analyze
            140+ crypto pairs in real-time using technical indicators and market data.
        </p>
    """

    subject = "Welcome to ggbots - Let's Get Started!"

    return subject, render_email(content, subject)
