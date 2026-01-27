'use client'

import React, { useState, useEffect } from 'react'
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

type TxStep = 'idle' | 'approving' | 'approved' | 'depositing' | 'recording' | 'complete' | 'error'

export function BetModal({ isOpen, onClose, bot, currentRank }: BetModalProps) {
  const [amount, setAmount] = useState('')
  const [txStep, setTxStep] = useState<TxStep>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [txHash, setTxHash] = useState<string | null>(null)

  const { address, isConnected } = useAccount()

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

  // Preview sUSX shares for deposit amount
  const parsedAmount = amount ? parseUnits(amount, 18) : BigInt(0)
  const { data: previewShares } = useReadContract({
    address: SCROLL_CONTRACTS.SUSX_VAULT,
    abi: SUSX_VAULT_ABI,
    functionName: 'previewDeposit',
    args: [parsedAmount],
    query: { enabled: parsedAmount > BigInt(0) }
  })

  // Write contracts
  const { writeContract: writeApprove, data: approveHash } = useWriteContract()
  const { writeContract: writeDeposit, data: depositHash } = useWriteContract()

  // Wait for transactions
  const { isSuccess: approveSuccess } = useWaitForTransactionReceipt({
    hash: approveHash,
  })
  const { isSuccess: depositSuccess } = useWaitForTransactionReceipt({
    hash: depositHash,
  })

  // Handle approve success
  useEffect(() => {
    if (approveSuccess && txStep === 'approving') {
      setTxStep('approved')
      refetchAllowance()
      // Auto-proceed to deposit
      handleDeposit()
    }
  }, [approveSuccess])

  // Handle deposit success
  useEffect(() => {
    if (depositSuccess && txStep === 'depositing') {
      setTxHash(depositHash || null)
      recordPledge()
    }
  }, [depositSuccess])

  const pnlPercent = ((bot.current_equity - bot.initial_balance) / bot.initial_balance) * 100
  const isPositive = pnlPercent >= 0
  const formattedBalance = usxBalance ? formatUnits(usxBalance as bigint, 18) : '0'
  const formattedShares = previewShares ? formatUnits(previewShares as bigint, 18) : '0'

  const needsApproval = currentAllowance !== undefined && parsedAmount > BigInt(0)
    && (currentAllowance as bigint) < parsedAmount

  const handleApprove = async () => {
    if (!address) return
    setTxStep('approving')
    setErrorMessage(null)
    try {
      writeApprove({
        address: SCROLL_CONTRACTS.USX_TOKEN,
        abi: USX_ABI,
        functionName: 'approve',
        args: [SCROLL_CONTRACTS.SUSX_VAULT, parsedAmount]
      })
    } catch (err) {
      setTxStep('error')
      setErrorMessage(err instanceof Error ? err.message : 'Approval failed')
    }
  }

  const handleDeposit = async () => {
    if (!address) return
    setTxStep('depositing')
    try {
      writeDeposit({
        address: SCROLL_CONTRACTS.SUSX_VAULT,
        abi: SUSX_VAULT_ABI,
        functionName: 'deposit',
        args: [parsedAmount, address]
      })
    } catch (err) {
      setTxStep('error')
      setErrorMessage(err instanceof Error ? err.message : 'Deposit failed')
    }
  }

  const recordPledge = async () => {
    if (!address || !depositHash) return
    setTxStep('recording')
    try {
      await apiClient.recordArenaPledge({
        wallet_address: address,
        config_id: bot.config_id,
        usx_amount: amount,
        susx_amount: formattedShares,
        tx_hash: depositHash
      })
      setTxStep('complete')
      refetchBalance()
    } catch (err) {
      // Even if recording fails, the on-chain tx succeeded
      console.error('Failed to record pledge:', err)
      setTxStep('complete')
    }
  }

  const handleSubmit = () => {
    if (needsApproval) {
      handleApprove()
    } else {
      handleDeposit()
    }
  }

  const handleClose = () => {
    if (txStep === 'approving' || txStep === 'depositing' || txStep === 'recording') {
      return // Don't close during transaction
    }
    setAmount('')
    setTxStep('idle')
    setErrorMessage(null)
    setTxHash(null)
    onClose()
  }

  const setMaxAmount = () => {
    if (usxBalance) {
      setAmount(formatUnits(usxBalance as bigint, 18))
    }
  }

  if (!isOpen) return null

  const isProcessing = txStep === 'approving' || txStep === 'depositing' || txStep === 'recording'
  const canSubmit = isConnected && parsedAmount > BigInt(0) && !isProcessing && txStep !== 'complete'

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

          {/* Amount Input (only show when connected) */}
          {isConnected && txStep !== 'complete' && (
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
              {parsedAmount > BigInt(0) && (
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
              <div className="flex items-start gap-2 p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                <AlertCircle className="h-4 w-4 text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                <p className="text-xs text-[var(--text-muted)]">
                  {SUSX_COOLDOWN_DAYS}-day cooldown to unstake after competition ends.
                  Either way, your USX earns yield.
                </p>
              </div>
            </>
          )}

          {/* Transaction Status */}
          {isProcessing && (
            <div className="flex flex-col items-center gap-3 p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
              <Loader2 className="h-8 w-8 text-[var(--accent)] animate-spin" />
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {txStep === 'approving' && 'Approving USX...'}
                {txStep === 'depositing' && 'Staking USX...'}
                {txStep === 'recording' && 'Recording your bet...'}
              </p>
              <p className="text-xs text-[var(--text-muted)]">
                Please confirm in your wallet
              </p>
            </div>
          )}

          {/* Success State */}
          {txStep === 'complete' && (
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
              {txHash && (
                <a
                  href={`https://scrollscan.com/tx/${txHash}`}
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
          {txStep === 'error' && errorMessage && (
            <div className="p-3 rounded-xl bg-[var(--loss-color)]/10 border border-[var(--loss-color)]/30">
              <p className="text-sm text-[var(--loss-color)]">{errorMessage}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-[var(--border)]">
          {txStep === 'complete' ? (
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
              {isConnected && needsApproval && 'Approve & Bet'}
              {isConnected && !needsApproval && parsedAmount > BigInt(0) && 'Place Bet'}
              {isConnected && parsedAmount === BigInt(0) && 'Enter Amount'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
