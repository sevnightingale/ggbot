'use client'

import { motion, AnimatePresence, PanInfo } from 'framer-motion'
import { X } from 'lucide-react'
import { ReactNode } from 'react'

const VIBE = {
  obsidian: '#0B0C0E',
  carbon: '#1A1D23',
  ivory: '#EDEBE7',
  brass: '#C9A962',
  signal: '#00D9FF',
  ember: '#FF6B35',
  lilac: '#9D84B7',
}

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
            className="fixed inset-0 z-40"
            style={{ backgroundColor: 'rgba(11, 12, 14, 0.8)' }}
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
            className="fixed bottom-0 left-0 right-0 z-50 rounded-t-2xl shadow-2xl"
            style={{
              backgroundColor: VIBE.carbon,
              maxHeight: '80vh',
              borderTop: `2px solid ${VIBE.brass}`,
            }}
          >
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing">
              <div
                className="rounded-full"
                style={{
                  width: '40px',
                  height: '4px',
                  backgroundColor: VIBE.brass,
                  opacity: 0.5,
                }}
              />
            </div>

            {/* Header */}
            {title && (
              <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: VIBE.brass, opacity: 0.2 }}>
                <h3 className="text-lg font-semibold" style={{ color: VIBE.ivory }}>
                  {title}
                </h3>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg transition-colors hover:bg-opacity-10"
                  style={{ color: VIBE.brass }}
                >
                  <X size={20} />
                </button>
              </div>
            )}

            {/* Content - Scrollable */}
            <div className="overflow-y-auto overflow-x-hidden">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
