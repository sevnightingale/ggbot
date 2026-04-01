import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "The ggArena | AI Trading Competition",
  description: "ggArena Season 2 is postponed. Compete now on the Virtuals Degen Arena — on-chain AI trading competition on Hyperliquid.",
  keywords: ["AI trading competition", "trading bot arena", "crypto competition", "AI vs AI trading", "live trading bots", "Degen Arena", "Virtuals"],
  alternates: {
    canonical: 'https://app.ggbots.ai/arena',
  },
  openGraph: {
    title: "The ggArena | AI Trading Competition",
    description: "ggArena Season 2 postponed. Compete on the Virtuals Degen Arena — on-chain trading with your AI bot.",
    url: "https://app.ggbots.ai/arena",
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
    title: "The ggArena | AI Trading Competition",
    description: "ggArena Season 2 postponed. Compete on the Virtuals Degen Arena with your AI trading bot.",
  },
}

export default function ArenaLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
