'use client'

import dynamic from 'next/dynamic'
import { Loader2 } from 'lucide-react'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalTitle,
} from '@/components/ui/modal'

interface LiveTradingSetupModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onComplete?: () => void
}

/**
 * Inner content loaded dynamically (SSR disabled).
 * Contains the full Web3 flow: wagmi + RainbowKit + HyperliquidContent.
 */
const LiveTradingModalContent = dynamic(
  () => import('@/components/hyperliquid/LiveTradingModalContent'),
  {
    ssr: false,
    loading: () => (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
        <span className="text-sm text-[var(--text-muted)]">Loading wallet tools...</span>
      </div>
    ),
  }
)

export function LiveTradingSetupModal({ open, onOpenChange, onComplete }: LiveTradingSetupModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} size="lg">
      <ModalHeader onClose={() => onOpenChange(false)}>
        <ModalTitle>Live Trading Setup</ModalTitle>
      </ModalHeader>
      <ModalBody>
        {open && (
          <LiveTradingModalContent
            onComplete={() => {
              onComplete?.()
            }}
          />
        )}
      </ModalBody>
    </Modal>
  )
}
