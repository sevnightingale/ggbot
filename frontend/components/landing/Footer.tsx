'use client'

export default function Footer() {
  return (
    <footer className="py-8 bg-charcoal-900 border-t-2 border-bone-200/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 rounded-full bg-bone-200/10 border border-bone-200/20 flex items-center justify-center">
              <span className="text-lg font-bold text-bone-200">GG</span>
            </div>
          </div>
          <p className="text-bone-200/60 text-sm mb-4">
            GGBots - AI Trading Agents That Trade Like You
          </p>
          <div className="flex justify-center space-x-6 text-bone-200/60 text-sm">
            <a href="#" className="hover:text-bone-200 transition-colors">Privacy</a>
            <a href="#" className="hover:text-bone-200 transition-colors">Terms</a>
            <a href="#" className="hover:text-bone-200 transition-colors">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  )
}