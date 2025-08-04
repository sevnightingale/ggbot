'use client'

import { useEffect } from 'react'
import { MainDashboard } from '@/components/MainDashboard'
import { DemoAuth } from '@/components/auth/DemoAuth'

export default function AppPage() {
  useEffect(() => {
    console.log('App page: Component mounted')
    console.log('App page: Environment variables:', {
      API_URL: process.env.NEXT_PUBLIC_API_URL,
      USER_ID: process.env.NEXT_PUBLIC_USER_ID
    })
  }, [])

  console.log('App page: Rendering demo-protected dashboard...')
  return (
    <DemoAuth>
      <MainDashboard />
    </DemoAuth>
  )
}