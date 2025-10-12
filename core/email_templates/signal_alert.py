"""
Signal alert email template.

Sent when a high-confidence trading signal is detected.
"""

from .base_template import render_email
from typing import Dict, Any, List


def create_signal_alert_email(
    signal_data: Dict[str, Any]
) -> tuple[str, str]:
    """
    Create signal alert email HTML.

    Args:
        signal_data: Dictionary containing signal details
            - symbol: Trading pair
            - direction: "LONG" or "SHORT"
            - confidence: AI confidence score (0-1)
            - indicators: List of supporting indicators
            - reasoning: AI reasoning summary
            - timestamp: Signal timestamp

    Returns:
        Tuple of (subject, html_content)
    """
    symbol = signal_data.get("symbol", "N/A")
    direction = signal_data.get("direction", "N/A")
    confidence = signal_data.get("confidence", 0)
    indicators = signal_data.get("indicators", [])
    reasoning = signal_data.get("reasoning", "AI detected favorable market conditions.")

    # Format confidence
    confidence_pct = confidence * 100 if confidence else 0
    confidence_badge_class = (
        "badge-success" if confidence_pct >= 75
        else "badge-warning" if confidence_pct >= 60
        else "badge-info"
    )

    # Direction badge
    direction_badge_class = "badge-success" if direction.upper() == "LONG" else "badge-danger"

    # Format indicators list
    indicators_html = ""
    if indicators:
        indicators_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for indicator in indicators:
            indicators_html += f"<li style='margin: 5px 0;'>{indicator}</li>"
        indicators_html += "</ul>"

    content = f"""
        <h2>High-Confidence Signal Detected 🎯</h2>
        <p>
            Your AI agent has identified a trading opportunity with strong supporting indicators.
        </p>

        <div class="stats">
            <div class="stats-row">
                <span class="stats-label">Symbol</span>
                <span class="stats-value">{symbol}</span>
            </div>
            <div class="stats-row">
                <span class="stats-label">Direction</span>
                <span class="badge {direction_badge_class}">{direction}</span>
            </div>
            <div class="stats-row">
                <span class="stats-label">Confidence</span>
                <span class="badge {confidence_badge_class}">{confidence_pct:.1f}%</span>
            </div>
        </div>

        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #667eea;">
            <p style="margin: 0 0 10px 0; font-weight: 600; color: #495057;">AI Reasoning:</p>
            <p style="margin: 0; color: #6c757d;">{reasoning}</p>
        </div>

        {f'''
        <div style="margin: 20px 0;">
            <p style="font-weight: 600; margin: 0 0 10px 0;">Supporting Indicators:</p>
            {indicators_html}
        </div>
        ''' if indicators else ''}

        <center>
            <a href="https://app.ggbots.ai/dashboard" class="button">
                Review Signal
            </a>
        </center>

        <p style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px;">
            <strong>Note:</strong> Signals are informational and do not guarantee results.
            If auto-trading is enabled, your bot may act on this signal based on your configuration.
        </p>
    """

    subject = f"Signal Alert: {direction} {symbol} ({confidence_pct:.0f}% confidence) - ggbots"

    return subject, render_email(content, subject)
