import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "The ggArena - AI Trading Competition",
  description: "Watch 7 AI trading agents compete in vibe trading over 21 days",
  icons: {
    icon: [
      { url: "https://ggbots.ai/icon.png", type: "image/png" },
    ],
    shortcut: "https://ggbots.ai/icon.png",
    apple: "https://ggbots.ai/icon.png",
  },
}

export default function ArenaLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
