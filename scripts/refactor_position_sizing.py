#!/usr/bin/env python3
"""
Automated refactoring script for position sizing simplification.
This script updates all backend files to remove old position sizing methods
and use the new simplified max_margin_percent approach.
"""

import re
from pathlib import Path

def update_paper_service():
    """Remove max_positions check from paper trading service."""
    file_path = Path("/home/sev/ggbot/trading/paper/supabase_service.py")
    content = file_path.read_text()

    # Remove PositionSizingMethod from imports (line 22)
    content = re.sub(
        r'from core\.config import config_repo, BotConfig, PositionSizingMethod',
        r'from core.config import config_repo, BotConfig',
        content
    )

    # Remove the sizing_method line (line 126)
    content = re.sub(
        r'sizing_method = config\.trading\.position_sizing\.method\.value\s*\n',
        '',
        content
    )

    # Remove the entire max_positions check block (lines 142-151)
    max_pos_pattern = r'max_positions = config\.trading\.risk_management\.max_positions.*?return False, f"Maximum positions limit reached.*?\)"\s*\n'
    content = re.sub(max_pos_pattern, '', content, flags=re.DOTALL)

    file_path.write_text(content)
    print(f"✅ Updated {file_path}")

def update_symphony_service():
    """Simplify _calculate_weight in Symphony service."""
    file_path = Path("/home/sev/ggbot/trading/live/symphony_service.py")
    content = file_path.read_text()

    # Remove PositionSizingMethod import
    content = re.sub(
        r'from core\.config\.models import PositionSizingMethod\s*\n',
        '',
        content
    )

    # Replace the entire _calculate_weight method
    old_method = r'def _calculate_weight\(self, config, confidence: float\) -> float:.*?return weight'
    new_method = '''def _calculate_weight(self, config, confidence: float) -> float:
        """Calculate position weight: confidence × max_margin_percent (clamped 0.1-100%)"""
        sizing = config.trading.get("position_sizing", {})
        max_pct = sizing.get("max_margin_percent", 10.0)
        weight = confidence * max_pct

        # Clamp to 0.1-100 range
        weight = max(0.1, min(weight, 100.0))

        self._log.info(f"Calculated weight: {weight:.1f}% (confidence={confidence:.3f}, max_margin={max_pct}%)")
        return weight'''

    content = re.sub(old_method, new_method, content, flags=re.DOTALL)

    file_path.write_text(content)
    print(f"✅ Updated {file_path}")

def update_aster_service():
    """Simplify _calculate_weight in Aster service."""
    file_path = Path("/home/sev/ggbot/trading/live/aster_service_v3.py")
    content = file_path.read_text()

    # Remove PositionSizingMethod from imports
    content = re.sub(
        r', PositionSizingMethod',
        '',
        content
    )

    # Find and simplify the margin calculation in _calculate_weight
    # Replace the complex sizing_method logic with simple max_margin_percent
    old_calc = r'sizing_method = sizing_config\.get\(\'method\', \'fixed_usd\'\).*?margin = confidence \* 0\.10 \* total_equity'
    new_calc = '''# Calculate margin: confidence × max_margin_percent × equity
        max_pct = sizing_config.get('max_margin_percent', 10.0) / 100.0
        margin = confidence * max_pct * total_equity'''

    content = re.sub(old_calc, new_calc, content, flags=re.DOTALL)

    file_path.write_text(content)
    print(f"✅ Updated {file_path}")

def update_config_service():
    """Update default configs in config_service.py."""
    file_path = Path("/home/sev/ggbot/core/services/config_service.py")
    content = file_path.read_text()

    # Replace position_sizing section
    old_pos_sizing = r'"position_sizing": \{[^}]*"max_position_percent": [0-9.]+\s*\}'
    new_pos_sizing = '"position_sizing": {\n                "max_margin_percent": 20.0\n            }'
    content = re.sub(old_pos_sizing, new_pos_sizing, content)

    # Replace risk_management section
    old_risk_mgmt = r'"risk_management": \{[^}]*"max_daily_loss_usd": [0-9]+\s*\}'
    new_risk_mgmt = '"risk_management": {\n                "default_stop_loss_percent": 5.0,\n                "default_take_profit_percent": 10.0\n            }'
    content = re.sub(old_risk_mgmt, new_risk_mgmt, content)

    file_path.write_text(content)
    print(f"✅ Updated {file_path}")

if __name__ == "__main__":
    print("🚀 Starting position sizing refactor...")
    print()

    try:
        update_paper_service()
        update_symphony_service()
        update_aster_service()
        update_config_service()
        print()
        print("✅ All backend services updated successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
