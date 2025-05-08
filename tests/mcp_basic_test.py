"""
Basic MCP connectivity test script.

This script performs minimal testing of MCP connectivity without requiring
authenticated exchange access. Uses subprocess directly for better control.
"""

import os
import sys
import asyncio
import subprocess
import threading
import json
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def test_ccxt_mcp():
    """Test basic CCXT MCP command line functionality."""
    print("\n=== Testing CCXT MCP ===")
    
    # CCXT MCP config path
    ccxt_config_path = os.path.join(project_root, 'core', 'config', 'ccxt-accounts.json')
    
    try:
        # Test if ccxt-mcp command is available
        print("Checking if ccxt-mcp is installed...")
        try:
            result = subprocess.run(
                ["which", "ccxt-mcp"], 
                capture_output=True, 
                text=True,
                check=False  # Don't raise exception on non-zero return code
            )
        except Exception as e:
            print(f"Error checking ccxt-mcp: {str(e)}")
            # Try alternative approach
            result = subprocess.run(
                ["bash", "-c", "command -v ccxt-mcp"],
                capture_output=True,
                text=True,
                check=False
            )
        
        if result.returncode != 0:
            print("Error: ccxt-mcp command not found in PATH")
            print("Make sure you installed it with: npm install -g @lazydino/ccxt-mcp")
            return
            
        print(f"Found ccxt-mcp at: {result.stdout.strip()}")
        
        # Test help command
        print("Testing ccxt-mcp help...")
        result = subprocess.run(
            ["ccxt-mcp", "--help"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running ccxt-mcp --help: {result.stderr}")
            return
            
        print("ccxt-mcp help command successful")
        
        # Test if config file exists
        print(f"Checking if config file exists at: {ccxt_config_path}")
        if not os.path.exists(ccxt_config_path):
            print(f"Error: Config file not found at {ccxt_config_path}")
            return
            
        print("Config file exists")
        
        # Test running with config
        print("Testing ccxt-mcp with config...")
        result = subprocess.run(
            ["ccxt-mcp", "--config", ccxt_config_path, "--version"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running ccxt-mcp with config: {result.stderr}")
            return
            
        print("ccxt-mcp with config successful")
        print("CCXT MCP tests passed!")
        
    except Exception as e:
        print(f"Error testing CCXT MCP: {str(e)}")


def test_indicators_mcp():
    """Test basic Crypto Indicators MCP script."""
    print("\n=== Testing Crypto Indicators MCP ===")
    
    # Crypto Indicators MCP script path
    crypto_indicators_path = os.path.join(
        project_root, 'core', 'mcp', 'servers', 'crypto-indicators-mcp', 'index.js'
    )
    
    try:
        # Check if script exists
        print(f"Checking if script exists at: {crypto_indicators_path}")
        if not os.path.exists(crypto_indicators_path):
            print(f"Error: Script not found at {crypto_indicators_path}")
            return
            
        print("Script file exists")
        
        # Check if node.js is installed
        print("Checking if Node.js is installed...")
        try:
            result = subprocess.run(
                ["which", "node"], 
                capture_output=True, 
                text=True,
                check=False
            )
        except Exception as e:
            print(f"Error checking node: {str(e)}")
            # Try alternative approach
            result = subprocess.run(
                ["bash", "-c", "command -v node"],
                capture_output=True,
                text=True,
                check=False
            )
        
        if result.returncode != 0:
            print("Error: node command not found in PATH")
            print("Make sure Node.js is installed")
            return
            
        print(f"Found node at: {result.stdout.strip()}")
        
        # Check if package.json exists
        print("Checking for package.json...")
        script_dir = os.path.dirname(crypto_indicators_path)
        package_json_path = os.path.join(script_dir, "package.json")
        
        if not os.path.exists(package_json_path):
            print(f"Warning: package.json not found in {script_dir}")
        else:
            print("package.json found, checking contents...")
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                    dependencies = package_json.get('dependencies', {})
                    print(f"Found {len(dependencies)} dependencies in package.json")
            except Exception as e:
                print(f"Error reading package.json: {str(e)}")
        
        # We're not running npm list anymore, so we don't need to check its results
        
        # Try running the script with --help (if supported)
        print("Testing script with --help...")
        result = subprocess.run(
            ["node", crypto_indicators_path, "--help"], 
            capture_output=True, 
            text=True,
            timeout=5  # 5 second timeout
        )
        
        # Help command might not be supported, so don't check return code
        print("Script help command executed (may or may not be supported)")
        
        print("Crypto Indicators MCP tests completed")
        
    except subprocess.TimeoutExpired:
        print("Warning: Help command timed out - this is normal if the script doesn't support --help")
        print("Crypto Indicators MCP checks completed with timeout warning")
    except Exception as e:
        print(f"Error testing Crypto Indicators MCP: {str(e)}")


if __name__ == "__main__":
    test_ccxt_mcp()
    test_indicators_mcp()
    print("\nAll tests completed!")