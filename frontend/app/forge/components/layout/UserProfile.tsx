'use client'

import React, { useState, useEffect } from 'react'
import { User, LogOut } from 'lucide-react'
import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

interface UserProfileProps {
  className?: string
}

interface UserData {
  id: string
  email?: string
  user_metadata?: {
    name?: string
    full_name?: string
    avatar_url?: string
  }
}

export function UserProfile({}: UserProfileProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [userData, setUserData] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()

  // Fetch user data
  useEffect(() => {
    const getUserData = async () => {
      try {
        const { data: { user }, error } = await supabase.auth.getUser()

        if (error) {
          console.error('Error fetching user:', error)
          return
        }

        if (user) {
          setUserData({
            id: user.id,
            email: user.email,
            user_metadata: user.user_metadata
          })
        }
      } catch (error) {
        console.error('Error in getUserData:', error)
      } finally {
        setLoading(false)
      }
    }

    getUserData()
  }, [supabase.auth])

  // Logout handler
  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/login')
    } catch (error) {
      console.error('Error logging out:', error)
    }
  }

  // Get display name from user metadata
  const getDisplayName = () => {
    if (!userData) return 'User'

    // Try full_name first (common for Google OAuth), then name, then fallback to 'User'
    return userData.user_metadata?.full_name ||
           userData.user_metadata?.name ||
           'User'
  }

  // Get display email
  const getDisplayEmail = () => {
    if (loading) return 'Loading...'
    return userData?.email || 'No email'
  }

  // Get avatar URL if available
  const getAvatarUrl = () => {
    return userData?.user_metadata?.avatar_url
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors overflow-hidden"
        title="User profile and settings"
      >
        {getAvatarUrl() ? (
          <Image
            src={getAvatarUrl()!}
            alt={getDisplayName()}
            width={32}
            height={32}
            className="h-full w-full object-cover"
          />
        ) : (
          <User className="h-4 w-4 text-[var(--text-primary)]" />
        )}
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-2 shadow-lg">
            <div className="border-b border-[var(--border)] px-3 py-2 mb-2">
              <div className="text-sm font-medium text-[var(--text-primary)]">{getDisplayName()}</div>
              <div className="text-xs text-[var(--text-muted)] truncate" title={getDisplayEmail()}>
                {getDisplayEmail()}
              </div>
            </div>

            <div className="space-y-1">
              <MenuButton icon={LogOut} label="Log out" onClick={handleLogout} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

interface MenuButtonProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  onClick?: () => void
}

function MenuButton({ icon: Icon, label, onClick }: MenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  )
}