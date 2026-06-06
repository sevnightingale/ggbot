# core/auth/vault_utils.py
"""
Encrypted API-key storage and retrieval via the application-managed vault.

Secrets are Fernet-encrypted under GGBOT_VAULT_KEY in the local `vault_secrets`
table (see core/auth/local_vault.py). Public signatures and return shapes are
unchanged from the previous Supabase-Vault implementation.
"""

import uuid
from typing import Optional, Dict, Any
from core.common.db import get_db_connection
from core.common.logger import logger
from core.auth.local_vault import (
    vault_create_secret,
    vault_decrypt_secret,
    vault_delete_secret,
)


class VaultManager:
    """Manager for vault operations with user LLM + Hyperliquid credentials."""
    
    @staticmethod
    async def store_user_credential(
        user_id: str, 
        credential_name: str, 
        provider: str, 
        api_key: str
    ) -> Optional[str]:
        """
        Store a user's LLM API key securely in Vault.
        
        Args:
            user_id: UUID of the user
            credential_name: Human-readable name (e.g., "GPT-4 Production") 
            provider: LLM provider ("openai", "deepseek", "anthropic")
            api_key: The API key to encrypt and store
            
        Returns:
            UUID of the credential record, or None if failed
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create unique vault secret name for this credential
                    vault_secret_name = f"user_{user_id}_{provider}_{credential_name}".replace(" ", "_").lower()

                    # Store in vault (returns vault secret UUID)
                    vault_secret_id = vault_create_secret(cur, api_key, vault_secret_name)
                    
                    # Store credential metadata in user_llm_credentials table
                    cur.execute("""
                        INSERT INTO user_llm_credentials 
                        (user_id, credential_name, provider, vault_secret_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (user_id, credential_name)
                        DO UPDATE SET 
                            provider = EXCLUDED.provider,
                            vault_secret_id = EXCLUDED.vault_secret_id,
                            updated_at = NOW()
                        RETURNING id;
                    """, (user_id, credential_name, provider, vault_secret_id))
                    
                    credential_id = cur.fetchone()[0]
                    conn.commit()
                    
                    logger.bind(user_id=user_id).info(
                        f"Stored credential '{credential_name}' for provider {provider}"
                    )
                    return str(credential_id)
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to store credential: {e}")
            return None
    
    @staticmethod
    async def get_user_credential(
        user_id: str, 
        credential_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user's LLM API key from Vault.
        
        Args:
            user_id: UUID of the user
            credential_name: Name of the credential to retrieve
            
        Returns:
            Dict with 'provider' and 'api_key', or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get credential metadata and vault secret ID
                    cur.execute("""
                        SELECT provider, vault_secret_id
                        FROM user_llm_credentials
                        WHERE user_id = %s AND credential_name = %s;
                    """, (user_id, credential_name))
                    
                    result = cur.fetchone()
                    if not result:
                        return None
                    
                    provider, vault_secret_id = result

                    # Retrieve decrypted API key from vault
                    api_key = vault_decrypt_secret(cur, vault_secret_id)
                    if api_key is None:
                        logger.bind(user_id=user_id).error(
                            f"Vault secret not found for credential '{credential_name}'"
                        )
                        return None

                    return {
                        'provider': provider,
                        'api_key': api_key
                    }
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to retrieve credential: {e}")
            return None
    
    @staticmethod
    async def list_user_credentials(user_id: str) -> list[Dict[str, Any]]:
        """
        List all LLM credentials for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of dicts with credential metadata (no API keys)
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, credential_name, provider, created_at, updated_at
                        FROM user_llm_credentials
                        WHERE user_id = %s
                        ORDER BY credential_name;
                    """, (user_id,))
                    
                    results = cur.fetchall()
                    return [
                        {
                            'id': str(row[0]),
                            'credential_name': row[1],
                            'provider': row[2],
                            'created_at': row[3].isoformat(),
                            'updated_at': row[4].isoformat()
                        }
                        for row in results
                    ]
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to list credentials: {e}")
            return []
    
    @staticmethod
    async def delete_user_credential(
        user_id: str, 
        credential_name: str
    ) -> bool:
        """
        Delete a user's LLM credential and its Vault secret.
        
        Args:
            user_id: UUID of the user
            credential_name: Name of the credential to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get vault secret ID before deleting
                    cur.execute("""
                        SELECT vault_secret_id
                        FROM user_llm_credentials
                        WHERE user_id = %s AND credential_name = %s;
                    """, (user_id, credential_name))
                    
                    result = cur.fetchone()
                    if not result:
                        return False
                    
                    vault_secret_id = result[0]

                    # Delete from user_llm_credentials table
                    cur.execute("""
                        DELETE FROM user_llm_credentials
                        WHERE user_id = %s AND credential_name = %s;
                    """, (user_id, credential_name))

                    # Delete the encrypted secret itself (now possible with the local vault)
                    if vault_secret_id:
                        vault_delete_secret(cur, vault_secret_id)
                    conn.commit()
                    
                    logger.bind(user_id=user_id).info(
                        f"Deleted credential '{credential_name}'"
                    )
                    return True
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to delete credential: {e}")
            return False

    @staticmethod
    async def store_hyperliquid_credential(
        user_id: str,
        api_wallet_private_key: str,
        wallet_address: str
    ) -> bool:
        """
        Store Hyperliquid API wallet key in Vault and wallet address in user_profiles.

        The API wallet is a separate key authorized by the user's main wallet.
        It can trade but CANNOT withdraw — enforced at the Hyperliquid protocol level.

        Args:
            user_id: UUID of the user
            api_wallet_private_key: API wallet private key to encrypt and store
            wallet_address: User's main Hyperliquid wallet address (0x...)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    vault_secret_name = f"hyperliquid_{user_id}".replace("-", "_")

                    # Store API wallet key in vault
                    vault_secret_id = vault_create_secret(cur, api_wallet_private_key, vault_secret_name)

                    # Update user_profiles with vault reference and wallet address
                    cur.execute("""
                        UPDATE user_profiles
                        SET hyperliquid_vault_id = %s,
                            hyperliquid_wallet_address = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (vault_secret_id, wallet_address, user_id))

                    if cur.rowcount == 0:
                        logger.bind(user_id=user_id).error("User profile not found")
                        return False

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        "Stored Hyperliquid credentials securely"
                    )
                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to store Hyperliquid credential: {e}")
            return False

    @staticmethod
    async def get_hyperliquid_credential(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve Hyperliquid API wallet key from Vault.

        Args:
            user_id: UUID of the user

        Returns:
            Dict with 'api_wallet_key' and 'wallet_address', or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT hyperliquid_vault_id, hyperliquid_wallet_address
                        FROM user_profiles
                        WHERE user_id = %s;
                    """, (user_id,))

                    result = cur.fetchone()
                    if not result or not result[0]:
                        return None

                    vault_secret_id, wallet_address = result

                    # Retrieve decrypted API wallet key from vault
                    api_wallet_key = vault_decrypt_secret(cur, vault_secret_id)
                    if api_wallet_key is None:
                        logger.bind(user_id=user_id).error(
                            "Vault secret not found for Hyperliquid credential"
                        )
                        return None

                    return {
                        'api_wallet_key': api_wallet_key,
                        'wallet_address': wallet_address
                    }

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to retrieve Hyperliquid credential: {e}")
            return None

    @staticmethod
    async def delete_hyperliquid_credential(user_id: str) -> bool:
        """
        Delete Hyperliquid credentials and disable hyperliquid trading for all user's bots.

        Deletes the vault secret, nulls profile columns, and sets all hyperliquid
        bots to paper mode.

        Args:
            user_id: UUID of the user

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get vault secret ID before clearing
                    cur.execute("""
                        SELECT hyperliquid_vault_id
                        FROM user_profiles
                        WHERE user_id = %s
                    """, (user_id,))

                    result = cur.fetchone()
                    vault_secret_id = result[0] if result else None

                    # Delete the vault secret if it exists
                    if vault_secret_id:
                        try:
                            vault_delete_secret(cur, vault_secret_id)
                        except Exception as vault_error:
                            logger.bind(user_id=user_id).warning(
                                f"Could not delete vault secret: {vault_error}"
                            )

                    # Clear Hyperliquid credentials from user_profiles
                    cur.execute("""
                        UPDATE user_profiles
                        SET hyperliquid_vault_id = NULL,
                            hyperliquid_wallet_address = NULL,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))

                    if cur.rowcount == 0:
                        logger.bind(user_id=user_id).warning("User profile not found")
                        return False

                    # Deactivate hyperliquid bots but keep the slot
                    # (don't convert to paper — preserves strategy for reconnection)
                    cur.execute("""
                        UPDATE configurations
                        SET state = 'inactive',
                            updated_at = NOW()
                        WHERE user_id = %s
                        AND trading_mode = 'hyperliquid'
                        AND state = 'active'
                    """, (user_id,))

                    disabled_bots = cur.rowcount

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        f"Deleted Hyperliquid credentials and deactivated {disabled_bots} live bot(s)"
                    )
                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to delete Hyperliquid credential: {e}")
            return False

# Convenience functions for common operations
async def store_credential(user_id: str, name: str, provider: str, api_key: str) -> Optional[str]:
    """Store a user credential. Convenience wrapper."""
    return await VaultManager.store_user_credential(user_id, name, provider, api_key)

async def get_credential(user_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Get a user credential. Convenience wrapper."""
    return await VaultManager.get_user_credential(user_id, name)

async def list_credentials(user_id: str) -> list[Dict[str, Any]]:
    """List user credentials. Convenience wrapper.""" 
    return await VaultManager.list_user_credentials(user_id)

async def delete_credential(user_id: str, name: str) -> bool:
    """Delete a user credential. Convenience wrapper."""
    return await VaultManager.delete_user_credential(user_id, name)

async def store_hyperliquid_credential(user_id: str, api_wallet_private_key: str, wallet_address: str) -> bool:
    """Store Hyperliquid credential. Convenience wrapper."""
    return await VaultManager.store_hyperliquid_credential(user_id, api_wallet_private_key, wallet_address)

async def get_hyperliquid_credential(user_id: str) -> Optional[Dict[str, Any]]:
    """Get Hyperliquid credential. Convenience wrapper."""
    return await VaultManager.get_hyperliquid_credential(user_id)

async def delete_hyperliquid_credential(user_id: str) -> bool:
    """Delete Hyperliquid credential. Convenience wrapper."""
    return await VaultManager.delete_hyperliquid_credential(user_id)


# =========================================================================
# Low-level vault primitives
# =========================================================================

async def create_vault_secret(name: str, value: str) -> Optional[str]:
    """Create an opaque vault secret. Returns the UUID (as str), or None."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                vault_id = vault_create_secret(cur, value, name)
                conn.commit()
                return vault_id
    except Exception as e:
        logger.error(f"create_vault_secret failed for '{name}': {e}")
        return None


async def get_vault_secret(vault_id: str) -> Optional[str]:
    """Read back a vault secret by its UUID. Returns plaintext or None."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                return vault_decrypt_secret(cur, vault_id)
    except Exception as e:
        logger.error(f"get_vault_secret failed for {vault_id}: {e}")
        return None


async def resolve_hl_credentials(
    trading_mode: str,
    user_id: str,
    config_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Single source of truth for Hyperliquid credential resolution.

    - trading_mode='hyperliquid' → user-attached HL credentials

    Returns a dict with at least {api_wallet_key, wallet_address} or None.
    Fields mirror what HyperliquidLiveTradingService expects today, so
    callers don't have to care about the underlying trading_mode.
    """
    if trading_mode == 'hyperliquid':
        return await VaultManager.get_hyperliquid_credential(user_id)

    logger.error(f"resolve_hl_credentials: unsupported trading_mode for HL resolution: {trading_mode}")
    return None