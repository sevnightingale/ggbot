import React from 'react'
import Link from 'next/link'
import { Settings, Key, User, Bell } from 'lucide-react'

interface SettingsLayoutProps {
  children: React.ReactNode
}

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  const navigation = [
    {
      name: 'API Keys',
      href: '/settings/api-keys',
      icon: Key,
      description: 'Manage your personal AI provider API keys'
    },
    {
      name: 'Profile',
      href: '/settings/profile',
      icon: User,
      description: 'Account settings and preferences'
    },
    {
      name: 'Notifications',
      href: '/settings/notifications',
      icon: Bell,
      description: 'Configure alerts and notifications'
    }
  ]

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:w-64 flex-shrink-0">
            <div className="bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] p-4">
              <div className="flex items-center gap-2 mb-6">
                <Settings className="h-5 w-5 text-[var(--text-primary)]" />
                <h2 className="font-semibold text-[var(--text-primary)]">Settings</h2>
              </div>

              <nav className="space-y-2">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors group"
                  >
                    <item.icon className="h-4 w-4 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-[var(--text-primary)] text-sm">
                        {item.name}
                      </div>
                      <div className="text-xs text-[var(--text-muted)] mt-1">
                        {item.description}
                      </div>
                    </div>
                  </Link>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}