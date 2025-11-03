import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || ''
  const pathname = request.nextUrl.pathname

  // If accessing via aster subdomain (Aster Vibe Trading competition submission)
  if (hostname.startsWith('aster.')) {
    // Aster Vibe Trader config ID
    const ASTER_VIBE_TRADER_CONFIG_ID = 'bb2560fd-b053-464f-8a58-8e254e4d36fa'

    // Route root to the specific vibe trader's activity timeline
    if (pathname === '/') {
      return NextResponse.rewrite(new URL(`/view/${ASTER_VIBE_TRADER_CONFIG_ID}`, request.url))
    }

    // Allow direct access to the view page
    if (pathname.startsWith('/view/')) {
      return NextResponse.next()
    }

    // All other routes redirect to root (which shows the vibe trader)
    return NextResponse.redirect(new URL('/', request.url))
  }

  // If accessing via arena subdomain
  if (hostname.startsWith('arena.')) {
    // Handle root arena subdomain -> arena page
    if (pathname === '/') {
      return NextResponse.rewrite(new URL('/arena', request.url))
    }

    // All other arena subdomain routes should redirect to arena
    return NextResponse.redirect(new URL('/', request.url))
  }

  // If accessing via app subdomain
  if (hostname.startsWith('app.')) {
    // Allow auth pages and callbacks through
    if (pathname === '/login' || pathname === '/signup') {
      return NextResponse.next()
    }

    // Handle root app subdomain -> forge
    if (pathname === '/') {
      return NextResponse.rewrite(new URL('/forge', request.url))
    }

    // All other app subdomain routes go through normally
    return NextResponse.next()
  }

  // Main domain routing
  if (pathname === '/') {
    return NextResponse.rewrite(new URL('/landing', request.url))
  }

  // All other main domain routes go through normally
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}