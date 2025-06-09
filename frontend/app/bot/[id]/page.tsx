import { BotDashboardClient } from './BotDashboardClient'

export default async function BotDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const resolvedParams = await params
  
  return <BotDashboardClient botId={resolvedParams.id} />
}