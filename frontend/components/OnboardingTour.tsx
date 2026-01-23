'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, ChevronRight, ChevronLeft } from 'lucide-react'

interface TourStep {
  target: string  // CSS selector
  title: string
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  onEnter?: () => void  // Called when entering this step (for navigation, etc.)
}

interface OnboardingTourProps {
  steps: TourStep[]
  storageKey: string  // localStorage key to track completion
  onComplete?: () => void
  active?: boolean  // External control
}

export function OnboardingTour({ steps, storageKey, onComplete, active = true }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isVisible, setIsVisible] = useState(false)
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null)

  // Check if tour was already completed
  useEffect(() => {
    if (!active) return undefined
    const completed = localStorage.getItem(storageKey)
    if (!completed) {
      // Small delay to let page render
      const timer = setTimeout(() => setIsVisible(true), 500)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [storageKey, active])

  // Update target element position and call onEnter callback
  useEffect(() => {
    if (!isVisible || currentStep >= steps.length) return

    const step = steps[currentStep]

    // Call onEnter callback (e.g., for navigation)
    step.onEnter?.()

    const updateTargetRect = () => {
      const target = document.querySelector(step.target)
      if (target) {
        setTargetRect(target.getBoundingClientRect())
        target.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }

    // Delay to allow React to re-render after onEnter (e.g., tab switch)
    const initialTimer = setTimeout(updateTargetRect, 100)

    // Also update on scroll/resize
    window.addEventListener('scroll', updateTargetRect, true)
    window.addEventListener('resize', updateTargetRect)

    return () => {
      clearTimeout(initialTimer)
      window.removeEventListener('scroll', updateTargetRect, true)
      window.removeEventListener('resize', updateTargetRect)
    }
  }, [currentStep, isVisible, steps])

  const handleComplete = useCallback(() => {
    localStorage.setItem(storageKey, 'true')
    setIsVisible(false)
    onComplete?.()
  }, [storageKey, onComplete])

  const handleNext = useCallback(() => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      handleComplete()
    }
  }, [currentStep, steps.length, handleComplete])

  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }, [currentStep])

  const handleSkip = useCallback(() => {
    handleComplete()
  }, [handleComplete])

  // Handle keyboard navigation
  useEffect(() => {
    if (!isVisible) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleSkip()
      } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
        handleNext()
      } else if (e.key === 'ArrowLeft') {
        handlePrev()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isVisible, handleNext, handlePrev, handleSkip])

  if (!isVisible || !targetRect) return null

  const step = steps[currentStep]

  // Calculate tooltip position (prefer below target, but adjust if near bottom)
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800
  const tooltipTop = targetRect.bottom + 12 > viewportHeight - 200
    ? targetRect.top - 12 - 180 // Position above if not enough space below
    : targetRect.bottom + 12

  return (
    <div className="fixed inset-0 z-[100]" aria-modal="true" role="dialog">
      {/* Overlay with cutout - click to skip */}
      <div
        className="absolute inset-0 bg-black/60 transition-opacity"
        onClick={handleSkip}
        aria-label="Skip tour"
      />

      {/* Spotlight on target */}
      <div
        className="absolute border-2 border-[var(--accent)] rounded-lg pointer-events-none transition-all duration-300"
        style={{
          top: targetRect.top - 4,
          left: targetRect.left - 4,
          width: targetRect.width + 8,
          height: targetRect.height + 8,
          boxShadow: '0 0 0 9999px rgba(0,0,0,0.6)'
        }}
      />

      {/* Tooltip */}
      <div
        className="absolute bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl p-4 shadow-xl max-w-sm transition-all duration-300"
        style={{
          top: tooltipTop,
          left: Math.max(16, Math.min(targetRect.left, typeof window !== 'undefined' ? window.innerWidth - 360 : 400)),
        }}
      >
        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-2 right-2 p-1.5 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors"
          aria-label="Close tour"
        >
          <X className="w-4 h-4 text-[var(--text-muted)]" />
        </button>

        <h3 className="font-semibold text-[var(--text-primary)] mb-2 pr-6">
          {step.title}
        </h3>
        <p className="text-sm text-[var(--text-secondary)] mb-4 leading-relaxed">
          {step.content}
        </p>

        {/* Progress dots and navigation */}
        <div className="flex items-center justify-between">
          <div className="flex gap-1.5">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === currentStep ? 'bg-[var(--accent)]' : 'bg-[var(--border)]'
                }`}
              />
            ))}
          </div>

          <div className="flex gap-2">
            {currentStep > 0 && (
              <button
                onClick={handlePrev}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-4 py-1.5 text-sm bg-[var(--accent)] text-[var(--bg-primary)] rounded-lg font-medium hover:brightness-110 transition-all"
            >
              {currentStep === steps.length - 1 ? 'Done' : 'Next'}
              {currentStep < steps.length - 1 && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
