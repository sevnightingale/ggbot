'use client'

export default function Footer() {
  return (
    <footer className="py-8 bg-charcoal-900 border-t-2 border-bone-200/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-bone-200/60 text-xs mb-4">
            ggbots - AI trading agents that trade like you
          </p>
          <div className="flex justify-center space-x-6 text-bone-200/60 text-xs">
            <a href="#" className="hover:text-bone-200 transition-colors">Privacy</a>
            <a href="#" className="hover:text-bone-200 transition-colors">Terms</a>
            <a href="#" className="hover:text-bone-200 transition-colors">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  )
}