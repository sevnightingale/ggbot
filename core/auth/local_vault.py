# core/auth/local_vault.py
"""
Application-managed secret vault (replaces Supabase Vault).

Secrets are encrypted with Fernet (AES-128-CBC + HMAC) under GGBOT_VAULT_KEY and
stored in the local `vault_secrets` table. MultiFernet supports key rotation:
GGBOT_VAULT_KEY may be a comma-separated list — the FIRST key encrypts, all keys
are tried for decryption (rolling re-encrypt without a flag day).

These helpers operate on a caller-supplied psycopg2 cursor so vault writes share
the caller's transaction (matching the previous Supabase-Vault behavior, where
`vault.create_secret(...)` and the metadata INSERT committed together).

Fail-loud: a missing GGBOT_VAULT_KEY raises — never a silent fallback.
"""
import os
from typing import Optional
from cryptography.fernet import Fernet, MultiFernet

_fernet: Optional[MultiFernet] = None


def _get_fernet() -> MultiFernet:
    global _fernet
    if _fernet is None:
        raw = os.getenv("GGBOT_VAULT_KEY")
        if not raw:
            raise RuntimeError(
                "GGBOT_VAULT_KEY is not set — refusing to operate the secret vault "
                "without an encryption key (no fallback)."
            )
        keys = [Fernet(k.strip().encode()) for k in raw.split(",") if k.strip()]
        if not keys:
            raise RuntimeError("GGBOT_VAULT_KEY is set but empty after parsing.")
        _fernet = MultiFernet(keys)
    return _fernet


def vault_create_secret(cur, value: str, name: Optional[str] = None) -> str:
    """Encrypt `value` and INSERT into vault_secrets. Returns the new UUID (str).

    `name` is optional (the LLM-key path historically created nameless secrets).
    Runs on the caller's cursor; the caller owns commit/rollback.
    """
    token = _get_fernet().encrypt(value.encode()).decode()
    cur.execute(
        "INSERT INTO vault_secrets (name, secret_encrypted, key_version) "
        "VALUES (%s, %s, 1) RETURNING id",
        (name, token),
    )
    return str(cur.fetchone()[0])


def vault_decrypt_secret(cur, secret_id) -> Optional[str]:
    """Read + decrypt a vault secret by UUID. Returns plaintext, or None if absent."""
    cur.execute("SELECT secret_encrypted FROM vault_secrets WHERE id = %s", (secret_id,))
    row = cur.fetchone()
    if not row:
        return None
    return _get_fernet().decrypt(row[0].encode()).decode()


def vault_delete_secret(cur, secret_id) -> None:
    """Delete a vault secret by UUID. Runs on the caller's cursor."""
    cur.execute("DELETE FROM vault_secrets WHERE id = %s", (secret_id,))
