'use client'

import { Coins } from 'lucide-react'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalTitle,
  ModalDescription,
} from '@/components/ui/modal'
import { CreditPicker } from '@/components/CreditPicker'

interface AddCreditsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentBalance?: number
}

export function AddCreditsModal({ open, onOpenChange, currentBalance }: AddCreditsModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} size="sm">
      <ModalHeader onClose={() => onOpenChange(false)}>
        <ModalTitle className="flex items-center gap-2">
          <Coins size={20} className="text-[var(--accent)]" />
          Add AI Credits
        </ModalTitle>
        <ModalDescription>
          AI credits pay for your bot&apos;s decisions. Never expires.
        </ModalDescription>
      </ModalHeader>

      <ModalBody>
        <CreditPicker currentBalance={currentBalance} />
      </ModalBody>
    </Modal>
  )
}
