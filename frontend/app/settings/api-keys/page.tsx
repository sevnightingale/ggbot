'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ApiKeysPage() {
  const router = useRouter()

  useEffect(() => {
    router.push('/forge')
  }, [router])

  return null
}
