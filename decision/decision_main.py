"""
Decision Module Main Entry Point.

This module provides the main function to run the decision-making process.
It can be called from scheduled tasks or API endpoints.
"""

import asyncio
import argparse
from typing import Dict, Any, Optional
from core.common.config import DEFAULT_USER_ID
from core.common.logger import logger
from decision.engine import DecisionEngine


async def run_decision_process(
    user_id: str = DEFAULT_USER_ID,
    config_id: Optional[str] = None,
    config_name: str = 'default',
    symbol: str = 'BTC/USD',
    timeframes: Optional[list] = None
) -> Dict[str, Any]:
    """
    Run the decision-making process for a user.
    
    Args:
        user_id (str): UUID of the user
        config_id (Optional[str]): UUID of the configuration (if known)
        config_name (str): Name of the configuration to use (if config_id not provided)
        symbol (str): Trading symbol to analyze
        timeframes (Optional[list]): Timeframes to analyze
        
    Returns:
        Dict[str, Any]: Trading intent or error information
    """
    try:
        # If config_id not provided, look it up by name
        if not config_id:
            from decision.utils import get_config_id_by_name
            config_id = get_config_id_by_name(user_id, config_name)
            if not config_id:
                raise ValueError(f"No configuration found with name '{config_name}'")
        
        # Initialize the decision engine
        engine = DecisionEngine(user_id, config_id)
        await engine.initialize()
        
        # Make the decision
        intent = await engine.make_decision(symbol, timeframes)
        
        logger.bind(module="decision.main").info(
            f"Decision process completed: {intent['action']} "
            f"with confidence {intent['confidence']}"
        )
        
        return intent
        
    except Exception as e:
        logger.bind(module="decision.main").error(
            f"Error in decision process: {str(e)}"
        )
        return {
            'action': 'error',
            'error': str(e),
            'user_id': user_id,
            'config_id': config_id
        }


def main():
    """
    Command-line entry point for the decision module.
    """
    parser = argparse.ArgumentParser(description='Run trading decision process')
    parser.add_argument('--user-id', default=DEFAULT_USER_ID, help='User UUID')
    parser.add_argument('--config-id', help='Configuration UUID')
    parser.add_argument('--config-name', default='default', help='Configuration name')
    parser.add_argument('--symbol', default='BTC/USD', help='Trading symbol')
    parser.add_argument('--timeframes', nargs='+', default=['15m', '1h', '4h'],
                        help='Timeframes to analyze')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Run without executing trades')
    
    args = parser.parse_args()
    
    # Run the async function
    intent = asyncio.run(run_decision_process(
        user_id=args.user_id,
        config_id=args.config_id,
        config_name=args.config_name,
        symbol=args.symbol,
        timeframes=args.timeframes
    ))
    
    # Print the result
    if intent.get('action') == 'error':
        print(f"Error: {intent.get('error')}")
    else:
        print(f"Decision: {intent.get('action')}")
        print(f"Confidence: {intent.get('confidence')}")
        if intent.get('reasoning'):
            print(f"Reasoning: {intent.get('reasoning')[:200]}...")
    
    # If not dry run and we have a real trading action, we could call the trading module here
    if not args.dry_run and intent.get('action') in ['open_position', 'close_position', 'adjust_position']:
        print("\nNote: In production, this intent would be sent to the Trading Module")


if __name__ == '__main__':
    main()