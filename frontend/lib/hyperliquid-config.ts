import { getDefaultConfig } from '@rainbow-me/rainbowkit'
import { arbitrum } from 'wagmi/chains'

/**
 * Wagmi configuration for Hyperliquid setup page
 *
 * Scoped to /hyperliquid page only — uses Arbitrum chain.
 * Separate from Arena config which uses Scroll.
 */
export const hyperliquidWagmiConfig = getDefaultConfig({
  appName: 'ggbots Hyperliquid',
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || '',
  chains: [arbitrum],
  ssr: true,
})

// Arbitrum chain ID
export const ARBITRUM_CHAIN_ID = 42161

// USDC on Arbitrum (native, not bridged)
export const ARBITRUM_USDC_ADDRESS = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' as const

// Minimal ERC-20 ABI for balance reading
export const ERC20_ABI = [
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ name: '', type: 'uint256' }],
  },
  {
    name: 'decimals',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'uint8' }],
  },
] as const

// Hyperliquid API URL
export const HYPERLIQUID_API_URL = 'https://api.hyperliquid.xyz'

// EIP-712 Domain for Hyperliquid transaction signing
export const HYPERLIQUID_EIP712_DOMAIN = {
  name: 'HyperliquidSignTransaction',
  version: '1',
  chainId: ARBITRUM_CHAIN_ID,
  verifyingContract: '0x0000000000000000000000000000000000000000' as `0x${string}`,
} as const

// EIP-712 Types for approveAgent action
export const HYPERLIQUID_APPROVE_AGENT_TYPES = {
  'HyperliquidTransaction:ApproveAgent': [
    { name: 'hyperliquidChain', type: 'string' },
    { name: 'agentAddress', type: 'address' },
    { name: 'agentName', type: 'string' },
    { name: 'nonce', type: 'uint64' },
  ],
} as const
