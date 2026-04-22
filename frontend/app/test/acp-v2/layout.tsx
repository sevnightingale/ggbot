import React from 'react'
import { createServerClient } from '@/lib/supabase-server'
import { redirect } from 'next/navigation'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'ACP v2 Test',
  robots: { index: false, follow: false },
}

export default async function AcpV2TestLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session) redirect('/login')

  const adminUserId = process.env.NEXT_PUBLIC_ADMIN_USER_ID
  if (!adminUserId || session.user.id !== adminUserId) redirect('/forge')

  return <div className="min-h-screen bg-charcoal-950">{children}</div>
}
