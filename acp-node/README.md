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

**Response**:
```json
{ "success": true, "hlResponse": { "status": "ok", ... } }
```

### `POST /authorize-hl-api-wallet`
Generates a fresh viem secp256k1 keypair, signs `approveAgent` via Privy, POSTs to HL, returns the new API wallet's private key for Vault storage. Ports `dgclaw-skill/scripts/add-api-wallet.ts`.

**Body**:
```json
{
  "agentWalletAddress": "0x…",
  "agentWalletId": "privy-wallet-id",
  "signerPrivateKey": "base64-PEM",
  "agentName": "optional-friendly-name"
}
```

**Response**:
```json
{
  "success": true,
  "apiWalletAddress": "0x…",
  "apiWalletPrivateKey": "0x…64hex",
  "hlResponse": { "status": "ok" }
}
```

Python backend must store `apiWalletPrivateKey` in Supabase Vault immediately on receipt — it is NOT retained by this sidecar.

### `GET /health`
Returns `{ status: "ok", version }`. No auth required.

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
