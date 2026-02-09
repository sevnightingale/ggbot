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

interface LiveTradingModalContentProps {
  onComplete?: () => void
}

type SetupStep = 'idle' | 'generating' | 'signing' | 'submitting' | 'storing' | 'done'

function ModalContent({ onComplete }: LiveTradingModalContentProps) {
  const { address, isConnected } = useAccount()
  const { signTypedDataAsync } = useSignTypedData()

  // Hyperliquid connection state (from backend)
  const [hlStatus, setHlStatus] = useState<{
    connected: boolean
    wallet_address: string | null
    account_value: number | null
    available_balance: number | null
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

  useEffect(() => {
    if (depositData) {
      setDepositTxHash(depositData)
    }
  }, [depositData])

  useEffect(() => {
    if (isDepositConfirmed) {
      setDepositAmount('')
      refetchUsdcBalance()
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

      setSetupStep('generating')
      const apiPrivateKey = generatePrivateKey()
      const apiAccount = privateKeyToAccount(apiPrivateKey)
      const agentAddress = apiAccount.address

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

      const r = signature.slice(0, 66) as `0x${string}`
      const s = `0x${signature.slice(66, 130)}` as `0x${string}`
      const v = parseInt(signature.slice(130, 132), 16)

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

      setSetupStep('storing')
      await apiClient.setupHyperliquid(apiPrivateKey, address)

      setSetupStep('done')
      await fetchStatus()
      onComplete?.()

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

  const handleDeposit = () => {
    if (!depositAmount || !address) return

    const amountFloat = parseFloat(depositAmount)
    if (isNaN(amountFloat) || amountFloat < 5) return

    const amountWei = parseUnits(depositAmount, 6)

    writeDeposit({
      address: ARBITRUM_USDC_ADDRESS,
      abi: ERC20_ABI,
      functionName: 'transfer',
      args: [HYPERLIQUID_BRIDGE_ADDRESS, amountWei],
    })
  }

  const handleWithdraw = async () => {
    if (!withdrawAmount || !address) return

    const amountFloat = parseFloat(withdrawAmount)
    if (isNaN(amountFloat) || amountFloat <= 0) return

    try {
      setWithdrawLoading(true)
      setWithdrawResult(null)

      const timestamp = Date.now()

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

      const r = signature.slice(0, 66) as `0x${string}`
      const s = `0x${signature.slice(66, 130)}` as `0x${string}`
      const v = parseInt(signature.slice(130, 132), 16)

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

  const handleDisconnect = async () => {
    try {
      setDisconnecting(true)
      await apiClient.disconnectHyperliquid()
      setHlStatus({ connected: false, wallet_address: null, account_value: null, available_balance: null, positions_count: null })
      setTestTradeResult(null)
      onComplete?.()
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
      <div className="flex flex-col items-center justify-center py-12 gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
        <span className="text-sm text-[var(--text-muted)]">Checking connection...</span>
      </div>
    )
  }

  // Connected state — manage funds
  if (hlStatus?.connected) {
    return (
      <div className="space-y-4">
        {/* Status */}
        <div className="rounded-xl border border-[var(--signal)]/30 bg-[var(--signal)]/5 p-4">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 className="h-5 w-5 text-[var(--signal)]" />
            <span className="font-medium text-[var(--text-primary)]">Live Trading Connected</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-3">
              <div className="text-xs text-[var(--text-muted)] mb-0.5">Wallet</div>
              <div className="text-sm font-mono text-[var(--text-primary)]">
                {hlStatus.wallet_address ? truncateAddress(hlStatus.wallet_address) : '...'}
              </div>
            </div>
            <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-3">
              <div className="text-xs text-[var(--text-muted)] mb-0.5">Account Value</div>
              <div className="text-sm font-mono font-bold text-[var(--accent)]">
                {hlStatus.account_value !== null ? `$${hlStatus.account_value.toFixed(2)}` : '...'}
              </div>
            </div>
            <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-3">
              <div className="text-xs text-[var(--text-muted)] mb-0.5">Available</div>
              <div className="text-sm font-mono text-[var(--text-primary)]">
                {hlStatus.available_balance !== null ? `$${hlStatus.available_balance.toFixed(2)}` : '...'}
              </div>
            </div>
            <div className="rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] p-3">
              <div className="text-xs text-[var(--text-muted)] mb-0.5">Positions</div>
              <div className="text-sm font-mono text-[var(--text-primary)]">
                {hlStatus.positions_count ?? '...'}
              </div>
            </div>
          </div>
        </div>

        {/* Deposit & Withdraw (requires wallet) */}
        {isConnected && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Deposit */}
            <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowDownToLine className="h-4 w-4 text-[var(--accent)]" />
                <span className="text-sm font-medium text-[var(--text-primary)]">Deposit</span>
              </div>
              <div className="flex items-center gap-1 text-xs text-[var(--text-muted)] mb-2">
                <Wallet className="h-3 w-3" />
                <span>{formattedUsdcBalance} USDC (Arbitrum)</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="5"
                  step="1"
                  placeholder="Min $5"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="flex-1 px-2 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
                />
                <button
                  onClick={handleDeposit}
                  disabled={!isValidDeposit || isDepositPending || isDepositConfirming}
                  className="px-3 py-1.5 rounded-lg font-medium text-xs transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDepositPending ? 'Confirm...' : isDepositConfirming ? 'Sending...' : 'Deposit'}
                </button>
              </div>
              {isDepositConfirmed && (
                <p className="text-xs text-[var(--profit-color)] mt-1">Sent! Updates in ~30s.</p>
              )}
            </div>

            {/* Withdraw */}
            <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowUpFromLine className="h-4 w-4 text-[var(--accent)]" />
                <span className="text-sm font-medium text-[var(--text-primary)]">Withdraw</span>
              </div>
              <div className="flex items-center gap-1 text-xs text-[var(--text-muted)] mb-2">
                <Wallet className="h-3 w-3" />
                <span>${hlStatus.available_balance?.toFixed(2) ?? '...'} available</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  placeholder="Amount"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  className="flex-1 px-2 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
                />
                <button
                  onClick={handleWithdraw}
                  disabled={!withdrawAmount || parseFloat(withdrawAmount) <= 0 || withdrawLoading}
                  className="px-3 py-1.5 rounded-lg font-medium text-xs transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {withdrawLoading ? 'Signing...' : 'Withdraw'}
                </button>
              </div>
              {withdrawResult && (
                <p className={`text-xs mt-1 ${withdrawResult.status === 'success' ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}`}>
                  {withdrawResult.message}
                </p>
              )}
            </div>
          </div>
        )}

        {!isConnected && (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
            <p className="text-sm text-[var(--text-secondary)] mb-3">
              Connect your wallet to deposit or withdraw USDC.
            </p>
            <ConnectButton />
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handleTestTrade}
            disabled={testTradeLoading}
            className="flex-1 flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50"
          >
            {testTradeLoading ? (
              <><Loader2 className="h-3 w-3 animate-spin" /> Testing...</>
            ) : (
              <><Zap className="h-3 w-3" /> Test Trade</>
            )}
          </button>

          <button
            onClick={handleDisconnect}
            disabled={disconnecting}
            className="flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--loss-color)] hover:border-[var(--loss-color)] disabled:opacity-50"
          >
            {disconnecting ? <Loader2 className="h-3 w-3 animate-spin" /> : <X className="h-3 w-3" />}
            Disconnect
          </button>

          <button
            onClick={fetchStatus}
            className="flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]"
          >
            Refresh
          </button>
        </div>

        {/* Test Trade Result */}
        {testTradeResult && (
          <div className={`rounded-lg border p-3 text-sm ${
            testTradeResult.status === 'success'
              ? 'border-[var(--profit-color)] bg-[var(--profit-color)]/10'
              : 'border-[var(--loss-color)] bg-[var(--loss-color)]/10'
          }`}>
            {testTradeResult.status === 'success' ? (
              <div>
                <span className="font-medium text-[var(--profit-color)]">Test trade successful</span>
                <span className="text-[var(--text-secondary)] ml-2">
                  Entry: ${testTradeResult.entry_price?.toFixed(2)}
                </span>
              </div>
            ) : (
              <div>
                <span className="font-medium text-[var(--loss-color)]">Test trade failed</span>
                <span className="text-[var(--text-secondary)] ml-2">{testTradeResult.error}</span>
              </div>
            )}
          </div>
        )}

        {statusError && (
          <div className="rounded-lg border border-[var(--loss-color)] bg-[var(--loss-color)]/10 p-3">
            <div className="text-sm text-[var(--loss-color)]">{statusError}</div>
          </div>
        )}

        <p className="text-xs text-center text-[var(--text-muted)]">
          Powered by Hyperliquid
        </p>
      </div>
    )
  }

  // Not connected — Setup flow
  return (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-secondary)]">
        Trade real perpetual futures with your AI bots. Powered by Hyperliquid.
      </p>

      {/* Step 1: Connect Wallet */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center">
            <span className="text-xs font-bold text-[var(--accent)]">1</span>
          </div>
          <span className="text-sm font-medium text-[var(--text-primary)]">Connect Wallet</span>
        </div>

        <p className="text-xs text-[var(--text-secondary)] mb-3">
          Connect your wallet on Arbitrum. You need USDC on Hyperliquid to trade.
        </p>

        <div className="flex items-center gap-3">
          <ConnectButton />
          {isConnected && (
            <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]">
              <Wallet className="h-3 w-3 text-[var(--text-muted)]" />
              <span className="text-xs font-mono text-[var(--text-secondary)]">
                {formattedUsdcBalance} USDC
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Step 2: Deposit (optional, only shown when wallet connected) */}
      {isConnected && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-6 h-6 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center">
              <ArrowDownToLine className="h-3 w-3 text-[var(--accent)]" />
            </div>
            <span className="text-sm font-medium text-[var(--text-primary)]">Deposit USDC</span>
            <span className="text-xs text-[var(--text-muted)] px-1.5 py-0.5 rounded bg-[var(--bg-primary)] border border-[var(--border)]">Optional</span>
          </div>

          <p className="text-xs text-[var(--text-secondary)] mb-3">
            Send USDC from Arbitrum to Hyperliquid. Minimum $5. Costs gas.
          </p>

          <div className="flex gap-2">
            <input
              type="number"
              min="5"
              step="1"
              placeholder="Amount (min $5)"
              value={depositAmount}
              onChange={(e) => setDepositAmount(e.target.value)}
              className="flex-1 px-2 py-1.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
            />
            <button
              onClick={handleDeposit}
              disabled={!isValidDeposit || isDepositPending || isDepositConfirming}
              className="px-4 py-1.5 rounded-lg font-medium text-sm transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isDepositPending ? 'Confirm...' : isDepositConfirming ? 'Sending...' : 'Deposit'}
            </button>
          </div>
          {depositAmountFloat > 0 && depositAmountFloat < 5 && (
            <p className="text-xs text-[var(--loss-color)] mt-1">Minimum deposit is $5</p>
          )}
          {isDepositConfirmed && (
            <p className="text-xs text-[var(--profit-color)] mt-1">Deposit sent! Balance updates in ~30s.</p>
          )}
        </div>
      )}

      {/* Step 3: Authorize */}
      <div className={`rounded-xl border bg-[var(--bg-secondary)] p-4 ${
        isConnected ? 'border-[var(--border)]' : 'border-[var(--border)]/50 opacity-50'
      }`}>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)] flex items-center justify-center">
            <span className="text-xs font-bold text-[var(--accent)]">2</span>
          </div>
          <span className="text-sm font-medium text-[var(--text-primary)]">Authorize ggbots to Trade</span>
        </div>

        <p className="text-xs text-[var(--text-secondary)] mb-1">
          Creates an API wallet that can trade but <strong>cannot withdraw</strong>. Protocol-enforced.
        </p>
        <p className="text-xs text-[var(--text-muted)] mb-3">
          Sign a message in MetaMask. No gas fees. No funds leave your wallet.
        </p>

        <button
          onClick={handleAuthorize}
          disabled={!isConnected || setupStep !== 'idle'}
          className="flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {setupStep !== 'idle' ? (
            <><Loader2 className="h-3 w-3 animate-spin" /> {setupStepLabels[setupStep]}</>
          ) : (
            <><Zap className="h-3 w-3" /> Authorize ggbots to Trade</>
          )}
        </button>

        {setupError && (
          <div className="mt-3 flex items-start gap-2 p-2 rounded-lg bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30">
            <AlertCircle className="h-3 w-3 text-[var(--loss-color)] mt-0.5 flex-shrink-0" />
            <span className="text-xs text-[var(--loss-color)]">{setupError}</span>
          </div>
        )}
      </div>

      {statusError && (
        <div className="rounded-lg border border-[var(--loss-color)] bg-[var(--loss-color)]/10 p-3">
          <div className="text-sm text-[var(--loss-color)]">{statusError}</div>
        </div>
      )}

      <p className="text-xs text-center text-[var(--text-muted)]">
        Powered by Hyperliquid &middot; USDC on Arbitrum &middot; Non-custodial
      </p>
    </div>
  )
}

/**
 * Wraps the modal content in Web3 providers (wagmi + RainbowKit).
 * This component is dynamically imported with SSR disabled.
 */
export default function LiveTradingModalContent({ onComplete }: LiveTradingModalContentProps) {
  return (
    <WagmiProvider config={hyperliquidWagmiConfig}>
      <QueryClientProvider client={web3QueryClient}>
        <RainbowKitProvider theme={ggbotsTheme}>
          <ModalContent onComplete={onComplete} />
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  )
}
