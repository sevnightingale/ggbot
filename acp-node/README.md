# acp-node

Thin TypeScript PM2 sidecar for ACP v2 operations that can't run from Python: Privy-wallet EIP-712 signing for Hyperliquid setup actions.

> ⚠️ **2026-04-24**: this sidecar is **mid-pivot**. Some routes here are dead architecture (see "Dead routes" below). Read [DOCS/todo/ACP_V2_SESSION_HANDOFF.md](../DOCS/todo/ACP_V2_SESSION_HANDOFF.md) before making changes.

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
  "signerPrivateKey": "base64(PKCS8-DER) P-256 private key — NOT base64(PEM)! Privy rejects PEM-with-headers. TS fallback will strip legacy PEM frames."
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

## Dead routes (remove in next pivot)

### `POST /bridge-usdc-to-hl` — DO NOT USE
**Architecture was wrong.** Attempted to push USDC from the agent's Privy smart wallet on Arbitrum to HL's bridge contract via `adapter.sendCalls(42161, ...)`. Virtuals' Alchemy paymaster policy is **Base-only** — the call returns HTTP 400 from `api.acp.virtuals.io/wallets/alchemy-rpc` for any non-Base chainId.

Correct architecture (per `dgclaw-skill/SKILL.md` Step 2): deposits are **ACP buyer jobs** against the DGClaw provider agent with offering `perp_deposit`. DGClaw's backend bridges Base → Arbitrum → HL internally. User sends USDC to agent wallet on **Base**, then backend creates + funds an ACP job.

Next session should:
1. Delete `src/routes/bridge-usdc-to-hl.ts`
2. Replace with `src/routes/deposit-to-dgclaw.ts` using `AcpAgent.createJobByOfferingName` with `perp_deposit` (possibly needs v1 SDK since DGClaw is still ACP v1 — see handoff doc)
3. Remove the `crypto` polyfill from `src/index.ts` (only needed for `sendCalls`)
4. Remove `chains: [arbitrum]` handling in `src/lib/privy-sign.ts` `getEvmAdapter`

## Untested routes (may also need v1 SDK)

- `POST /join-leaderboard` — ACP buyer-side job flow against DegenClaw agent with offering `join_leaderboard`, $0.01 fee. **Built but not end-to-end tested**; DGClaw is a v1 provider agent and our SDK is v2 — interop unverified.
- `POST /forum-post` — `degen.virtuals.io` forum posts for AI Council visibility. Auth scheme (JWT vs ACP-signed) not verified against live endpoint.

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
