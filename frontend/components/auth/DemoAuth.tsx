'use client'

import { useState, useEffect } from 'react'
import { PasswordGate } from './PasswordGate'
import { EmailSignup } from './EmailSignup'
// import { api } from '@/lib/api/client' // Not needed in stable version

interface DemoAuthProps {
  children: React.ReactNode
}

export function DemoAuth({ children }: DemoAuthProps) {
  const [userState, setUserState] = useState<{
    userId: string | null
    email: string | null
    isLoading: boolean
  }>({
    userId: null,
    email: null,
    isLoading: true
  })

  useEffect(() => {
    // Check if user is already signed up
    const storedUserId = localStorage.getItem('demo_user_id')
    const storedEmail = localStorage.getItem('demo_user_email')
    
    if (storedUserId && storedEmail) {
      setUserState({
        userId: storedUserId,
        email: storedEmail,
        isLoading: false
      })
    } else {
      setUserState(prev => ({ ...prev, isLoading: false }))
    }
  }, [])

  const handleUserCreated = (userId: string, email: string) => {
    setUserState({
      userId,
      email,
      isLoading: false
    })
    // API client in old version doesn't need setUserId
    console.log('User logged in:', userId)
  }

  if (userState.isLoading) {
    return (
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center">
        <div className="text-bone-200">Loading...</div>
      </div>
    )
  }

  if (!userState.userId) {
    return (
      <PasswordGate>
        <EmailSignup onUserCreated={handleUserCreated} />
      </PasswordGate>
    )
  }

  return <>{children}</>
}

// Context for accessing user info throughout the app
import { createContext, useContext } from 'react'

interface DemoUserContextType {
  userId: string
  email: string
}

const DemoUserContext = createContext<DemoUserContextType | null>(null)

export function DemoUserProvider({ children, userId, email }: { 
  children: React.ReactNode
  userId: string
  email: string
}) {
  return (
    <DemoUserContext.Provider value={{ userId, email }}>
      {children}
    </DemoUserContext.Provider>
  )
}

export function useDemoUser() {
  const context = useContext(DemoUserContext)
  if (!context) {
    throw new Error('useDemoUser must be used within DemoUserProvider')
  }
  return context
}