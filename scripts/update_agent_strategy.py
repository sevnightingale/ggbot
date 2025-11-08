#!/usr/bin/env python3
"""
Update agent strategy in database
"""
import sys
sys.path.insert(0, '/home/sev/ggbot')

import json
from core.common.db import get_db_connection
from datetime import datetime, timezone

config_id = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'

# Read new strategy from NOTE.md
with open('/home/sev/ggbot/NOTE.md', 'r') as f:
    new_strategy = f.read()

# Update database
with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Get current config
        cur.execute("""
            SELECT config_data FROM configurations WHERE config_id = %s
        """, (config_id,))

        result = cur.fetchone()
        if not result:
            print(f"ERROR: Config {config_id} not found")
            sys.exit(1)

        config_data = result[0]

        # Get current version
        current_version = config_data.get('agent_strategy', {}).get('version', 4)
        new_version = current_version + 1

        # Update strategy
        if 'agent_strategy' not in config_data:
            config_data['agent_strategy'] = {}

        config_data['agent_strategy']['content'] = new_strategy
        config_data['agent_strategy']['version'] = new_version
        config_data['agent_strategy']['last_updated_at'] = datetime.now(timezone.utc).isoformat()
        config_data['agent_strategy']['last_updated_by'] = 'user'

        # Save (convert dict to JSON)
        cur.execute("""
            UPDATE configurations
            SET config_data = %s::jsonb,
                updated_at = NOW()
            WHERE config_id = %s
        """, (json.dumps(config_data), config_id))

        conn.commit()

        print(f"✅ Agent strategy updated successfully!")
        print(f"   Version: {current_version} → {new_version}")
        print(f"   Strategy length: {len(new_strategy)} characters")
        print(f"   Config ID: {config_id}")
