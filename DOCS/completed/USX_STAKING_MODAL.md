# USX Staking Modal - Bot Competition Betting

**Status**: 🟡 IN PROGRESS (Phases 1-3 complete, PledgeModal remaining)
**Created**: 2025-12-14
**Last Updated**: 2026-01-27
**Complexity**: Medium (~6-8 hours)

---

## Progress Summary (2026-01-27)

**Completed**:
- ✅ Phase 1: Research & Setup (contract addresses, WalletConnect ID, deps)
- ✅ Phase 2: Database & Backend (arena_pledges table, endpoints)
- ✅ Phase 3: Frontend Web3 Integration (wagmi config, ArenaWithStaking wrapper)
- ✅ Phase 4: On-Chain Integration (approve + deposit via BetModal)
- ✅ Phase 5: BetModal UI (full flow, error handling, retry)

**Remaining**:
- 🔲 End-to-end test with real USX tokens
- 🔲 Display layer: "Total Backed" per bot, "You bet X" badges
- 🔲 Prize distribution logic

**Key Files**:
- `frontend/lib/wagmi-config.ts` - Scroll chain + WalletConnect (Vercel env var)
- `frontend/lib/contracts.ts` - USX/sUSX addresses and ABIs
- `frontend/components/arena/ArenaWithStaking.tsx` - Web3 provider wrapper + Arena content
- `frontend/components/arena/BetModal.tsx` - Full betting modal with 6-step state machine
- `ggbot.py` - Public pledge endpoints (wallet = identity, no auth)
- `frontend/lib/api.ts` - `recordArenaPledge()` (regular fetch, no auth)

**Architecture Decisions**:
- Web3 lazy-loaded on Arena page only (~65KB savings elsewhere)
- wagmi v2 required (RainbowKit 2.x incompatible with wagmi v3)
- Pledge endpoint is public — wallet address is identity, no ggbots login needed
- `arena_pledges.user_id` nullable (public users may not have ggbots account)
- USX decimals read from contract dynamically, not hardcoded

---

## Overview

Gamification feature allowing users to stake USX tokens on which ggbot they think will win competitions. Users earn base staking yield (worst case) and get prize money if their bot wins (best case).

**Elegant Architecture**: Standard Scroll USX→sUSX staking + simple database record of which bot they picked. All competition logic (winners, prizes, leaderboards) deferred to future phases.

---

## User Flow

1. User clicks "Stake on Bot" (somewhere in UI - TBD)
2. Modal opens → Connect wallet (if not connected)
3. Select which bot to back (dropdown)
4. Enter USX amount to stake
5. Click "Stake" → 2 on-chain transactions:
   - TX 1: Approve USX spending
   - TX 2: Deposit USX → receive sUSX (via Scroll's ERC4626 vault)
6. On success → Record to database: `{ user_id, wallet_address, config_id, amount, tx_hash }`
7. Show success message: "You're backing {bot_name} with {amount} USX!"

**Key Insight**: We're NOT creating custom staking contracts. Users stake normally via Scroll's USX system. We just record their bot choice alongside it.

---

## Database Schema

**Single table** - Minimal, elegant:

```sql
CREATE TABLE usx_stakes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,              -- From Supabase auth (existing)
  wallet_address TEXT NOT NULL,       -- From connected wallet
  config_id UUID REFERENCES configurations(config_id), -- Which bot they're backing
  usx_amount DECIMAL(20, 6) NOT NULL, -- How much they staked
  susx_amount DECIMAL(20, 6),         -- How much sUSX they received (optional tracking)
  tx_hash TEXT NOT NULL,              -- On-chain proof
  staked_at TIMESTAMP DEFAULT NOW(),

  -- Future competition fields (not needed for MVP)
  competition_id UUID,                -- NULL for now, add competitions later
  prize_amount DECIMAL(20, 6),        -- Filled after competition ends
  unstaked_at TIMESTAMP               -- If they unstake early
);

CREATE INDEX idx_usx_stakes_user ON usx_stakes(user_id);
CREATE INDEX idx_usx_stakes_config ON usx_stakes(config_id);
CREATE INDEX idx_usx_stakes_wallet ON usx_stakes(wallet_address);
```

**Why this works**:
- user_id links to existing auth system
- config_id links to bot they're backing (existing configurations table)
- tx_hash proves it happened on-chain
- Everything else (competitions, prizes) we add later

---

## Frontend Web3 Integration

### Dependencies

```bash
cd frontend
npm install wagmi viem @rainbow-me/rainbowkit @tanstack/react-query
```

**Why these libraries:**
- **wagmi**: React hooks for Ethereum (wallet connection, contract calls, transactions)
- **viem**: Modern, lightweight Ethereum library (replaces ethers.js)
- **RainbowKit**: Beautiful wallet connection UI (supports MetaMask, WalletConnect, Coinbase, etc.)
- **@tanstack/react-query**: Required peer dependency for wagmi

### Wagmi Setup

**Create `frontend/lib/wagmi-config.ts`:**

```typescript
import { getDefaultConfig } from '@rainbow-me/rainbowkit'
import { scroll } from 'wagmi/chains'

export const wagmiConfig = getDefaultConfig({
  appName: 'ggbots',
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID!, // Get from WalletConnect Cloud
  chains: [scroll],
  ssr: true,
})
```

**Wrap app in providers (`frontend/app/layout.tsx`):**

```typescript
import { WagmiProvider } from 'wagmi'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RainbowKitProvider } from '@rainbow-me/rainbowkit'
import { wagmiConfig } from '@/lib/wagmi-config'
import '@rainbow-me/rainbowkit/styles.css'

const queryClient = new QueryClient()

export default function RootLayout({ children }) {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  )
}
```

---

## Scroll USX/sUSX Contract Integration

### Contract Addresses (NEED TO FIND THESE)

```typescript
// frontend/lib/contracts.ts
export const SCROLL_CONTRACTS = {
  USX_TOKEN: '0x...', // USX ERC20 token address (NEED TO FIND)
  SUSX_VAULT: '0x...', // sUSX ERC4626 vault address (NEED TO FIND)
} as const

export const SCROLL_CHAIN_ID = 534352 // Scroll mainnet
```

**How to find these:**
- Check official USX docs: https://docs.usx.capital
- Check Scroll's Discord/Telegram
- Look for USX deployment announcements
- Search Scrollscan for USX token deployments

### Contract ABIs

**USX Token (ERC20):**
```typescript
export const USX_ABI = [
  {
    name: 'approve',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'spender', type: 'address' },
      { name: 'amount', type: 'uint256' }
    ],
    outputs: [{ type: 'bool' }]
  },
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ type: 'uint256' }]
  }
] as const
```

**sUSX Vault (ERC4626):**
```typescript
export const SUSX_VAULT_ABI = [
  {
    name: 'deposit',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'assets', type: 'uint256' },
      { name: 'receiver', type: 'address' }
    ],
    outputs: [{ name: 'shares', type: 'uint256' }]
  },
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ type: 'uint256' }]
  }
] as const
```

---

## StakingModal Component

**Create `frontend/components/StakingModal.tsx`:**

```typescript
'use client'

import { useState } from 'react'
import { useAccount, useBalance, useWriteContract, useWaitForTransactionReceipt } from 'wagmi'
import { ConnectButton } from '@rainbow-me/rainbowkit'
import { parseUnits } from 'viem'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { SCROLL_CONTRACTS, USX_ABI, SUSX_VAULT_ABI } from '@/lib/contracts'
import { apiClient } from '@/lib/api'

interface StakingModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function StakingModal({ open, onOpenChange }: StakingModalProps) {
  const { address, isConnected } = useAccount()
  const [selectedBot, setSelectedBot] = useState<string>('')
  const [amount, setAmount] = useState('')
  const [step, setStep] = useState<'input' | 'approving' | 'staking' | 'success'>('input')

  // Get user's USX balance
  const { data: usxBalance } = useBalance({
    address: address,
    token: SCROLL_CONTRACTS.USX_TOKEN,
  })

  const { writeContract } = useWriteContract()

  const handleStake = async () => {
    if (!address || !selectedBot || !amount) return

    try {
      const amountWei = parseUnits(amount, 18) // USX has 18 decimals

      // Step 1: Approve USX spending
      setStep('approving')
      const approveTx = await writeContract({
        address: SCROLL_CONTRACTS.USX_TOKEN,
        abi: USX_ABI,
        functionName: 'approve',
        args: [SCROLL_CONTRACTS.SUSX_VAULT, amountWei],
      })

      // Wait for approval
      await waitForTransaction(approveTx)

      // Step 2: Deposit to vault
      setStep('staking')
      const depositTx = await writeContract({
        address: SCROLL_CONTRACTS.SUSX_VAULT,
        abi: SUSX_VAULT_ABI,
        functionName: 'deposit',
        args: [amountWei, address],
      })

      // Wait for deposit
      await waitForTransaction(depositTx)

      // Step 3: Record to database
      await apiClient.recordUsxStake({
        wallet_address: address,
        config_id: selectedBot,
        usx_amount: amount,
        tx_hash: depositTx,
      })

      setStep('success')
    } catch (error) {
      console.error('Staking error:', error)
      setStep('input')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Stake USX on a Bot</DialogTitle>
        </DialogHeader>

        {!isConnected ? (
          <div className="text-center py-8">
            <p className="mb-4">Connect your wallet to stake</p>
            <ConnectButton />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Bot Selection */}
            <div>
              <label>Select Bot to Back</label>
              <select
                value={selectedBot}
                onChange={(e) => setSelectedBot(e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="">Choose a bot...</option>
                {/* TODO: Fetch active bots */}
              </select>
            </div>

            {/* Amount Input */}
            <div>
              <label>USX Amount</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full p-2 border rounded"
              />
              <p className="text-sm text-gray-500">
                Balance: {usxBalance?.formatted || '0'} USX
              </p>
            </div>

            {/* Stake Button */}
            <button
              onClick={handleStake}
              disabled={!selectedBot || !amount || step !== 'input'}
              className="w-full bg-blue-500 text-white p-3 rounded disabled:opacity-50"
            >
              {step === 'input' && 'Stake USX'}
              {step === 'approving' && 'Approving...'}
              {step === 'staking' && 'Staking...'}
              {step === 'success' && '✓ Staked!'}
            </button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

---

## Backend API

**Add to `ggbot.py`:**

```python
@app.post("/api/v2/usx/stake")
async def record_usx_stake(request: Request):
    """Record user's USX stake on a bot after on-chain transaction"""
    user_id = request.state.user_id  # From auth middleware
    data = await request.json()

    wallet_address = data['wallet_address']
    config_id = data['config_id']
    usx_amount = Decimal(data['usx_amount'])
    tx_hash = data['tx_hash']

    # Optional: Verify transaction on-chain (via Scroll RPC)
    # For MVP, trust the frontend

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usx_stakes (user_id, wallet_address, config_id, usx_amount, tx_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, wallet_address, config_id, usx_amount, tx_hash))
            stake_id = cur.fetchone()[0]
            conn.commit()

    return {"success": True, "stake_id": stake_id}

@app.get("/api/v2/usx/stakes")
async def get_user_stakes(request: Request):
    """Get all USX stakes for current user"""
    user_id = request.state.user_id

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, c.config_name as bot_name
                FROM usx_stakes s
                JOIN configurations c ON s.config_id = c.config_id
                WHERE s.user_id = %s
                ORDER BY s.staked_at DESC
            """, (user_id,))
            stakes = cur.fetchall()

    return {"stakes": stakes}
```

**Add to `frontend/lib/api.ts`:**

```typescript
recordUsxStake: async (data: {
  wallet_address: string
  config_id: string
  usx_amount: string
  tx_hash: string
}) => {
  return apiRequest('/api/v2/usx/stake', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
```

---

## Implementation Phases

### Phase 1: Research & Setup ✅ COMPLETE
- [x] Find USX and sUSX contract addresses on Scroll mainnet
  - USX: `0x3b005fefc63ca7c8d25ee21fba3787229ba4cf03`
  - sUSX: `0xcB14BcdF6cD483665D10dfD6f87d908996C7F922`
- [x] Get WalletConnect Project ID (`66a0c85a2532de4ad0b841ff3b79cb5c`)
- [x] Install dependencies: `wagmi`, `viem`, `@rainbow-me/rainbowkit`
- [x] Set up wagmi config with Scroll chain (`frontend/lib/wagmi-config.ts`)

### Phase 2: Database & Backend ✅ COMPLETE
- [x] Create `arena_pledges` table (renamed from usx_stakes)
- [x] Add `POST /api/v2/arena/pledge` endpoint
- [x] Add `GET /api/v2/arena/pledges` endpoint
- [x] API client methods in `frontend/lib/api.ts`

### Phase 3: Frontend Web3 Integration ✅ COMPLETE
- [x] Lazy-load Web3 providers on Arena page only (`ArenaWithStaking.tsx`)
- [x] Create contract constants file (`lib/contracts.ts`)
- [x] RainbowKit themed with brass palette
- [x] Build passing, bundle ~65KB scoped to Arena

### Phase 4: On-Chain Integration (REMAINING)
- [ ] Implement approve transaction (USX → sUSX vault)
- [ ] Implement deposit transaction (receive sUSX)
- [ ] Add transaction waiting states
- [ ] Test full flow on Scroll mainnet with small amounts

### Phase 5: PledgeModal UI (REMAINING)
- [ ] Build `PledgeModal.tsx` component
- [ ] Bot selection dropdown
- [ ] Amount input with USX balance display
- [ ] Transaction progress overlay
- [ ] Add trigger button to Arena leaderboard
- [ ] Communicate 15-day unstaking cooldown in UI

---

## Future Work (Deferred)

**Competition Logic** - Add later when we're ready:
- Create `bot_competitions` table
- Define competition rules (time windows, eligibility)
- Build leaderboard UI showing bot performance during competition
- Implement prize distribution logic (% of stakes based on winner)
- Add competition admin interface
- Build public competition pages

**Why defer**: We already have bot performance tracking via `account_snapshots`. We can determine "winners" retroactively. Getting the staking mechanism working is the hard part - competition rules are just queries and UX.

---

## Technical Notes

**Why Scroll?**
- USX is Scroll's native stablecoin
- sUSX vault is deployed on Scroll mainnet
- Need Scroll RPC endpoint for transactions

**Why RainbowKit?**
- Beautiful UX out of the box
- Handles multiple wallet types
- Mobile-friendly
- Maintained by WalletConnect team

**Why ERC4626?**
- Standard vault interface
- `deposit(assets, receiver)` → returns shares
- User gets sUSX (yield-bearing) automatically
- No custom logic needed

**Transaction Flow:**
```
User approves → USX.approve(vault, amount)
User deposits → Vault.deposit(amount, userAddress)
Vault mints sUSX → Transfer to userAddress
Frontend records → POST /api/v2/usx/stake
```

---

## Open Questions

1. **Where to trigger the modal?** Bot leaderboard? Competition page? Bot detail page?
2. **Bot eligibility:** Any active bot? Only public performance bots? Admin-curated?
3. **Minimum stake:** Require minimum USX amount?
4. **Competition scope:** Per-user bots only? Platform-wide?
5. **Prize pool:** Who funds it initially? Platform? Percentage of stakes?

---

## Success Criteria

✅ User can connect wallet
✅ User can see their USX balance
✅ User can select a bot from dropdown
✅ User can stake USX and receive sUSX
✅ Stake is recorded in database with bot association
✅ User can view their active stakes

**Later:**
- Competition winners determined
- Prize distribution implemented
- Public leaderboards

---

**Total Estimated Time:** 6-8 hours (excluding competition logic)
