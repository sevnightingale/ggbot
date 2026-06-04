"""
Test script to enable funding rates and run a test extraction + decision.

This script demonstrates the end-to-end flow:
1. Load a bot config
2. Enable funding rates in config
3. Run extraction (technical + funding rates)
4. Run decision (should see funding rates in reasoning)
"""

import asyncio
from core.services.config_service import ConfigService
from extraction.v2.engine import ExtractionEngineV2
from decision.engine_v2 import DecisionEngineV2
from core.common.logger import logger


async def test_funding_rates_integration():
    """Test funding rates flowing through extraction → decision pipeline."""

    # Configuration
    USER_ID = "YOUR_USER_ID"  # Replace with actual user ID
    CONFIG_ID = "YOUR_CONFIG_ID"  # Replace with actual config ID

    logger.info("=" * 80)
    logger.info("TESTING: Funding Rates Integration (Orchestrator → Decision Engine)")
    logger.info("=" * 80)

    # Step 1: Load config
    logger.info(f"\n📋 Step 1: Loading config {CONFIG_ID}")
    config_service = ConfigService()
    config = await config_service.get_config(CONFIG_ID, USER_ID)

    if not config:
        logger.error(f"Config {CONFIG_ID} not found for user {USER_ID}")
        return

    logger.info(f"✅ Config loaded: {config.config_name}")
    logger.info(f"   Symbol: {config.selected_pair}")

    # Step 2: Enable funding rates in config
    logger.info(f"\n⚙️  Step 2: Enabling funding rates in config")
    if 'selected_data_sources' not in config.extraction:
        config.extraction['selected_data_sources'] = {}

    config.extraction['selected_data_sources']['derivatives_leverage'] = {
        'data_points': ['btc_funding_rate', 'eth_funding_rate']
    }

    # Save updated config
    updated_config = await config_service.update_config(CONFIG_ID, USER_ID, {
        'extraction': config.extraction
    })

    logger.info("✅ Funding rates enabled:")
    logger.info("   - BTC Funding Rate")
    logger.info("   - ETH Funding Rate")

    # Step 3: Run extraction
    logger.info(f"\n📊 Step 3: Running extraction with funding rates")
    extraction_engine = ExtractionEngineV2(
        user_id=USER_ID,
        use_advanced_preprocessing=True,
        use_database_storage=False
    )

    # Get indicators from config
    technical_config = config.extraction.get('selected_data_sources', {}).get('technical_analysis', {})
    indicators = technical_config.get('data_points', ['rsi', 'macd'])

    # Import and use orchestrator's extraction wrapper
    from ggbot import GGBotOrchestrator
    orchestrator = GGBotOrchestrator()

    extraction_result = await orchestrator._run_extraction_v2(
        extraction_engine=extraction_engine,
        config=config,
        user_id=USER_ID,
        indicators=indicators,
        timeframes=['1h']
    )

    # Check results
    logger.info("\n✅ Extraction completed:")
    logger.info(f"   Technical indicators: {extraction_result.get('status')}")

    if 'market_intelligence' in extraction_result:
        market_intel = extraction_result['market_intelligence']
        logger.info(f"   Market intelligence categories: {list(market_intel.keys())}")

        if 'derivatives_leverage' in market_intel:
            derivatives = market_intel['derivatives_leverage']
            logger.info(f"   Funding rates fetched: {list(derivatives.keys())}")

            # Show BTC funding rate details
            if 'btc_funding_rate' in derivatives:
                btc_funding = derivatives['btc_funding_rate']
                logger.info(f"\n   BTC Funding Rate Details:")
                logger.info(f"      Rate: {btc_funding.get('funding_rate_pct', 'N/A')}%")
                interp = btc_funding.get('interpretation', {})
                logger.info(f"      Level: {interp.get('level', 'N/A')}")
                logger.info(f"      Risk: {interp.get('risk', 'N/A')}")
                logger.info(f"      Implication: {interp.get('trading_implication', 'N/A')}")
    else:
        logger.warning("   ⚠️  No market intelligence in extraction result!")

    # Step 4: Run decision
    logger.info(f"\n🧠 Step 4: Running decision engine")
    decision_engine = DecisionEngineV2(CONFIG_ID, USER_ID)
    await decision_engine.initialize()

    market_intelligence = extraction_result.get('market_intelligence', {})

    decision_result = await decision_engine.make_decision(
        symbol=config.selected_pair,
        market_intelligence=market_intelligence
    )

    logger.info("\n✅ Decision completed:")
    logger.info(f"   Action: {decision_result.get('action')}")
    logger.info(f"   Confidence: {decision_result.get('confidence', 0):.3f}")

    # Check if funding rates mentioned in reasoning
    reasoning = decision_result.get('reasoning', '')
    if 'funding' in reasoning.lower() or 'derivative' in reasoning.lower():
        logger.info(f"   ✅ FUNDING RATES MENTIONED IN REASONING!")
        logger.info(f"\n📝 Decision Reasoning Excerpt:")
        # Show first 500 chars of reasoning
        logger.info(f"   {reasoning[:500]}...")
    else:
        logger.warning(f"   ⚠️  Funding rates NOT mentioned in reasoning")
        logger.info(f"\n📝 Full Reasoning:")
        logger.info(f"   {reasoning}")

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    asyncio.run(test_funding_rates_integration())
