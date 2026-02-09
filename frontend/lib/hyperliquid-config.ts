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

// Arbitrum chain ID (network the wallet connects to)
export const ARBITRUM_CHAIN_ID = 42161

// Hyperliquid signing chain ID (0x66eee = 421614, used in EIP-712 domain)
// This is separate from the network chain — it's the EIP-712 signing context.
// The SDK uses this for ALL user-signed actions (approve, withdraw, etc.)
export const HYPERLIQUID_SIGNATURE_CHAIN_ID = 421614
export const HYPERLIQUID_SIGNATURE_CHAIN_ID_HEX = '0x66eee'

// USDC on Arbitrum (native, not bridged)
export const ARBITRUM_USDC_ADDRESS = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' as const

// Hyperliquid bridge contract on Arbitrum (for USDC deposits)
export const HYPERLIQUID_BRIDGE_ADDRESS = '0x2df1c51e09aecf9cacb7bc98cb1742757f163df7' as const

// ERC-20 ABI for balance reading and transfers
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
  {
    name: 'transfer',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'to', type: 'address' },
      { name: 'amount', type: 'uint256' },
    ],
    outputs: [{ name: '', type: 'bool' }],
  },
] as const

// Hyperliquid API URL
export const HYPERLIQUID_API_URL = 'https://api.hyperliquid.xyz'

// EIP-712 Domain for Hyperliquid transaction signing
// chainId is the SIGNING chain (421614), not the Arbitrum network chain (42161)
export const HYPERLIQUID_EIP712_DOMAIN = {
  name: 'HyperliquidSignTransaction',
  version: '1',
  chainId: HYPERLIQUID_SIGNATURE_CHAIN_ID,
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

// EIP-712 Types for withdraw action (withdraw from Hyperliquid L1 → Arbitrum)
export const HYPERLIQUID_WITHDRAW_TYPES = {
  'HyperliquidTransaction:Withdraw': [
    { name: 'hyperliquidChain', type: 'string' },
    { name: 'destination', type: 'string' },
    { name: 'amount', type: 'string' },
    { name: 'time', type: 'uint64' },
  ],
} as const
