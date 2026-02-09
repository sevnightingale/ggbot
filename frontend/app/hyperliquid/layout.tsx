import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Hyperliquid Setup - ggbots",
  description: "Connect your wallet and authorize ggbots to trade on Hyperliquid. Non-custodial API wallet — protocol-enforced withdrawal protection.",
}

export default function HyperliquidLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
