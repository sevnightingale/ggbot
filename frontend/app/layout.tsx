import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "ggbots - Your Edge, Amplified",
  description: "Build autonomous AI trading agents that trade like you",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <div className="min-h-screen bg-charcoal-900 text-bone-200">
          {children}
        </div>
      </body>
    </html>
  )
}