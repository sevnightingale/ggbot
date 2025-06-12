'use client'

import { useEffect } from 'react'
import { MainDashboard } from '@/components/MainDashboard'

export default function Home() {
  useEffect(() => {
    console.log('Home page: Component mounted')
    console.log('Home page: Environment variables:', {
      API_URL: process.env.NEXT_PUBLIC_API_URL,
      USER_ID: process.env.NEXT_PUBLIC_USER_ID
    })
  }, [])

  console.log('Home page: Rendering...')
  return <MainDashboard />
}