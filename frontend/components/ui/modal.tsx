'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { useEffect, useCallback, useRef, type ReactNode } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// Size Variants (Responsive)
// Mobile: full-screen | Desktop: centered with max-width that scales up on larger screens
// ─────────────────────────────────────────────────────────────────────────────
const SIZES = {
  sm:   'sm:max-w-md  lg:max-w-lg',     // 448→512px (focused actions: upgrade, add credits)
  md:   'sm:max-w-lg  lg:max-w-xl',     // 512→576px (detail views: activity)
  lg:   'sm:max-w-xl  lg:max-w-2xl',    // 576→672px (forms: settings)
  xl:   'sm:max-w-2xl lg:max-w-3xl',    // 672→768px (wizards: bot creation)
  full: 'sm:max-w-4xl lg:max-w-6xl',    // 896→1152px (data tables: trade history)
} as const

type ModalSize = keyof typeof SIZES

// ─────────────────────────────────────────────────────────────────────────────
// Focus Trap Hook
// Keeps Tab/Shift+Tab cycling within the modal
// ─────────────────────────────────────────────────────────────────────────────
function useFocusTrap(modalRef: React.RefObject<HTMLDivElement | null>, isOpen: boolean) {
  useEffect(() => {
    if (!isOpen || !modalRef.current) return

    const modal = modalRef.current
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Tab') return

      const focusableElements = modal.querySelectorAll<HTMLElement>(focusableSelector)
      if (focusableElements.length === 0) return

      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]

      // Shift+Tab on first element → go to last
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault()
        lastElement.focus()
      }
      // Tab on last element → go to first
      else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault()
        firstElement.focus()
      }
    }

    modal.addEventListener('keydown', handleKeyDown)
    return () => modal.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, modalRef])
}

// ─────────────────────────────────────────────────────────────────────────────
// Modal Component
// ─────────────────────────────────────────────────────────────────────────────
interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  size?: ModalSize
  children: ReactNode
  preventClose?: boolean  // For forced modals (onboarding, confirmations)
}

export function Modal({
  open,
  onOpenChange,
  size = 'md',
  children,
  preventClose = false
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)
  const previousActiveElement = useRef<HTMLElement | null>(null)

  // Focus trap
  useFocusTrap(modalRef, open)

  // Escape key handler
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && !preventClose) {
      onOpenChange(false)
    }
  }, [onOpenChange, preventClose])

  // Focus management + body scroll lock
  useEffect(() => {
    if (open) {
      // Store the element that had focus before modal opened
      previousActiveElement.current = document.activeElement as HTMLElement

      // Lock body scroll
      document.body.style.overflow = 'hidden'
      document.addEventListener('keydown', handleKeyDown)

      // Focus the modal (or first focusable element) after animation
      setTimeout(() => {
        if (modalRef.current) {
          const firstFocusable = modalRef.current.querySelector<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          )
          if (firstFocusable) {
            firstFocusable.focus()
          } else {
            modalRef.current.focus()
          }
        }
      }, 50)
    }

    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', handleKeyDown)

      // Restore focus to previous element
      if (!open && previousActiveElement.current) {
        previousActiveElement.current.focus()
      }
    }
  }, [open, handleKeyDown])

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={() => !preventClose && onOpenChange(false)}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            aria-hidden="true"
          />

          {/* Modal */}
          <motion.div
            ref={modalRef}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            role="dialog"
            aria-modal="true"
            tabIndex={-1}
            className={`
              fixed inset-0 z-50 flex flex-col
              bg-[var(--bg-secondary)]
              sm:inset-auto sm:left-1/2 sm:top-1/2
              sm:-translate-x-1/2 sm:-translate-y-1/2
              sm:rounded-xl sm:border sm:border-[var(--border)]
              sm:max-h-[85vh] w-full ${SIZES[size]}
            `}
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ModalHeader
// Title area with optional close button
// ─────────────────────────────────────────────────────────────────────────────
interface ModalHeaderProps {
  children: ReactNode
  onClose?: () => void
  hideCloseButton?: boolean
}

export function ModalHeader({
  children,
  onClose,
  hideCloseButton = false
}: ModalHeaderProps) {
  return (
    <div className="flex items-start justify-between p-4 sm:p-6 border-b border-[var(--border)] flex-shrink-0">
      <div className="flex-1 pr-4">{children}</div>
      {!hideCloseButton && onClose && (
        <button
          onClick={onClose}
          className="p-2 -m-2 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          aria-label="Close modal"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ModalBody
// Scrollable content area
// ─────────────────────────────────────────────────────────────────────────────
interface ModalBodyProps {
  children: ReactNode
  className?: string
}

export function ModalBody({ children, className = '' }: ModalBodyProps) {
  return (
    <div className={`flex-1 overflow-y-auto p-4 sm:p-6 ${className}`}>
      {children}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ModalFooter
// Action buttons area (sticky at bottom on mobile)
// ─────────────────────────────────────────────────────────────────────────────
interface ModalFooterProps {
  children: ReactNode
}

export function ModalFooter({ children }: ModalFooterProps) {
  return (
    <div className="flex items-center justify-end gap-3 p-4 sm:p-6 border-t border-[var(--border)] flex-shrink-0 bg-[var(--bg-secondary)]">
      {children}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ModalTitle
// Semantic heading for the modal (use inside ModalHeader)
// ─────────────────────────────────────────────────────────────────────────────
interface ModalTitleProps {
  children: ReactNode
  id?: string
  className?: string
}

export function ModalTitle({ children, id, className = '' }: ModalTitleProps) {
  return (
    <h2
      id={id}
      className={`text-lg font-semibold text-[var(--text-primary)] ${className}`}
    >
      {children}
    </h2>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ModalDescription
// Secondary text below title (use inside ModalHeader)
// ─────────────────────────────────────────────────────────────────────────────
interface ModalDescriptionProps {
  children: ReactNode
}

export function ModalDescription({ children }: ModalDescriptionProps) {
  return (
    <p className="text-sm text-[var(--text-secondary)] mt-1">
      {children}
    </p>
  )
}
