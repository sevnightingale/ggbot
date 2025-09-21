'use client'

import { redirect } from 'next/navigation'

export default function SettingsPage() {
  // Redirect to API Keys as default settings page
  redirect('/settings/api-keys')
}