"""
Hummingbot Instance Manager

Maps config_id to persistent Hummingbot instances for paper trading isolation.
Prevents random instance creation and ensures one instance per configuration.
"""

import uuid
from typing import Dict, Optional
from core.common.logger import logger
from core.common.db import get_db_connection


class HummingbotInstanceManager:
    """
    Maps config_id to Hummingbot bot instances for paper trading isolation.
    
    Key responsibilities:
    - Generate consistent instance names from user_id + config_id
    - Maintain config_instances table mapping
    - Ensure one instance per configuration
    - Support account isolation for multi-user paper trading
    """
    
    def get_instance_name(self, user_id: str, config_id: str) -> str:
        """
        Generate consistent instance name from user_id and config_id.
        
        Format: ggbot-{user_id[:8]}-{config_id[:8]}
        Example: ggbot-e249bb49-a1b2c3d4
        """
        return f"ggbot-{user_id[:8]}-{config_id[:8]}"
    
    def get_account_name(self, user_id: str, config_id: str) -> str:
        """
        Generate consistent account name for paper trading.
        
        Format: paper_ggbot_{user_id[:8]}_{config_id[:8]}
        Example: paper_ggbot_e249bb49_a1b2c3d4
        """
        return f"paper_ggbot_{user_id[:8]}_{config_id[:8]}"
    
    async def ensure_mapping(self, user_id: str, config_id: str) -> Dict[str, str]:
        """
        Ensure config-to-instance mapping exists, creating if needed.
        
        Args:
            user_id: User UUID string
            config_id: Configuration UUID string
            
        Returns:
            Dict with config_id, instance_name, hummingbot_account
        """
        try:
            # Check if mapping already exists
            existing = await self._get_mapping(config_id)
            if existing:
                logger.bind(service="instance_manager").info(
                    f"Using existing mapping for config {config_id}: {existing['instance_name']}"
                )
                return existing
            
            # Create new mapping
            instance_name = self.get_instance_name(user_id, config_id)
            account_name = self.get_account_name(user_id, config_id)
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO config_instances (config_id, instance_name, hummingbot_account)
                        VALUES (%s, %s, %s)
                    """, (config_id, instance_name, account_name))
                    conn.commit()
            
            mapping = {
                'config_id': config_id,
                'instance_name': instance_name,
                'hummingbot_account': account_name
            }
            
            logger.bind(service="instance_manager").info(
                f"Created new mapping for config {config_id}: {instance_name}"
            )
            
            return mapping
            
        except Exception as e:
            logger.error(f"Failed to ensure mapping for config {config_id}: {e}")
            raise
    
    async def _get_mapping(self, config_id: str) -> Optional[Dict[str, str]]:
        """Get existing mapping for config_id."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT config_id, instance_name, hummingbot_account, status
                        FROM config_instances 
                        WHERE config_id = %s
                    """, (config_id,))
                    
                    result = cur.fetchone()
                    if result:
                        return {
                            'config_id': str(result[0]),
                            'instance_name': result[1],
                            'hummingbot_account': result[2],
                            'status': result[3]
                        }
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get mapping for config {config_id}: {e}")
            return None
    
    async def get_mapping(self, config_id: str) -> Optional[Dict[str, str]]:
        """Public method to get existing mapping (no creation)."""
        return await self._get_mapping(config_id)
    
    async def disable_mapping(self, config_id: str) -> bool:
        """
        Disable instance mapping (for cleanup/reset scenarios).
        
        Args:
            config_id: Configuration UUID string
            
        Returns:
            True if successfully disabled, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE config_instances 
                        SET status = 'disabled'
                        WHERE config_id = %s
                    """, (config_id,))
                    
                    if cur.rowcount > 0:
                        conn.commit()
                        logger.bind(service="instance_manager").info(
                            f"Disabled mapping for config {config_id}"
                        )
                        return True
                    else:
                        logger.bind(service="instance_manager").warning(
                            f"No mapping found to disable for config {config_id}"
                        )
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to disable mapping for config {config_id}: {e}")
            return False
    
    async def list_active_mappings(self, user_id: Optional[str] = None) -> list:
        """
        List all active instance mappings.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of mapping dictionaries
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        # Filter by user_id via configurations table
                        cur.execute("""
                            SELECT ci.config_id, ci.instance_name, ci.hummingbot_account, 
                                   ci.status, ci.paper_balance_usd, c.config_name
                            FROM config_instances ci
                            JOIN configurations c ON ci.config_id = c.config_id
                            WHERE c.user_id = %s AND ci.status = 'active'
                            ORDER BY ci.created_at DESC
                        """, (user_id,))
                    else:
                        # All active mappings
                        cur.execute("""
                            SELECT ci.config_id, ci.instance_name, ci.hummingbot_account, 
                                   ci.status, ci.paper_balance_usd, c.config_name
                            FROM config_instances ci
                            JOIN configurations c ON ci.config_id = c.config_id
                            WHERE ci.status = 'active'
                            ORDER BY ci.created_at DESC
                        """)
                    
                    results = cur.fetchall()
                    mappings = []
                    
                    for row in results:
                        mappings.append({
                            'config_id': str(row[0]),
                            'instance_name': row[1],
                            'hummingbot_account': row[2],
                            'status': row[3],
                            'paper_balance_usd': float(row[4]) if row[4] else 10000.00,
                            'config_name': row[5]
                        })
                    
                    return mappings
                    
        except Exception as e:
            logger.error(f"Failed to list active mappings: {e}")
            return []