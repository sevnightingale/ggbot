import Script from 'next/script'

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      {children}
      <Script 
        src="https://getlaunchlist.com/js/widget.js" 
        strategy="afterInteractive"
      />
    </>
  )
}