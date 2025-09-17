'use client'

import { useState } from 'react'

interface EmailSignupProps {
  onUserCreated: (userId: string, email: string) => void
}

export function EmailSignup({ onUserCreated }: EmailSignupProps) {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      // Call backend API to create/get user
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/users/demo-signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      })

      if (!response.ok) {
        throw new Error('Failed to create user account')
      }

      const data = await response.json()
      
      // Store user info and call parent callback
      localStorage.setItem('demo_user_id', data.user_id)
      localStorage.setItem('demo_user_email', email.trim().toLowerCase())
      
      onUserCreated(data.user_id, email.trim().toLowerCase())
    } catch (error) {
      console.error('Error creating user:', error)
      setError('Failed to create account. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-bone-200 mb-2">Welcome to ggBot</h1>
          <p className="text-bone-400">Enter your email to start trading with AI</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-bone-200 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              className="w-full p-4 bg-charcoal-700 border border-bone-200/80 text-bone-200 placeholder-bone-400 focus:border-agents-decision focus:outline-none"
              autoFocus
              disabled={isLoading}
            />
            {error && (
              <p className="mt-2 text-sm text-red-400">{error}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-4 font-medium transition-colors ${
              isLoading
                ? 'bg-agents-decision/50 text-charcoal-900/70 cursor-not-allowed'
                : 'bg-agents-decision hover:bg-agents-decision/80 text-charcoal-900'
            }`}
          >
            {isLoading ? 'Creating Account...' : 'Start Trading'}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-xs text-bone-400">
            Your email will be used to generate a unique trading account.<br/>
            No password required for this demo.
          </p>
        </div>
      </div>
    </div>
  )
}