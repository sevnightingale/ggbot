import React from 'react'

// TODO: Add Supabase Auth imports when ready
// import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
// import { cookies } from 'next/headers'
// import { redirect } from 'next/navigation'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // TODO: Add Supabase authentication check
  // const supabase = createServerComponentClient({ cookies })
  // const { data: { session } } = await supabase.auth.getSession()
  
  // if (!session) {
  //   redirect('/login')
  // }

  return (
    <div className="min-h-screen bg-charcoal-900">
      {/* TODO: Add navigation header */}
      {/* <DashboardNav user={session.user} /> */}
      
      {children}
    </div>
  )
}