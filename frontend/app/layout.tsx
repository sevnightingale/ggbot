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
  metadataBase: new URL('https://ggbots.ai'),
  title: {
    default: "ggbots - Your Edge, Amplified",
    template: "%s | ggbots",
  },
  description: "Build autonomous AI trading agents that think, adapt, and execute your strategies 24/7. Created by traders, for traders.",
  keywords: ["AI trading", "autonomous trading bots", "cryptocurrency trading", "algorithmic trading", "adaptive AI", "trading agents", "crypto bots"],
  authors: [{ name: "ggbots" }],
  creator: "ggbots",
  publisher: "ggbots",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://ggbots.ai",
    siteName: "ggbots",
    title: "ggbots - Your Edge, Amplified",
    description: "Build autonomous AI trading agents that think, adapt, and execute your strategies 24/7.",
    images: [
      {
        url: "/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "ggbots - AI Trading Agents",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ggbots - Your Edge, Amplified",
    description: "Build autonomous AI trading agents that think, adapt, and execute your strategies 24/7.",
    images: ["/twitter-image.png"],
    creator: "@ggbots_ai",
  },
  icons: {
    icon: [
      { url: "/icon.png", sizes: "any" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  manifest: "/manifest.json",
  other: {
    "virtual-protocol-site-verification": "c4316302f905b5de7bc4470b35aeec0a",
  },
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