// Privy-wallet EIP-712 signing via our registered P-256 delegated signer.
//
// TODO(Phase 1 integration): wire up to @privy-io/node + @virtuals-protocol/acp-node-v2.
//
// What this function must do end-to-end:
//   1. Initialize Privy client (PrivyClient({ appId, appSecret }))
//   2. Load the P-256 signer private key (passed in as base64-PEM) into a KeyQuorum / session-signer context
//   3. Call privy.walletApi.ethereum.signTypedData({ walletId, typedData }) with the Privy-wallet's walletId
//      — Privy authenticates the request via our signer, then signs the typed data with the embedded wallet's secp256k1 key
//   4. Return the 0x-prefixed hex signature (r || s || v, 65 bytes)
//
// Reference:
//   - @virtuals-protocol/acp-cli/src/lib/api/agent.ts — uses `addSignerWithUrl` which is the registration half of this same flow
//   - @virtuals-protocol/acp-cli/src/commands/wallet.ts — `wallet sign-typed-data` command (the escape hatch dgclaw-skill scripts call via execSync)
//   - docs.privy.io/api-reference/signers — session signer auth + signing

export interface SignTypedDataRequest {
  agentWalletAddress: `0x${string}`
  agentWalletId: string
  signerPrivateKey: string  // base64-encoded PEM, from our Vault
  typedData: {
    domain: Record<string, unknown>
    types: Record<string, readonly { name: string; type: string }[]>
    primaryType: string
    message: Record<string, unknown>
  }
}

export async function signTypedDataWithPrivy(req: SignTypedDataRequest): Promise<string> {
  // Deliberately throws until we verify the exact @privy-io/node session-signer API.
  // Swapping the throw for a live call is a ~30-line change once we confirm the shape.
  void req
  throw new Error(
    'privy-sign: NotImplemented. See TODO in src/lib/privy-sign.ts. ' +
    'Expected call: privy.walletApi.ethereum.signTypedData({ walletId, typedData }) with session signer auth.',
  )
}
