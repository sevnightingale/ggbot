'use client'

import { motion, AnimatePresence, PanInfo } from 'framer-motion'
import { X } from 'lucide-react'
import { ReactNode } from 'react'

interface BottomSheetProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
  title?: string
}

export default function BottomSheet({ isOpen, onClose, children, title }: BottomSheetProps) {
  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    // If dragged down more than 100px or velocity is high, close
    if (info.offset.y > 100 || info.velocity.y > 500) {
      onClose()
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />

          {/* Bottom Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            drag="y"
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={{ top: 0, bottom: 0.5 }}
            onDragEnd={handleDragEnd}
            className="fixed bottom-0 left-0 right-0 md:left-8 md:right-8 lg:left-16 lg:right-16 xl:left-24 xl:right-24 z-50 rounded-t-2xl shadow-2xl bg-[var(--bg-secondary)] border-t-2 border-[var(--accent)] flex flex-col"
            style={{ height: '80vh' }}
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing">
              <div className="w-10 h-1 rounded-full bg-[var(--accent)] opacity-50" />
            </div>

            {/* Header */}
            {title && (
              <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--accent)] border-opacity-20">
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  {title}
                </h3>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg transition-colors hover:bg-[var(--bg-tertiary)] text-[var(--accent)]"
                >
                  <X size={20} />
                </button>
              </div>
            )}

            {/* Content - Scrollable, fills remaining space with bottom padding */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden pb-8">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
