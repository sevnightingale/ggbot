'use client'

import { useState } from 'react'

interface PasswordGateProps {
  children: React.ReactNode
}

export function PasswordGate({ children }: PasswordGateProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (password === 'vibecodecamp') {
      setIsAuthenticated(true)
      setError('')
    } else {
      setError('Incorrect password. Please try again.')
      setPassword('')
    }
  }

  if (isAuthenticated) {
    return <>{children}</>
  }

  return (
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-bone-200 mb-2">ggBot Demo Access</h1>
          <p className="text-bone-400">Enter the demo password to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-bone-200 mb-2">
              Demo Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter demo password"
              className="w-full p-4 bg-charcoal-700 border border-bone-200/80 text-bone-200 placeholder-bone-400 focus:border-agents-extraction focus:outline-none"
              autoFocus
            />
            {error && (
              <p className="mt-2 text-sm text-red-400">{error}</p>
            )}
          </div>

          <button
            type="submit"
            className="w-full py-4 bg-agents-extraction hover:bg-agents-extraction/80 text-charcoal-900 font-medium transition-colors"
          >
            Access Demo
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-xs text-bone-400">
            This is a demo environment for hackathon presentation
          </p>
        </div>
      </div>
    </div>
  )
}