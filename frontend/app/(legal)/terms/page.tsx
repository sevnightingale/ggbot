'use client'

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Terms of Service</h1>
          <p className="text-[var(--text-secondary)] text-sm">Last updated: November 20, 2025</p>
        </div>

        <div className="prose prose-invert max-w-none space-y-6 text-[var(--text-primary)]">
          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">1. Introduction</h2>
            <p>These Terms of Service (&quot;Terms&quot; or &quot;Agreement&quot;) are a contract between you and ggbots.ai (&quot;ggbots,&quot; &quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) and govern your access to and use of the website hosted at https://ggbots.ai/ and https://app.ggbots.ai/, and all related software applications and online services (together, the &quot;Services&quot;).</p>
            <p>By accessing or using any portion of the Services, or by clicking on an &quot;I Agree&quot; button or checkbox, you agree to comply with and be bound by these Terms. If you do not agree, you are not authorized to access or use the Services.</p>
            <p className="font-semibold">These terms include a waiver of any right to participate in a class action, as well as a mandatory arbitration clause. Please read Section 18 carefully.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">2. Amendments</h2>
            <p>ggbots reserves the right to amend this Agreement from time to time. Changes will be effective immediately upon posting, and you waive any right to receive specific notices. By continuing to use the Services after changes are posted, you agree to be bound by those changes.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">3. The Services</h2>
            <h3 className="text-xl font-semibold mb-3 text-[var(--text-primary)]">3.1 Platform Overview</h3>
            <p>ggbots provides a platform for creating, configuring, and deploying AI-powered autonomous trading agents. The platform integrates with third-party trading APIs (including but not limited to Hyperliquid) to execute trades based on AI-generated decisions.</p>
            <p>You understand that ggbots does not execute trades directly, but rather facilitates communication between your configured trading agents and third-party execution venues. Your relationship with third-party trading platforms is governed by their respective terms of service.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">3.2 Third Party Services</h3>
            <p>The Services may include links to or integrations with third-party services, including trading platforms, data providers, and AI model providers. ggbots has no control over and is not responsible for the accuracy, availability, or reliability of Third Party Services. You are responsible for all costs associated with your use of Third Party Services.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">4. Eligibility</h2>
            <p>You represent and warrant that:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>You are at least 18 years old</li>
              <li>You are capable of forming a binding contract</li>
              <li>You are not a Restricted Party (as defined below)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">4.1 Restricted Parties</h3>
            <p>You represent and warrant that:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>You will comply with all applicable laws including export restrictions, antiterrorism laws, anti-money laundering laws, and economic sanctions</li>
              <li>You are not subject to Sanctions Laws administered by the U.S. Department of Treasury, U.S. Department of Commerce, United Nations, European Union, or other applicable authorities</li>
              <li>You are not located or headquartered in a comprehensively sanctioned jurisdiction including but not limited to Afghanistan, Belarus, Cuba, Iran, North Korea, Russia, Syria, or Venezuela</li>
              <li>You are not a resident of the United States</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">5. Account Security</h2>
            <p>You are responsible for maintaining the security of your account credentials, API keys, and any third-party authentication tokens. You should never share your credentials with anyone. We accept no responsibility for unauthorized access resulting from your failure to maintain secure credentials.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">6. Risk Disclosures</h2>
            <p className="font-semibold">You understand, accept, and agree to assume all risks involved in using the Services and trading digital assets, including:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Market Risk:</strong> Digital assets are highly volatile and may decrease in value or lose all value in a short period. Past performance is not indicative of future results.</li>
              <li><strong>AI Decision Risk:</strong> Trading decisions generated by AI models may be incorrect, based on flawed data, or fail to account for market conditions. AI models can and do make losing trades.</li>
              <li><strong>Technical Risk:</strong> Software bugs, API failures, network interruptions, or malicious attacks may prevent trades from executing as intended or cause unintended trades.</li>
              <li><strong>Execution Risk:</strong> Trades may not execute at desired prices due to slippage, liquidity constraints, or exchange failures.</li>
              <li><strong>Total Loss:</strong> You may lose your entire trading capital. Only trade with funds you can afford to lose.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">7. AI-Generated Content Disclaimer</h2>
            <p>The ggbots platform utilizes AI models (including GPT-5, Claude Opus 4, Grok, DeepSeek R1, and others) to analyze markets and generate trading decisions. All AI-generated content is automated and provided strictly for execution purposes.</p>
            <p className="font-semibold">AI models are not financial advisors and do not provide investment, legal, tax, or financial advice.</p>
            <p>You acknowledge and agree:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>ggbots and its AI models are not registered with any financial regulatory authority</li>
              <li>Your use of ggbots does not create any fiduciary, brokerage, or advisory relationship</li>
              <li>AI models do not consider your personal financial circumstances, goals, or risk tolerance</li>
              <li>AI outputs rely on third-party data which may be delayed, incorrect, or manipulated</li>
              <li>You bear full responsibility for all trades executed by your agents, including losses</li>
              <li>Trading in digital assets involves substantial risk including potential total loss</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">8. Non-Reliance</h2>
            <p>You are not relying on any communication from ggbots as advice or as a recommendation to trade. ggbots has not provided any guarantee regarding potential success, return, or benefit of trading. You have made your own independent decision that using the Services is suitable for you. You must seek professional advice regarding your particular financial, legal, and technical situation before using the Services.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">9. Prohibited Uses</h2>
            <p>You may not use the Services to engage in:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Unlawful Activity:</strong> Any activity that violates laws, regulations, or sanctions programs</li>
              <li><strong>Fraud:</strong> Deceiving or defrauding ggbots, users, or any other person</li>
              <li><strong>Market Manipulation:</strong> Wash trading, spoofing, or other manipulative trading practices</li>
              <li><strong>Abusive Activity:</strong> Causing the Services to work other than as intended or damaging our reputation or legal rights</li>
              <li><strong>Intellectual Property Infringement:</strong> Violating the legal rights of others</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">10. Subscription and Fees</h2>
            <h3 className="text-xl font-semibold mb-3 text-[var(--text-primary)]">10.1 Subscription Plans</h3>
            <p>ggbots offers usage-based and fixed-price subscription plans. Current pricing is available at https://app.ggbots.ai/. We reserve the right to modify fees at any time.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">10.2 Metered Billing</h3>
            <p>LLM usage costs are billed based on actual token consumption with a 1.70x markup. Billing occurs weekly or monthly depending on your subscription plan. Fees are non-refundable except when required by law.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">10.3 Trading Fees</h3>
            <p>Third-party trading platforms may charge additional fees for trade execution, deposits, withdrawals, and other services. You are responsible for all such fees.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">11. Suspension and Termination</h2>
            <p>We may, at our discretion and without liability, suspend or terminate your access to the Services at any time for any reason, including violation of these Terms or failure to pay fees. We will not be liable for losses resulting from suspension or termination.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">12. Intellectual Property</h2>
            <p>The Services and all contents are owned by ggbots and protected by copyright, trademark, and other intellectual property laws. You may use the Services solely as authorized. You may not resell, modify, reverse engineer, or create derivative works of the Services.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">13. Warranty Disclaimer</h2>
            <p className="font-semibold uppercase">To the fullest extent provided by law, the services are provided &quot;as is&quot; without warranties of any kind. ggbots disclaims all warranties, express or implied, including warranties of merchantability, fitness for a particular purpose, and non-infringement.</p>
            <p className="font-semibold uppercase">ggbots will not be liable for any loss or damage caused by viruses, technical failures, or other harmful material that may affect your equipment or data.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">14. Limitation of Liability</h2>
            <p className="font-semibold uppercase">To the fullest extent provided by law, in no event will ggbots be liable for any indirect, special, incidental, consequential, or punitive damages arising from your use of the services.</p>
            <p className="font-semibold uppercase">In no event will ggbots&apos;s total liability exceed the greater of $100 or the amount you paid to ggbots in the last six months.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">15. Indemnification</h2>
            <p>You agree to defend, indemnify, and hold harmless ggbots from any claims, damages, losses, or expenses (including attorneys&apos; fees) arising from:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Your violation of these Terms</li>
              <li>Your use of the Services</li>
              <li>Your trading activities and losses</li>
              <li>Your violation of any laws or regulations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">16. Relationship of Parties</h2>
            <p>ggbots is not your broker, intermediary, agent, or advisor and has no fiduciary relationship or obligation to you. ggbots does not provide investment, tax, or legal advice. You are solely responsible for your trading decisions and strategies.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">17. Taxes</h2>
            <p>You are solely responsible for determining and paying all applicable taxes on your trading activities. ggbots does not provide tax advice.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">18. Dispute Resolution and Arbitration</h2>
            <p className="font-semibold">Please read this section carefully. It waives your right to participate in class actions and requires arbitration of certain disputes.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">18.1 Class Action Waiver</h3>
            <p className="font-semibold uppercase">Any disputes must be brought in your individual capacity, not as a class action. You waive the right to participate in any class, collective, or representative proceeding. You waive the right to trial by jury.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">18.2 Informal Resolution</h3>
            <p>Before filing a claim, you agree to try to resolve disputes by emailing support@ggbots.ai. If we can&apos;t resolve the dispute within sixty days, either party may submit to binding arbitration.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">18.3 Arbitration Agreement</h3>
            <p>All disputes must be resolved by final and binding arbitration conducted by the International Chamber of Commerce (ICC) under its Commercial Arbitration Rules. Arbitration shall be in English and administered in Panama or another mutually agreeable location.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">18.4 Time Limit</h3>
            <p>Any arbitration must be commenced within one year after the claim arose. If not filed within this period, the claim is permanently barred.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">19. Governing Law</h2>
            <p>This Agreement shall be governed by and construed in accordance with the laws of Panama, without regard to conflict of law principles.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">20. Miscellaneous</h2>
            <h3 className="text-xl font-semibold mb-3 text-[var(--text-primary)]">20.1 Entire Agreement</h3>
            <p>These Terms constitute the entire agreement between you and ggbots and supersede all prior agreements.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">20.2 Severability</h3>
            <p>If any provision is found invalid, the remaining provisions remain in full effect.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">20.3 Survival</h3>
            <p>Sections regarding liability, indemnification, dispute resolution, and intellectual property survive termination.</p>

            <h3 className="text-xl font-semibold mb-3 mt-4 text-[var(--text-primary)]">20.4 Privacy</h3>
            <p>To understand how we collect and use information, please review our <a href="/privacy" className="text-[var(--accent)] hover:underline">Privacy Policy</a>.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold mb-4 text-[var(--text-primary)]">21. Contact</h2>
            <p>For questions about these Terms, please contact us at:</p>
            <p className="mt-2">
              <strong>ggbots.ai</strong><br />
              Email: support@ggbots.ai
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
