'use client'

export default function EmailForm() {
  return (
    <section id="waitlist" className="py-16 bg-charcoal-900 border-t-2 border-bone-200/20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-bone-200 mb-4 font-display">
            Join the Waitlist
          </h2>
          <p className="text-bone-200/80">
            Be among the first to deploy AI agents that trade like professional traders. 
            Get early access and exclusive updates.
          </p>
        </div>

        {/* LaunchList Embed Container */}
        <div className="max-w-md mx-auto">
          <div className="launchlist-widget" data-key-id="8390qp" data-height="180px"></div>
        </div>

        {/* Referral Incentive */}
        <div className="mt-8 text-center">
          <p className="text-bone-200/60 text-sm">
            💡 Refer friends to move up the waitlist. Share your unique link after signing up!
          </p>
        </div>
      </div>
    </section>
  )
}