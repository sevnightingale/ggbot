// Hyperliquid helpers — straight port of the action/signature pattern used by
// dgclaw-skill. The EIP-712 domain is the same for every HL action:
// { name: 'HyperliquidSignTransaction', version: '1', chainId: 42161, verifyingContract: 0x0 }

export const HL_API_URL = process.env.HL_API_URL || 'https://api.hyperliquid.xyz/exchange'
export const CHAIN_ID = Number(process.env.HL_CHAIN_ID || 42161)
export const ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

export const HL_DOMAIN = {
  name: 'HyperliquidSignTransaction',
  version: '1',
  chainId: CHAIN_ID,
  verifyingContract: ZERO_ADDRESS as `0x${string}`,
} as const

export const UserSetAbstractionTypes = {
  'HyperliquidTransaction:UserSetAbstraction': [
    { name: 'hyperliquidChain', type: 'string' },
    { name: 'user', type: 'address' },
    { name: 'abstraction', type: 'string' },
    { name: 'nonce', type: 'uint64' },
  ],
} as const

export const ApproveAgentTypes = {
  'HyperliquidTransaction:ApproveAgent': [
    { name: 'hyperliquidChain', type: 'string' },
    { name: 'agentAddress', type: 'address' },
    { name: 'agentName', type: 'string' },
    { name: 'nonce', type: 'uint64' },
  ],
} as const

// Hyperliquid withdraw3 — returns USDC from HL to an EVM address on Arbitrum.
// Protocol charges a small fee (currently $1 flat), settles on Arbitrum.
export const WithdrawTypes = {
  'HyperliquidTransaction:Withdraw': [
    { name: 'hyperliquidChain', type: 'string' },
    { name: 'destination', type: 'string' },
    { name: 'amount', type: 'string' },
    { name: 'time', type: 'uint64' },
  ],
} as const

export function parseSignature(sig: string): { r: `0x${string}`; s: `0x${string}`; v: number } {
  const raw = sig.startsWith('0x') ? sig.slice(2) : sig
  return {
    r: `0x${raw.slice(0, 64)}` as `0x${string}`,
    s: `0x${raw.slice(64, 128)}` as `0x${string}`,
    v: parseInt(raw.slice(128, 130), 16),
  }
}

export async function broadcastToHL(action: unknown, signature: { r: string; s: string; v: number }, nonce: number) {
  const response = await fetch(HL_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, signature, nonce }),
  })
  const body = await response.json()
  return { httpStatus: response.status, body }
}
