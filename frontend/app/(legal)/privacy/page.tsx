'use client'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Privacy Policy</h1>
          <p className="text-[var(--text-secondary)] text-sm">Last updated: November 20, 2025</p>
        </div>

        <div className="prose prose-invert max-w-none space-y-6 text-[var(--text-primary)]">
          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">1. Introduction</h2>
            <p>This Privacy Policy describes how ggbots.ai (&quot;ggbots,&quot; &quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) collects, uses, shares, and protects personal information gathered from users through our website at https://ggbots.ai/ and https://app.ggbots.ai/ and related services (together, the &quot;Services&quot;).</p>
            <p>By accessing or using the Services, you agree to this Privacy Policy.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">2. Information We Collect</h2>
            <p>We collect the following types of information:</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">2.1 Account Information</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li>Email address (provided during signup)</li>
              <li>Authentication credentials (managed by Supabase)</li>
              <li>User ID and profile data</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">2.2 Trading Configuration Data</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li>Bot configurations and trading strategies</li>
              <li>Selected trading pairs and timeframes</li>
              <li>Risk management settings</li>
              <li>API credentials for third-party trading platforms (encrypted in secure vault)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">2.3 Trading Activity</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li>Trade execution records</li>
              <li>AI decision logs and reasoning</li>
              <li>Account balance history</li>
              <li>Performance metrics</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">2.4 Usage Data</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li>Page views and interactions</li>
              <li>Device type, browser, and operating system</li>
              <li>IP address and approximate location</li>
              <li>Session duration and feature usage</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">2.5 Payment Information</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li>Billing information (processed by Stripe)</li>
              <li>Subscription tier and status</li>
              <li>Usage billing records</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">3. How We Use Your Information</h2>
            <p>We use your information to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide, operate, and maintain the Services</li>
              <li>Execute trading strategies via your configured bots</li>
              <li>Process subscription payments and billing</li>
              <li>Improve user experience and platform functionality</li>
              <li>Communicate with you about updates, security alerts, and support</li>
              <li>Monitor system performance and detect technical issues</li>
              <li>Ensure security and prevent fraud or abuse</li>
              <li>Comply with legal obligations and law enforcement requests</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">4. Data Storage and Security</h2>
            <p>We implement reasonable security measures to protect your information:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Authentication managed by Supabase with industry-standard security</li>
              <li>API credentials encrypted in Supabase Vault</li>
              <li>Database hosted on secure Supabase infrastructure</li>
              <li>HTTPS encryption for all data transmission</li>
              <li>Redis caching with automatic expiration for temporary data</li>
            </ul>
            <p className="mt-4">However, no internet transmission or electronic storage method is completely secure. We cannot guarantee absolute security.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">5. Sharing and Disclosure</h2>
            <p>We do not sell your personal information. We may share information:</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">5.1 With Third-Party Service Providers</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Supabase:</strong> Authentication and database hosting</li>
              <li><strong>Stripe:</strong> Payment processing and subscription management</li>
              <li><strong>Vercel:</strong> Frontend hosting and delivery</li>
              <li><strong>AI Providers:</strong> OpenAI, Anthropic, XAI, DeepSeek, Google (for LLM inference)</li>
              <li><strong>Trading Platforms:</strong> Hyperliquid, Binance (for trade execution and market data)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">5.2 For Legal Compliance</h3>
            <p>We may disclose information if required by law, regulation, legal process, or government request.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">5.3 Business Transfers</h3>
            <p>In connection with a merger, acquisition, or sale of assets, user information may be transferred as part of the transaction.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">5.4 Public Performance Data</h3>
            <p>If you opt-in to make your bot&apos;s performance public, trading activity and performance metrics will be visible to other users. Bot names are shown, but your email and personal identity remain private.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">6. Data Retention</h2>
            <p>We retain your personal data:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>For as long as your account is active</li>
              <li>As needed to provide Services</li>
              <li>As required by applicable laws and regulations</li>
              <li>Until you request deletion (subject to legal retention requirements)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">7. Your Privacy Rights</h2>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">7.1 EU Users (GDPR)</h3>
            <p>If you are in the European Union, you have the right to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Access your personal data</li>
              <li>Correct inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Object to or restrict processing</li>
              <li>Data portability</li>
              <li>Withdraw consent</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">7.2 All Users</h3>
            <p>You may request to view, correct, or delete your personal information by contacting us. We will consider your request in accordance with applicable laws.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">8. Cookies and Analytics</h2>
            <p>We use cookies and similar technologies to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Maintain user sessions</li>
              <li>Remember preferences</li>
              <li>Analyze usage patterns</li>
              <li>Improve platform performance</li>
            </ul>
            <p className="mt-4">You can control cookies through your browser settings. However, disabling cookies may affect functionality.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">9. Third-Party Services</h2>
            <p>Our Services integrate with third-party platforms that have their own privacy policies:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Trading platforms (Hyperliquid, etc.)</li>
              <li>AI model providers (OpenAI, Anthropic, XAI, etc.)</li>
              <li>Market data providers (Binance, etc.)</li>
            </ul>
            <p className="mt-4">We encourage you to review their privacy policies. We are not responsible for third-party privacy practices.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">10. International Data Transfers</h2>
            <p>Your information may be transferred to and processed in countries other than your country of residence. These countries may have different data protection laws. By using the Services, you consent to such transfers.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">11. Children&apos;s Privacy</h2>
            <p>The Services are not intended for individuals under 18 years of age. We do not knowingly collect information from children. If we discover we have collected information from a child, we will delete it promptly.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">12. Changes to This Privacy Policy</h2>
            <p>We may update this Privacy Policy periodically. Changes will be posted on this page with an updated &quot;Last updated&quot; date. Your continued use of the Services after changes indicates your acceptance of the revised policy.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">13. Contact Us</h2>
            <p>If you have questions or requests about this Privacy Policy or our data handling practices, please contact us at:</p>
            <p className="mt-2">
              <strong>ggbots.ai</strong><br />
              Email: support@ggbots.ai
            </p>
            <p className="mt-4">For data protection inquiries from EU residents, please include &quot;GDPR Request&quot; in your subject line.</p>
          </section>
        </div>
      </div>
    </div>
  )
}
