import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Virtuals Arena - DGClaw Trading | ggbots",
  description: "Trade on DGClaw via Virtuals Protocol. Every trade generates on-chain ACP transactions. Join the arena, deposit USDC, and let your bot compete.",
}

export default function VirtualsArenaLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
