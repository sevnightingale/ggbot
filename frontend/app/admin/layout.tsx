import React from 'react'
import { createServerClient } from '@/lib/supabase-server'
import { redirect } from 'next/navigation'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Admin',
  robots: {
    index: false,
    follow: false,
  },
}

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  // Redirect to login if not authenticated
  if (!session) {
    redirect('/login')
  }

  // Admin user ID check
  const adminUserId = process.env.NEXT_PUBLIC_ADMIN_USER_ID
  if (!adminUserId || session.user.id !== adminUserId) {
    // Not admin - redirect to main app
    redirect('/forge')
  }

  return (
    <div className="min-h-screen bg-charcoal-950">
      {children}
    </div>
  )
}
