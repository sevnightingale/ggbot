#!/usr/bin/env python3
"""
Test script for Decision Engine V2 integration with dynamic LLM providers.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decision.engine_v2 import DecisionEngineV2


async def test_decision_engine():
    """Test DecisionEngineV2 with dynamic LLM provider selection."""
    print("🤖 Testing DecisionEngineV2 Integration")
    print("=" * 50)

    # Test with existing config ID
    config_id = "18665f58-fb3c-4655-a648-449427be0073"  # Actual config
    user_id = "00000000-0000-0000-0000-000000000000"   # Actual user

    try:
        # Create decision engine
        engine = DecisionEngineV2(config_id=config_id, user_id=user_id)
        print(f"✅ DecisionEngineV2 created")

        # Initialize (this should load config and create LLM provider)
        await engine.initialize()
        print(f"✅ Engine initialized successfully")

        # Check that LLM provider was created
        if engine.llm_provider:
            provider_type = engine.llm_provider.__class__.__name__
            model = engine.llm_provider.model
            print(f"✅ LLM Provider: {provider_type} with model {model}")
        else:
            print("❌ No LLM provider created")
            return

        print("\n🎉 DecisionEngineV2 integration test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    print("🚀 Starting DecisionEngineV2 Integration Test\n")
    asyncio.run(test_decision_engine())
    print("\n✨ Test completed!")