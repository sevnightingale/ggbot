'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Coins, Check } from 'lucide-react'

export default function CreditsSuccessPage() {
  const router = useRouter()
  const [countdown, setCountdown] = useState(3)

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          router.push('/forge')
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] px-4">
      <div className="max-w-md w-full text-center">
        {/* Celebration Icon */}
        <div className="relative inline-flex items-center justify-center mb-6">
          <div className="absolute inset-0 bg-[var(--profit-color)] opacity-20 blur-3xl rounded-full animate-pulse" />
          <div className="relative bg-gradient-to-br from-[var(--profit-color)] to-emerald-600 rounded-full p-6 shadow-2xl">
            <Coins className="w-12 h-12 text-white" />
          </div>
        </div>

        {/* Heading */}
        <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-3">
          Credits Added!
        </h1>
        <p className="text-[var(--text-muted)] mb-8">
          Your credits are now available to use
        </p>

        {/* Info Box */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-2xl p-6 mb-8 space-y-4">
          <InfoItem text="Credits applied to your account" />
          <InfoItem text="Auto-deducted from future usage" />
          <InfoItem text="Never expires" />
        </div>

        {/* Countdown */}
        <p className="text-sm text-[var(--text-muted)]">
          Redirecting to your dashboard in <span className="font-mono text-[var(--profit-color)]">{countdown}</span>...
        </p>
      </div>
    </div>
  )
}

function InfoItem({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--profit-color)] flex items-center justify-center">
        <Check className="w-3 h-3 text-white" strokeWidth={3} />
      </div>
      <span className="text-[var(--text-primary)] text-left">{text}</span>
    </div>
  )
}
