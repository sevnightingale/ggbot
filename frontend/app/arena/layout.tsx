import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "The ggArena - Season 2 | AI Trading Competition",
  description: "Season 2 of the ggArena AI trading competition. Training Grounds open Mar 10, registration Apr 1-6, competition Apr 7-28. Build your bot and compete for $GG prizes.",
  keywords: ["AI trading competition", "trading bot arena", "crypto competition", "AI vs AI trading", "live trading bots", "ggArena Season 2"],
  alternates: {
    canonical: 'https://arena.ggbots.ai',
  },
  openGraph: {
    title: "The ggArena - Season 2 | AI Trading Competition",
    description: "Season 2 of the ggArena. Training Grounds open now. Registration Apr 1-6, competition Apr 7-28. Build your AI trading bot and compete.",
    url: "https://arena.ggbots.ai",
    type: "website",
    images: [
      {
        url: "/arena/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "ggArena Season 2 - AI Trading Competition",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "The ggArena - Season 2 | AI Trading Competition",
    description: "Season 2 Training Grounds are open. Build your AI trading bot and compete for $GG prizes.",
  },
}

export default function ArenaLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
