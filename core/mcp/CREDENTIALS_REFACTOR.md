# MCP Credentials Refactoring

## Overview

This document outlines the changes made to implement a secure, flexible credential management system for the CCXT MCP integration in the ggbots platform.

## Motivation

The previous implementation had several limitations:
- API credentials were hardcoded in configuration files
- No support for per-user credentials in a multi-user environment
- Credential rotation required manual edits to configuration files
- Potential security risks from storing API keys in plaintext files

## Implementation Details

### 1. Credential Provider Architecture

Created a flexible credential provider system to support different credential sources:

- **Core Interface**: `core/config/interfaces/credential_provider.py`
  - Defines the `CredentialProvider` abstract base class
  - Methods for retrieving credentials and exchange options

- **Environment Variable Provider**: `core/config/providers/env_credential_provider.py`
  - Uses environment variables for development
  - Reads EXCHANGE_NAME, EXCHANGE_API, and EXCHANGE_SECRET

- **Database Provider (Future)**: `core/config/providers/db_credential_provider.py`
  - Placeholder for future implementation
  - Will use encrypted database storage for production use

### 2. Dynamic Account Configuration

Created a system to generate temporary configuration files with credentials at runtime:

- **Dynamic Account Manager**: `core/mcp/dynamic_account.py`
  - Creates temporary JSON configuration files with credentials
  - Manages cleanup of temporary files
  - Supports adding credentials to existing configurations

### 3. CCXT MCP Client Updates

Updated the CCXT MCP client to use the new credential system:

- Added `exchange_id` parameter to `CCXTMCPClient.__init__`
- Integrated with `DynamicAccountManager` to generate configurations
- Maintained backward compatibility with static configuration files

### 4. Data Source Implementation

Created a new DataSource implementation using CCXT MCP with credential support:

- **CCXT MCP DataSource**: `extraction/sources/exchange_api/ccxt_mcp_datasource.py`
  - Implements the DataSource interface for CCXT MCP
  - Supports the `DataTimeframe` enum for standardized timeframes
  - Uses async context manager pattern for clean resource management

## Testing

- Created test scripts to verify the implementation:
  - `tests/test_dynamic_credentials.py`: Tests the credential provider and dynamic account manager
  - `tests/test_ccxt_datasource.py`: Tests the CCXT MCP DataSource implementation

## Documentation

- Updated the MCP README (`core/mcp/README.md`)
- Added usage examples for the new credential system
- Documented future enhancements

## Next Steps

1. **Database Integration**: Complete the database credential provider implementation
2. **User Management**: Add support for user-specific credentials
3. **Security Enhancements**: Implement proper encryption for stored credentials
4. **Testing**: Add comprehensive unit and integration tests