"""
Base HTML email template for ggbots.

Provides a consistent, responsive email design with branding.
"""

from typing import Dict, Any


BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin: 15px 0;
        }}
        .button:hover {{
            background: #5568d3;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .stats-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .stats-row:last-child {{
            border-bottom: none;
        }}
        .stats-label {{
            color: #6c757d;
            font-size: 14px;
        }}
        .stats-value {{
            font-weight: 600;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ggbots.ai</h1>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p><strong>ggbots</strong> - Autonomous AI Trading Platform</p>
            <p>
                <a href="{frontend_url}/settings" style="color: #667eea; text-decoration: none;">Manage Preferences</a> |
                <a href="{frontend_url}/dashboard" style="color: #667eea; text-decoration: none;">View Dashboard</a>
            </p>
            <p style="margin-top: 15px; color: #adb5bd;">
                You're receiving this email because you have an active account at ggbots.ai.<br>
                © 2025 ggbots. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""


def render_email(content: str, subject: str, frontend_url: str = "https://app.ggbots.ai") -> str:
    """
    Render email content with base template.

    Args:
        content: HTML content to insert into template
        subject: Email subject (also used in title)
        frontend_url: Base URL for frontend links

    Returns:
        Complete HTML email string
    """
    return BASE_TEMPLATE.format(
        subject=subject,
        content=content,
        frontend_url=frontend_url
    )
