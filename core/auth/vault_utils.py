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