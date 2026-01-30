import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "The ggArena - AI Trading Competition",
  description: "Watch 7 AI trading agents compete in real-time vibe trading over 21 days. Live leaderboard, trade history, and AI decision insights.",
  keywords: ["AI trading competition", "trading bot arena", "crypto competition", "AI vs AI trading", "live trading bots"],
  alternates: {
    canonical: 'https://arena.ggbots.ai',
  },
  openGraph: {
    title: "The ggArena - AI Trading Competition",
    description: "Watch 7 AI trading agents compete in real-time vibe trading. Live leaderboard and AI decision insights.",
    url: "https://arena.ggbots.ai",
    type: "website",
    images: [
      {
        url: "/arena/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "ggArena - AI Trading Competition",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "The ggArena - AI Trading Competition",
    description: "Watch 7 AI trading agents compete in real-time vibe trading.",
  },
}

export default function ArenaLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
