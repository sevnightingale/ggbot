Stripe Metered Billing for Dynamic LLM Usage Pricing
Overview of Stripe Meters and Usage Events

Stripe’s usage-based billing (Meters API) allows you to record customer usage as events and bill in arrears based on that usage. You create a Meter (a usage metric) attached to a Price, and then send meter events for each usage occurrence. Each meter event has a payload that includes the customer identifier and the usage amount (value) for that event
openmeter.io
. You can optionally tag events with custom metadata fields (called Dimensions) such as the model name, token type, region, etc.
docs.stripe.com
. For example, an event could include fields like model: "gpt-5", input_tokens: 150, output_tokens: 75, along with the Stripe customer ID and usage value. Stripe will aggregate these usage events over the billing period (e.g. monthly) according to the meter’s settings (summing values, counting events, etc.) and use that total to compute the invoice line item
docs.stripe.com
.

Including Custom Metadata (Dimensions) in Usage Events

Stripe does support sending usage events with custom metadata via Dimensions. When configuring a Meter, you can define Dimensions to tag each usage event with attributes like LLM model or token type
docs.stripe.com
. These fields are recorded for analytics, reporting, and alerting purposes. They allow you and your customers to see granular breakdowns of usage (e.g. usage per model or per token type) and set up usage alerts by segment. In other words, you can submit rich usage data to Stripe – for instance, tagging each event with which model was used and how many input vs. output tokens – and Stripe will store those details for later analysis
docs.stripe.com
.

However, it’s important to note that these metadata tags do not automatically change how Stripe bills the event. The Meter’s core “value” (the quantity used for billing) is typically a single numeric field in the event payload (e.g. total tokens or API calls), and the Price’s rate applies uniformly to that value. The Dimensions are not used by Stripe to apply different rates within one meter in real time – they are primarily for data segmentation
openmeter.io
.

Pricing Rules Based on Metadata – Limitations

Stripe’s current metered billing cannot apply dynamic pricing logic per event based on event metadata. There is no built-in “if metadata X, then price Y” rule within a single Meter or Price. In fact, as of mid-2024, Stripe meters do not support “group by” or conditional pricing on dimensions
openmeter.io
. This means you cannot have one meter automatically charge $0.05 per 1K tokens for model A and $0.01 per 1K tokens for model B just by sending model identifiers in the events. All usage reported to a single Meter will be rated at that meter’s fixed unit price or tiered rates defined in its Price. The Stripe documentation encourages using Dimensions for analytics or “to granularly price usage based on a combination of attributes,” but in practice this means you must handle the attribute-based pricing logic yourself when setting up your billing model
docs.stripe.com
openmeter.io
.

In short, Stripe will aggregate usage and bill it, but it will not dynamically compute different costs per event from multiple fields in the payload. You need to model each distinct rate as a separate billable unit in Stripe.

Implementing Variable Per-Event Pricing: Two Approaches

Given Stripe’s limitations, there are two primary ways to handle a use case with multiple models and different per-token costs:

1. Multiple Meters and Prices (One per Usage Type) – You can create separate meters (and corresponding price entries) for each category of usage that has a different rate. For example, you might define one meter for “GPT-5 input tokens”, another for “GPT-5 output tokens”, another for “Claude Opus input tokens”, and so on. Each meter/price would be configured with the appropriate unit cost (including your 70% markup) for that specific token type. You would then send separate usage events for each portion of an API request: e.g. one event reporting the input tokens on the GPT-5-input meter, and another event for the output tokens on the GPT-5-output meter, etc. Stripe would track each meter’s usage independently and create multiple line items on the customer’s invoice, one for each meter/price. This approach is confirmed by Stripe experts – a single subscription can have multiple metered items, each tracking usage separately with its own unit price and tiers
reddit.com
. For instance, one subscription item could bill “GPT-5 Input Tokens at $0.085 per 1K” and another bills “GPT-5 Output Tokens at $0.17 per 1K”, each with its usage totaled monthly. This effectively implements per-model, per-token-type pricing by splitting the usage into separate buckets. (In a similar example, a Stripe user achieved multi-unit billing by having one metered item for “TIFF image requests” and another for “GIF image requests” under the same subscription
reddit.com
.)

Using multiple meters does increase the number of subscription items and invoice lines, but it leverages Stripe’s built-in aggregation per item. You can also combine this with tiered pricing for each item if needed (e.g. free allowances per model, graduated pricing) by configuring each Price’s tiers.

2. Pre-Compute Cost and Use a Single Meter – The alternative is to handle all the pricing calculation on your side for each event, then report only a single unified usage value that represents the cost of that event. In practice, this could mean defining one Meter for “LLM API Usage (cost)” and setting its Price to, say, $0.01 per unit, treating one unit as one cent of usage cost. When an API request comes in, you would compute its cost based on the model’s token rates and your markup – for example, a request with GPT-5 using 150 input and 75 output tokens would cost:
(150/1000 * $0.05 + 75/1000 * $0.10) * 1.70 markup = approximately $0.0204 (about 2.04 cents). You would then send a meter event with value: 2.04 (if measuring cents) or value: 0.0204 (if measuring dollars, depending on how you configure the unit). Stripe will simply sum these “cost units” for all events during the month and charge that total at the fixed rate of $0.01 per unit (in this example), effectively billing the exact aggregated cost
docs.stripe.com
. In this approach, the Stripe meter is just tracking a generic usage quantity that already represents money, so Stripe’s role is aggregation and invoicing, not applying any further pricing math per event.

The benefit of pre-computing cost is that the customer sees a single line item (e.g. “Total AI API Usage”) on their invoice. The downside is that you must perform the calculation for every event and ensure it matches your intended pricing. You also lose Stripe’s built-in per-category quantity tracking on the invoice (all usage is lumped together as a currency amount). Some businesses choose this route for simplicity if they prefer one billing metric, whereas others prefer the transparency of separate line items per model or token type.

Monthly Aggregation and Invoicing

Whichever approach you take, Stripe will aggregate usage events over the billing period and invoice in arrears. You can configure the Price’s billing interval (e.g. monthly) and set the usage to be metered. Stripe’s usage-based subscription will then automatically total up all reported usage quantities for that period and multiply by the unit price or apply the tiered rates you defined. This occurs at invoice time – you do not need to manually sum anything per customer. According to Stripe’s documentation, during each billing period you report usage, and Stripe “adds them up to determine how much to bill” for that period
docs.stripe.com
. The new Meters system is more flexible with timing of reporting as well (it allows some delay in sending events), ensuring late-arriving usage events can still count toward the correct period’s invoice
prefab.cloud
prefab.cloud
. In short, Stripe can invoice monthly based on aggregated usage – either per meter (if you use multiple meters for different models) or in total (if you use one cost-based meter) – as long as you have set up the corresponding subscription prices.

Current Stripe Support (2025) Summary

In 2025, Stripe Billing’s Meters API provides robust support for usage-based subscriptions, but it does not natively support multi-variable pricing calculations on a single usage event. You can send rich usage data with custom metadata for each event (e.g. model names, token counts)
docs.stripe.com
, but Stripe’s billing engine will not apply different unit prices within one meter based on that metadata
openmeter.io
. To implement per-event variable pricing (such as different rates for different models or token types), you must design your Stripe integration accordingly: either by tracking each rate category with its own usage-based price (yielding multiple subscription items/invoice lines)
reddit.com
, or by calculating the cost externally and reporting a single monetary usage value per event. Both methods are in active use by developers and are supported by Stripe’s infrastructure.

In conclusion, Stripe Metered Billing supports your use case with some assembly required. It will handle the accumulation of usage and customer invoicing reliably, but you (as the developer) must map your complex pricing logic into Stripe’s supported models. That likely means splitting usage events by model/token type or converting usage into a unified cost metric before reporting. The official guidance and community examples reflect this: Stripe gives you the tools to meter any custom unit, but the pricing rules based on those units need to be encoded in your product & price setup or in your pre-processing of usage data, rather than in Stripe’s metadata parsing. This ensures that at invoice time, the charges for each customer accurately reflect the different per-token prices of GPT-5, Claude, DeepSeek, plus your markup – even if Stripe isn’t computing those differences itself.

Sources: Stripe documentation on usage-based pricing and Meters
docs.stripe.com
docs.stripe.com
, Stripe community guidance on multiple metered items for different usage types
reddit.com
, and third-party analysis of Stripe’s Metering capabilities (OpenMeter) confirming the lack of automatic dimension-based pricing as of 2024