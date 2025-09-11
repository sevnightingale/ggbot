"""
Scheduled extraction runner for periodic market data collection.

This module provides functionality to run the MCP-based extraction
on a schedule, ensuring fresh market data is available for trading decisions.
"""
import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Optional

from core.common.logger import logger
from core.common.config import DEFAULT_USER_ID
from extraction.extraction_main import extract_mcp_indicators, ExtractionManager


def _convert_manager_results_to_legacy(manager_results: Dict) -> Dict:
    """
    Convert ExtractionManager results to legacy format for compatibility.
    
    Args:
        manager_results: Results from ExtractionManager.extract_all()
        
    Returns:
        Results in legacy format
    """
    legacy_results = {}
    
    for source_name, source_results in manager_results.items():
        if isinstance(source_results, dict) and 'error' not in source_results:
            # Merge all source results into legacy format
            for symbol, symbol_results in source_results.items():
                if symbol not in legacy_results:
                    legacy_results[symbol] = {}
                
                if isinstance(symbol_results, dict):
                    for timeframe, result in symbol_results.items():
                        legacy_results[symbol][timeframe] = result
        else:
            # Handle source-level errors
            logger.error(f"Error in source {source_name}: {source_results.get('error', 'Unknown error')}")
    
    return legacy_results


async def run_scheduled_extraction(
    symbols: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None,
    user_id: str = DEFAULT_USER_ID,
    llm_model: str = "gpt-4o-mini",
    use_config: bool = True
):
    """
    Run a scheduled extraction using either configuration-driven or legacy mode.
    
    Args:
        symbols: List of trading symbols (optional, uses config if None and use_config=True)
        timeframes: List of timeframes (optional, uses config if None and use_config=True)
        user_id: User ID to associate with the data
        llm_model: LLM model to use for analysis (legacy mode only)
        use_config: Whether to use configuration-driven extraction (default: True)
        
    Returns:
        Extraction results dictionary
    """
    log = logger.bind(user_id=user_id)
    
    if use_config:
        # Use new configuration-driven approach
        log.info(f"Starting configuration-driven extraction at {datetime.utcnow().isoformat()}")
        
        try:
            # Create and initialize ExtractionManager
            manager = ExtractionManager(user_id)
            await manager.initialize_sources()
            
            # Run extraction using user configuration
            results = await manager.extract_all()
            
            # Convert results to legacy format for compatibility
            return _convert_manager_results_to_legacy(results)
            
        except Exception as e:
            log.error(f"Error in configuration-driven extraction: {str(e)}")
            return {"error": str(e)}
    
    else:
        # Use legacy MCP extraction for backward compatibility
        if not symbols or not timeframes:
            raise ValueError("symbols and timeframes are required when use_config=False")
            
        log.info(
            f"Starting legacy extraction for {len(symbols)} symbols, "
            f"{len(timeframes)} timeframes at {datetime.utcnow().isoformat()}"
        )
        
        # Run the legacy MCP extraction
        results = await extract_mcp_indicators(
            symbols=symbols,
            timeframes=timeframes,
            user_id=user_id,
            use_llm=True,
            llm_model=llm_model
        )
        
        # Log summary
        success_count = 0
        error_count = 0
        
        for symbol, timeframe_results in results.items():
            if isinstance(timeframe_results, dict):
                for timeframe, result in timeframe_results.items():
                    if isinstance(result, dict) and result.get("status") == "success":
                        success_count += 1
                    else:
                        error_count += 1
        
        log.info(
            f"Legacy extraction complete: {success_count} successful, {error_count} errors"
        )
        
        return results


def main():
    """
    Main entry point for scheduled extraction.
    
    Can be run from command line with arguments or used by cron/scheduler.
    """
    parser = argparse.ArgumentParser(
        description="Run scheduled extraction of market indicators"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated list of trading symbols (uses config by default)"
    )
    parser.add_argument(
        "--timeframes", 
        type=str,
        default=None,
        help="Comma-separated list of timeframes (uses config by default)"
    )
    parser.add_argument(
        "--use-config",
        action="store_true",
        default=True,
        help="Use configuration-driven extraction (default: True)"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy extraction mode (overrides --use-config)"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=DEFAULT_USER_ID,
        help="User ID to associate with the data"
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously with interval"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,  # 5 minutes
        help="Interval in seconds for continuous mode (default: 300)"
    )
    
    args = parser.parse_args()
    
    # Determine extraction mode
    use_config = args.use_config and not args.legacy
    
    # Parse symbols and timeframes if provided
    symbols = None
    timeframes = None
    
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    if args.timeframes:
        timeframes = [t.strip() for t in args.timeframes.split(",")]
    
    # Validate arguments for legacy mode
    if not use_config and (not symbols or not timeframes):
        print("Error: --symbols and --timeframes are required when using --legacy mode")
        return
    
    if use_config:
        logger.bind(user_id=args.user_id).info(f"Scheduled extraction starting in configuration-driven mode for user {args.user_id}")
    else:
        logger.bind(user_id=args.user_id).info(f"Scheduled extraction starting in legacy mode with symbols={symbols}, timeframes={timeframes}")
    
    async def run_once():
        """Run extraction once."""
        return await run_scheduled_extraction(
            symbols=symbols,
            timeframes=timeframes,
            user_id=args.user_id,
            llm_model=args.llm_model,
            use_config=use_config
        )
    
    async def run_continuous():
        """Run extraction continuously with interval."""
        while True:
            try:
                await run_once()
            except Exception as e:
                logger.error(f"Error in scheduled extraction: {e}")
            
            logger.info(f"Waiting {args.interval} seconds until next extraction...")
            await asyncio.sleep(args.interval)
    
    # Run the extraction
    if args.continuous:
        logger.info(f"Running in continuous mode with {args.interval}s interval")
        asyncio.run(run_continuous())
    else:
        results = asyncio.run(run_once())
        
        # Print summary for single run
        print("\n=== Extraction Summary ===")
        for symbol, timeframe_results in results.items():
            if isinstance(timeframe_results, dict):
                print(f"\n{symbol}:")
                for timeframe, result in timeframe_results.items():
                    if isinstance(result, dict):
                        status = result.get("status", "unknown")
                        if status == "success":
                            interpretation = result.get("interpretation") or {}
                            current_state = interpretation.get("current_state", "N/A")
                            confidence = interpretation.get("confidence_in_analysis", 0)
                            print(f"  {timeframe}: {status} - {current_state[:50]}... (confidence: {confidence:.2f})")
                        else:
                            error = result.get("error", "Unknown error")
                            print(f"  {timeframe}: {status} - {error}")


if __name__ == "__main__":
    main()