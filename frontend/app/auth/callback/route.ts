import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const error = requestUrl.searchParams.get('error')

  // Handle OAuth errors (user cancelled, etc.)
  if (error) {
    console.error('OAuth error:', error)
    return NextResponse.redirect(new URL('/login?error=oauth_error', request.url))
  }

  if (code) {
    const cookieStore = cookies()
    const supabase = createRouteHandlerClient({ cookies: () => cookieStore })

    try {
      // Exchange the auth code for a session (works for both OAuth and magic link)
      const { data, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)

      if (exchangeError) {
        console.error('Auth callback error:', exchangeError)
        return NextResponse.redirect(new URL('/login?error=auth_error', request.url))
      }

      // Verify we have a valid session
      if (data.session && data.user) {
        console.log('Auth callback successful for user:', data.user.id)
        // Redirect to forge after successful authentication
        return NextResponse.redirect(new URL('/forge', request.url))
      } else {
        console.error('Auth callback: No session or user data received')
        return NextResponse.redirect(new URL('/login?error=no_session', request.url))
      }
    } catch (err) {
      console.error('Auth callback exception:', err)
      return NextResponse.redirect(new URL('/login?error=callback_error', request.url))
    }
  }

  // If no code parameter, this might be a direct OAuth callback
  // For Google OAuth, Supabase might handle the redirect differently
  console.log('Auth callback: No code parameter, redirecting to forge')
  return NextResponse.redirect(new URL('/forge', request.url))
}