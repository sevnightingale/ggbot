import ActivityTimelineViewer from '@/components/ActivityTimelineViewer'

export default async function ViewPage({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = await params

  return (
    <div className="min-h-screen">
      <ActivityTimelineViewer configId={config_id} />
    </div>
  )
}
