import React from 'react'

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-charcoal-900">
      {children}
    </div>
  )
}