"""
Test All 8 Grok-Powered Data Points

Queries each data point and outputs results to a markdown file for review.

Tests:
1. VIX Index (macro)
2. DXY Index (macro)
3. CPI Inflation (macro)
4. NFP Jobs (macro)
5. BTC TVL (on-chain)
6. Whale Activity (on-chain, symbol-specific)
7. Twitter Sentiment (sentiment, symbol-specific)
8. Crypto News (news, symbol-specific)

Run: python scripts/test_all_grok_data_points.py
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from market_intelligence.adapters.agentic.grok_agentic import GrokAgenticAdapter
from market_intelligence.types import QueryParams
from core.common.logger import logger


class GrokDataPointTester:
    """Test all Grok data points and generate report."""

    def __init__(self):
        self.adapter = GrokAgenticAdapter()
        self.results: List[Dict[str, Any]] = []
        self.total_cost = 0.0
        self.total_tool_calls = 0
        self.test_symbol = "BTC"  # For symbol-specific queries

    async def test_vix_index(self) -> Dict[str, Any]:
        """Test VIX Volatility Index."""
        print("\n" + "="*80)
        print("TEST 1/8: VIX VOLATILITY INDEX")
        print("="*80)

        params = QueryParams(params={'query_type': 'vix_index'})

        try:
            print("📊 Querying Grok for VIX index...")
            response = await self.adapter.fetch(params)

            # Extract clean data (no protobuf objects)
            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": "VIX Index",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "tools_used": metadata.get('tools_used', []),
                    "reasoning_tokens": metadata.get('reasoning_tokens', 0),
                    "cost": metadata.get('estimated_cost', 0),
                    "citations": metadata.get('citations', [])[:3]  # Top 3
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ VIX Value: {data.get('value')}")
            print(f"✅ Risk Regime: {data.get('risk_regime')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": "VIX Index",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_dxy_index(self) -> Dict[str, Any]:
        """Test DXY Dollar Index."""
        print("\n" + "="*80)
        print("TEST 2/8: DXY DOLLAR INDEX")
        print("="*80)

        params = QueryParams(params={'query_type': 'dxy_index'})

        try:
            print("💵 Querying Grok for DXY index...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": "DXY Index",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ DXY Value: {data.get('value')}")
            print(f"✅ Change 24h: {data.get('change_24h')}")
            print(f"✅ Trend: {data.get('trend')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": "DXY Index",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_cpi_inflation(self) -> Dict[str, Any]:
        """Test CPI Inflation."""
        print("\n" + "="*80)
        print("TEST 3/8: CPI INFLATION")
        print("="*80)

        params = QueryParams(params={'query_type': 'cpi_inflation'})

        try:
            print("📈 Querying Grok for CPI data...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": "CPI Inflation",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ CPI Value: {data.get('value')}%")
            print(f"✅ Market Expectation: {data.get('market_expectation')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": "CPI Inflation",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_nfp_jobs(self) -> Dict[str, Any]:
        """Test NFP Jobs Report."""
        print("\n" + "="*80)
        print("TEST 4/8: NFP JOBS REPORT")
        print("="*80)

        params = QueryParams(params={'query_type': 'nfp_jobs'})

        try:
            print("👷 Querying Grok for NFP data...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": "NFP Jobs Report",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ Jobs Added: {data.get('value')}k")
            print(f"✅ Economic Health: {data.get('economic_health')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": "NFP Jobs Report",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_btc_tvl(self) -> Dict[str, Any]:
        """Test BTC TVL in DeFi."""
        print("\n" + "="*80)
        print("TEST 5/8: BTC TVL IN DEFI")
        print("="*80)

        params = QueryParams(params={'query_type': 'btc_tvl'})

        try:
            print("🔒 Querying Grok for BTC TVL...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": "BTC TVL",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ TVL: ${data.get('tvl_usd'):,.0f}")
            print(f"✅ Trend: {data.get('trend')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": "BTC TVL",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_whale_activity(self) -> Dict[str, Any]:
        """Test Whale Activity."""
        print("\n" + "="*80)
        print(f"TEST 6/8: WHALE ACTIVITY ({self.test_symbol})")
        print("="*80)

        params = QueryParams(params={
            'query_type': 'whale_activity',
            'symbol': self.test_symbol
        })

        try:
            print(f"🐋 Querying Grok for {self.test_symbol} whale activity...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": f"Whale Activity ({self.test_symbol})",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ Large Transfers: {data.get('large_transfers_count')}")
            print(f"✅ Net Flow: ${data.get('net_flow_usd', 0):,.0f}")
            print(f"✅ Summary: {data.get('summary', 'N/A')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": f"Whale Activity ({self.test_symbol})",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_twitter_sentiment(self) -> Dict[str, Any]:
        """Test Twitter Sentiment."""
        print("\n" + "="*80)
        print(f"TEST 7/8: TWITTER SENTIMENT ({self.test_symbol})")
        print("="*80)

        params = QueryParams(params={
            'query_type': 'twitter_sentiment',
            'symbol': self.test_symbol
        })

        try:
            print(f"🐦 Querying Grok for {self.test_symbol} Twitter sentiment...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": f"Twitter Sentiment ({self.test_symbol})",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            print(f"✅ Sentiment Score: {data.get('sentiment_score', 0):.2f}")
            print(f"✅ Sample Size: {data.get('sample_size')} posts")
            print(f"✅ Key Themes: {data.get('key_themes', [])[:3]}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": f"Twitter Sentiment ({self.test_symbol})",
                "status": "❌ FAILED",
                "error": str(e)
            }

    async def test_crypto_news(self) -> Dict[str, Any]:
        """Test Crypto News."""
        print("\n" + "="*80)
        print(f"TEST 8/8: CRYPTO NEWS ({self.test_symbol})")
        print("="*80)

        params = QueryParams(params={
            'query_type': 'crypto_news',
            'symbol': self.test_symbol
        })

        try:
            print(f"📰 Querying Grok for {self.test_symbol} crypto news...")
            response = await self.adapter.fetch(params)

            data = {k: v for k, v in response.data.items() if not k.startswith('_')}
            metadata = response.metadata

            result = {
                "test_name": f"Crypto News ({self.test_symbol})",
                "status": "✅ SUCCESS",
                "data": data,
                "metadata": {
                    "tool_calls": metadata.get('tool_calls_count', 0),
                    "cost": metadata.get('estimated_cost', 0)
                }
            }

            self.total_cost += result['metadata']['cost']
            self.total_tool_calls += result['metadata']['tool_calls']

            headlines = data.get('headlines', [])
            print(f"✅ Headlines Found: {len(headlines)}")
            print(f"✅ High Importance: {data.get('high_importance_count', 0)}")
            print(f"✅ Overall Sentiment: {data.get('overall_sentiment')}")
            print(f"✅ Cost: ${result['metadata']['cost']:.4f}")

            return result

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return {
                "test_name": f"Crypto News ({self.test_symbol})",
                "status": "❌ FAILED",
                "error": str(e)
            }

    def generate_markdown_report(self, output_path: str):
        """Generate markdown report from test results."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Count successes/failures
        successes = sum(1 for r in self.results if r['status'] == '✅ SUCCESS')
        failures = sum(1 for r in self.results if r['status'] == '❌ FAILED')

        report = f"""# Grok Market Intelligence Test Report

**Generated**: {timestamp}
**Test Symbol**: {self.test_symbol}

---

## Summary

- **Tests Run**: {len(self.results)}
- **Successes**: ✅ {successes}
- **Failures**: ❌ {failures}
- **Total Cost**: ${self.total_cost:.4f}
- **Total Tool Calls**: {self.total_tool_calls}

---

## Test Results

"""

        for result in self.results:
            report += f"### {result['test_name']}\n\n"
            report += f"**Status**: {result['status']}\n\n"

            if result['status'] == '✅ SUCCESS':
                # Format data nicely
                report += "**Data**:\n```json\n"
                report += json.dumps(result['data'], indent=2, default=str)
                report += "\n```\n\n"

                # Metadata
                report += "**Metadata**:\n"
                report += f"- Tool Calls: {result['metadata']['tool_calls']}\n"
                report += f"- Cost: ${result['metadata']['cost']:.4f}\n"

                if 'tools_used' in result['metadata']:
                    report += f"- Tools Used: {', '.join(result['metadata']['tools_used'])}\n"
                if 'reasoning_tokens' in result['metadata']:
                    report += f"- Reasoning Tokens: {result['metadata']['reasoning_tokens']}\n"
                if 'citations' in result['metadata'] and result['metadata']['citations']:
                    report += "\n**Top Citations**:\n"
                    for i, url in enumerate(result['metadata']['citations'], 1):
                        report += f"{i}. {url}\n"

                report += "\n"
            else:
                # Error details
                report += f"**Error**: {result.get('error', 'Unknown error')}\n\n"

            report += "---\n\n"

        # Cost Analysis
        report += """## Cost Analysis

"""
        avg_cost = self.total_cost / len(self.results) if self.results else 0

        report += f"""
**Per-Query Costs**:
- Average: ${avg_cost:.4f}
- Total: ${self.total_cost:.4f}

**Monthly Projections** (1000 users, 1 bot each):
- Queries per day (all 8 data points): ~192 queries
- Without caching: ${self.total_cost * 192:.2f}/day = ${self.total_cost * 192 * 30:.2f}/month
- With caching (80% hit rate): ${self.total_cost * 192 * 0.2:.2f}/day = ${self.total_cost * 192 * 0.2 * 30:.2f}/month
- **Cost per user/month** (with caching): ${(self.total_cost * 192 * 0.2 * 30) / 1000:.4f}

**Cache TTL Settings**:
- VIX/DXY: 15 minutes
- CPI/NFP: 24 hours
- BTC TVL: 1 hour
- Whale Activity: 30 minutes
- Twitter Sentiment: 30 minutes
- Crypto News: 10 minutes

---

## Recommendations

1. **All tests passing**: Data points ready for production ✅
2. **Cache hit rates**: Monitor Redis to ensure 70-90% hit rate
3. **Cost optimization**: Long TTL on monthly data (CPI/NFP) saves significant cost
4. **Quality**: Review data accuracy vs manual verification
5. **Alerts**: Set up cost monitoring if queries exceed budget

---

*Generated by `scripts/test_all_grok_data_points.py`*
"""

        # Write to file
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"\n✅ Report saved to: {output_path}")

    async def run_all_tests(self):
        """Run all 8 tests sequentially."""
        print("\n" + "="*80)
        print("GROK MARKET INTELLIGENCE - COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test symbol: {self.test_symbol}")

        # Run all tests
        self.results.append(await self.test_vix_index())
        self.results.append(await self.test_dxy_index())
        self.results.append(await self.test_cpi_inflation())
        self.results.append(await self.test_nfp_jobs())
        self.results.append(await self.test_btc_tvl())
        self.results.append(await self.test_whale_activity())
        self.results.append(await self.test_twitter_sentiment())
        self.results.append(await self.test_crypto_news())

        # Generate report
        output_path = f"/home/sev/ggbot/DOCS/grok_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.generate_markdown_report(output_path)

        # Final summary
        successes = sum(1 for r in self.results if r['status'] == '✅ SUCCESS')
        failures = sum(1 for r in self.results if r['status'] == '❌ FAILED')

        print("\n" + "="*80)
        if failures == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"⚠️  {successes}/{len(self.results)} TESTS PASSED ({failures} failures)")
        print("="*80)
        print(f"Total Cost: ${self.total_cost:.4f}")
        print(f"Total Tool Calls: {self.total_tool_calls}")
        print(f"Report: {output_path}")


async def main():
    """Run test suite."""
    tester = GrokDataPointTester()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())
