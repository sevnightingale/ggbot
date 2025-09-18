Thought for 20s

Here’s the standard, clean way to wire Google sign-in with Supabase so users can click on /login or /signup, auth with Google, and land already logged in at /forge.

1) Allow the redirect(s) in Supabase

In Auth → URL configuration, add:

https://app.ggbots.ai/**

(Dev) http://localhost:3000/**

Supabase only redirects to URLs on this allow-list; otherwise it falls back to SITE_URL. 
Supabase
+2
Supabase
+2

2) Call OAuth from /login and /signup

Use one Google button on both pages. The only thing it needs to do is call signInWithOAuth and tell Supabase where to land after Google:

// client-side
await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://app.ggbots.ai/forge' // must match your allow-list
  }
});


This sends the user to Google, then back to your redirectTo with a valid session. 
Supabase
+1

Alternative (SSR/PKCE): point redirectTo to a dedicated callback route (e.g., /auth/callback) that immediately router.replace('/forge'). Recommended if you’re doing server-side auth with cookies. 
Supabase

3) Persist the session (Next.js recommended)

If you’re on Next.js (App Router), use Supabase’s server-side auth so /forge is protected and sessions don’t disappear:

Install and wire @supabase/ssr per docs.

Add a middleware.ts that refreshes tokens & stores them in cookies.

Guard your app routes (e.g., /forge) server-side; redirect unauthenticated users to /login.

This is the current, recommended pattern; the old “auth-helpers” are deprecated. 
Supabase
+1

4) Minimal route protection

Server component / RSC-friendly approach (sketch):

// app/forge/page.tsx (server)
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function ForgePage() {
  const cookieStore = cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { get: (key) => cookieStore.get(key)?.value } }
  )

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  return <YourForgeApp />
}


(Your middleware.ts handles refreshing/setting cookies so the user arrives at /forge already logged in.) 
Supabase

5) Quality-of-life tips

If you want to always land at /forge, pass that exact URL in redirectTo. If you want to return users to whatever page they started on, stash a returnTo query param and read it after auth. (The allow-list still applies.) 
Supabase

If you see a redirect problem, it’s almost always an allow-list mismatch—exact URL must be listed. 
Supabase

On purely client-side apps, you can also just listen for session changes with onAuthStateChange and route accordingly (works, but SSR+middleware is sturdier). 
Supabase

TL;DR (opinionated defaults)

Allow-list https://app.ggbots.ai/**. 
Supabase

On both /login and /signup, call signInWithOAuth({ provider:'google', redirectTo:'/forge' }). 
Supabase

Use server-side auth + middleware so /forge is protected and the user arrives already authenticated. 
Supabase

That’s the standard setup—and the least brittle.