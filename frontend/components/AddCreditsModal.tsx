'use client'

import React from 'react'
import { Coins } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { CreditPicker } from '@/components/CreditPicker'

interface AddCreditsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentBalance?: number
}

export function AddCreditsModal({ open, onOpenChange, currentBalance }: AddCreditsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm p-0 gap-0 overflow-hidden">
        {/* Header */}
        <div className="p-6 pb-4">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold flex items-center gap-2">
              <Coins size={20} className="text-[var(--accent)]" />
              Add Credits
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            Buy credits to prepay for usage. Never expires.
          </p>
        </div>

        {/* Credit Picker */}
        <div className="px-6 pb-6">
          <CreditPicker currentBalance={currentBalance} />
        </div>
      </DialogContent>
    </Dialog>
  )
}
