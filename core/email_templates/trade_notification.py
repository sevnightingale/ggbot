"""
Trade execution notification email template.

Sent when a trade is executed by the user's bot.
"""

from .base_template import render_email
from typing import Dict, Any


def create_trade_notification_email(
    trade_data: Dict[str, Any]
) -> tuple[str, str]:
    """
    Create trade notification email HTML.

    Args:
        trade_data: Dictionary containing trade details
            - symbol: Trading pair (e.g., "BTC/USD")
            - side: "BUY" or "SELL"
            - size: Position size
            - price: Execution price
            - confidence: AI confidence score (0-1)
            - timestamp: Trade timestamp
            - config_name: Bot configuration name

    Returns:
        Tuple of (subject, html_content)
    """
    symbol = trade_data.get("symbol", "N/A")
    side = trade_data.get("side", "N/A")
    size = trade_data.get("size", 0)
    price = trade_data.get("price", 0)
    confidence = trade_data.get("confidence", 0)
    config_name = trade_data.get("config_name", "Your Bot")

    # Determine badge style based on side
    side_badge_class = "badge-success" if side.upper() == "BUY" else "badge-danger"

    # Format confidence as percentage
    confidence_pct = confidence * 100 if confidence else 0
    confidence_badge_class = (
        "badge-success" if confidence_pct >= 75
        else "badge-warning" if confidence_pct >= 60
        else "badge-info"
    )

    content = f"""
        <h2>Trade Executed 📊</h2>
        <p>
            <strong>{config_name}</strong> just executed a trade based on AI analysis.
        </p>

        <div class="stats">
            <div class="stats-row">
                <span class="stats-label">Symbol</span>
                <span class="stats-value">{symbol}</span>
            </div>
            <div class="stats-row">
                <span class="stats-label">Side</span>
                <span class="badge {side_badge_class}">{side}</span>
            </div>
            <div class="stats-row">
                <span class="stats-label">Size</span>
                <span class="stats-value">{size}</span>
            </div>
            <div class="stats-row">
                <span class="stats-label">Price</span>
                <span class="stats-value">${price:,.2f}</span>
            </div>
            <div class="stats-row">
                <span class="stats-label">AI Confidence</span>
                <span class="badge {confidence_badge_class}">{confidence_pct:.1f}%</span>
            </div>
        </div>

        <center>
            <a href="https://app.ggbots.ai/dashboard" class="button">
                View Position
            </a>
        </center>

        <p style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px;">
            <strong>Note:</strong> This trade was executed automatically based on your bot's configuration
            and AI decision engine analysis. You can adjust settings or pause trading anytime in your dashboard.
        </p>
    """

    subject = f"Trade Alert: {side} {symbol} - ggbots"

    return subject, render_email(content, subject)
