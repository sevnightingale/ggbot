# acp-node

Thin TypeScript PM2 sidecar for ACP v2 operations that can't run from Python: Privy-wallet EIP-712 signing for Hyperliquid setup actions.

## Why this exists

Virtuals v2 provisions agents with Privy-backed smart wallets. To trade on Hyperliquid the agent must:

1. Activate a HL unified account (EIP-712 `userSetAbstraction`)
2. Authorize an HL API wallet (EIP-712 `approveAgent`)

Both actions must be signed by the Privy wallet, authenticated via the P-256 delegated signer we registered during the Deploy Live Version flow. `@privy-io/node` is the only canonical path and has no Python equivalent.

## What it is NOT

- Not a trading execution service — bot trades flow through the Python `HyperliquidLiveTradingService` using the HL API wallet key this sidecar generates.
- Not an ACP provider/buyer — that's `sebastian-virtuals` (v1) and will migrate here only if/when we have a reason to.
- Not user-facing — every endpoint requires the `X-Service-Auth` shared secret; only the Python backend calls it over localhost.

## Signing internals

All EIP-712 signing goes through `PrivyAlchemyEvmProviderAdapter` from `@virtuals-protocol/acp-node-v2`. The adapter accepts our P-256 signer private key in memory (no OS keychain dependency), handles Privy's session-signer authentication protocol internally, and returns standard Ethereum `{r, s, v}` signatures.

See `src/lib/privy-sign.ts`.

## API

All POSTs require `X-Service-Auth: <ACP_NODE_SHARED_SECRET>`.

### `POST /setup-hl-unified-account`
Signs `userSetAbstraction` typed data via Privy, POSTs to HL. Ports `dgclaw-skill/scripts/activate-unified.ts`.

**Body**:
```json
{
  "agentWalletAddress": "0x…",
  "agentWalletId": "privy-wallet-id-from-acp-agents-response",
  "signerPrivateKey": "base64-PEM-encoded P-256 private key"
}
```

### `POST /authorize-hl-api-wallet`
Generates a fresh viem secp256k1 keypair, signs `approveAgent` via Privy, POSTs to HL, returns the new API wallet's private key for Vault storage. Ports `dgclaw-skill/scripts/add-api-wallet.ts`.

**Body** same as above plus optional `agentName`.

**Response** includes `apiWalletAddress` + `apiWalletPrivateKey` (0x-hex). Python backend must store in Vault immediately — this sidecar is stateless.

### `POST /withdraw-from-hl`
Signs `withdraw3` typed data via Privy, POSTs to HL. Destination defaults to the agent's own wallet; optional `destination` param for withdrawing to a different address. HL charges a small flat fee (~$1).

**Body**:
```json
{
  "agentWalletAddress": "0x…",
  "agentWalletId": "privy-wallet-id",
  "signerPrivateKey": "base64-PEM",
  "amountUsdc": "100",
  "destination": "0x… (optional, defaults to agentWalletAddress)"
}
```

### `GET /health`
Returns `{ status, service, version }`. No auth required.

## Not yet implemented (roadmap)

These are required for complete DGClaw parity per `dgclaw-skill/SKILL.md`, but not blockers for MVP Deploy Live Version:

- `POST /bridge-usdc-to-hl` — Arbitrum USDC → HL deposit. For MVP, users deposit USDC directly to their agent's wallet **on Arbitrum** (not Base) and then send to HL's bridge contract `0x2df1c51e09aecf9cacb7bc98cb1742757f163df7`. Full automation (signing an `adapter.sendTransaction()` with the USDC transfer calldata) comes in a follow-up.
- `POST /join-leaderboard` — ACP v2 buyer-side job flow against DegenClaw agent (wallet `0xd478a8B40372db16cA8045F28C6FE07228F3781A`, offering `join_leaderboard`, $0.01 fee). Requires `AcpAgent` class setup, not just the provider adapter. **May be optional** — the AI Council reads all HL trades; need to verify whether explicit leaderboard registration is required.
- `POST /forum-post` — `degen.virtuals.io` forum posts for AI Council visibility. Deferred.

## Dev

```bash
cd acp-node
npm install
cp .env.example .env            # fill in PRIVY_APP_SECRET + ACP_NODE_SHARED_SECRET
npm run dev
```

## Deploy

PM2 entry added in `ecosystem.config.js`. Starts with:

```bash
pm2 start ecosystem.config.js --only acp-node
pm2 logs acp-node
```

## Related

- `api/arena_v2.py` (Python backend) — orchestrates Deploy Live Version flow, calls this sidecar
- `dgclaw-skill` (reference) — `github.com/Virtual-Protocol/dgclaw-skill`, the TypeScript originals we ported
- `@virtuals-protocol/acp-node-v2` — Virtuals SDK, provides `ACP_SERVER_URL` + Privy provider adapter
