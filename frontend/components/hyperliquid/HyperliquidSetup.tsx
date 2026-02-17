'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { WagmiProvider } from 'wagmi'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RainbowKitProvider, ConnectButton, darkTheme } from '@rainbow-me/rainbowkit'
import '@rainbow-me/rainbowkit/styles.css'
import { useAccount, useReadContract, useSignTypedData, useWriteContract, useWaitForTransactionReceipt } from 'wagmi'
import { parseUnits } from 'viem'
import { generatePrivateKey, privateKeyToAccount } from 'viem/accounts'
import { Loader2, CheckCircle2, AlertCircle, Wallet, Zap, X, ArrowDownToLine, ArrowUpFromLine } from 'lucide-react'

import {
  hyperliquidWagmiConfig,
  ARBITRUM_USDC_ADDRESS,
  HYPERLIQUID_BRIDGE_ADDRESS,
  ERC20_ABI,
  HYPERLIQUID_API_URL,
  HYPERLIQUID_EIP712_DOMAIN,
  HYPERLIQUID_APPROVE_AGENT_TYPES,
  HYPERLIQUID_WITHDRAW_TYPES,
  HYPERLIQUID_SIGNATURE_CHAIN_ID_HEX,
} from '@/lib/hyperliquid-config'
import { apiClient } from '@/lib/api'

const web3QueryClient = new QueryClient()

const ggbotsTheme = darkTheme({
  accentColor: '#c1a87d',
  accentColorForeground: '#0b0b0c',
  borderRadius: 'medium',
  fontStack: 'system',
})

type SetupStep = 'idle' | 'generating' | 'signing' | 'submitting' | 'storing' | 'done'

function HyperliquidContent() {
  const { address, isConnected } = useAccount()
  const { signTypedDataAsync } = useSignTypedData()

  // Hyperliquid connection state (from backend)
  const [hlStatus, setHlStatus] = useState<{
    connected: boolean
    wallet_address: string | null
    account_value: number | null
    margin_used: number | null
    open_notional: number | null
    withdrawable: number | null
    positions_count: number | null
  } | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [statusError, setStatusError] = useState<string | null>(null)

  // Setup flow state
  const [setupStep, setSetupStep] = useState<SetupStep>('idle')
  const [setupError, setSetupError] = useState<string | null>(null)

  // Test trade state
  const [testTradeLoading, setTestTradeLoading] = useState(false)
  const [testTradeResult, setTestTradeResult] = useState<{
    status: string
    entry_price?: number
    close_status?: string
    error?: string
  } | null>(null)

  // Disconnect state
  const [disconnecting, setDisconnecting] = useState(false)

  // Deposit state
  const [depositAmount, setDepositAmount] = useState('')
  const [depositTxHash, setDepositTxHash] = useState<`0x${string}` | undefined>()

  // Withdraw state
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawLoading, setWithdrawLoading] = useState(false)
  const [withdrawResult, setWithdrawResult] = useState<{ status: string; message?: string } | null>(null)

  // Read Arbitrum USDC balance
  const { data: usdcBalance, refetch: refetchUsdcBalance } = useReadContract({
    address: ARBITRUM_USDC_ADDRESS,
    abi: ERC20_ABI,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: { enabled: !!address },
  })

  const formattedUsdcBalance = usdcBalance
    ? (Number(usdcBalance) / 1e6).toFixed(2)
    : '0.00'

  // Deposit: ERC-20 transfer to bridge
  const { writeContract: writeDeposit, isPending: isDepositPending, data: depositData } = useWriteContract()

  // Track deposit tx confirmation
  const { isLoading: isDepositConfirming, isSuccess: isDepositConfirmed } = useWaitForTransactionReceipt({
    hash: depositTxHash,
  })

  // When deposit tx hash comes back, save it
  useEffect(() => {
    if (depositData) {
      setDepositTxHash(depositData)
    }
  }, [depositData])

  // When deposit confirms, refresh balances
  useEffect(() => {
    if (isDepositConfirmed) {
      setDepositAmount('')
      refetchUsdcBalance()
      // Give Hyperliquid a moment to process the deposit
      setTimeout(() => fetchStatus(), 5000)
    }
  }, [isDepositConfirmed]) // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch Hyperliquid status from backend
  const fetchStatus = useCallback(async () => {
    try {
      setStatusLoading(true)
      setStatusError(null)
      const status = await apiClient.getHyperliquidStatus()
      setHlStatus(status)
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : 'Failed to check status')
      setHlStatus(null)
    } finally {
      setStatusLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // Authorize API wallet flow
  const handleAuthorize = async () => {
    if (!address) return

    try {
      setSetupError(null)

      // Step 1: Generate API wallet keypair
      setSetupStep('generating')
      const apiPrivateKey = generatePrivateKey()
      const apiAccount = privateKeyToAccount(apiPrivateKey)
      const agentAddress = apiAccount.address

      // Step 2: Construct EIP-712 message and sign
      setSetupStep('signing')
      const nonce = Date.now()

      const signature = await signTypedDataAsync({
        domain: HYPERLIQUID_EIP712_DOMAIN,
        types: HYPERLIQUID_APPROVE_AGENT_TYPES,
        primaryType: 'HyperliquidTransaction:ApproveAgent',
        message: {
          hyperliquidChain: 'Mainnet',
          agentAddress: agentAddress,
          agentName: 'ggbots',
          nonce: BigInt(nonce),
        },
      })

      // Parse signature into r, s, v
      const r = signature.slice(0, 66) as `0x${string}`
      const s = `0x${signature.slice(66, 130)}` as `0x${string}`
      const v = parseInt(signature.slice(130, 132), 16)

      // Step 3: POST to Hyperliquid API
      setSetupStep('submitting')
      const hlPayload = {
        action: {
          type: 'approveAgent',
          hyperliquidChain: 'Mainnet',
          signatureChainId: HYPERLIQUID_SIGNATURE_CHAIN_ID_HEX,
          agentAddress: agentAddress,
          agentName: 'ggbots',
          nonce: nonce,
        },
        nonce: nonce,
        signature: { r, s, v },
      }

      const hlResponse = await fetch(`${HYPERLIQUID_API_URL}/exchange`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hlPayload),
      })

      if (!hlResponse.ok) {
        const hlError = await hlResponse.text()
        throw new Error(`Hyperliquid API error: ${hlError}`)
      }

      const hlResult = await hlResponse.json()
      if (hlResult.status !== 'ok') {
        throw new Error(`Hyperliquid rejected: ${JSON.stringify(hlResult)}`)
      }

      // Step 4: Store credentials in our backend
      setSetupStep('storing')
      await apiClient.setupHyperliquid(apiPrivateKey, address)

      // Done - refresh status
      setSetupStep('done')
      await fetchStatus()

      // Reset after a moment
      setTimeout(() => setSetupStep('idle'), 2000)
    } catch (err) {
      console.error('Hyperliquid setup error:', err)
      const message = err instanceof Error ? err.message : 'Setup failed'

      if (message.includes('User rejected') || message.includes('user rejected')) {
        setSetupError('Signature rejected. Please try again.')
      } else {
        setSetupError(message)
      }
      setSetupStep('idle')
    }
  }

  // Deposit USDC to Hyperliquid (on-chain ERC-20 transfer to bridge)
  const handleDeposit = () => {
    if (!depositAmount || !address) return

    const amountFloat = parseFloat(depositAmount)
    if (isNaN(amountFloat) || amountFloat < 5) return

    // USDC has 6 decimals
    const amountWei = parseUnits(depositAmount, 6)

    writeDeposit({
      address: ARBITRUM_USDC_ADDRESS,
      abi: ERC20_ABI,
      functionName: 'transfer',
      args: [HYPERLIQUID_BRIDGE_ADDRESS, amountWei],
    })
  }

  // Withdraw USDC from Hyperliquid (EIP-712 signed message, no gas)
  const handleWithdraw = async () => {
    if (!withdrawAmount || !address) return

    const amountFloat = parseFloat(withdrawAmount)
    if (isNaN(amountFloat) || amountFloat <= 0) return

    try {
      setWithdrawLoading(true)
      setWithdrawResult(null)

      const timestamp = Date.now()

      // Sign EIP-712 withdraw message
      const signature = await signTypedDataAsync({
        domain: HYPERLIQUID_EIP712_DOMAIN,
        types: HYPERLIQUID_WITHDRAW_TYPES,
        primaryType: 'HyperliquidTransaction:Withdraw',
        message: {
          hyperliquidChain: 'Mainnet',
          destination: address,
          amount: withdrawAmount,
          time: BigInt(timestamp),
        },
      })

      // Parse signature
      const r = signature.slice(0, 66) as `0x${string}`
      const s = `0x${signature.slice(66, 130)}` as `0x${string}`
      const v = parseInt(signature.slice(130, 132), 16)

      // POST to Hyperliquid API
      const hlPayload = {
        action: {
          type: 'withdraw3',
          hyperliquidChain: 'Mainnet',
          signatureChainId: HYPERLIQUID_SIGNATURE_CHAIN_ID_HEX,
          destination: address,
          amount: withdrawAmount,
          time: timestamp,
        },
        nonce: timestamp,
        signature: { r, s, v },
      }

      const hlResponse = await fetch(`${HYPERLIQUID_API_URL}/exchange`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(hlPayload),
      })

      if (!hlResponse.ok) {
        const hlError = await hlResponse.text()
        throw new Error(`Withdrawal failed: ${hlError}`)
      }

      const hlResult = await hlResponse.json()
      if (hlResult.status !== 'ok') {
        throw new Error(`Withdrawal rejected: ${JSON.stringify(hlResult)}`)
      }

      setWithdrawResult({ status: 'success', message: `Withdrawal of $${withdrawAmount} initiated. Funds will arrive on Arbitrum shortly.` })
      setWithdrawAmount('')

      // Refresh balances after a delay
      setTimeout(() => {
        fetchStatus()
        refetchUsdcBalance()
      }, 5000)

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Withdrawal failed'
      if (message.includes('User rejected') || message.includes('user rejected')) {
        setWithdrawResult({ status: 'failed', message: 'Signature rejected.' })
      } else {
        setWithdrawResult({ status: 'failed', message })
      }
    } finally {
      setWithdrawLoading(false)
    }
  }

  // Test trade
  const handleTestTrade = async () => {
    try {
      setTestTradeLoading(true)
      setTestTradeResult(null)
      const result = await apiClient.testHyperliquidTrade()
      setTestTradeResult(result)
      await fetchStatus()
    } catch (err) {
      setTestTradeResult({
        status: 'failed',
        error: err instanceof Error ? err.message : 'Test trade failed',
      })
    } finally {
      setTestTradeLoading(false)
    }
  }

  // Disconnect
  const handleDisconnect = async () => {
    try {
      setDisconnecting(true)
      await apiClient.disconnectHyperliquid()
      setHlStatus({ connected: false, wallet_address: null, account_value: null, margin_used: null, open_notional: null, withdrawable: null, positions_count: null })
      setTestTradeResult(null)
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : 'Failed to disconnect')
    } finally {
      setDisconnecting(false)
    }
  }

  const setupStepLabels: Record<SetupStep, string> = {
    idle: '',
    generating: 'Generating API wallet...',
    signing: 'Sign in MetaMask...',
    submitting: 'Registering with Hyperliquid...',
    storing: 'Storing credentials...',
    done: 'Connected!',
  }

  const truncateAddress = (addr: string) =>
    `${addr.slice(0, 6)}...${addr.slice(-4)}`

  const depositAmountFloat = parseFloat(depositAmount) || 0
  const hasEnoughUsdc = usdcBalance ? depositAmountFloat <= Number(usdcBalance) / 1e6 : false
  const isValidDeposit = depositAmountFloat >= 5 && hasEnoughUsdc

  // Loading state
  if (statusLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
        <span className="text-[var(--text-muted)]">Checking connection...</span>
      </div>
    )
  }

  // Connected state
  if (hlStatus?.connected) {
    return (
      <div className="space-y-6">
        {/* Connection Status */}
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle2 className="h-6 w-6 text-[var(--profit-color)]" />
            <h2 className="text-xl font-display text-[var(--text-primary)]">Hyperliquid Connected</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Wallet</div>
              <div className="text-sm font-mono text-[var(--text-primary)]">
                {hlStatus.wallet_address ? truncateAddress(hlStatus.wallet_address) : '...'}
              </div>
            </div>

            <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Account Value</div>
              <div className="text-lg font-mono font-bold text-[var(--accent)]">
                {hlStatus.account_value !== null ? `$${hlStatus.account_value.toFixed(2)}` : '...'}
              </div>
            </div>

            <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Withdrawable</div>
              <div className="text-sm font-mono text-[var(--text-primary)]">
                ${hlStatus.withdrawable?.toFixed(2) ?? '0.00'}
              </div>
            </div>

            <div className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border)] p-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Open Positions</div>
              <div className="text-sm font-mono text-[var(--text-primary)]">
                {hlStatus.positions_count !== null ? hlStatus.positions_count : '...'}
              </div>
            </div>
          </div>
        </div>

        {/* Deposit & Withdraw — only shown when wallet is connected via RainbowKit */}
        {isConnected && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Deposit */}
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
              <div className="flex items-center gap-2 mb-4">
                <ArrowDownToLine className="h-5 w-5 text-[var(--accent)]" />
                <h3 className="text-base font-display text-[var(--text-primary)]">Deposit</h3>
              </div>
              <p className="text-xs text-[var(--text-muted)] mb-3">
                Send USDC from Arbitrum to Hyperliquid. Minimum $5. Costs gas.
              </p>
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-3">
                <Wallet className="h-3 w-3" />
                <span>Arbitrum balance: {formattedUsdcBalance} USDC</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="5"
                  step="1"
                  placeholder="Amount (min $5)"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
                />
                <button
                  onClick={handleDeposit}
                  disabled={!isValidDeposit || isDepositPending || isDepositConfirming}
                  className="px-4 py-2 rounded-lg font-medium text-sm transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDepositPending ? 'Confirm...' : isDepositConfirming ? 'Sending...' : 'Deposit'}
                </button>
              </div>
              {depositAmountFloat > 0 && depositAmountFloat < 5 && (
                <p className="text-xs text-[var(--loss-color)] mt-2">Minimum deposit is $5</p>
              )}
              {isDepositConfirmed && (
                <p className="text-xs text-[var(--profit-color)] mt-2">Deposit sent! Balance will update in ~30 seconds.</p>
              )}
            </div>

            {/* Withdraw */}
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
              <div className="flex items-center gap-2 mb-4">
                <ArrowUpFromLine className="h-5 w-5 text-[var(--accent)]" />
                <h3 className="text-base font-display text-[var(--text-primary)]">Withdraw</h3>
              </div>
              <p className="text-xs text-[var(--text-muted)] mb-3">
                Withdraw USDC from Hyperliquid to Arbitrum. No gas fees. Signed by your wallet.
              </p>
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-3">
                <Wallet className="h-3 w-3" />
                <span>Withdrawable: ${hlStatus.withdrawable?.toFixed(2) ?? '0.00'}</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  placeholder="Amount"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
                />
                <button
                  onClick={handleWithdraw}
                  disabled={!withdrawAmount || parseFloat(withdrawAmount) <= 0 || withdrawLoading}
                  className="px-4 py-2 rounded-lg font-medium text-sm transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {withdrawLoading ? 'Signing...' : 'Withdraw'}
                </button>
              </div>
              {withdrawResult && (
                <p className={`text-xs mt-2 ${withdrawResult.status === 'success' ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
                  {withdrawResult.message}
                </p>
              )}
            </div>
          </div>
        )}

        {!isConnected && (
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
            <p className="text-sm text-[var(--text-secondary)] mb-3">
              Connect your wallet to deposit or withdraw USDC.
            </p>
            <ConnectButton />
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleTestTrade}
            disabled={testTradeLoading}
            className="flex-1 flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50"
          >
            {testTradeLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Trading 0.001 ETH...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Test Trade (0.001 ETH)
              </>
            )}
          </button>

          <button
            onClick={handleDisconnect}
            disabled={disconnecting}
            className="flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-medium transition-colors border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--loss-color)] hover:border-[var(--loss-color)] disabled:opacity-50"
          >
            {disconnecting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <X className="h-4 w-4" />
            )}
            Disconnect
          </button>

          <button
            onClick={fetchStatus}
            className="flex items-center justify-center gap-2 rounded-xl px-4 py-3 font-medium transition-colors border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]"
          >
            Refresh
          </button>
        </div>

        {/* Test Trade Result */}
        {testTradeResult && (
          <div className={`rounded-xl border p-4 ${
            testTradeResult.status === 'success'
              ? 'border-[var(--profit-color)] bg-[var(--profit-color)]/10'
              : 'border-[var(--loss-color)] bg-[var(--loss-color)]/10'
          }`}>
            {testTradeResult.status === 'success' ? (
              <div className="space-y-1">
                <div className="font-medium text-[var(--profit-color)]">Test trade successful</div>
                <div className="text-sm text-[var(--text-secondary)]">
                  Entry: ${testTradeResult.entry_price?.toFixed(2)} | Close: {testTradeResult.close_status}
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                <div className="font-medium text-[var(--loss-color)]">Test trade failed</div>
                <div className="text-sm text-[var(--text-secondary)]">{testTradeResult.error}</div>
              </div>
            )}
          </div>
        )}

        {statusError && (
          <div className="rounded-xl border border-[var(--loss-color)] bg-[var(--loss-color)]/10 p-4">
            <div className="text-sm text-[var(--loss-color)]">{statusError}</div>
          </div>
        )}
      </div>
    )
  }

  // Not connected state — Setup flow
  return (
    <div className="space-y-6">
      {/* Step 1: Connect Wallet */}
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center">
            <span className="text-sm font-bold text-[var(--accent)]">1</span>
          </div>
          <h2 className="text-lg font-display text-[var(--text-primary)]">Connect Wallet</h2>
        </div>

        <p className="text-sm text-[var(--text-secondary)] mb-4">
          Connect your wallet on Arbitrum. You need USDC deposited on Hyperliquid to trade.
        </p>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <ConnectButton />

          {isConnected && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]">
              <Wallet className="h-3.5 w-3.5 text-[var(--text-muted)]" />
              <span className="text-sm font-mono text-[var(--text-secondary)]">
                {formattedUsdcBalance} USDC
              </span>
              <span className="text-xs text-[var(--text-muted)]">(Arbitrum)</span>
            </div>
          )}
        </div>
      </div>

      {/* Step 2: Deposit USDC (optional, shown when wallet connected) */}
      {isConnected && (
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center">
              <ArrowDownToLine className="h-4 w-4 text-[var(--accent)]" />
            </div>
            <h2 className="text-lg font-display text-[var(--text-primary)]">Deposit USDC to Hyperliquid</h2>
            <span className="text-xs text-[var(--text-muted)] px-2 py-0.5 rounded bg-[var(--bg-primary)] border border-[var(--border)]">Optional</span>
          </div>

          <p className="text-sm text-[var(--text-secondary)] mb-4">
            Send USDC from your Arbitrum wallet to Hyperliquid. Minimum $5. This is an on-chain transaction (costs gas).
          </p>

          <div className="flex gap-2">
            <input
              type="number"
              min="5"
              step="1"
              placeholder="Amount (min $5)"
              value={depositAmount}
              onChange={(e) => setDepositAmount(e.target.value)}
              className="flex-1 px-3 py-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
            />
            <button
              onClick={handleDeposit}
              disabled={!isValidDeposit || isDepositPending || isDepositConfirming}
              className="px-5 py-2.5 rounded-lg font-medium text-sm transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isDepositPending ? 'Confirm in wallet...' : isDepositConfirming ? 'Sending...' : 'Deposit'}
            </button>
          </div>
          {depositAmountFloat > 0 && depositAmountFloat < 5 && (
            <p className="text-xs text-[var(--loss-color)] mt-2">Minimum deposit is $5</p>
          )}
          {depositAmountFloat > 0 && !hasEnoughUsdc && (
            <p className="text-xs text-[var(--loss-color)] mt-2">Insufficient USDC balance on Arbitrum</p>
          )}
          {isDepositConfirmed && (
            <p className="text-xs text-[var(--profit-color)] mt-2">Deposit sent! Your Hyperliquid balance will update in ~30 seconds.</p>
          )}
        </div>
      )}

      {/* Step 3: Authorize API Wallet */}
      <div className={`rounded-2xl border bg-[var(--bg-secondary)] p-6 ${
        isConnected ? 'border-[var(--border)]' : 'border-[var(--border)]/50 opacity-50'
      }`}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center">
            <span className="text-sm font-bold text-[var(--accent)]">2</span>
          </div>
          <h2 className="text-lg font-display text-[var(--text-primary)]">Authorize ggbots to Trade</h2>
        </div>

        <p className="text-sm text-[var(--text-secondary)] mb-2">
          This creates an API wallet that can execute trades but <strong>cannot withdraw funds</strong>.
          Enforced at the Hyperliquid protocol level.
        </p>
        <p className="text-xs text-[var(--text-muted)] mb-4">
          You&apos;ll sign a message in MetaMask. No gas fees. No funds leave your wallet.
        </p>

        <button
          onClick={handleAuthorize}
          disabled={!isConnected || setupStep !== 'idle'}
          className="flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {setupStep !== 'idle' ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {setupStepLabels[setupStep]}
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              Authorize ggbots to Trade
            </>
          )}
        </button>

        {setupError && (
          <div className="mt-4 flex items-start gap-2 p-3 rounded-lg bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30">
            <AlertCircle className="h-4 w-4 text-[var(--loss-color)] mt-0.5 flex-shrink-0" />
            <span className="text-sm text-[var(--loss-color)]">{setupError}</span>
          </div>
        )}
      </div>

      {statusError && (
        <div className="rounded-xl border border-[var(--loss-color)] bg-[var(--loss-color)]/10 p-4">
          <div className="text-sm text-[var(--loss-color)]">{statusError}</div>
        </div>
      )}
    </div>
  )
}

/**
 * Hyperliquid setup page with Web3 wallet connection.
 *
 * Wraps content in its own WagmiProvider (Arbitrum chain) + RainbowKit.
 * Isolated from Arena's Scroll-chain config.
 */
export default function HyperliquidSetup() {
  return (
    <WagmiProvider config={hyperliquidWagmiConfig}>
      <QueryClientProvider client={web3QueryClient}>
        <RainbowKitProvider theme={ggbotsTheme}>
          <div className="min-h-screen bg-[var(--bg-primary)]">
            {/* Header */}
            <header className="border-b border-[var(--border)] bg-[var(--bg-primary)]">
              <div className="flex items-center justify-between px-4 py-3 max-w-3xl mx-auto">
                <a href="https://app.ggbots.ai" className="flex items-center gap-2">
                  <img
                    src="https://ggbots.ai/ggbots_logo.png"
                    alt="ggbots logo"
                    width={28}
                    height={28}
                    className="h-7 w-auto"
                  />
                  <span className="font-display text-lg text-[var(--accent)]">ggbots</span>
                </a>
                <a
                  href="https://app.ggbots.ai/forge"
                  className="text-sm text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                >
                  Back to Forge
                </a>
              </div>
            </header>

            {/* Content */}
            <div className="max-w-3xl mx-auto px-4 py-8">
              <div className="mb-8">
                <h1 className="font-display text-3xl text-[var(--text-primary)] mb-2">
                  Hyperliquid Setup
                </h1>
                <p className="text-[var(--text-secondary)]">
                  Connect your wallet to enable live trading on Hyperliquid.
                </p>
              </div>

              <HyperliquidContent />
            </div>
          </div>
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  )
}
