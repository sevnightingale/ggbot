"""
Create and manage a pool of Virtuals arena agents.

Three-step process:
  1. Auth:     Paste a Virtuals JWT (from browser → Network tab → copy token)
  2. Create:   Batch-create lite agents via Virtuals API
  3. Register: Register agents on DGClaw (join_leaderboard)

Usage:
  python scripts/create_arena_pool.py auth
  python scripts/create_arena_pool.py create --count 5 --start-index 2
  python scripts/create_arena_pool.py register
  python scripts/create_arena_pool.py seed --agent-id 1 --claw-key acp-xxx --dgclaw-key dgc_xxx
  python scripts/create_arena_pool.py status
"""

import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from core.common.db import get_db_connection
from core.auth.vault_utils import VaultManager


# Virtuals API
VIRTUALS_API = "https://acpx.virtuals.io/api"
DGCLAW_BACKEND = "https://dgclaw-app-production.up.railway.app"

# Stored JWT (file-based, short-lived ~30min)
TOKEN_FILE = "/tmp/virtuals_jwt.txt"


def cmd_auth(args):
    """Authenticate with Virtuals via browser link."""
    import time as _time

    AUTH_URL_ENDPOINT = "https://acpx.virtuals.io/api/auth/lite/auth-url"
    TOKEN_ENDPOINT = "https://acpx.virtuals.io/api/auth/lite/auth-status"

    # Step 1: Get auth URL
    print("Requesting auth URL from Virtuals...")
    resp = requests.get(AUTH_URL_ENDPOINT, timeout=10)
    if resp.status_code != 200:
        print(f"Failed to get auth URL: {resp.status_code} {resp.text[:200]}")
        print("\nFallback: paste a JWT token manually.")
        token = input("JWT token: ").strip()
        if token.startswith("Bearer "):
            token = token[7:]
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        print(f"Token saved.")
        return

    data = resp.json().get("data", {})
    auth_url = data.get("authUrl")
    request_id = data.get("requestId")

    print(f"\nOpen this link in your browser and authenticate:\n")
    print(f"  {auth_url}\n")
    print("Waiting for authentication (polling every 3s, 5min timeout)...")

    # Step 2: Poll for token
    start = _time.time()
    while (_time.time() - start) < 300:
        _time.sleep(3)
        try:
            token_resp = requests.get(
                f"{TOKEN_ENDPOINT}?requestId={request_id}",
                timeout=5,
            )
            if token_resp.status_code == 200:
                token_data = token_resp.json().get("data", {})
                token = token_data.get("token") or token_data.get("accessToken")
                if token:
                    with open(TOKEN_FILE, 'w') as f:
                        f.write(token)
                    print(f"\nAuthenticated! Token saved.")
                    print("Note: Virtuals JWTs expire in ~30 minutes.")
                    return
        except Exception:
            pass
        elapsed = int(_time.time() - start)
        if elapsed % 15 == 0:
            print(f"  Still waiting... ({elapsed}s)")

    print("\nTimed out after 5 minutes. Try again or paste token manually:")
    token = input("JWT token: ").strip()
    if token.startswith("Bearer "):
        token = token[7:]
    if token:
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        print(f"Token saved.")


def _get_token():
    if not os.path.exists(TOKEN_FILE):
        print("No token found. Run: python scripts/create_arena_pool.py auth")
        sys.exit(1)
    with open(TOKEN_FILE, 'r') as f:
        return f.read().strip()


def cmd_create(args):
    """Batch-create lite Virtuals agents."""
    token = _get_token()
    count = args.count
    start = args.start_index

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    created = []
    for i in range(start, start + count):
        name = f"ggbot-{i:03d}"
        print(f"Creating agent {name}...", end=" ")

        resp = requests.post(
            f"{VIRTUALS_API}/agents/lite/key",
            headers=headers,
            json={"data": {"name": name}},
            timeout=30,
        )

        if resp.status_code not in (200, 201):
            print(f"FAILED: {resp.status_code} {resp.text[:200]}")
            continue

        data = resp.json()
        agent_data = data.get("data", data)
        agent_id = agent_data.get("id") or agent_data.get("agentId")
        wallet = agent_data.get("walletAddress") or agent_data.get("wallet")
        api_key = agent_data.get("apiKey") or agent_data.get("key")

        print(f"OK (id={agent_id}, wallet={wallet})")

        # Insert into DB
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO arena_agents (virtuals_id, agent_name, wallet_address)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (wallet_address) DO NOTHING
                    RETURNING id
                """, (agent_id or 0, name, wallet))
                row = cur.fetchone()
                conn.commit()

                if row:
                    db_id = row[0]
                    # Store API key in vault
                    if api_key:
                        asyncio.run(VaultManager.store_arena_credential(db_id, api_key))
                        print(f"  -> DB id={db_id}, API key stored in vault")
                    else:
                        print(f"  -> DB id={db_id}, no API key returned")

                    created.append({
                        'db_id': db_id,
                        'name': name,
                        'wallet': wallet,
                        'virtuals_id': agent_id,
                    })

    print(f"\nCreated {len(created)}/{count} agents")
    for a in created:
        print(f"  {a['name']}: wallet={a['wallet']}, db_id={a['db_id']}")


def cmd_register(args):
    """Register arena agents on DGClaw (join_leaderboard)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Find agents that have API keys but no token (not yet on DGClaw)
            cur.execute("""
                SELECT id, agent_name, wallet_address, claw_api_key_vault_id
                FROM arena_agents
                WHERE claw_api_key_vault_id IS NOT NULL
                AND status = 'available'
            """)
            agents = cur.fetchall()

    if not agents:
        print("No agents to register")
        return

    print(f"Found {len(agents)} agents to register on DGClaw")

    for agent_id, name, wallet, vault_id in agents:
        print(f"Registering {name} ({wallet})...", end=" ")

        # Get DGClaw API key from vault
        cred = asyncio.run(VaultManager.get_arena_credential(agent_id))
        if not cred or not cred.get('claw_api_key'):
            print("SKIP (no claw API key)")
            continue

        # Call DGClaw join_leaderboard
        try:
            resp = requests.post(
                f"{DGCLAW_BACKEND}/leaderboard/join",
                json={"walletAddress": wallet},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                print("OK")
            else:
                print(f"FAILED: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"ERROR: {e}")


def cmd_seed(args):
    """Manually seed credentials for an existing arena agent (e.g., the test agent)."""
    agent_id = args.agent_id
    claw_key = args.claw_key
    dgclaw_key = args.dgclaw_key

    success = asyncio.run(
        VaultManager.store_arena_credential(agent_id, claw_key, dgclaw_key)
    )
    if success:
        print(f"Credentials stored for agent {agent_id}")
    else:
        print(f"Failed to store credentials for agent {agent_id}")


def cmd_status(args):
    """Show current pool status."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status, COUNT(*) FROM arena_agents GROUP BY status
            """)
            statuses = cur.fetchall()

            cur.execute("""
                SELECT id, agent_name, wallet_address, status,
                       assigned_user_id, token_symbol,
                       claw_api_key_vault_id IS NOT NULL as has_claw_key
                FROM arena_agents
                ORDER BY id
            """)
            agents = cur.fetchall()

    print("=== Arena Agent Pool ===\n")

    for status, count in statuses:
        print(f"  {status}: {count}")
    print()

    if agents:
        print(f"{'ID':<5} {'Name':<25} {'Status':<12} {'Token':<12} {'Key':<5} {'User':<10}")
        print("-" * 75)
        for a in agents:
            user = a[4][:8] + "..." if a[4] else "-"
            token = a[5] or "-"
            key = "yes" if a[6] else "no"
            print(f"{a[0]:<5} {a[1]:<25} {a[3]:<12} {token:<12} {key:<5} {user:<10}")
    else:
        print("No agents in pool")


def main():
    parser = argparse.ArgumentParser(description="Manage arena agent pool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("auth", help="Store Virtuals JWT token")

    create_parser = subparsers.add_parser("create", help="Batch-create lite agents")
    create_parser.add_argument("--count", type=int, default=5, help="Number of agents")
    create_parser.add_argument("--start-index", type=int, default=2, help="Starting index for naming")

    subparsers.add_parser("register", help="Register agents on DGClaw")

    seed_parser = subparsers.add_parser("seed", help="Seed credentials for existing agent")
    seed_parser.add_argument("--agent-id", type=int, required=True, help="arena_agents.id")
    seed_parser.add_argument("--claw-key", required=True, help="Claw API key")
    seed_parser.add_argument("--dgclaw-key", default=None, help="DGClaw API key")

    subparsers.add_parser("status", help="Show pool status")

    args = parser.parse_args()

    commands = {
        "auth": cmd_auth,
        "create": cmd_create,
        "register": cmd_register,
        "seed": cmd_seed,
        "status": cmd_status,
    }
    commands[args.command](args)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
