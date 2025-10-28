"""
Tests for Market Intelligence Orchestrator

Tests config parsing, permission checking, catalog mapping, and full integration
with the MarketIntelligence gateway.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from market_intelligence.orchestrator import (
    fetch_market_intelligence,
    _parse_config_sources,
    _get_user_permissions,
    _check_permission,
    _get_catalog_mapping,
    _replace_param_templates
)


class TestConfigParsing:
    """Test config parsing logic."""

    def test_parse_valid_config(self):
        """Test parsing valid config with multiple sources."""
        # Mock config
        config = Mock()
        config.extraction = {
            'selected_data_sources': {
                'derivatives_leverage': {
                    'data_points': ['btc_funding_rate', 'eth_funding_rate']
                },
                'macro_economics': {
                    'data_points': ['vix', 'dxy']
                }
            }
        }

        result = _parse_config_sources(config)

        assert 'derivatives_leverage' in result
        assert 'macro_economics' in result
        assert result['derivatives_leverage'] == ['btc_funding_rate', 'eth_funding_rate']
        assert result['macro_economics'] == ['vix', 'dxy']

    def test_parse_filters_technical_analysis(self):
        """Test that technical_analysis is filtered out (handled by ExtractionEngine)."""
        config = Mock()
        config.extraction = {
            'selected_data_sources': {
                'technical_analysis': {
                    'data_points': ['rsi', 'macd']
                },
                'derivatives_leverage': {
                    'data_points': ['btc_funding_rate']
                }
            }
        }

        result = _parse_config_sources(config)

        # Technical analysis should be filtered out
        assert 'technical_analysis' not in result
        # But derivatives should remain
        assert 'derivatives_leverage' in result

    def test_parse_empty_config(self):
        """Test parsing config with no sources."""
        config = Mock()
        config.extraction = {'selected_data_sources': {}}

        result = _parse_config_sources(config)

        assert result == {}

    def test_parse_config_with_empty_data_points(self):
        """Test that sources with empty data_points are filtered out."""
        config = Mock()
        config.extraction = {
            'selected_data_sources': {
                'derivatives_leverage': {
                    'data_points': []  # Empty
                },
                'macro_economics': {
                    'data_points': ['vix']
                }
            }
        }

        result = _parse_config_sources(config)

        assert 'derivatives_leverage' not in result
        assert 'macro_economics' in result


class TestCatalogMapping:
    """Test catalog mapping lookup."""

    def test_get_mapping_for_funding_rate(self):
        """Test getting mapping for BTC funding rate."""
        mapping = _get_catalog_mapping('derivatives_leverage', 'btc_funding_rate')

        assert mapping is not None
        assert mapping['data_type'] == 'funding_rate'
        assert mapping['params_template']['symbol'] == 'BTC/USDT'

    def test_get_mapping_for_ggshot(self):
        """Test getting mapping for ggShot signals."""
        mapping = _get_catalog_mapping('trading_signals', 'ggshot')

        assert mapping is not None
        assert mapping['data_type'] == 'ggshot_signals'
        assert mapping['params_template']['symbol'] == '{symbol}'

    def test_get_mapping_not_found(self):
        """Test that unmapped data points return None."""
        mapping = _get_catalog_mapping('unknown_source', 'unknown_point')

        assert mapping is None


class TestTemplateReplacement:
    """Test parameter template replacement."""

    def test_replace_symbol_template(self):
        """Test replacing {symbol} template."""
        params = {
            'symbol': '{symbol}',
            'limit': 200
        }

        result = _replace_param_templates(params, symbol='BTC/USDT')

        assert result['symbol'] == 'BTC/USDT'
        assert result['limit'] == 200

    def test_replace_no_templates(self):
        """Test params without templates pass through unchanged."""
        params = {
            'symbol': 'BTC/USDT',
            'limit': 100
        }

        result = _replace_param_templates(params, symbol='ETH/USDT')

        # Should not replace non-template values
        assert result['symbol'] == 'BTC/USDT'
        assert result['limit'] == 100

    def test_replace_multiple_templates(self):
        """Test replacing multiple template variables."""
        params = {
            'symbol': '{symbol}',
            'timeframe': '{timeframe}',
            'limit': 100
        }

        result = _replace_param_templates(params, symbol='ETH/USDT', timeframe='1h')

        assert result['symbol'] == 'ETH/USDT'
        assert result['timeframe'] == '1h'
        assert result['limit'] == 100


class TestPermissionChecking:
    """Test permission checking logic."""

    @pytest.mark.asyncio
    async def test_free_data_point_allowed(self):
        """Test that free data points are always allowed."""
        with patch('market_intelligence.orchestrator.get_db_connection') as mock_db:
            # Mock database returning requires_premium=False
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (False,)
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = await _check_permission(
                user_id='test_user',
                source_name='derivatives_leverage',
                point_name='btc_funding_rate',
                user_permissions=[]  # Empty permissions
            )

            assert result is True  # Free data points always allowed

    @pytest.mark.asyncio
    async def test_premium_data_point_with_access(self):
        """Test that premium data points are allowed for users with permission."""
        with patch('market_intelligence.orchestrator.get_db_connection') as mock_db:
            # Mock database returning requires_premium=True
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (True,)
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = await _check_permission(
                user_id='test_user',
                source_name='trading_signals',
                point_name='ggshot',
                user_permissions=['ggshot']  # Has permission
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_premium_data_point_without_access(self):
        """Test that premium data points are denied for users without permission."""
        with patch('market_intelligence.orchestrator.get_db_connection') as mock_db:
            # Mock database returning requires_premium=True
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (True,)
            mock_db.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = await _check_permission(
                user_id='test_user',
                source_name='trading_signals',
                point_name='ggshot',
                user_permissions=[]  # No permission
            )

            assert result is False


class TestFullIntegration:
    """Test full orchestrator integration."""

    @pytest.mark.asyncio
    async def test_fetch_market_intelligence_with_funding_rates(self):
        """Test fetching funding rates through orchestrator."""
        # Mock config
        config = Mock()
        config.extraction = {
            'selected_data_sources': {
                'derivatives_leverage': {
                    'data_points': ['btc_funding_rate']
                }
            }
        }

        # Mock user permissions (funding rate is free, so empty permissions OK)
        with patch('market_intelligence.orchestrator._get_user_permissions') as mock_perms:
            mock_perms.return_value = []

            # Mock permission check (free data point)
            with patch('market_intelligence.orchestrator._check_permission') as mock_check:
                mock_check.return_value = True

                # Mock MarketIntelligence gateway
                with patch('market_intelligence.orchestrator.MarketIntelligence') as mock_gateway_class:
                    mock_gateway = AsyncMock()
                    mock_gateway_class.return_value = mock_gateway

                    # Mock gateway response
                    mock_response = Mock()
                    mock_response.data = {
                        'symbol': 'BTC/USDT',
                        'funding_rate_pct': 0.0026,
                        'interpretation': {
                            'level': 'neutral',
                            'risk': 'minimal'
                        }
                    }
                    mock_response.source = 'binance_funding'
                    mock_response.latency_ms = 50
                    mock_response.from_cache = False
                    mock_gateway.query.return_value = mock_response

                    # Execute
                    result = await fetch_market_intelligence(config, 'test_user', 'BTC/USDT')

                    # Verify
                    assert 'derivatives_leverage' in result
                    assert 'btc_funding_rate' in result['derivatives_leverage']
                    assert result['derivatives_leverage']['btc_funding_rate']['funding_rate_pct'] == 0.0026

                    # Verify gateway was called correctly
                    mock_gateway.query.assert_called_once()
                    call_args = mock_gateway.query.call_args
                    assert call_args[1]['data_type'] == 'funding_rate'
                    assert call_args[1]['params']['symbol'] == 'BTC/USDT'

    @pytest.mark.asyncio
    async def test_fetch_with_no_enabled_sources(self):
        """Test that empty config returns empty dict."""
        config = Mock()
        config.extraction = {'selected_data_sources': {}}

        result = await fetch_market_intelligence(config, 'test_user', 'BTC/USDT')

        assert result == {}

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_adapter_failure(self):
        """Test that adapter failures don't break the entire orchestrator."""
        # Mock config with multiple data points
        config = Mock()
        config.extraction = {
            'selected_data_sources': {
                'derivatives_leverage': {
                    'data_points': ['btc_funding_rate', 'eth_funding_rate']
                }
            }
        }

        with patch('market_intelligence.orchestrator._get_user_permissions') as mock_perms:
            mock_perms.return_value = []

            with patch('market_intelligence.orchestrator._check_permission') as mock_check:
                mock_check.return_value = True

                with patch('market_intelligence.orchestrator.MarketIntelligence') as mock_gateway_class:
                    mock_gateway = AsyncMock()
                    mock_gateway_class.return_value = mock_gateway

                    # First query succeeds, second fails
                    from market_intelligence.types import DataSourceError

                    mock_response = Mock()
                    mock_response.data = {'funding_rate_pct': 0.0026}
                    mock_response.source = 'binance'
                    mock_response.latency_ms = 50
                    mock_response.from_cache = False

                    mock_gateway.query.side_effect = [
                        mock_response,  # BTC succeeds
                        DataSourceError("API error")  # ETH fails
                    ]

                    # Execute
                    result = await fetch_market_intelligence(config, 'test_user', 'BTC/USDT')

                    # Verify - should have BTC but not ETH
                    assert 'derivatives_leverage' in result
                    assert 'btc_funding_rate' in result['derivatives_leverage']
                    assert 'eth_funding_rate' not in result['derivatives_leverage']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
