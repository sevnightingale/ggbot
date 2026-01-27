import { getDefaultConfig } from '@rainbow-me/rainbowkit'
import { scroll } from 'wagmi/chains'

/**
 * Wagmi configuration for ggbots Arena staking
 *
 * This config is scoped to the Arena page only - not loaded app-wide.
 * Uses Scroll mainnet for USX/sUSX staking.
 */
export const wagmiConfig = getDefaultConfig({
  appName: 'ggbots Arena',
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || '',
  chains: [scroll],
  ssr: true,
})

// Scroll chain ID for reference
export const SCROLL_CHAIN_ID = 534352
