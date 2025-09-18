'use client'

import { createClient } from '@/lib/supabase'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import OTPVerification from '@/components/OTPVerification'

export default function SignupPage() {
  const supabase = createClient()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showOTP, setShowOTP] = useState(false)
  const [otpEmail, setOtpEmail] = useState('')

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        router.push('/forge')
      }
    })

    return () => subscription.unsubscribe()
  }, [supabase.auth, router])

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // First create the user account
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      })

      if (signUpError) {
        setError(signUpError.message)
        return
      }

      // Then send OTP for email verification
      const { error: otpError } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: false
        }
      })

      if (otpError) {
        setError(otpError.message)
        return
      }

      setOtpEmail(email)
      setShowOTP(true)
    } catch {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleOtpSuccess = () => {
    router.push('/forge')
  }

  const handleOtpBack = () => {
    setShowOTP(false)
    setOtpEmail('')
  }

  if (showOTP) {
    return (
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
        <OTPVerification
          email={otpEmail}
          onSuccess={handleOtpSuccess}
          onBack={handleOtpBack}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-bone-200 mb-2">Join ggbots</h1>
          <p className="text-gray-400">Create your account and start building autonomous trading agents</p>
        </div>

        <div className="bg-charcoal-800 p-8 rounded-lg border border-gray-700">
          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-bone-300 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-charcoal-900 border border-charcoal-600 rounded-lg text-bone-200 focus:border-orange-400 focus:outline-none"
                placeholder="Enter your email"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-bone-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-charcoal-900 border border-charcoal-600 rounded-lg text-bone-200 focus:border-orange-400 focus:outline-none"
                placeholder="Create a password"
                minLength={6}
                required
              />
            </div>

            {error && (
              <div className="text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>
        </div>

        <div className="text-center mt-6">
          <p className="text-sm text-gray-400">
            Already have an account?{' '}
            <a href="/login" className="text-orange-400 hover:text-orange-300">
              Sign in
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}