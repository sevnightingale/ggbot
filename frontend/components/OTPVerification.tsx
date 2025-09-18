'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase'

interface OTPVerificationProps {
  email: string
  onSuccess: () => void
  onBack: () => void
}

export default function OTPVerification({ email, onSuccess, onBack }: OTPVerificationProps) {
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const supabase = createClient()

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const { error } = await supabase.auth.verifyOtp({
        email,
        token: otp,
        type: 'email'
      })

      if (error) {
        setError(error.message)
      } else {
        onSuccess()
      }
    } catch {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setResendLoading(true)
    setError('')

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: false
        }
      })

      if (error) {
        setError(error.message)
      }
    } catch {
      setError('Failed to resend code')
    } finally {
      setResendLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-bone-200 mb-2">Check your email</h2>
        <p className="text-gray-400">
          We sent a 6-digit code to <span className="text-bone-300">{email}</span>
        </p>
      </div>

      <form onSubmit={handleVerifyOtp} className="space-y-4">
        <div>
          <label htmlFor="otp" className="block text-sm font-medium text-bone-300 mb-2">
            Enter verification code
          </label>
          <input
            id="otp"
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="123456"
            className="w-full px-4 py-3 bg-charcoal-900 border border-charcoal-600 rounded-lg text-bone-200 text-center text-xl tracking-widest focus:border-orange-400 focus:outline-none"
            maxLength={6}
            required
          />
        </div>

        {error && (
          <div className="text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || otp.length !== 6}
          className="w-full px-4 py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {loading ? 'Verifying...' : 'Verify Code'}
        </button>

        <div className="text-center space-y-2">
          <button
            type="button"
            onClick={handleResendOtp}
            disabled={resendLoading}
            className="text-orange-400 hover:text-orange-300 text-sm disabled:text-gray-500"
          >
            {resendLoading ? 'Sending...' : 'Resend code'}
          </button>

          <button
            type="button"
            onClick={onBack}
            className="block mx-auto text-gray-400 hover:text-gray-300 text-sm"
          >
            ← Back to email entry
          </button>
        </div>
      </form>
    </div>
  )
}