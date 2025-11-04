import Timeline from '@/components/Timeline'

export default async function TimelineV2Page({ params }: { params: Promise<{ config_id: string }> }) {
  const { config_id } = await params

  return (
    <div className="min-h-screen">
      {/* @ts-expect-error - Timeline is JSX, props are optional */}
      <Timeline configId={config_id} />
    </div>
  )
}
