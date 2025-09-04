import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

// Server-side Supabase client
export const createServerClient = () => createServerComponentClient({ cookies })