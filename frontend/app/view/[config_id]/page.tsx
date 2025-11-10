import TVTimeline from '@/components/tv-timeline'
import { ThemeProvider } from '@/lib/theme'

async function ViewPageContent({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = await params

  return (
    <div className="min-h-screen">
      <TVTimeline configId={config_id} />
    </div>
  )
}

export default function ViewPage({ params }: { params: Promise<{ config_id: string }> }) {
  return (
    <ThemeProvider>
      <ViewPageContent params={params} />
    </ThemeProvider>
  )
}
