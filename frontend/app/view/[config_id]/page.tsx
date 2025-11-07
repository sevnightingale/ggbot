import TVTimeline from '@/components/tv-timeline'

export default async function ViewPage({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = await params

  return (
    <div className="min-h-screen">
      <TVTimeline configId={config_id} />
    </div>
  )
}
