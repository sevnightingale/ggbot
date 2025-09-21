"""
LLM API Key Resolution Service

Handles resolution of API keys with priority system:
1. User's encrypted key from Supabase Vault
2. Platform key from environment variables
3. Error if neither available
"""

import os
from typing import Optional
from core.common.logger import logger
from core.common.db import get_db_connection


class LLMKeyService:
    """Service for resolving LLM API keys with user/platform fallback."""

    @staticmethod
    async def get_api_key(user_id: str, provider: str) -> str:
        """
        Get API key for a user and provider with priority system.

        Priority:
        1. User's encrypted key from Supabase Vault
        2. Platform key from environment variables
        3. Raise error if neither available

        Args:
            user_id: User ID to check for personal API keys
            provider: LLM provider name ('openai', 'deepseek', 'anthropic')

        Returns:
            str: API key to use

        Raises:
            ValueError: If no API key is available
        """
        logger.bind(user_id=user_id, provider=provider).debug("Resolving API key")

        # Step 1: Check for user's personal API key
        user_key = await LLMKeyService._get_user_api_key(user_id, provider)
        if user_key:
            logger.bind(user_id=user_id, provider=provider).info("Using user's personal API key")
            return user_key

        # Step 2: Fallback to platform API key
        platform_key = LLMKeyService._get_platform_api_key(provider)
        if platform_key:
            logger.bind(user_id=user_id, provider=provider).info("Using platform API key")
            return platform_key

        # Step 3: No key available
        raise ValueError(f"No API key available for {provider}. User {user_id} has no personal key and no platform key is configured.")

    @staticmethod
    async def _get_user_api_key(user_id: str, provider: str) -> Optional[str]:
        """
        Get user's encrypted API key from Supabase Vault.

        Args:
            user_id: User ID
            provider: Provider name

        Returns:
            Decrypted API key or None if not found
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if user has a credential for this provider
                    cur.execute("""
                        SELECT vault_secret_id, credential_name
                        FROM user_llm_credentials
                        WHERE user_id = %s AND provider = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (user_id, provider))

                    result = cur.fetchone()
                    if not result:
                        return None

                    vault_secret_id, credential_name = result

                    # Decrypt from Supabase Vault using SQL function
                    # Note: This uses Supabase's vault.decrypt_secret function
                    cur.execute("""
                        SELECT vault.decrypt_secret(%s) as decrypted_key
                    """, (vault_secret_id,))

                    vault_result = cur.fetchone()
                    if not vault_result or not vault_result[0]:
                        logger.bind(user_id=user_id, provider=provider).warning(
                            f"Failed to decrypt user API key '{credential_name}' from vault"
                        )
                        return None

                    decrypted_key = vault_result[0]
                    logger.bind(user_id=user_id, provider=provider).info(
                        f"Successfully retrieved user API key '{credential_name}' from vault"
                    )
                    return decrypted_key

        except Exception as e:
            logger.bind(user_id=user_id, provider=provider).error(
                f"Error retrieving user API key from vault: {e}"
            )
            return None

    @staticmethod
    def _get_platform_api_key(provider: str) -> Optional[str]:
        """
        Get platform API key from environment variables.

        Args:
            provider: Provider name ('openai', 'deepseek', 'anthropic')

        Returns:
            API key from environment or None if not found
        """
        env_var_map = {
            'openai': 'OPENAI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'xai': 'XAI_API_KEY',
            'grok': 'XAI_API_KEY'
        }

        env_var = env_var_map.get(provider.lower())
        if not env_var:
            logger.warning(f"Unknown provider '{provider}', cannot map to environment variable")
            return None

        api_key = os.getenv(env_var)
        if not api_key:
            logger.warning(f"Platform API key not found in environment: {env_var}")
            return None

        return api_key

    @staticmethod
    async def store_user_api_key(user_id: str, provider: str, credential_name: str, api_key: str) -> str:
        """
        Store user's API key encrypted in Supabase Vault.

        Args:
            user_id: User ID
            provider: Provider name
            credential_name: User-defined name for the credential
            api_key: API key to encrypt and store

        Returns:
            credential_id: UUID of the stored credential

        Raises:
            ValueError: If storage fails
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # First encrypt the API key in Supabase Vault
                    cur.execute("""
                        SELECT vault.create_secret(%s) as vault_secret_id
                    """, (api_key,))

                    vault_result = cur.fetchone()
                    if not vault_result or not vault_result[0]:
                        raise ValueError("Failed to encrypt API key in vault")

                    vault_secret_id = vault_result[0]

                    # Store the credential reference
                    cur.execute("""
                        INSERT INTO user_llm_credentials (
                            user_id, provider, credential_name, vault_secret_id
                        ) VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (user_id, provider, credential_name, vault_secret_id))

                    result = cur.fetchone()
                    if not result:
                        raise ValueError("Failed to store credential reference")

                    credential_id = result[0]
                    conn.commit()

                    logger.bind(user_id=user_id, provider=provider).info(
                        f"Successfully stored user API key '{credential_name}' in vault"
                    )

                    return str(credential_id)

        except Exception as e:
            logger.bind(user_id=user_id, provider=provider).error(
                f"Error storing user API key: {e}"
            )
            raise ValueError(f"Failed to store API key: {e}")

    @staticmethod
    async def list_user_credentials(user_id: str) -> list:
        """
        List all stored credentials for a user.

        Args:
            user_id: User ID

        Returns:
            List of credential info dictionaries
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, provider, credential_name, created_at, updated_at
                        FROM user_llm_credentials
                        WHERE user_id = %s
                        ORDER BY provider, credential_name
                    """, (user_id,))

                    results = cur.fetchall()
                    credentials = []

                    for row in results:
                        credentials.append({
                            'id': str(row[0]),
                            'provider': row[1],
                            'credential_name': row[2],
                            'created_at': row[3].isoformat(),
                            'updated_at': row[4].isoformat()
                        })

                    return credentials

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error listing user credentials: {e}")
            return []

    @staticmethod
    async def delete_user_credential(user_id: str, credential_id: str) -> bool:
        """
        Delete a user's stored credential.

        Args:
            user_id: User ID (for security check)
            credential_id: Credential ID to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get vault_secret_id before deletion for cleanup
                    cur.execute("""
                        SELECT vault_secret_id, credential_name
                        FROM user_llm_credentials
                        WHERE id = %s AND user_id = %s
                    """, (credential_id, user_id))

                    result = cur.fetchone()
                    if not result:
                        logger.bind(user_id=user_id).warning(
                            f"Credential {credential_id} not found or not owned by user"
                        )
                        return False

                    vault_secret_id, credential_name = result

                    # Delete the credential record
                    cur.execute("""
                        DELETE FROM user_llm_credentials
                        WHERE id = %s AND user_id = %s
                    """, (credential_id, user_id))

                    if cur.rowcount == 0:
                        return False

                    # Delete the secret from vault (optional, vault handles cleanup)
                    try:
                        cur.execute("""
                            SELECT vault.delete_secret(%s)
                        """, (vault_secret_id,))
                    except Exception as vault_error:
                        logger.bind(user_id=user_id).warning(
                            f"Failed to delete vault secret {vault_secret_id}: {vault_error}"
                        )
                        # Continue anyway since credential record was deleted

                    conn.commit()

                    logger.bind(user_id=user_id).info(
                        f"Successfully deleted credential '{credential_name}'"
                    )

                    return True

        except Exception as e:
            logger.bind(user_id=user_id).error(f"Error deleting credential: {e}")
            return False