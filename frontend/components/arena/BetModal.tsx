'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { X, Loader2, Check, AlertCircle, Wallet, TrendingUp } from 'lucide-react'
import { ConnectButton } from '@rainbow-me/rainbowkit'
import { useAccount, useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi'
import { parseUnits, formatUnits } from 'viem'
import { SCROLL_CONTRACTS, USX_ABI, SUSX_VAULT_ABI, SUSX_COOLDOWN_DAYS } from '@/lib/contracts'
import { apiClient } from '@/lib/api'

interface BetModalProps {
  isOpen: boolean
  onClose: () => void
  bot: {
    config_id: string
    config_name: string
    current_equity: number
    initial_balance: number
    profile_image_url?: string | null
  }
  currentRank: number
}

type Step = 'idle' | 'approving' | 'waitApproval' | 'depositing' | 'waitDeposit' | 'recording' | 'complete' | 'error'

export function BetModal({ isOpen, onClose, bot, currentRank }: BetModalProps) {
  const [amount, setAmount] = useState('')
  const [step, setStep] = useState<Step>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Ref to track step without stale closures in effects
  const stepRef = useRef<Step>('idle')
  const updateStep = useCallback((newStep: Step) => {
    stepRef.current = newStep
    setStep(newStep)
  }, [])

  const { address, isConnected } = useAccount()

  // Read USX decimals dynamically (don't assume 18)
  const { data: usxDecimals } = useReadContract({
    address: SCROLL_CONTRACTS.USX_TOKEN,
    abi: USX_ABI,
    functionName: 'decimals',
  })
  const decimals = (usxDecimals as number) ?? 18

  // Read USX balance
  const { data: usxBalance, refetch: refetchBalance } = useReadContract({
    address: SCROLL_CONTRACTS.USX_TOKEN,
    abi: USX_ABI,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: { enabled: !!address }
  })

  // Read current allowance
  const { data: currentAllowance, refetch: refetchAllowance } = useReadContract({
    address: SCROLL_CONTRACTS.USX_TOKEN,
    abi: USX_ABI,
    functionName: 'allowance',
    args: address ? [address, SCROLL_CONTRACTS.SUSX_VAULT] : undefined,
    query: { enabled: !!address }
  })

  // Parse amount with correct decimals
  const parsedAmount = amount && parseFloat(amount) > 0
    ? parseUnits(amount, decimals)
    : BigInt(0)

  // Keep a ref so effects don't capture stale values
  const parsedAmountRef = useRef(parsedAmount)
  const addressRef = useRef(address)
  useEffect(() => { parsedAmountRef.current = parsedAmount }, [parsedAmount])
  useEffect(() => { addressRef.current = address }, [address])

  // Preview sUSX shares for deposit amount
  const { data: previewShares } = useReadContract({
    address: SCROLL_CONTRACTS.SUSX_VAULT,
    abi: SUSX_VAULT_ABI,
    functionName: 'previewDeposit',
    args: [parsedAmount],
    query: { enabled: parsedAmount > BigInt(0) }
  })

  // Write contract hooks (separate for approve and deposit)
  const {
    writeContract: doApprove,
    data: approveHash,
    error: approveError,
    isPending: approvePending,
    reset: resetApprove
  } = useWriteContract()

  const {
    writeContract: doDeposit,
    data: depositHash,
    error: depositError,
    isPending: depositPending,
    reset: resetDeposit
  } = useWriteContract()

  // Wait for transaction confirmations
  const {
    isSuccess: approveConfirmed,
    error: approveTxError
  } = useWaitForTransactionReceipt({ hash: approveHash })

  const {
    isSuccess: depositConfirmed,
    error: depositTxError
  } = useWaitForTransactionReceipt({ hash: depositHash })

  // === Step transitions via effects ===

  // Approve submitted to chain → waiting for confirmation
  useEffect(() => {
    if (approveHash && stepRef.current === 'approving') {
      updateStep('waitApproval')
    }
  }, [approveHash, updateStep])

  // Approve confirmed → start deposit
  useEffect(() => {
    if (approveConfirmed && stepRef.current === 'waitApproval') {
      updateStep('depositing')
      refetchAllowance()
      doDeposit({
        address: SCROLL_CONTRACTS.SUSX_VAULT,
        abi: SUSX_VAULT_ABI,
        functionName: 'deposit',
        args: [parsedAmountRef.current, addressRef.current!]
      })
    }
  }, [approveConfirmed, updateStep, refetchAllowance, doDeposit])

  // Deposit submitted to chain → waiting for confirmation
  useEffect(() => {
    if (depositHash && stepRef.current === 'depositing') {
      updateStep('waitDeposit')
    }
  }, [depositHash, updateStep])

  // Deposit confirmed → record pledge on backend
  useEffect(() => {
    if (depositConfirmed && stepRef.current === 'waitDeposit') {
      updateStep('recording')
      const formattedShares = previewShares
        ? formatUnits(previewShares as bigint, decimals)
        : undefined
      apiClient.recordArenaPledge({
        wallet_address: addressRef.current!,
        config_id: bot.config_id,
        usx_amount: amount,
        susx_amount: formattedShares,
        tx_hash: depositHash!
      }).then(() => {
        updateStep('complete')
        refetchBalance()
      }).catch((err) => {
        // On-chain tx succeeded, just log backend failure
        console.error('Failed to record pledge on backend:', err)
        updateStep('complete')
        refetchBalance()
      })
    }
  }, [depositConfirmed, updateStep, depositHash, bot.config_id, amount, previewShares, decimals, refetchBalance])

  // === Error handling ===

  // Wallet rejected approve
  useEffect(() => {
    if (approveError && (stepRef.current === 'approving' || stepRef.current === 'idle')) {
      updateStep('error')
      setErrorMessage(approveError.message?.includes('User rejected')
        ? 'Transaction rejected in wallet'
        : approveError.message || 'Approval failed')
    }
  }, [approveError, updateStep])

  // Approve tx failed on-chain
  useEffect(() => {
    if (approveTxError && stepRef.current === 'waitApproval') {
      updateStep('error')
      setErrorMessage('Approval transaction failed on-chain')
    }
  }, [approveTxError, updateStep])

  // Wallet rejected deposit
  useEffect(() => {
    if (depositError && stepRef.current === 'depositing') {
      updateStep('error')
      setErrorMessage(depositError.message?.includes('User rejected')
        ? 'Transaction rejected in wallet'
        : depositError.message || 'Deposit failed')
    }
  }, [depositError, updateStep])

  // Deposit tx failed on-chain
  useEffect(() => {
    if (depositTxError && stepRef.current === 'waitDeposit') {
      updateStep('error')
      setErrorMessage('Deposit transaction failed on-chain')
    }
  }, [depositTxError, updateStep])

  // === Derived values ===

  const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
  const isPositive = pnlPercent >= 0
  const formattedBalance = usxBalance ? formatUnits(usxBalance as bigint, decimals) : '0'
  const formattedShares = previewShares ? formatUnits(previewShares as bigint, decimals) : '0'

  const needsApproval = currentAllowance !== undefined
    && parsedAmount > BigInt(0)
    && (currentAllowance as bigint) < parsedAmount

  // === Actions ===

  const handleSubmit = useCallback(() => {
    setErrorMessage(null)
    if (needsApproval) {
      updateStep('approving')
      doApprove({
        address: SCROLL_CONTRACTS.USX_TOKEN,
        abi: USX_ABI,
        functionName: 'approve',
        args: [SCROLL_CONTRACTS.SUSX_VAULT, parsedAmountRef.current]
      })
    } else {
      updateStep('depositing')
      doDeposit({
        address: SCROLL_CONTRACTS.SUSX_VAULT,
        abi: SUSX_VAULT_ABI,
        functionName: 'deposit',
        args: [parsedAmountRef.current, addressRef.current!]
      })
    }
  }, [needsApproval, updateStep, doApprove, doDeposit])

  const handleRetry = useCallback(() => {
    resetApprove()
    resetDeposit()
    updateStep('idle')
    setErrorMessage(null)
  }, [resetApprove, resetDeposit, updateStep])

  const handleClose = useCallback(() => {
    // Block close during active transactions
    if (approvePending || depositPending) return
    if (stepRef.current === 'waitApproval' || stepRef.current === 'waitDeposit' || stepRef.current === 'recording') return

    setAmount('')
    updateStep('idle')
    setErrorMessage(null)
    resetApprove()
    resetDeposit()
    onClose()
  }, [approvePending, depositPending, updateStep, resetApprove, resetDeposit, onClose])

  const setMaxAmount = useCallback(() => {
    if (usxBalance) {
      setAmount(formatUnits(usxBalance as bigint, decimals))
    }
  }, [usxBalance, decimals])

  if (!isOpen) return null

  const isProcessing = step === 'approving' || step === 'waitApproval'
    || step === 'depositing' || step === 'waitDeposit' || step === 'recording'
  const canSubmit = isConnected && parsedAmount > BigInt(0) && !isProcessing && step !== 'complete'

  // Step display messages
  const stepMessage: Record<string, string> = {
    'approving': 'Confirm approval in your wallet...',
    'waitApproval': 'Waiting for approval confirmation...',
    'depositing': 'Confirm deposit in your wallet...',
    'waitDeposit': 'Waiting for deposit confirmation...',
    'recording': 'Recording your bet...',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--bg-primary)] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[var(--border)]">
          <div>
            <h2 className="text-lg font-display text-[var(--text-primary)]">
              Bet on {bot.config_name}
            </h2>
            <p className="text-sm text-[var(--text-muted)]">
              Pick the winner, share the $2,500 prize
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={isProcessing}
            className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-5">
          {/* Bot Info */}
          <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
            {bot.profile_image_url ? (
              <img
                src={bot.profile_image_url}
                alt={bot.config_name}
                className="w-12 h-12 rounded-full object-cover border-2 border-[var(--border)]"
              />
            ) : (
              <div className="w-12 h-12 rounded-full flex items-center justify-center bg-[var(--bg-tertiary)] border-2 border-[var(--border)]">
                <TrendingUp className="h-6 w-6 text-[var(--text-muted)]" />
              </div>
            )}
            <div className="flex-1">
              <div className="font-semibold text-[var(--text-primary)]">{bot.config_name}</div>
              <div className="text-sm text-[var(--text-muted)]">
                Rank #{currentRank} · <span className={isPositive ? 'text-[var(--profit-color)]' : 'text-[var(--loss-color)]'}>
                  {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          {/* Wallet Connection */}
          {!isConnected && (
            <div className="flex flex-col items-center gap-3 p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
              <Wallet className="h-8 w-8 text-[var(--text-muted)]" />
              <p className="text-sm text-[var(--text-muted)] text-center">
                Connect your wallet to place a bet
              </p>
              <ConnectButton />
            </div>
          )}

          {/* Amount Input (only show when connected and not complete) */}
          {isConnected && step !== 'complete' && (
            <>
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  Amount
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    disabled={isProcessing}
                    className="w-full px-4 py-3 pr-20 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-primary)] font-mono text-lg focus:outline-none focus:border-[var(--accent)] disabled:opacity-50"
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    <button
                      onClick={setMaxAmount}
                      disabled={isProcessing}
                      className="px-2 py-1 text-xs font-medium rounded bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 transition-colors disabled:opacity-50"
                    >
                      MAX
                    </button>
                    <span className="text-sm font-medium text-[var(--text-muted)]">USX</span>
                  </div>
                </div>
                <div className="mt-2 text-sm text-[var(--text-muted)]">
                  Balance: {parseFloat(formattedBalance).toFixed(2)} USX
                </div>
              </div>

              {/* Preview */}
              {parsedAmount > BigInt(0) && !isProcessing && (
                <div className="p-3 rounded-xl bg-[var(--accent)]/10 border border-[var(--accent)]/30">
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--text-secondary)]">You&apos;ll receive</span>
                    <span className="font-mono font-medium text-[var(--accent)]">
                      ~{parseFloat(formattedShares).toFixed(4)} sUSX
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-[var(--text-muted)]">
                    Earning yield while you wait for results
                  </div>
                </div>
              )}

              {/* Cooldown Warning */}
              {!isProcessing && (
                <div className="flex items-start gap-2 p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <AlertCircle className="h-4 w-4 text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-muted)]">
                    {SUSX_COOLDOWN_DAYS}-day cooldown to unstake after competition ends.
                    Either way, your USX earns yield.
                  </p>
                </div>
              )}
            </>
          )}

          {/* Transaction Progress */}
          {isProcessing && (
            <div className="flex flex-col items-center gap-3 p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
              <Loader2 className="h-8 w-8 text-[var(--accent)] animate-spin" />
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {stepMessage[step] || 'Processing...'}
              </p>
              {(step === 'waitApproval' || step === 'waitDeposit') && (
                <p className="text-xs text-[var(--text-muted)]">
                  Waiting for on-chain confirmation...
                </p>
              )}
              {(step === 'approving' || step === 'depositing') && (
                <p className="text-xs text-[var(--text-muted)]">
                  Check your wallet for the transaction
                </p>
              )}
            </div>
          )}

          {/* Success State */}
          {step === 'complete' && (
            <div className="flex flex-col items-center gap-3 p-4 rounded-xl bg-[var(--profit-color)]/10 border border-[var(--profit-color)]/30">
              <div className="w-12 h-12 rounded-full bg-[var(--profit-color)]/20 flex items-center justify-center">
                <Check className="h-6 w-6 text-[var(--profit-color)]" />
              </div>
              <div className="text-center">
                <p className="font-medium text-[var(--text-primary)]">
                  You&apos;re backing {bot.config_name}!
                </p>
                <p className="text-sm text-[var(--text-muted)] mt-1">
                  {amount} USX staked · Earning yield now
                </p>
              </div>
              {depositHash && (
                <a
                  href={`https://scrollscan.com/tx/${depositHash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[var(--accent)] hover:underline"
                >
                  View on Scrollscan →
                </a>
              )}
            </div>
          )}

          {/* Error State */}
          {step === 'error' && errorMessage && (
            <div className="p-3 rounded-xl bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30">
              <p className="text-sm text-[var(--loss-color)] mb-2">{errorMessage}</p>
              <button
                onClick={handleRetry}
                className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] underline"
              >
                Try again
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-[var(--border)]">
          {step === 'complete' ? (
            <button
              onClick={handleClose}
              className="w-full py-3 rounded-xl font-medium transition-colors bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)] border border-[var(--border)]"
            >
              Done
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="w-full py-3 rounded-xl font-medium transition-colors bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--bg-primary)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {!isConnected && 'Connect Wallet to Bet'}
              {isConnected && step === 'error' && 'Try Again'}
              {isConnected && step !== 'error' && needsApproval && parsedAmount > BigInt(0) && 'Approve & Bet'}
              {isConnected && step !== 'error' && !needsApproval && parsedAmount > BigInt(0) && 'Place Bet'}
              {isConnected && step !== 'error' && parsedAmount === BigInt(0) && 'Enter Amount'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
