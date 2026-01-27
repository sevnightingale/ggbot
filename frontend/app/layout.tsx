import type { Metadata } from "next"
import { Bodoni_Moda, Space_Grotesk, IBM_Plex_Mono } from 'next/font/google'
import { Analytics } from "@vercel/analytics/next"
import { Providers } from "@/lib/providers"
import "./globals.css"

const bodoniModa = Bodoni_Moda({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: "ggbots - your edge, amplified",
  description: "build autonomous AI trading agents that trade like you",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${bodoniModa.variable} ${spaceGrotesk.variable} ${ibmPlexMono.variable}`}>
      <body className="font-sans antialiased">
        <Providers>
          <div className="min-h-screen bg-charcoal-900 text-bone-200">
            {children}
          </div>
        </Providers>
        <Analytics />
      </body>
    </html>
  )
}