'use client'

import { use } from 'react'
import TVTimeline from '@/components/tv-timeline'
import { ThemeProvider } from '@/lib/theme'

export default function ViewPage({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = use(params)

  return (
    <ThemeProvider>
      <div className="min-h-screen">
        <TVTimeline configId={config_id} />
      </div>
    </ThemeProvider>
  )
}
