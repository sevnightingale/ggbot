/**
 * Scroll mainnet contract addresses and ABIs for USX staking
 *
 * USX is Scroll's native stablecoin (pegged 1:1 to USDC)
 * sUSX is the yield-bearing staked version (ERC-4626 vault)
 *
 * Source: https://docs.usx.capital
 */

// Contract addresses on Scroll mainnet
export const SCROLL_CONTRACTS = {
  // USX ERC-20 stablecoin
  USX_TOKEN: '0x3b005fefc63ca7c8d25ee21fba3787229ba4cf03' as const,

  // sUSX ERC-4626 vault (yield-bearing staked USX)
  SUSX_VAULT: '0xcB14BcdF6cD483665D10dfD6f87d908996C7F922' as const,

  // Supporting contracts (for reference, not directly used)
  RESERVE_FUND: '0xD09e956353Fc641792a0F1a7d748773358848F65' as const,
  ASSET_MANAGER: '0xd16909Ecc9c71d481ee3b2Cb1968C0dAdCf0d300' as const,
  TREASURY: '0x9F3d4b0C9E930Ca3957eCD3DEdb7417f8e0e4c35' as const,
} as const

// USX Token ABI (ERC-20 subset we need)
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
  },
  {
    name: 'allowance',
    type: 'function',
    stateMutability: 'view',
    inputs: [
      { name: 'owner', type: 'address' },
      { name: 'spender', type: 'address' }
    ],
    outputs: [{ type: 'uint256' }]
  },
  {
    name: 'decimals',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ type: 'uint8' }]
  },
  {
    name: 'symbol',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ type: 'string' }]
  }
] as const

// sUSX Vault ABI (ERC-4626 subset we need)
export const SUSX_VAULT_ABI = [
  // Deposit USX, receive sUSX shares
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
  // Preview how many shares you'd get for an asset amount
  {
    name: 'previewDeposit',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'assets', type: 'uint256' }],
    outputs: [{ type: 'uint256' }]
  },
  // Get sUSX balance (shares)
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ type: 'uint256' }]
  },
  // Convert shares to assets (how much USX your sUSX is worth)
  {
    name: 'convertToAssets',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'shares', type: 'uint256' }],
    outputs: [{ type: 'uint256' }]
  },
  // Get the underlying asset (USX) address
  {
    name: 'asset',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ type: 'address' }]
  },
  // Total assets in the vault
  {
    name: 'totalAssets',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ type: 'uint256' }]
  }
] as const

/**
 * Important: sUSX has a 15-day cooldown period for unstaking.
 * This is by design - funds are deployed in yield strategies.
 * For Arena competitions, this actually helps prevent gaming.
 */
export const SUSX_COOLDOWN_DAYS = 15
