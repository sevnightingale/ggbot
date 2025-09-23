import React from 'react'
import { createServerClient } from '@/lib/supabase-server'
import { redirect } from 'next/navigation'
import { HelpWidget } from '@/components/HelpWidget'

export default async function ForgeLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Check for maintenance mode
  const isMaintenanceMode = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === 'true'

  if (isMaintenanceMode) {
    return (
      <div className="min-h-screen bg-charcoal-900 text-bone-200 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Under Maintenance</h1>
          <p className="text-gray-300 mb-8">
            We&apos;re currently performing scheduled maintenance. Please check back soon.
          </p>
          <div className="text-sm text-gray-500">
            Follow us for updates: <a href="https://twitter.com/ggbots_ai" className="text-blue-400">@ggbots_ai</a>
          </div>
        </div>
      </div>
    )
  }

  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  // Redirect to login if not authenticated
  if (!session) {
    redirect('/login')
  }

  return (
    <>
      {children}
      <HelpWidget />
    </>
  )
}