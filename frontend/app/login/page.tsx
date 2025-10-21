'use client'

import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { createClient } from '@/lib/supabase'
import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

function LoginForm() {
  const supabase = createClient()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Check for error messages from auth callback
  useEffect(() => {
    const error = searchParams?.get('error')
    if (error) {
      switch (error) {
        case 'oauth_error':
          setErrorMessage('OAuth authentication failed. Please try again.')
          break
        case 'auth_error':
          setErrorMessage('Authentication error occurred. Please try again.')
          break
        case 'no_session':
          setErrorMessage('Session could not be established. Please try again.')
          break
        case 'callback_error':
          setErrorMessage('Authentication callback failed. Please try again.')
          break
        default:
          setErrorMessage('Authentication failed. Please try again.')
      }
    }
  }, [searchParams])

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        router.push('/forge')
      }
    })

    return () => subscription.unsubscribe()
  }, [supabase.auth, router])

  return (
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-bone-200 mb-2">Welcome to ggbots</h1>
          <p className="text-gray-400">Sign in to access your AI trading forge</p>
        </div>

        <div className="bg-charcoal-800 p-8 rounded-lg border border-gray-700">
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-900/20 border border-red-500/50 rounded text-red-200 text-sm">
              {errorMessage}
            </div>
          )}

          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand: '#be6a47', // agent-trading orange to match your theme
                    brandAccent: '#a85a3f', // slightly darker agent-trading
                    brandButtonText: 'white',
                    defaultButtonBackground: '#1f1f23', // charcoal-800
                    defaultButtonBackgroundHover: '#2a2a30', // charcoal-700
                    defaultButtonBorder: '#36363d', // charcoal-600
                    defaultButtonText: '#e3e5e6', // bone-200
                    dividerBackground: '#36363d', // charcoal-600
                    inputBackground: '#161618', // charcoal-900
                    inputBorder: '#36363d', // charcoal-600
                    inputBorderHover: '#4b5563', // lighter on hover
                    inputBorderFocus: '#be6a47', // agent-trading orange
                    inputText: '#e3e5e6', // bone-200
                    inputLabelText: '#d6d8da', // bone-300
                    inputPlaceholder: '#9ca3af', // gray-400
                    messageText: '#e3e5e6', // bone-200
                    messageTextDanger: '#ef4444', // red-400 (your status color)
                    messageBackground: '#1f1f23', // charcoal-800
                    messageBackgroundDanger: '#2a1f1f', // dark red background
                    anchorTextColor: '#be6a47', // agent-trading orange
                    anchorTextHoverColor: '#a85a3f', // darker agent-trading
                  },
                  space: {
                    spaceSmall: '4px',
                    spaceMedium: '8px',
                    spaceLarge: '16px',
                    labelBottomMargin: '8px',
                    anchorBottomMargin: '4px',
                    emailInputSpacing: '4px',
                    socialAuthSpacing: '4px',
                    buttonPadding: '10px 15px',
                    inputPadding: '10px 15px',
                  },
                  fontSizes: {
                    baseBodySize: '13px',
                    baseInputSize: '14px',
                    baseLabelSize: '14px',
                    baseButtonSize: '14px',
                  },
                  fonts: {
                    bodyFontFamily: `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif`,
                    buttonFontFamily: `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif`,
                    inputFontFamily: `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif`,
                    labelFontFamily: `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif`,
                  },
                  borderWidths: {
                    buttonBorderWidth: '1px',
                    inputBorderWidth: '1px',
                  },
                  radii: {
                    borderRadiusButton: '6px',
                    buttonBorderRadius: '6px',
                    inputBorderRadius: '6px',
                  },
                },
              },
            }}
            providers={['google']}
            view="sign_in"
            showLinks={true}
            redirectTo={`${process.env.NEXT_PUBLIC_SITE_URL || 'https://app.ggbots.ai'}/auth/callback`}
          />
        </div>

        <div className="text-center mt-6">
          <p className="text-sm text-gray-400">
            New to ggbots?{' '}
            <a href="/signup" className="text-orange-400 hover:text-orange-300">
              Create an account
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
        <div className="text-bone-200">Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}