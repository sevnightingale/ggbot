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
      <body className={`${inter.variable} ${kanit.variable} antialiased`}>
        <div className="min-h-screen bg-charcoal-900 text-bone-200">
          {children}
        </div>
      </body>
    </html>
  )
}