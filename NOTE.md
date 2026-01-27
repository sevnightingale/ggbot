Perfect! Got all the contract addresses. Let me also check the sUSX page to understand the staking mechanism:
Perfect! I've got all the contract addresses and staking mechanism details. Let me compile this for you:

Scroll USX/sUSX Contract Addresses

Core Token Contracts

USX (Stablecoin)
• Address: 0x3b005fefc63ca7c8d25ee21fba3787229ba4cf03
• Type: ERC-20 stablecoin pegged 1:1 to USDC
• Scrollscan: https://scrollscan.com/address/0x3b005fefc63ca7c8d25ee21fba3787229ba4cf03

sUSX (Staked/Yield-Bearing USX)
• Address: 0xcB14BcdF6cD483665D10dfD6f87d908996C7F922
• Type: ERC-4626 vault token (yield-bearing wrapper)
• Scrollscan: https://scrollscan.com/address/0xcB14BcdF6cD483665D10dfD6f87d908996C7F922

Supporting Contracts

Reserve Fund
• Address: 0xD09e956353Fc641792a0F1a7d748773358848F65
• Purpose: Insurance buffer ($5M SCR seed, targets 2% of deployed principal)

Asset Manager
• Address: 0xd16909Ecc9c71d481ee3b2Cb1968C0dAdCf0d300
• Purpose: Manages yield strategy deployments

Treasury
• Address: 0x9F3d4b0C9E930Ca3957eCD3DEdb7417f8e0e4c35

How sUSX Staking Works

Mechanism (ERC-4626 Vault)

1. Stake USX → receive sUSX at current exchange rate
2. sUSX appreciates as protocol generates yield (90% to stakers, 10% protocol fee)
3. Unstake sUSX → receive original USX + accumulated yield
4. 15-day cooldown required for unstaking (to unwind yield positions)

Example

• Stake 1,000 USX when rate is 1 USX = 0.9 sUSX → receive 900 sUSX
• Later, rate becomes 1 sUSX = 1.1 USX
• Unstake 900 sUSX → receive 990 USX (10% yield earned)

Yield Sources

Protocol deploys funds via Blend execution layer across:
• Morpho, Aave, Euler (lending)
• Pendle (yield tranching)
• Delta-neutral strategies

Current Distribution (Temporary - Jan/Feb 2026)

Two-week staking epochs while they develop improved smart contract

For "Stake Your Bet on a ggbot" Feature

You'll want to integrate with:
• USX contract (0x3b00...cf03) - for deposits/balances
• sUSX contract (0xcB14...F922) - for staking/unstaking

The sUSX contract is ERC-4626 compliant, so you can use standard vault methods:
• deposit(uint256 assets, address receiver) - stake USX → receive sUSX
• redeem(uint256 shares, address receiver, address owner) - unstake sUSX → receive USX
• withdraw(uint256 assets, address receiver, address owner) - alternative unstaking method
• previewDeposit(uint256 assets) - calculate sUSX you'd receive
• previewRedeem(uint256 shares) - calculate USX you'd receive

Note: 15-day cooldown on unstaking, so you'll need to handle that in your UX!

Sources:
• USX Token on Scrollscan
• sUSX: Yield Bearing USX | USX Docs
• Smart Contract Addresses | USX Docs
• USX: A private, gasless and spendable stablecoin - Scroll.io