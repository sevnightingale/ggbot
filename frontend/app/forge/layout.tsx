import React from 'react'
import { createServerClient } from '@/lib/supabase-server'
import { redirect } from 'next/navigation'
import { HelpWidget } from '@/components/HelpWidget'

export default async function ForgeLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Get session FIRST (before maintenance check)
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  // Redirect to login if not authenticated
  if (!session) {
    redirect('/login')
  }

  // Check for maintenance mode (after auth)
  const isMaintenanceMode = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === 'true'
  const whitelistUserId = process.env.NEXT_PUBLIC_WHITELIST_USER_ID
  const isWhitelisted = session.user.id === whitelistUserId

  // Show maintenance page if enabled and user is not whitelisted
  if (isMaintenanceMode && !isWhitelisted) {
    return (
      <div className="min-h-screen bg-charcoal-900 text-bone-200 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Under Maintenance</h1>
          <p className="text-gray-300 mb-8">
            We&apos;re upgrading ggbots with exciting new features. Back soon!
          </p>
          <div className="text-sm text-gray-500">
            Follow us for updates: <a href="https://twitter.com/ggbots_ai" className="text-blue-400 hover:text-blue-300">@ggbots_ai</a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {children}
      <HelpWidget />
    </>
  )
}