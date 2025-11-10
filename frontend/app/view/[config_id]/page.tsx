'use client'

import { use, useState, useEffect } from 'react'
import TVTimeline from '@/components/tv-timeline'
import { ThemeProvider } from '@/lib/theme'

export default function ViewPage({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = use(params)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Prevent hydration mismatch by only rendering TVTimeline on client
  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#0B0B0C] flex items-center justify-center">
        <div className="text-[#EDEBE7]">Loading...</div>
      </div>
    )
  }

  return (
    <ThemeProvider>
      <div className="min-h-screen">
        <TVTimeline configId={config_id} />
      </div>
    </ThemeProvider>
  )
}
