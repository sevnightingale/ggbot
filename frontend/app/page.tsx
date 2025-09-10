import { redirect } from 'next/navigation'

export default function RootPage() {
  // Middleware handles domain routing, this should never be reached
  // But just in case, redirect to landing page
  redirect('/landing')
}