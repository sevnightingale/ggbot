import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    // The client-side auth will handle the session automatically
    // Just redirect to dashboard and let the auth state update
  }

  // Redirect to forge after successful authentication
  return NextResponse.redirect(new URL('/forge', request.url))
}