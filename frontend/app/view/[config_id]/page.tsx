'use client'

import { use } from 'react'
import TVTimelineStandalone from '@/components/tv-timeline-standalone'

export default function ViewPage({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = use(params)

  return (
    <div className="min-h-screen">
      <TVTimelineStandalone configId={config_id} />
    </div>
  )
}
