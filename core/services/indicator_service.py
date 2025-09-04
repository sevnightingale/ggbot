# core/services/indicator_service.py
"""
Indicator and Data Source Management Service

Provides dynamic indicator management with premium gating, quality control,
and user-specific access control for the multi-tier business model.
"""

from typing import List, Dict, Any, Optional
from core.common.db import get_db_connection
from core.common.logger import logger


class IndicatorService:
    """Service for managing indicators and data sources with premium gating."""
    
    @staticmethod
    async def get_user_available_indicators(user_id: str) -> List[Dict[str, Any]]:
        """
        Get all indicators available to a user based on their subscription tier.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of indicator dictionaries with metadata
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get user's subscription tier
                    cur.execute("""
                        SELECT subscription_tier 
                        FROM user_profiles 
                        WHERE user_id = %s;
                    """, (user_id,))
                    
                    profile_result = cur.fetchone()
                    is_premium = profile_result and profile_result[0] == 'signals' if profile_result else False
                    
                    # Get indicators based on user access
                    if is_premium:
                        # Premium users get all indicators
                        cur.execute("""
                            SELECT indicator_id, name, display_name, description, 
                                   category, status, requires_premium, default_params, sort_order
                            FROM indicators 
                            WHERE enabled = TRUE 
                            ORDER BY sort_order ASC, display_name ASC;
                        """)
                    else:
                        # Free users only get non-premium indicators
                        cur.execute("""
                            SELECT indicator_id, name, display_name, description, 
                                   category, status, requires_premium, default_params, sort_order
                            FROM indicators 
                            WHERE enabled = TRUE AND requires_premium = FALSE
                            ORDER BY sort_order ASC, display_name ASC;
                        """)
                    
                    indicators = cur.fetchall()
                    return [
                        {
                            'indicator_id': str(row[0]),
                            'name': row[1],
                            'display_name': row[2],
                            'description': row[3],
                            'category': row[4],
                            'status': row[5],
                            'requires_premium': row[6],
                            'default_params': row[7] or {},
                            'sort_order': row[8],
                            'available': True  # All returned indicators are available to user
                        }
                        for row in indicators
                    ]
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to get user indicators: {e}")
            return []
    
    @staticmethod
    async def get_all_indicators_with_access(user_id: str) -> List[Dict[str, Any]]:
        """
        Get ALL indicators with user access status (for premium upsell display).
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of all indicators with 'available' flag indicating user access
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if user is premium
                    cur.execute("""
                        SELECT subscription_tier 
                        FROM user_profiles 
                        WHERE user_id = %s;
                    """, (user_id,))
                    
                    profile_result = cur.fetchone()
                    is_premium = profile_result and profile_result[0] == 'signals' if profile_result else False
                    
                    # Get all indicators
                    cur.execute("""
                        SELECT indicator_id, name, display_name, description, 
                               category, status, requires_premium, default_params, sort_order
                        FROM indicators 
                        WHERE enabled = TRUE 
                        ORDER BY sort_order ASC, display_name ASC;
                    """)
                    
                    indicators = cur.fetchall()
                    return [
                        {
                            'indicator_id': str(row[0]),
                            'name': row[1],
                            'display_name': row[2],
                            'description': row[3],
                            'category': row[4],
                            'status': row[5],
                            'requires_premium': row[6],
                            'default_params': row[7] or {},
                            'sort_order': row[8],
                            'available': is_premium or not row[6]  # Available if premium user OR not premium-required
                        }
                        for row in indicators
                    ]
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to get all indicators: {e}")
            return []
    
    @staticmethod
    async def get_available_data_sources(user_id: str) -> List[Dict[str, Any]]:
        """
        Get all data sources available to a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of data source dictionaries
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if user is premium
                    cur.execute("""
                        SELECT subscription_tier 
                        FROM user_profiles 
                        WHERE user_id = %s;
                    """, (user_id,))
                    
                    profile_result = cur.fetchone()
                    is_premium = profile_result and profile_result[0] == 'signals' if profile_result else False
                    
                    # Get data sources based on user access
                    if is_premium:
                        # Premium users get all sources
                        cur.execute("""
                            SELECT source_id, name, display_name, description, requires_premium
                            FROM data_sources 
                            WHERE enabled = TRUE 
                            ORDER BY display_name ASC;
                        """)
                    else:
                        # Free users only get non-premium sources
                        cur.execute("""
                            SELECT source_id, name, display_name, description, requires_premium
                            FROM data_sources 
                            WHERE enabled = TRUE AND requires_premium = FALSE
                            ORDER BY display_name ASC;
                        """)
                    
                    sources = cur.fetchall()
                    return [
                        {
                            'source_id': str(row[0]),
                            'name': row[1],
                            'display_name': row[2],
                            'description': row[3],
                            'requires_premium': row[4],
                            'available': True  # All returned sources are available
                        }
                        for row in sources
                    ]
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to get data sources: {e}")
            return []
    
    @staticmethod
    async def check_indicator_access(user_id: str, indicator_name: str) -> bool:
        """
        Check if a user has access to a specific indicator.
        
        Args:
            user_id: UUID of the user
            indicator_name: Name of the indicator to check
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check indicator requirements and user access
                    cur.execute("""
                        SELECT i.requires_premium, up.subscription_tier
                        FROM indicators i
                        LEFT JOIN user_profiles up ON up.user_id = %s
                        WHERE i.name = %s AND i.enabled = TRUE;
                    """, (user_id, indicator_name))
                    
                    result = cur.fetchone()
                    if not result:
                        return False  # Indicator doesn't exist or is disabled
                    
                    requires_premium, user_tier = result
                    
                    # Access granted if indicator is free OR user has premium subscription
                    return not requires_premium or user_tier == 'signals'
                    
        except Exception as e:
            logger.bind(user_id=user_id).error(f"Failed to check indicator access: {e}")
            return False
    
    @staticmethod
    async def get_indicators_by_category() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all indicators grouped by category for admin/management purposes.
        
        Returns:
            Dictionary with category names as keys and indicator lists as values
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT indicator_id, name, display_name, description, 
                               category, status, requires_premium, default_params, sort_order
                        FROM indicators 
                        WHERE enabled = TRUE 
                        ORDER BY category ASC, sort_order ASC, display_name ASC;
                    """)
                    
                    indicators = cur.fetchall()
                    grouped = {}
                    
                    for row in indicators:
                        category = row[4] or 'uncategorized'
                        if category not in grouped:
                            grouped[category] = []
                            
                        grouped[category].append({
                            'indicator_id': str(row[0]),
                            'name': row[1],
                            'display_name': row[2],
                            'description': row[3],
                            'status': row[5],
                            'requires_premium': row[6],
                            'default_params': row[7] or {},
                            'sort_order': row[8]
                        })
                    
                    return grouped
                    
        except Exception as e:
            logger.error(f"Failed to get indicators by category: {e}")
            return {}


# Convenience functions
async def get_user_indicators(user_id: str) -> List[Dict[str, Any]]:
    """Get indicators available to user. Convenience wrapper."""
    return await IndicatorService.get_user_available_indicators(user_id)

async def get_user_data_sources(user_id: str) -> List[Dict[str, Any]]:
    """Get data sources available to user. Convenience wrapper."""
    return await IndicatorService.get_available_data_sources(user_id)

async def can_use_indicator(user_id: str, indicator_name: str) -> bool:
    """Check if user can use an indicator. Convenience wrapper."""
    return await IndicatorService.check_indicator_access(user_id, indicator_name)