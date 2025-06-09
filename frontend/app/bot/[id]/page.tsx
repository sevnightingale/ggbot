import { BotDashboardClient } from './BotDashboardClient'

interface BotDetailPageProps {
  params: Promise<{ id: string }>
}

export default async function BotDetailPage({ params }: BotDetailPageProps) {
  const resolvedParams = await params
  
  return <BotDashboardClient botId={resolvedParams.id} />
}