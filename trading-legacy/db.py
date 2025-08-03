"""
Database operations for the Trading module.

This module provides a PostgreSQL-based implementation of trade storage
and retrieval, replacing the MockDb used in testing.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from core.common.logger import logger


class TradeDb:
    """PostgreSQL-based trade database operations."""
    
    def __init__(self):
        """Initialize database connection pool."""
        # Get database configuration from environment
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'ggbot'),
            'user': os.getenv('DB_USER', 'ggbot_user'),
            'password': os.getenv('DB_PASS', 'ggbot123')
        }
        
        # Create connection pool
        self.pool = SimpleConnectionPool(
            1,  # Min connections
            10,  # Max connections
            **self.db_config
        )
        
        logger.info("TradeDb initialized with PostgreSQL connection pool")
    
    def _get_connection(self):
        """Get a connection from the pool."""
        return self.pool.getconn()
    
    def _put_connection(self, conn):
        """Return a connection to the pool."""
        self.pool.putconn(conn)
    
    async def create_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new trade record in the database.
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            Dictionary with trade_id on success
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Map fields from Trade model to database columns
            db_data = {
                'trade_id': trade_data.get('trade_id'),
                'user_id': trade_data.get('user_id'),
                'config_id': trade_data.get('config_id'),
                'exchange': trade_data.get('exchange'),
                'symbol': trade_data.get('symbol'),  # Database now uses 'symbol' not 'pair'
                'trade_status': trade_data.get('status', 'open'),
                'opened_at': trade_data.get('created_at', datetime.utcnow()),
                'entry_price': trade_data.get('entry_price'),
                'stop_loss': trade_data.get('stop_loss_price'),
                'take_profit': trade_data.get('take_profit_price'),
                'leverage': trade_data.get('leverage'),
                'collateral_amount': trade_data.get('collateral_amount'),
                'confidence_score': trade_data.get('confidence'),
                'reasoning_log': trade_data.get('reasoning')
            }
            
            # Build INSERT query
            columns = []
            values = []
            placeholders = []
            
            for key, value in db_data.items():
                if value is not None:
                    columns.append(key)
                    values.append(value)
                    placeholders.append('%s')
            
            query = f"""
                INSERT INTO trades ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING trade_id
            """
            
            cursor.execute(query, values)
            result = cursor.fetchone()
            conn.commit()
            
            logger.info(f"Created trade record: {result['trade_id']}")
            
            return {'trade_id': str(result['trade_id'])}
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating trade: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._put_connection(conn)
    
    async def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a trade record by ID.
        
        Args:
            trade_id: UUID of the trade
            
        Returns:
            Trade data dictionary or None if not found
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM trades
                WHERE trade_id = %s
            """
            
            cursor.execute(query, (trade_id,))
            result = cursor.fetchone()
            
            if result:
                # Convert to dict and map database fields to model fields
                trade_data = dict(result)
                
                # No mapping needed - use symbol directly
                
                # No mapping needed - use trade_status directly
                
                # Parse JSON fields
                if trade_data.get('execution_details'):
                    try:
                        trade_data['execution_details'] = json.loads(trade_data['execution_details'])
                    except json.JSONDecodeError:
                        pass
                
                return trade_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting trade {trade_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._put_connection(conn)
    
    async def update_trade(self, trade_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing trade record.
        
        Args:
            trade_id: UUID of the trade
            update_data: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Map model fields to database fields
            db_updates = {}
            
            # Direct mappings
            field_mappings = {
                'stop_loss_price': 'stop_loss',
                'take_profit_price': 'take_profit'
            }
            
            for model_field, db_field in field_mappings.items():
                if model_field in update_data:
                    db_updates[db_field] = update_data[model_field]
            
            # Copy other fields directly
            direct_fields = [
                'entry_price', 'exit_price', 'profit_loss', 
                'closed_at', 'execution_details'
            ]
            
            for field in direct_fields:
                if field in update_data:
                    if field == 'execution_details':
                        db_updates[field] = json.dumps(update_data[field])
                    else:
                        db_updates[field] = update_data[field]
            
            # Build UPDATE query
            set_clauses = []
            values = []
            
            for key, value in db_updates.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
            
            if not set_clauses:
                return True  # Nothing to update
            
            values.append(trade_id)  # Add trade_id for WHERE clause
            
            query = f"""
                UPDATE trades
                SET {', '.join(set_clauses)}
                WHERE trade_id = %s
            """
            
            cursor.execute(query, values)
            updated = cursor.rowcount > 0
            conn.commit()
            
            if updated:
                logger.info(f"Updated trade {trade_id}")
            
            return updated
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating trade {trade_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._put_connection(conn)
    
    async def get_active_trades(self, user_id: str, trade_status: Optional[str] = 'open') -> List[Dict[str, Any]]:
        """
        Get active trades for a user.
        
        Args:
            user_id: User UUID
            trade_status: Trade status to filter by
            
        Returns:
            List of trade dictionaries
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM trades
                WHERE user_id = %s
                AND trade_status = %s
                ORDER BY opened_at DESC
            """
            
            cursor.execute(query, (user_id, trade_status))
            results = cursor.fetchall()
            
            trades = []
            for result in results:
                trade_data = dict(result)
                
                # No mapping needed - use trade_status directly
                
                # Parse JSON fields
                if trade_data.get('execution_details'):
                    try:
                        trade_data['execution_details'] = json.loads(trade_data['execution_details'])
                    except json.JSONDecodeError:
                        pass
                
                trades.append(trade_data)
            
            logger.debug(f"Found {len(trades)} active trades for user {user_id}")
            return trades
            
        except Exception as e:
            logger.error(f"Error getting active trades: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._put_connection(conn)
    
    def close(self):
        """Close all connections in the pool."""
        if hasattr(self, 'pool'):
            self.pool.closeall()
            logger.info("TradeDb connection pool closed")


# Create a singleton instance
_db_instance = None

def get_trade_db() -> TradeDb:
    """Get the singleton TradeDb instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = TradeDb()
    return _db_instance