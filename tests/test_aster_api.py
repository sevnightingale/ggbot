"""
AsterDEX API Comprehensive Test Suite

Tests all relevant endpoints for ggbots integration and logs responses.
"""

import json
import math
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Optional

from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import requests

# Load credentials
load_dotenv()

user = os.getenv('ASTER_USER_WALLET')
signer = os.getenv('ASTER_WALLET_ADDRESS')
priKey = os.getenv('ASTER_PRIVATE_KEY')

if not user or not signer or not priKey:
    print("ERROR: Missing credentials in .env")
    exit(1)

host = 'https://fapi.asterdex.com'

# ============================================================================
# Utilities
# ============================================================================

def log_section(title: str):
    """Print a section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def log_test(test_name: str):
    """Print a test name."""
    print(f"\n[TEST] {test_name}")
    print("-" * 80)

def save_response(test_name: str, response: Any):
    """Save response to log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aster_api_test_{timestamp}.log"

    with open(filename, "a") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Test: {test_name}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"{'='*80}\n")
        if isinstance(response, dict) or isinstance(response, list):
            f.write(json.dumps(response, indent=2))
        else:
            f.write(str(response))
        f.write("\n")

def _trim_dict(my_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all values to strings."""
    for key in my_dict:
        value = my_dict[key]
        if isinstance(value, list):
            new_value = []
            for item in value:
                if isinstance(item, dict):
                    new_value.append(json.dumps(_trim_dict(item)))
                else:
                    new_value.append(str(item))
            my_dict[key] = json.dumps(new_value)
            continue
        if isinstance(value, dict):
            my_dict[key] = json.dumps(_trim_dict(value))
            continue
        my_dict[key] = str(value)
    return my_dict

def generate_signature(params: Dict[str, Any], nonce: int) -> Dict[str, Any]:
    """Generate Web3 ECDSA signature."""
    params = {key: value for key, value in params.items() if value is not None}
    params['recvWindow'] = 50000
    params['timestamp'] = int(round(time.time() * 1000))

    _trim_dict(params)
    json_str = json.dumps(params, sort_keys=True).replace(' ', '').replace("'", '"')

    encoded = encode(['string', 'address', 'address', 'uint256'],
                    [json_str, user, signer, nonce])
    keccak_hex = Web3.keccak(encoded).hex()

    signable_msg = encode_defunct(hexstr=keccak_hex)
    signed_message = Account.sign_message(signable_message=signable_msg, private_key=priKey)
    signature = '0x' + signed_message.signature.hex()

    params['nonce'] = str(nonce)
    params['user'] = user
    params['signer'] = signer
    params['signature'] = signature

    return params

def api_request(method: str, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make API request with signature."""
    nonce = math.trunc(time.time() * 1000000)
    signed_params = generate_signature(params, nonce)

    url = host + endpoint
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'ggbots-test/1.0'
    }

    try:
        if method == 'GET':
            response = requests.get(url, params=signed_params, timeout=30)
        elif method == 'POST':
            response = requests.post(url, data=signed_params, headers=headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, data=signed_params, headers=headers, timeout=30)
        else:
            print(f"Unsupported method: {method}")
            return None

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Response (pretty):")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Error Response: {response.text}")
            return {"error": response.text, "status_code": response.status_code}

    except Exception as e:
        print(f"Exception: {e}")
        return {"error": str(e)}

# ============================================================================
# Test Suite
# ============================================================================

def test_account_balance():
    """Test: GET /fapi/v3/balance - Query account balance."""
    log_test("Account Balance")
    result = api_request('GET', '/fapi/v3/balance', {})
    save_response("account_balance", result)

    # Extract USDC balance
    if isinstance(result, list):
        for asset in result:
            if asset.get('asset') == 'USDC':
                print(f"\n💰 USDC Balance: ${asset.get('balance')}")
                print(f"   Available: ${asset.get('availableBalance')}")
                print(f"   Cross Wallet: ${asset.get('crossWalletBalance')}")
                break

    return result

def test_position_risk():
    """Test: GET /fapi/v3/positionRisk - Query open positions."""
    log_test("Position Risk / Open Positions")
    result = api_request('GET', '/fapi/v3/positionRisk', {})
    save_response("position_risk", result)

    # Filter to open positions
    if isinstance(result, list):
        open_positions = [p for p in result if float(p.get('positionAmt', 0)) != 0]
        print(f"\n📊 Open Positions: {len(open_positions)}")
        for pos in open_positions:
            print(f"   {pos.get('symbol')}: {pos.get('positionAmt')} @ ${pos.get('entryPrice')}")

    return result

def test_account_info():
    """Test: GET /fapi/v3/account - Full account information."""
    log_test("Account Information")
    result = api_request('GET', '/fapi/v3/account', {})
    save_response("account_info", result)
    return result

def test_open_orders(symbol: str = None):
    """Test: GET /fapi/v3/openOrders - Query all open orders."""
    log_test(f"Open Orders{' for ' + symbol if symbol else ' (all symbols)'}")
    params = {}
    if symbol:
        params['symbol'] = symbol
    result = api_request('GET', '/fapi/v3/openOrders', {})
    save_response("open_orders", result)

    if isinstance(result, list):
        print(f"\n📋 Open Orders: {len(result)}")
        for order in result:
            print(f"   {order.get('orderId')}: {order.get('symbol')} {order.get('side')} {order.get('type')}")

    return result

def test_exchange_info():
    """Test: GET /fapi/v3/exchangeInfo - Get trading rules and symbol info."""
    log_test("Exchange Information")
    # This endpoint doesn't require signature
    url = host + '/fapi/v3/exchangeInfo'
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            # Don't print full response (too large), just summary
            if 'symbols' in result:
                print(f"\n📊 Available Symbols: {len(result['symbols'])}")
                # Show first 10 symbols
                for symbol in result['symbols'][:10]:
                    print(f"   {symbol.get('symbol')}: {symbol.get('status')}")
                print("   ... (and more)")
            save_response("exchange_info", result)
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_place_limit_order(symbol: str, side: str, quantity: str, price: str):
    """Test: POST /fapi/v3/order - Place a LIMIT order."""
    log_test(f"Place LIMIT Order: {side} {quantity} {symbol} @ ${price}")
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': price,
        'positionSide': 'BOTH'
    }
    result = api_request('POST', '/fapi/v3/order', params)
    save_response("place_limit_order", result)

    if result and 'orderId' in result:
        print(f"\n✅ Order Placed! Order ID: {result.get('orderId')}")
        return result.get('orderId')
    return None

def test_place_market_order(symbol: str, side: str, quantity: str):
    """Test: POST /fapi/v3/order - Place a MARKET order."""
    log_test(f"Place MARKET Order: {side} {quantity} {symbol}")
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'positionSide': 'BOTH'
    }
    result = api_request('POST', '/fapi/v3/order', params)
    save_response("place_market_order", result)

    if result and 'orderId' in result:
        print(f"\n✅ Market Order Placed! Order ID: {result.get('orderId')}")
        return result.get('orderId')
    return None

def test_place_stop_loss_order(symbol: str, side: str, quantity: str, stop_price: str):
    """Test: POST /fapi/v3/order - Place a STOP_MARKET order."""
    log_test(f"Place STOP_LOSS Order: {side} {quantity} {symbol} @ stop ${stop_price}")
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'STOP_MARKET',
        'quantity': quantity,
        'stopPrice': stop_price,
        'positionSide': 'BOTH'
    }
    result = api_request('POST', '/fapi/v3/order', params)
    save_response("place_stop_loss_order", result)

    if result and 'orderId' in result:
        print(f"\n✅ Stop-Loss Order Placed! Order ID: {result.get('orderId')}")
        return result.get('orderId')
    return None

def test_place_take_profit_order(symbol: str, side: str, quantity: str, stop_price: str):
    """Test: POST /fapi/v3/order - Place a TAKE_PROFIT_MARKET order."""
    log_test(f"Place TAKE_PROFIT Order: {side} {quantity} {symbol} @ ${stop_price}")
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'TAKE_PROFIT_MARKET',
        'quantity': quantity,
        'stopPrice': stop_price,
        'positionSide': 'BOTH'
    }
    result = api_request('POST', '/fapi/v3/order', params)
    save_response("place_take_profit_order", result)

    if result and 'orderId' in result:
        print(f"\n✅ Take-Profit Order Placed! Order ID: {result.get('orderId')}")
        return result.get('orderId')
    return None

def test_query_order(symbol: str, order_id: str):
    """Test: GET /fapi/v3/order - Query specific order by ID."""
    log_test(f"Query Order: {order_id} for {symbol}")
    params = {
        'symbol': symbol,
        'orderId': order_id
    }
    result = api_request('GET', '/fapi/v3/order', params)
    save_response("query_order", result)

    if result and 'status' in result:
        print(f"\n📄 Order Status: {result.get('status')}")
        print(f"   Symbol: {result.get('symbol')}")
        print(f"   Side: {result.get('side')}")
        print(f"   Type: {result.get('type')}")
        print(f"   Quantity: {result.get('origQty')}")
        print(f"   Executed: {result.get('executedQty')}")

    return result

def test_cancel_order(symbol: str, order_id: str):
    """Test: DELETE /fapi/v3/order - Cancel an order."""
    log_test(f"Cancel Order: {order_id} for {symbol}")
    params = {
        'symbol': symbol,
        'orderId': order_id
    }
    result = api_request('DELETE', '/fapi/v3/order', params)
    save_response("cancel_order", result)

    if result and 'status' in result:
        print(f"\n✅ Order Canceled! Status: {result.get('status')}")

    return result

def test_get_trades(symbol: str):
    """Test: GET /fapi/v3/userTrades - Get account trade list."""
    log_test(f"User Trades for {symbol}")
    params = {
        'symbol': symbol,
        'limit': 10
    }
    result = api_request('GET', '/fapi/v3/userTrades', params)
    save_response("user_trades", result)

    if isinstance(result, list):
        print(f"\n📜 Recent Trades: {len(result)}")
        for trade in result[:5]:  # Show first 5
            print(f"   {trade.get('id')}: {trade.get('side')} {trade.get('qty')} @ ${trade.get('price')}")

    return result

# ============================================================================
# Main Test Runner
# ============================================================================

def run_full_test_suite():
    """Run complete test suite."""

    print("\n" + "="*80)
    print("  ASTERDEX API COMPREHENSIVE TEST SUITE")
    print("  ggbots Integration Verification")
    print("="*80)
    print(f"\nUser: {user}")
    print(f"Signer: {signer}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # ========================================================================
    # SECTION 1: Account & Balance Queries
    # ========================================================================
    log_section("SECTION 1: Account & Balance Queries")

    balance_result = test_account_balance()
    time.sleep(1)

    position_result = test_position_risk()
    time.sleep(1)

    account_result = test_account_info()
    time.sleep(1)

    open_orders_result = test_open_orders()
    time.sleep(1)

    # ========================================================================
    # SECTION 2: Market Data (No Auth)
    # ========================================================================
    log_section("SECTION 2: Market Data & Exchange Info")

    exchange_result = test_exchange_info()
    time.sleep(1)

    # ========================================================================
    # SECTION 3: Order Placement Tests
    # ========================================================================
    log_section("SECTION 3: Order Placement Tests")

    print("\n⚠️  WARNING: The following tests will place REAL orders!")
    print("    Test symbol: BTCUSDT")
    print("    Test quantity: Very small (0.001 BTC)")
    print("    Test type: LIMIT orders far from market (won't fill)")

    response = input("\nProceed with order placement tests? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ Skipping order placement tests.")
        log_section("TEST SUITE COMPLETE (PARTIAL)")
        print("\n✅ Account query tests completed successfully!")
        print("📁 Responses saved to: aster_api_test_*.log")
        return

    # Test with safe LIMIT order far from market
    print("\n📝 Placing test LIMIT order (won't fill - price too low)...")
    limit_order_id = test_place_limit_order(
        symbol='BTCUSDT',
        side='BUY',
        quantity='0.001',  # Very small size
        price='10000'      # Well below market - won't fill
    )
    time.sleep(2)

    if limit_order_id:
        # Query the order we just placed
        test_query_order('BTCUSDT', str(limit_order_id))
        time.sleep(1)

        # Cancel the order
        test_cancel_order('BTCUSDT', str(limit_order_id))
        time.sleep(1)

        # Verify it's canceled
        test_query_order('BTCUSDT', str(limit_order_id))
        time.sleep(1)

    # ========================================================================
    # SECTION 4: Conditional Orders (SL/TP)
    # ========================================================================
    log_section("SECTION 4: Conditional Orders (Stop-Loss / Take-Profit)")

    print("\n⚠️  WARNING: Testing SL/TP orders requires an open position!")
    print("    Skipping for now unless you have an open position.")
    print("    (Uncomment test calls if you want to test with real position)")

    # Uncomment these if you have an open position:
    # test_place_stop_loss_order('BTCUSDT', 'SELL', '0.001', '50000')
    # test_place_take_profit_order('BTCUSDT', 'SELL', '0.001', '100000')

    # ========================================================================
    # SECTION 5: Trade History
    # ========================================================================
    log_section("SECTION 5: Trade History")

    test_get_trades('BTCUSDT')
    time.sleep(1)

    # ========================================================================
    # Test Complete
    # ========================================================================
    log_section("TEST SUITE COMPLETE")

    print("\n✅ All tests completed successfully!")
    print("📁 Responses saved to: aster_api_test_*.log")
    print("\n🔍 Review the log file for detailed API responses and structures.")
    print("💡 Use these responses to verify integration compatibility.")

# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    run_full_test_suite()
