'use client'

import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { createClient } from '@/lib/supabase'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function SignupPage() {
  const supabase = createClient()
  const router = useRouter()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        router.push('/forge')
      }

      // Handle OTP verification flow
      if (event === 'USER_UPDATED' && session?.user?.email_confirmed_at) {
        router.push('/forge')
      }
    })

    return () => subscription.unsubscribe()
  }, [supabase.auth, router])

  return (
    <div className="min-h-screen bg-charcoal-900 flex items-center justify-center p-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-bone-200 mb-2">Join ggbots</h1>
          <p className="text-gray-400">Create your account and start building autonomous trading agents</p>
        </div>
        
        <div className="bg-charcoal-800 p-8 rounded-lg border border-gray-700">
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
            providers={[]}
            view="sign_up"
            showLinks={true}
            otpType="email"
            onlyThirdPartyProviders={false}
          />
        </div>
        
        <div className="text-center mt-6">
          <p className="text-sm text-gray-400">
            Already have an account?{' '}
            <a href="/login" className="text-orange-400 hover:text-orange-300">
              Sign in
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}