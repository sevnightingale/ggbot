// Privy-wallet EIP-712 signing via the Virtuals v2 SDK's provider adapter.
//
// We don't talk to @privy-io/node directly — we use PrivyAlchemyEvmProviderAdapter
// from @virtuals-protocol/acp-node-v2, which is the exact same abstraction that
// acp-cli (and transitively dgclaw-skill) uses under the hood. The adapter wraps
// the Privy session-signer authentication protocol so we don't have to.
//
// The adapter's factory method — PrivyAlchemyEvmProviderAdapter.create({ ... }) —
// accepts our signer private key in memory, returning an object with a typed
// IEvmProviderAdapter interface (sendTransaction, signTypedData, etc).
//
// Ref:
//   - @virtuals-protocol/acp-node-v2/src/providers/evm/privyAlchemyEvmProviderAdapter.ts
//   - @virtuals-protocol/acp-node-v2/src/providers/types.ts (IEvmProviderAdapter)

import { PrivyAlchemyEvmProviderAdapter } from '@virtuals-protocol/acp-node-v2'

export interface SignTypedDataRequest {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string          // base64-encoded PEM (PKCS8) — decoded before use
  chainId: number
  typedData: {
    domain: Record<string, unknown>
    types: Record<string, readonly { name: string; type: string }[]>
    primaryType: string
    message: Record<string, unknown>
  }
}

function decodeSignerKey(b64: string): string {
  // Our Python backend stores the private key as base64(PEM). Decode to raw PEM
  // string since that's what @privy-io/node's generateAuthorizationSignature expects.
  return Buffer.from(b64, 'base64').toString('utf-8')
}

export async function signTypedDataWithPrivy(req: SignTypedDataRequest): Promise<string> {
  const adapter = await PrivyAlchemyEvmProviderAdapter.create({
    walletAddress: req.agentWalletAddress,
    walletId: req.agentWalletId,
    signerPrivateKey: decodeSignerKey(req.signerPrivateKey),
    privyAppId: process.env.PRIVY_APP_ID,
  })

  return adapter.signTypedData(req.chainId, req.typedData)
}

export async function getEvmAdapter(opts: {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string
}) {
  return PrivyAlchemyEvmProviderAdapter.create({
    walletAddress: opts.agentWalletAddress,
    walletId: opts.agentWalletId,
    signerPrivateKey: decodeSignerKey(opts.signerPrivateKey),
    privyAppId: process.env.PRIVY_APP_ID,
  })
}
