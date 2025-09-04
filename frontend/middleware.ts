import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || ''
  
  // If accessing via app subdomain, rewrite to dashboard routes
  if (hostname.startsWith('app.')) {
    // Handle app.ggbots.ai/login -> /login
    if (request.nextUrl.pathname === '/login') {
      return NextResponse.rewrite(new URL('/login', request.url))
    }
    // Handle app.ggbots.ai -> /dashboard
    if (request.nextUrl.pathname === '/') {
      return NextResponse.rewrite(new URL('/dashboard', request.url))
    }
    // All other app subdomain routes go through normally
    return NextResponse.next()
  }
  
  // Main domain routes to landing
  if (request.nextUrl.pathname === '/') {
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