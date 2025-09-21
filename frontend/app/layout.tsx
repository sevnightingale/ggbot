import type { Metadata } from "next"
import { Inter, Kanit } from 'next/font/google'
import "./globals.css"

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter'
})
const kanit = Kanit({ 
  weight: ['700', '800'], 
  subsets: ['latin'],
  variable: '--font-kanit'
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
  // Check for maintenance mode
  const isMaintenanceMode = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === 'true'

  if (isMaintenanceMode) {
    return (
      <html lang="en">
        <body className={`${inter.variable} ${kanit.variable} antialiased`}>
          <div className="min-h-screen bg-charcoal-900 text-bone-200 flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-white mb-4">Under Maintenance</h1>
              <p className="text-gray-300 mb-8">
                We're currently performing scheduled maintenance. Please check back soon.
              </p>
              <div className="text-sm text-gray-500">
                Follow us for updates: <a href="https://twitter.com/ggbots" className="text-blue-400">@ggbots</a>
              </div>
            </div>
          </div>
        </body>
      </html>
    )
  }

  return (
    <html lang="en">
      <body className={`${inter.variable} ${kanit.variable} antialiased`}>
        <div className="min-h-screen bg-charcoal-900 text-bone-200">
          {children}
        </div>
      </body>
    </html>
  )
}