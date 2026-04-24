# core/auth/vault_utils.py
"""
Supabase Vault utilities for encrypted API key storage and retrieval.
Provides secure storage of user LLM credentials using Supabase Vault extension.
"""

import uuid
from typing import Optional, Dict, Any
from core.common.db import get_db_connection
from core.common.logger import logger


class VaultManager:
    """Manager for Supabase Vault operations with user LLM credentials."""
    
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
                    
                    # Store in Vault (returns vault secret ID)
                    cur.execute(
                        "SELECT vault.create_secret(%s, %s) as secret_id;",
                        (vault_secret_name, api_key)
                    )
                    vault_secret_id = cur.fetchone()[0]
                    
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
                    
                    # Retrieve decrypted API key from Vault
                    cur.execute("""
                        SELECT decrypted_secret 
                        FROM vault.decrypted_secrets 
                        WHERE id = %s;
                    """, (vault_secret_id,))
                    
                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.bind(user_id=user_id).error(
                            f"Vault secret not found for credential '{credential_name}'"
                        )
                        return None
                    
                    api_key = vault_result[0]
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
                    
                    # Delete from Vault (note: vault secrets may not support direct deletion)
                    # For now, just mark as deleted in our table
                    conn.commit()
                    
                    logger.bind(user_id=user_id).info(
                        f"Deleted credential '{credential_name}'"
                    )
                    return True
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to delete credential: {e}")
            return False

    @staticmethod
    async def store_symphony_credential(
        user_id: str,
        api_key: str,
        smart_account: str
    ) -> bool:
        """
        Store Symphony API key in Vault and smart account in user_profiles.

        Args:
            user_id: UUID of the user
            api_key: Symphony API key to encrypt and store
            smart_account: Symphony smart account address (0x...)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create unique vault secret name for Symphony credential
                    vault_secret_name = f"symphony_{user_id}".replace("-", "_")

                    # Store API key in Vault (returns vault secret ID)
                    # vault.create_secret(secret, name, ...) - secret comes first!
                    cur.execute(
                        "SELECT vault.create_secret(%s, %s) as secret_id;",
                        (api_key, vault_secret_name)
                    )
                    vault_secret_id = cur.fetchone()[0]

                    # Update user_profiles with vault reference and smart account
                    cur.execute("""
                        UPDATE user_profiles
                        SET symphony_vault_id = %s,
                            symphony_smart_account = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (vault_secret_id, smart_account, user_id))

                    if cur.rowcount == 0:
                        logger.bind(user_id=user_id).error("User profile not found")
                        return False

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        "Stored Symphony credentials securely"
                    )
                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to store Symphony credential: {e}")
            return False

    @staticmethod
    async def get_symphony_credential(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve Symphony API key from Vault.

        Args:
            user_id: UUID of the user

        Returns:
            Dict with 'api_key' and 'smart_account', or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get vault secret ID and smart account from user_profiles
                    cur.execute("""
                        SELECT symphony_vault_id, symphony_smart_account
                        FROM user_profiles
                        WHERE user_id = %s;
                    """, (user_id,))

                    result = cur.fetchone()
                    if not result or not result[0]:
                        return None

                    vault_secret_id, smart_account = result

                    # Retrieve decrypted API key from Vault
                    cur.execute("""
                        SELECT decrypted_secret
                        FROM vault.decrypted_secrets
                        WHERE id = %s;
                    """, (vault_secret_id,))

                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.bind(user_id=user_id).error(
                            "Vault secret not found for Symphony credential"
                        )
                        return None

                    api_key = vault_result[0]
                    return {
                        'api_key': api_key,
                        'smart_account': smart_account
                    }

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to retrieve Symphony credential: {e}")
            return None

    @staticmethod
    async def delete_symphony_credential(user_id: str) -> bool:
        """
        Delete Symphony credentials and disable live trading for all user's bots.

        Deletes the vault secret and sets symphony_vault_id = NULL.
        Updates all configurations to paper mode.
        This ensures no live trading can occur without valid credentials.

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
                        SELECT symphony_vault_id
                        FROM user_profiles
                        WHERE user_id = %s
                    """, (user_id,))

                    result = cur.fetchone()
                    vault_secret_id = result[0] if result else None

                    # Delete the vault secret if it exists
                    if vault_secret_id:
                        try:
                            cur.execute("""
                                DELETE FROM vault.secrets
                                WHERE id = %s
                            """, (vault_secret_id,))
                        except Exception as vault_error:
                            # Log but don't fail if vault deletion fails
                            logger.bind(user_id=user_id).warning(
                                f"Could not delete vault secret: {vault_error}"
                            )

                    # Clear Symphony credentials from user_profiles
                    cur.execute("""
                        UPDATE user_profiles
                        SET symphony_vault_id = NULL,
                            symphony_smart_account = NULL,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))

                    if cur.rowcount == 0:
                        logger.bind(user_id=user_id).warning("User profile not found")
                        return False

                    # Disable live trading on all user's bots
                    cur.execute("""
                        UPDATE configurations
                        SET trading_mode = 'paper',
                            updated_at = NOW()
                        WHERE user_id = %s
                        AND trading_mode = 'symphony'
                    """, (user_id,))

                    disabled_bots = cur.rowcount

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        f"Deleted Symphony credentials and disabled {disabled_bots} live bot(s)"
                    )
                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to delete Symphony credential: {e}")
            return False

    @staticmethod
    async def store_aster_credential(
        user_id: str,
        user_wallet: str,
        aster_wallet: str,
        private_key: str
    ) -> bool:
        """
        Store AsterDEX credentials in Vault and wallet addresses in user_profiles.

        Note: Requires database migration to add columns:
        - aster_vault_id UUID (nullable)
        - aster_user_wallet VARCHAR(42) (nullable)
        - aster_wallet VARCHAR(42) (nullable)

        Args:
            user_id: UUID of the user
            user_wallet: User's Ethereum wallet address (0x...)
            aster_wallet: AsterDEX wallet address (0x...)
            private_key: AsterDEX wallet private key to encrypt and store

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create unique vault secret name for Aster private key
                    vault_secret_name = f"aster_{user_id}".replace("-", "_")

                    # Store private key in Vault (returns vault secret ID)
                    cur.execute(
                        "SELECT vault.create_secret(%s, %s) as secret_id;",
                        (private_key, vault_secret_name)
                    )
                    vault_secret_id = cur.fetchone()[0]

                    # Update user_profiles with vault reference and wallet addresses
                    cur.execute("""
                        UPDATE user_profiles
                        SET aster_vault_id = %s,
                            aster_user_wallet = %s,
                            aster_wallet = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (vault_secret_id, user_wallet, aster_wallet, user_id))

                    if cur.rowcount == 0:
                        logger.bind(user_id=user_id).error("User profile not found")
                        return False

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        "Stored AsterDEX credentials securely"
                    )
                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to store Aster credential: {e}")
            return False

    @staticmethod
    async def get_aster_credential(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve AsterDEX credentials from Vault.

        Args:
            user_id: UUID of the user

        Returns:
            Dict with 'user_wallet', 'aster_wallet', and 'private_key', or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get vault secret ID and wallet addresses from user_profiles
                    cur.execute("""
                        SELECT aster_vault_id, aster_user_wallet, aster_wallet
                        FROM user_profiles
                        WHERE user_id = %s;
                    """, (user_id,))

                    result = cur.fetchone()
                    if not result or not result[0]:
                        return None

                    vault_secret_id, user_wallet, aster_wallet = result

                    # Retrieve decrypted private key from Vault
                    cur.execute("""
                        SELECT decrypted_secret
                        FROM vault.decrypted_secrets
                        WHERE id = %s;
                    """, (vault_secret_id,))

                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.bind(user_id=user_id).error(
                            "Vault secret not found for Aster credential"
                        )
                        return None

                    private_key = vault_result[0]
                    return {
                        'user_wallet': user_wallet,
                        'aster_wallet': aster_wallet,
                        'private_key': private_key
                    }

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to retrieve Aster credential: {e}")
            return None

    @staticmethod
    async def delete_aster_credential(user_id: str) -> bool:
        """
        Delete AsterDEX credentials and disable aster trading for all user's bots.

        Sets aster_vault_id = NULL and updates all configurations to paper mode.
        This ensures no aster trading can occur without valid credentials.

        Args:
            user_id: UUID of the user

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Clear Aster credentials from user_profiles
                    cur.execute("""
                        UPDATE user_profiles
                        SET aster_vault_id = NULL,
                            aster_user_wallet = NULL,
                            aster_wallet = NULL,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))

                    if cur.rowcount == 0:
                        logger.bind(user_id=user_id).warning("User profile not found")
                        return False

                    # Disable aster trading on all user's bots
                    cur.execute("""
                        UPDATE configurations
                        SET trading_mode = 'paper',
                            updated_at = NOW()
                        WHERE user_id = %s
                        AND trading_mode = 'aster'
                    """, (user_id,))

                    disabled_bots = cur.rowcount

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        f"Deleted Aster credentials and disabled {disabled_bots} aster bot(s)"
                    )
                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to delete Aster credential: {e}")
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

                    # Store API wallet key in Vault (secret first, then name)
                    cur.execute(
                        "SELECT vault.create_secret(%s, %s) as secret_id;",
                        (api_wallet_private_key, vault_secret_name)
                    )
                    vault_secret_id = cur.fetchone()[0]

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

                    # Retrieve decrypted API wallet key from Vault
                    cur.execute("""
                        SELECT decrypted_secret
                        FROM vault.decrypted_secrets
                        WHERE id = %s;
                    """, (vault_secret_id,))

                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.bind(user_id=user_id).error(
                            "Vault secret not found for Hyperliquid credential"
                        )
                        return None

                    api_wallet_key = vault_result[0]
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
                            cur.execute("""
                                DELETE FROM vault.secrets
                                WHERE id = %s
                            """, (vault_secret_id,))
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

    # =========================================================================
    # Arena Agent Credentials (Supabase Vault → arena_agents table)
    # =========================================================================

    @staticmethod
    async def store_arena_credential(
        agent_id: int,
        claw_api_key: str,
        dgclaw_api_key: Optional[str] = None,
    ) -> bool:
        """
        Store arena agent API keys in Vault and update arena_agents vault_id columns.

        Args:
            agent_id: arena_agents.id (serial PK)
            claw_api_key: Claw REST API key (x-api-key header)
            dgclaw_api_key: Optional DGClaw API key

        Returns:
            True if stored successfully
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if claw key already stored (avoid duplicate vault secret)
                    cur.execute(
                        "SELECT claw_api_key_vault_id FROM arena_agents WHERE id = %s",
                        (agent_id,)
                    )
                    existing = cur.fetchone()
                    claw_vault_id = existing[0] if existing and existing[0] else None

                    if not claw_vault_id:
                        # Store claw API key in vault (first time only)
                        vault_name_claw = f"arena_claw_{agent_id}"
                        cur.execute(
                            "SELECT vault.create_secret(%s, %s) as secret_id;",
                            (claw_api_key, vault_name_claw)
                        )
                        claw_vault_id = cur.fetchone()[0]

                    # Store DGClaw API key if provided
                    dgclaw_vault_id = None
                    if dgclaw_api_key:
                        vault_name_dgclaw = f"arena_dgclaw_{agent_id}"
                        cur.execute(
                            "SELECT vault.create_secret(%s, %s) as secret_id;",
                            (dgclaw_api_key, vault_name_dgclaw)
                        )
                        dgclaw_vault_id = cur.fetchone()[0]

                    # Update arena_agents with vault references
                    update_parts = ["claw_api_key_vault_id = %s"]
                    update_params = [claw_vault_id]
                    if dgclaw_vault_id:
                        update_parts.append("dgclaw_api_key_vault_id = %s")
                        update_params.append(dgclaw_vault_id)
                    update_params.append(agent_id)

                    cur.execute(f"""
                        UPDATE arena_agents
                        SET {', '.join(update_parts)}
                        WHERE id = %s
                    """, tuple(update_params))

                    conn.commit()
                    logger.info(f"Stored arena credentials for agent {agent_id}")
                    return True

        except Exception as e:
            logger.error(f"Failed to store arena credential for agent {agent_id}: {e}")
            return False

    @staticmethod
    async def get_arena_credential(agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve arena agent API keys from Vault.

        Args:
            agent_id: arena_agents.id

        Returns:
            Dict with 'claw_api_key', 'wallet_address', 'agent_name', etc. or None
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT claw_api_key_vault_id, dgclaw_api_key_vault_id,
                               wallet_address, agent_name, token_symbol
                        FROM arena_agents
                        WHERE id = %s
                    """, (agent_id,))

                    result = cur.fetchone()
                    if not result or not result[0]:
                        return None

                    claw_vault_id, dgclaw_vault_id, wallet_address, agent_name, token_symbol = result

                    # Decrypt claw API key
                    cur.execute("""
                        SELECT decrypted_secret
                        FROM vault.decrypted_secrets
                        WHERE id = %s
                    """, (claw_vault_id,))
                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.error(f"Vault secret not found for arena agent {agent_id}")
                        return None

                    claw_api_key = vault_result[0]

                    # Decrypt DGClaw API key if present
                    dgclaw_api_key = None
                    if dgclaw_vault_id:
                        cur.execute("""
                            SELECT decrypted_secret
                            FROM vault.decrypted_secrets
                            WHERE id = %s
                        """, (dgclaw_vault_id,))
                        dgclaw_result = cur.fetchone()
                        if dgclaw_result:
                            dgclaw_api_key = dgclaw_result[0]

                    return {
                        'claw_api_key': claw_api_key,
                        'dgclaw_api_key': dgclaw_api_key,
                        'wallet_address': wallet_address,
                        'agent_name': agent_name,
                        'token_symbol': token_symbol,
                    }

        except Exception as e:
            logger.error(f"Failed to retrieve arena credential for agent {agent_id}: {e}")
            return None

    @staticmethod
    async def get_arena_credential_by_user(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the arena agent assigned to a user, with decrypted claw API key.
        Legacy — use get_arena_credential_by_config for the 1-bot-1-agent model.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT aa.id, aa.claw_api_key_vault_id, aa.wallet_address,
                               aa.agent_name, aa.token_symbol, aa.user_wallet_address
                        FROM arena_agents aa
                        WHERE aa.assigned_user_id = %s AND aa.status = 'assigned'
                    """, (user_id,))

                    result = cur.fetchone()
                    if not result or not result[1]:
                        return None

                    agent_id, claw_vault_id, wallet_address, agent_name, token_symbol, user_wallet = result

                    cur.execute("""
                        SELECT decrypted_secret
                        FROM vault.decrypted_secrets
                        WHERE id = %s
                    """, (claw_vault_id,))
                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.bind(user_id=user_id).error(
                            f"Vault secret not found for arena agent {agent_id}"
                        )
                        return None

                    return {
                        'agent_id': agent_id,
                        'claw_api_key': vault_result[0],
                        'wallet_address': wallet_address,
                        'agent_name': agent_name,
                        'token_symbol': token_symbol,
                        'user_wallet_address': user_wallet,
                    }

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to retrieve arena credential: {e}")
            return None

    @staticmethod
    async def get_arena_credential_by_config(config_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the arena agent assigned to a bot config, with decrypted claw API key.

        1-bot-1-agent model: each config_id maps to at most one arena agent.

        Returns:
            Dict with 'claw_api_key', 'wallet_address', 'agent_id', etc. or None
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT aa.id, aa.claw_api_key_vault_id, aa.wallet_address,
                               aa.agent_name, aa.token_symbol, aa.user_wallet_address,
                               aa.assigned_user_id, aa.hl_subaccount_address
                        FROM arena_agents aa
                        WHERE aa.assigned_config_id = %s AND aa.status = 'assigned'
                    """, (config_id,))

                    result = cur.fetchone()
                    if not result or not result[1]:
                        return None

                    (agent_id, claw_vault_id, wallet_address, agent_name,
                     token_symbol, user_wallet, user_id, hl_subaccount) = result

                    cur.execute("""
                        SELECT decrypted_secret
                        FROM vault.decrypted_secrets
                        WHERE id = %s
                    """, (claw_vault_id,))
                    vault_result = cur.fetchone()
                    if not vault_result:
                        logger.error(f"Vault secret not found for arena agent {agent_id}")
                        return None

                    return {
                        'agent_id': agent_id,
                        'claw_api_key': vault_result[0],
                        'wallet_address': wallet_address,
                        'agent_name': agent_name,
                        'token_symbol': token_symbol,
                        'user_wallet_address': user_wallet,
                        'user_id': user_id,
                        'hl_subaccount_address': hl_subaccount,
                    }

        except Exception as e:
            logger.error(f"Failed to retrieve arena credential for config {config_id}: {e}")
            return None


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

async def store_symphony_credential(user_id: str, api_key: str, smart_account: str) -> bool:
    """Store Symphony credential. Convenience wrapper."""
    return await VaultManager.store_symphony_credential(user_id, api_key, smart_account)

async def get_symphony_credential(user_id: str) -> Optional[Dict[str, Any]]:
    """Get Symphony credential. Convenience wrapper."""
    return await VaultManager.get_symphony_credential(user_id)

async def delete_symphony_credential(user_id: str) -> bool:
    """Delete Symphony credential. Convenience wrapper."""
    return await VaultManager.delete_symphony_credential(user_id)

async def store_aster_credential(user_id: str, user_wallet: str, aster_wallet: str, private_key: str) -> bool:
    """Store AsterDEX credential. Convenience wrapper."""
    return await VaultManager.store_aster_credential(user_id, user_wallet, aster_wallet, private_key)

async def get_aster_credential(user_id: str) -> Optional[Dict[str, Any]]:
    """Get AsterDEX credential. Convenience wrapper."""
    return await VaultManager.get_aster_credential(user_id)

async def delete_aster_credential(user_id: str) -> bool:
    """Delete AsterDEX credential. Convenience wrapper."""
    return await VaultManager.delete_aster_credential(user_id)

async def store_hyperliquid_credential(user_id: str, api_wallet_private_key: str, wallet_address: str) -> bool:
    """Store Hyperliquid credential. Convenience wrapper."""
    return await VaultManager.store_hyperliquid_credential(user_id, api_wallet_private_key, wallet_address)

async def get_hyperliquid_credential(user_id: str) -> Optional[Dict[str, Any]]:
    """Get Hyperliquid credential. Convenience wrapper."""
    return await VaultManager.get_hyperliquid_credential(user_id)

async def delete_hyperliquid_credential(user_id: str) -> bool:
    """Delete Hyperliquid credential. Convenience wrapper."""
    return await VaultManager.delete_hyperliquid_credential(user_id)

async def store_arena_credential(agent_id: int, claw_api_key: str, dgclaw_api_key: Optional[str] = None) -> bool:
    """Store arena agent credentials. Convenience wrapper."""
    return await VaultManager.store_arena_credential(agent_id, claw_api_key, dgclaw_api_key)

async def get_arena_credential(agent_id: int) -> Optional[Dict[str, Any]]:
    """Get arena agent credentials. Convenience wrapper."""
    return await VaultManager.get_arena_credential(agent_id)

async def get_arena_credential_by_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get arena agent for a user. Convenience wrapper."""
    return await VaultManager.get_arena_credential_by_user(user_id)

async def get_arena_credential_by_config(config_id: str) -> Optional[Dict[str, Any]]:
    """Get arena agent for a bot config. Convenience wrapper."""
    return await VaultManager.get_arena_credential_by_config(config_id)


# =========================================================================
# Low-level vault primitives
# =========================================================================

async def create_vault_secret(name: str, value: str) -> Optional[str]:
    """Create an opaque Vault secret. Returns the UUID (as str), or None."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT vault.create_secret(%s, %s) as id;",
                    (value, name),
                )
                row = cur.fetchone()
                conn.commit()
                return str(row[0]) if row else None
    except Exception as e:
        logger.error(f"create_vault_secret failed for '{name}': {e}")
        return None


async def get_vault_secret(vault_id: str) -> Optional[str]:
    """Read back a Vault secret by its UUID. Returns plaintext or None."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT decrypted_secret FROM vault.decrypted_secrets WHERE id = %s",
                    (vault_id,),
                )
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        logger.error(f"get_vault_secret failed for {vault_id}: {e}")
        return None


# =========================================================================
# Arena v2 (Virtuals ACP v2) — signer + HL API wallet + DGClaw API key
# =========================================================================
#
# Stored alongside arena_agents_v2 rows. Each row gets up to 3 vault
# secrets — signer is mandatory (created at agent provisioning), the other
# two land when the corresponding acp-node route completes.

async def store_arena_v2_signer(
    agent_record_id: str,
    signer_private_key_b64: str,
) -> Optional[str]:
    """
    Store the P-256 signer private key for a v2 arena agent in Vault and
    patch the arena_agents_v2 row with the vault ID.

    Returns the vault_secret_id, or None on failure.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                vault_name = f"arena_v2_signer_{agent_record_id}"
                cur.execute(
                    "SELECT vault.create_secret(%s, %s) as secret_id;",
                    (signer_private_key_b64, vault_name),
                )
                vault_id = cur.fetchone()[0]

                cur.execute(
                    """
                    UPDATE arena_agents_v2
                    SET signer_private_key_vault_id = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (vault_id, agent_record_id),
                )
                conn.commit()
                logger.info(f"arena_v2: stored signer key for agent_record {agent_record_id}")
                return str(vault_id)
    except Exception as e:
        logger.error(f"arena_v2: store_arena_v2_signer failed for {agent_record_id}: {e}")
        return None


async def store_arena_v2_hl_api_wallet(
    agent_record_id: str,
    hl_api_wallet_key: str,
) -> Optional[str]:
    """Store the HL API wallet private key for a v2 arena agent."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                vault_name = f"arena_v2_hl_api_{agent_record_id}"
                cur.execute(
                    "SELECT vault.create_secret(%s, %s) as secret_id;",
                    (hl_api_wallet_key, vault_name),
                )
                vault_id = cur.fetchone()[0]

                cur.execute(
                    """
                    UPDATE arena_agents_v2
                    SET hl_api_wallet_key_vault_id = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (vault_id, agent_record_id),
                )
                conn.commit()
                logger.info(f"arena_v2: stored HL API wallet key for agent_record {agent_record_id}")
                return str(vault_id)
    except Exception as e:
        logger.error(f"arena_v2: store_arena_v2_hl_api_wallet failed for {agent_record_id}: {e}")
        return None


async def store_arena_v2_dgclaw_key(
    agent_record_id: str,
    dgclaw_api_key: str,
) -> Optional[str]:
    """Store the DGClaw API key for a v2 arena agent."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                vault_name = f"arena_v2_dgclaw_{agent_record_id}"
                cur.execute(
                    "SELECT vault.create_secret(%s, %s) as secret_id;",
                    (dgclaw_api_key, vault_name),
                )
                vault_id = cur.fetchone()[0]

                cur.execute(
                    """
                    UPDATE arena_agents_v2
                    SET dgclaw_api_key_vault_id = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (vault_id, agent_record_id),
                )
                conn.commit()
                logger.info(f"arena_v2: stored DGClaw key for agent_record {agent_record_id}")
                return str(vault_id)
    except Exception as e:
        logger.error(f"arena_v2: store_arena_v2_dgclaw_key failed for {agent_record_id}: {e}")
        return None


async def store_arena_v2_forum_thread_id(
    agent_record_id: str,
    thread_id: str,
) -> bool:
    """Persist the DGClaw forum thread id so orchestrator forum-post hook fires."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE arena_agents_v2
                    SET dgclaw_forum_thread_id = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (thread_id, agent_record_id),
                )
                conn.commit()
                logger.info(
                    f"arena_v2: stored forum thread id for agent_record {agent_record_id}"
                )
                return True
    except Exception as e:
        logger.error(
            f"arena_v2: store_arena_v2_forum_thread_id failed for {agent_record_id}: {e}"
        )
        return False


async def store_arena_v2_token_address(
    agent_record_id: str,
    token_address: str,
) -> bool:
    """Persist the agent's on-chain ERC20 token address once tokenized on
    Virtuals. Source: https://api.acp.virtuals.io/agents/wallet/{wallet}
    → chains[0].tokenAddress. Presence acts as the `is_tokenized` flag."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE arena_agents_v2
                    SET token_address = %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (token_address, agent_record_id),
                )
                conn.commit()
                return True
    except Exception as e:
        logger.error(
            f"arena_v2: store_arena_v2_token_address failed for {agent_record_id}: {e}"
        )
        return False


async def store_arena_v2_hl_subaccount(
    agent_record_id: str,
    subaccount_address: str,
) -> bool:
    """Persist the DGClaw-assigned HL subaccount address. Populated
    opportunistically from /users/{wallet}/account when DGClaw exposes it
    during active trading. Powers v2 close-sync from HL fills."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE arena_agents_v2
                    SET hl_subaccount_address = %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (subaccount_address, agent_record_id),
                )
                conn.commit()
                return True
    except Exception as e:
        logger.error(
            f"arena_v2: store_arena_v2_hl_subaccount failed for {agent_record_id}: {e}"
        )
        return False


async def get_arena_v2_credential(config_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the arena_agents_v2 row for a config, with all vault secrets
    decrypted and returned as plaintext. Shape matches what acp-node sidecar
    requests need — signerPrivateKey (base64 PEM), hlApiWalletKey (0x-hex),
    optional dgclawApiKey.

    Returns rows in ANY status (provisioning/active) so deploy-time UIs can
    show wallet/agent info during setup. Callers that need an *active-only*
    agent (e.g. resolve_hl_credentials) must check creds['status'] themselves.
    Excludes status='retired' — those are genuinely dead.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, virtuals_agent_id, agent_name,
                           agent_wallet_address, wallet_id,
                           signer_private_key_vault_id,
                           hl_api_wallet_key_vault_id,
                           dgclaw_api_key_vault_id,
                           dgclaw_forum_thread_id,
                           token_address,
                           hl_subaccount_address,
                           status
                    FROM arena_agents_v2
                    WHERE config_id = %s AND status <> 'retired'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (config_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None

                (
                    agent_record_id, user_id, virtuals_agent_id, agent_name,
                    agent_wallet_address, wallet_id,
                    signer_vault_id, hl_vault_id, dgclaw_vault_id,
                    forum_thread_id, token_address, hl_subaccount_address, status,
                ) = row

                def _decrypt(vault_id: Any) -> Optional[str]:
                    if not vault_id:
                        return None
                    cur.execute(
                        "SELECT decrypted_secret FROM vault.decrypted_secrets WHERE id = %s",
                        (vault_id,),
                    )
                    r = cur.fetchone()
                    return r[0] if r else None

                signer_private_key = _decrypt(signer_vault_id)
                hl_api_wallet_key = _decrypt(hl_vault_id)
                dgclaw_api_key = _decrypt(dgclaw_vault_id)

                if not signer_private_key:
                    logger.error(
                        f"arena_v2: signer key missing in vault for agent {agent_record_id}"
                    )
                    return None

                return {
                    'agent_record_id': str(agent_record_id),
                    'user_id': str(user_id),
                    'virtuals_agent_id': virtuals_agent_id,
                    'agent_name': agent_name,
                    'agent_wallet_address': agent_wallet_address,
                    'wallet_id': wallet_id,
                    'signer_private_key': signer_private_key,  # base64-PEM
                    'hl_api_wallet_key': hl_api_wallet_key,    # 0x-hex or None
                    'dgclaw_api_key': dgclaw_api_key,          # plaintext or None
                    'dgclaw_forum_thread_id': forum_thread_id,
                    'token_address': token_address,
                    'hl_subaccount_address': hl_subaccount_address,
                    'status': status,
                }
    except Exception as e:
        logger.error(f"arena_v2: get_arena_v2_credential failed for config {config_id}: {e}")
        return None


async def get_arena_v2_by_agent_id(virtuals_agent_id: str) -> Optional[Dict[str, Any]]:
    """Lookup by Virtuals agent id — used during deploy-poll before config_id link."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, config_id, virtuals_agent_id, agent_name,
                           agent_wallet_address, wallet_id,
                           signer_private_key_vault_id,
                           hl_api_wallet_key_vault_id,
                           dgclaw_api_key_vault_id,
                           status
                    FROM arena_agents_v2
                    WHERE virtuals_agent_id = %s
                    """,
                    (virtuals_agent_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    'agent_record_id': str(row[0]),
                    'user_id': str(row[1]),
                    'config_id': str(row[2]) if row[2] else None,
                    'virtuals_agent_id': row[3],
                    'agent_name': row[4],
                    'agent_wallet_address': row[5],
                    'wallet_id': row[6],
                    'signer_private_key_vault_id': str(row[7]) if row[7] else None,
                    'hl_api_wallet_key_vault_id': str(row[8]) if row[8] else None,
                    'dgclaw_api_key_vault_id': str(row[9]) if row[9] else None,
                    'status': row[10],
                }
    except Exception as e:
        logger.error(f"arena_v2: get_arena_v2_by_agent_id failed for {virtuals_agent_id}: {e}")
        return None


async def resolve_hl_credentials(
    trading_mode: str,
    user_id: str,
    config_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Single source of truth for Hyperliquid credential resolution.

    - trading_mode='hyperliquid' → user-attached HL credentials
    - trading_mode='virtuals'    → per-agent HL API wallet via arena_agents_v2

    Returns a dict with at least {api_wallet_key, wallet_address} or None.
    Fields mirror what HyperliquidLiveTradingService expects today, so
    callers don't have to care about the underlying trading_mode.
    """
    if trading_mode == 'hyperliquid':
        return await VaultManager.get_hyperliquid_credential(user_id)

    if trading_mode == 'virtuals':
        if not config_id:
            logger.error("arena_v2: resolve_hl_credentials requires config_id for virtuals mode")
            return None
        creds = await get_arena_v2_credential(config_id)
        if not creds:
            return None
        # Runtime trading requires a fully-deployed agent. Provisioning agents
        # are still mid-setup and can't trade yet.
        if creds.get('status') != 'active':
            logger.error(
                f"arena_v2: config {config_id} agent status={creds.get('status')} "
                f"(not active) — cannot resolve HL credentials yet"
            )
            return None
        hl_key = creds.get('hl_api_wallet_key')
        if not hl_key:
            logger.error(
                f"arena_v2: config {config_id} has no HL API wallet key — "
                f"authorize-hl-api-wallet may not have completed"
            )
            return None
        return {
            'api_wallet_key': hl_key,
            'wallet_address': creds['agent_wallet_address'],
            'trading_mode': 'virtuals',
            'agent_record_id': creds['agent_record_id'],
            'virtuals_agent_id': creds['virtuals_agent_id'],
        }

    logger.error(f"arena_v2: unsupported trading_mode for HL resolution: {trading_mode}")
    return None