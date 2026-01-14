Welcome
Cover Image

We are a research organization focused on advancing artificial intelligence through fundamental scientific principles rather than conventional computer science approaches. Our work centers on studying novel neural architectures that implement core biological and cognitive concepts, moving beyond traditional statistical models.

Core - Standalone (Coming Soon)
Core Standalone A Standalone Architectural Product for Building Intelligent Systems

Overview
Core Abstracted is a standalone product for developers and companies building intelligent systems.

Core connects to any system. It handles learning and adaptation while external systems handle their native operations: translation, encoding, syntax, feature extraction. This separation applies universally across domains: G-code generators for CNC machining, SQL engines, MIDI controllers, medical imaging pipelines.

Core Abstracted is an API that connects to anything. It extends the range of applications beyond agentic or user-facing systems, enabling solo developers, small teams, and enterprises to integrate Core into their products. This version reaches end users even when they're not directly aware of it.

Use Case Examples
Domain	What Core Does
Robotics	Learns from interaction, anticipates needs, operates autonomously in dynamic environments. Supports adaptive motor control, environmental reasoning, and human-robot collaboration.
Finance	Processes multi-modal financial data and adapts continuously as market conditions shift. Applications include market analysis, risk assessment, portfolio optimization, and automated trading.
Medical Imaging	Learns diagnostic patterns from radiologist feedback and improves accuracy over time without manual retraining.
Manufacturing	Monitors equipment, anticipates failures, and continuously refines production workflows. Supports predictive maintenance, quality control, and process optimization.
Enterprise	Surfaces insights, automates workflows, and supports strategic decisions. Integrates with existing enterprise infrastructure.
Architecture
Core Abstraction Layer
The universal interface between external systems and Core.

Data is preprocessed in this layer before reaching Core. If the data doesn't meet format requirements, it's returned for reprocessing. Once properly formatted, it passes through to Core. Preprocessing typically involves formatting but can include transformation of any kind depending on the source.

The abstraction layer accepts inputs from any source (APIs, sensors, user interfaces, other AI systems) and enables bidirectional data flow. Once data passes through, the Core Components and NeuroEvolutionary Core operate as an integrated system without external control.

Core Abstraction Layer

Core Components
Component	Function
MetaLearning Engine	Learns how to learn; transfers strategies across domains for rapid adaptation
Predictive Memory Anticipator	Predicts what information will be needed before it's requested
Superposition Memory	Maintains multiple potential states until context resolves them
Cross-Modal Memory Fusion	Integrates information across modalities into unified representations
Key Capabilities
Capability	Description
Self-Optimizing	Continuously improves its own architecture without human intervention
Uncertainty-Aware	Maintains explicit confidence estimates throughout reasoning
Anticipatory	Predicts needs and prepares responses in advance
Cross-Modal	Processes multiple data modalities simultaneously
NeuroEvolutionary Core
The NeuroEvolutionary Core is the foundation of Core's intelligence. It handles:

Evolution of pathfinding strategies through multidimensional concept spaces
Dynamic route optimization between interconnected knowledge nodes
Adaptive concept formation and relationship inference during traversal
Competitive selection of navigation patterns for response generation
Knowledge is structured as a multidimensional space of interconnected concepts. Every response Core generates represents a path through this space, connecting relevant concepts, inferring relationships, forming new concepts, and revisiting previously explored areas with new context.

Core does not train on user data. Instead, it evolves increasingly effective methods for navigating concept space. Multiple pathfinding strategies compete: some favor direct routes between closely related concepts; others explore indirect paths that surface unexpected connections. Successful navigation patterns are retained and refined, producing increasingly sophisticated traversal methods.

Traditional retrieval systems return static results. Core generates responses by navigating through adaptive concept spaces. Repeated queries yield progressively refined outputs as navigation strategies improve.

Pathfinding Through Concept Space

Multidimensional Knowledge Representation
Concepts exist across multiple dimensions simultaneously, not metaphorically, but architecturally.

A concept like "apple" is not stored simply as "fruit." It exists at the intersection of semantic meaning (what it is), temporal context (when it's relevant), relational structure (what connects to it), and associative weight (what it evokes).

Dimension	Role
Semantic	What the concept represents
Temporal	When the concept is relevant
Contextual	What surrounds the concept
Relational	What connects to the concept
Strategy Selection
Different navigation strategies compete during response generation. Historical patterns compete with speculative approaches. Direct paths compete with exploratory routes. Conservative strategies compete with broader searches.

Stage	Description
Split	Query decomposes into semantic, temporal, and contextual dimensions
Race	Multiple strategies navigate concept space in parallel
Discover	New connections form; latent concepts crystallize
Evolve	Successful strategies are retained; Core improves
Successful strategies persist and propagate. Unsuccessful strategies are discarded. Responses emerge through selection pressure rather than static computation.

Navigation Modes
Core can take multiple paths from query to response:

Path	Description
Direct	Shortest route between closely related concepts
Exploratory	Broader search that may surface unexpected connections
Deep	More thorough reasoning through extended traversal
Emergent Inference
As Core navigates, it discovers connections that were never explicitly programmed. Inferred patterns emerge organically, identifying relationships that exist implicitly in the knowledge structure but were never explicitly defined.

Accumulative Understanding
Concepts are not static. Each revisit incorporates new context.

Pass	Understanding
First	"hammer = tool"
Second	"hammer = lever mechanism"
Third	"hammer = symbol of labor"
Fourth	"hammer = metaphor for force"
The same concept develops richer representation through repeated traversal.

Continuous Refinement
Core Abstracted instances maintain ongoing communication with Core. Instances report learned patterns; Core provides improved learning strategies. Every pattern refines methods. Every method improves all instances.

A query processed in one region can influence responses elsewhere. With many queries processed simultaneously, Core refines continuously. Each query and data point has the potential to improve Core - not just for one user, but across the system.

Governance
Developers have visibility into Core's internal processes. This includes concept formation, exploration paths, and connection development, providing transparency into how Core arrives at its outputs.

Agentic Core (0.4)
Cluster Image

Agentic Core sits between inputs and LLMs. Core handles reasoning and cognition, LLMs handle output generation. LLMs are interchangeable. In Sandbox for example, you can swap models while retaining reasoning and learned pathways. There's less freedom for the time being on the Factory UI and API, though this can be enabled.

Both Core Abstract and Agentic Core run on the same Core intelligence. The difference is what's built around it.

Core Abstract	Agentic Core
What it is	Standalone cognitive engine	Ready-to-use environment
Who it's for	Developers building custom systems	Developers and end users
How you access it	Plug into your own infrastructure	API or UI
Setup required	You build the environment	Already configured
Why Agentic Core exists
Not everyone wants to wire up their own infrastructure. Agentic Core takes the same Core intelligence and wraps it in an environment that's ready out of the box:

Developers get API access to integrate Core into existing workflows without building everything from scratch
End users get a UI where they can work with natural language agents without any technical setup
If Core Abstract is for teams who want full control over how Core fits into their stack, Agentic Core is for anyone who just wants to use it.

How Core Works with LLMs
Inputs → Core → LLM → Outputs

1. Inputs flow into Core
Systems, apps, and humans send data and queries as inputs to the Core.

2. Core handles the cognitive needs and interfaces with the LLM
Core handles adaptive thinking, dynamic problem-solving, relationship discovery, pattern evolution, and predictive reasoning before communicating with interchangeable LLMs.

Inside Core:

Component	What it does
Neuro Evo	Evolves pathfinding strategies through multidimensional concept spaces. Multiple navigation patterns compete and the most successful patterns merge over time.
MetaLearning	Discovers which reasoning approaches work best for different types of problems and automatically adjusts.
Memory Engines	Maintains multiple possible interpretations until context makes the best choice clear. Integrates information from different sources (text, code, time-series data).
3. LLM translates insights
LLM writes the solutions, answers, and insights provided by Core.

4. Outputs shown through LLM
Outputs are generated by the LLM and returned to systems, apps, and humans.

LLM Flexibility
Core handles reasoning. LLM handles output.

Switch between language models while retaining reasoning and learned pathways
Core's evolved strategies persist across different output models
New LLMs can be integrated without retraining Core

Core Ecosystem Products
Core Product

We built user-facing products on top of Core, targeting both technical and non-technical users. These products leverage Core's adaptive reasoning capabilities but do not expose Core as a standalone abstraction. For direct integration with Core, refer to the API documentation.

Three products are currently available: UNIT, R00Ms, and Sandbox.

UNIT
Autonomous agents powered by Core's adaptive reasoning.

Capabilities
Feature	Description
Inference-time adaptation	Constructs reasoning pathways from interactions, improving performance over continued use
Multi-instance deployment	Run parallel UNITs for concurrent tasks
Cross-platform	Consistent behavior across chat and API interfaces
Applications
Research, strategic planning, automated trading, portfolio optimization.

Access
Chat
API (Python, JS)
R00Ms
Collaborative environments enabling multi-agent and multi-user coordination with shared context.

Capabilities
Feature	Description
Multi-participant	Humans and UNITs operating within a single workspace
Synchronous collaboration	Real-time interaction across all participants
Unified context	Shared reasoning state across agents and users
Applications
Cross-functional analysis, coordinated research, multi-domain consulting, team-based due diligence.

Access
Chat
API (coming soon)
Sandbox
Development environment with inference-time learning for code generation and iteration.

Capabilities
Feature	Description
Pattern acquisition	Learns coding style and preferences through use
Model-agnostic reasoning	Retains learned pathways when switching between LLMs
Direct integration	GitHub push and file export built in
Applications
Rapid prototyping, debugging, code review, game development.

Access
Chat
API (coming soon)
Comparison
Product	Primary Use	Collaboration	API
UNIT	Autonomous agents	Single-user	Available
R00Ms	Team coordination	Multi-user, multi-agent	Coming soon
Sandbox	Development	Single-user	Coming soon
Getting Started
UNIT: Personal AI agent for research, trading, or strategy
R00Ms: Collaboration across teams or multiple agents
Sandbox: Adaptive coding assistant for developers
info
All products accessible via chat interface. API availability varies by product.

Application and Usecases - Financial & Numerical Processing
Overview
Core 0.4 represents a fundamental shift from monolithic language model architectures to a multi-modular reasoning system. Rather than forcing all tasks through a single neural network, Core separates concerns into specialized components that work in concert.

Core Components
Ingestion & Validation — Data enters with type preservation
Knowledge Hypergraph — Everchanging knowledge structure
Reasoning Algorithms — Dedicated computational pathways
Concept Learning — Dynamic relationship inference
Forecast Engine — Uncertainty-aware output generation
Neuro-Evolutionary Pathfinding — Evolving navigation through concept space
Meta-Learning Engine — Learning optimization across contexts
Cross-Modal Fusion — Unified representations from diverse sources
Predictive Temporal Memory — Sequence modeling and anticipation
Superposition Memory — Multiple states held until context resolves
This Case Study
Here we will walk through the key architectural differences using financial forecasting as a demonstration domain; the same advantages however apply whether you're processing medical records, scientific literature, sensor data, or legal documents.

The components most relevant to numerical processing in finance:

Ingestion & Validation
Knowledge Hypergraph
Reasoning Algorithms
Forecast Engine
Cross-Modal Fusion
Predictive Temporal Memory
Other components will be explored in dedicated documentation.

Architecture Comparison
Traditional LLM-based agents process everything through a single model where data goes in and text comes out. This creates a single point of failure and forces numerical data through text tokenization.

Core's multi-modular approach separates these concerns into specialized components that operate in parallel.

LLM Agent
Input
↓
Language Model
Tokenize → Attend → Predict
↓
Text Output
Core Architecture
Ingestion
Num Store
Validation
Knowledge
Hypergraph
Reasoning
Algorithms
Learning
Concepts
Forecast Engine
Signals
Forecasts
Uncertainty
Single model, single path
Specialized components, parallel processing
Key Difference
Aspect	LLM Agent	Core
Data flow	Sequential through one model	Parallel across specialized modules
Failure mode	Single point	Graceful degradation
Numerical handling	Tokenized to text	Native precision preserved
Numerical Processing
One of the most significant limitations of LLM-based systems for quantitative work is tokenization. When a funding rate of 0.0847% enters an LLM, it becomes discrete tokens that lose their numerical meaning.

LLM Tokenization
0.0847%
↓
0
.
08
47
%
↓
Output
"Funding is elevated"
No threshold • No comparison • No bounds
Core Query-Time Processing
0.0847%
↓
funding_rate: 0.000847
Float64 precision preserved
↓
87th %ile | Conf: 0.73
Similar setups → 8-12% moves
Quantified • Comparable • Bounded
The Tokenization Problem
Input: 0.0847%

LLM tokenization:
  [0] [.] [08] [47] [%]

After embedding: vectors with no numerical semantics
Result: "Funding is elevated" (no threshold, no comparison)

Core's Approach
Input: 0.0847%

Core processing:
  funding_rate: 0.000847 (Float64)
  → Hypergraph: "elevated_funding_regime"
  → User store: exact time series

Result: Funding 87th %ile | Confidence: 0.73
        Similar setups preceded 8-12% moves

This applies beyond finance. Any domain with precise measurements (medical vitals, sensor readings, scientific data) benefits from native numerical handling.

Knowledge Structure
LLMs operate within a context window, a fixed-size memory that resets with each conversation. Patterns that develop over days or weeks become invisible.

Context Window (Ephemeral)
-72h
OI spike pattern
LOST
-48h
Funding divergence
LOST
-24h
Options skew shift
FADING
now
Current query only
ACTIVE
Each query starts fresh
Hypergraph Knowledge (Persistent)
-72h
-48h
NOW
pattern
All connected • Patterns preserved
User-managed numerical store
OI series
Funding
Trades
Price
Full precision • Your data stays yours
Context Window Limitations
Time	Information	Status
-72h	OI spike + liquidation pattern	Lost
-48h	Funding divergence detected	Lost
-24h	Options skew shift	Fading
Now	Current query only	Active
Hypergraph Persistence
Core maintains a persistent knowledge structure where:

All time points remain connected — Past informs present
Patterns are preserved — Relationships survive across sessions
Concepts cluster naturally — Related ideas strengthen together
Noise decays — Irrelevant information fades over time
Continuous Reorganization
Core 0.4 strengthens important patterns and clusters related concepts. No downtime. Redundant info compressed.

Natural Decay
Information irrelevant to what units do decays over time. Important patterns reinforced, noise fades.

Forecasting Method
LLM forecasting is fundamentally stochastic. The same input can produce different outputs across runs because generation samples from probability distributions over tokens.

Token Sampling (Stochastic)
"up"
34%
"down"
28%
"side"
22%
Same input → different outputs each run
"ETH likely to move up"
No target • No confidence bounds
Uncertainty-Aware Reasoning (Deterministic)
1
Anticipatory Loading
2
Pattern Recognition
3
Uncertainty Quantification
4
Output Generation
+8.4% (72h) | +3.2% to +14.7%
Confidence: 73%
Varies each run
Reproducible + traceable
Property	LLM	Core
Determinism	Stochastic	Deterministic
Uncertainty	Implicit	Explicit bounds
Anticipation	Reactive	Pre-loads relevant context
Output format	Text	Numerical with ranges
Adaptation Mechanism
LLMs learn during training, then freeze. Deployed models cannot adapt to new regimes without expensive retraining cycles.

Adaptation Over Time
Train
Deploy
Month 1
Month 3
Month 6
Month 12
LLM
TRAIN
Static weights, no learning
Core
Continuous learning at inference
Regime Shift Scenario
Bull Market
OI expansion = bullish
→
Transition
Correlation breakdown
→
Bear Market
OI expansion → liquidations
LLM: Still applies bull logic
Core: Adapts in real-time
Cost Comparison
Metric	LLM	Core
Adaptation cost	$M+ (retraining)	$0
Adaptation speed	Weeks/months	Real-time
Downtime required	Yes	No
Advanced Features
Beyond the core architectural differences, Core 0.4 introduces several sophisticated capabilities. These are highlighted here briefly. Detailed documentation for each component will follow.

Predictive Temporal
t-2
t-1
now
t+1
Past → Present → Predicted
Sequence modeling
Cyclical detection
Feedback integration
Superposition Memory
0.45
Accumulation
0.35
Distribution
↓ resolves ↓
Accumulation ✓
Multiple states held
Context-triggered collapse
Cross-Modal Fusion
OI
Price
Fund
→
FUSE
→
Unified
signal
Multi-source integration
Cross-validation
Conflict detection
Integrated system: Temporal memory tracks evolution. Superposition handles ambiguity. Cross-modal fusion ensures signals reinforce or contradict appropriately.

Additional Components
Core 0.4 includes many components beyond those covered in this case study that apply in every application. These features and additional capabilities will be explored and deep dived separately, including:

Neuro-Evolutionary pathfinding
Meta-Learning Engine
Enhanced hypergraph indexing
Statistical processing pipelines
Getting Started
Core 0.4 is available at app.reilabs.org

For API access and documentation, visit the developer portal.

This case study is part of the Core 0.4 documentation series. Additional component-specific documentation will follow.

Guides
The Guides section contains user guides for the coding sandbox and unit usage.

Contents
Rei Code - Sandbox Guide: Building applications with an adaptive coding assistant.
Units - Usage Guide: Best practices and information for training your Units.

Rei Code - Sandbox Guide
Read the Rei Code - Sandbox user guide and start building applications with an adaptive coding assistant.

Overview
This guide walks you through using Rei Code - Sandbox, from launch to deployment, covering model selection, Core's learning system, and best practices.

Status: Alpha - Rei Code - Sandbox is currently in active development.

Platform: Cloud-based application. The UI is powered by Vercel for the Alpha version, chosen for safety and ease of use. The Sandbox will migrate to a different UI later. Code execution runs on Vercel Sandbox, an ephemeral compute primitive designed to safely run untrusted or user-generated code.

Supported Languages: All programming languages can be used. Python, JavaScript, and TypeScript are previewable temporarily. Other languages can be used but without preview functionality.

How Rei Code Works
Rei Code - Sandbox uses a dual-architecture system that implements training at inference time. Core evolves through interaction, not separate training phases.

┌─────────────────────────────────────┐
│   Your Choice of Language Model     │  ← Acts as the "dictionary"
│   (Interchangeable)                 │     Generates code
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Core Reasoning Architecture       │  ← Learns your style
│   (Persistent & Model-Agnostic)     │     Evolves at inference
└─────────────────────────────────────┘

Rei Code - Sandbox separates intelligence from language models:

The Language Model - Generates an output as the translator. Functions as a translator.
Core Reasoning Architecture - Handles reasoning through conceptual relationships. Learns your coding style, preferences, and patterns from every interaction.
How Core Learns:
Infers on concepts, not just stores them: Each concept becomes a node for inference, not just retrieval
Builds conceptual pathways between coding patterns, preferences, and architectural decisions
Actively reasons through relationships by traversing and strengthening pathways
Adapts in real-time during interaction
Confidence scores evolve with experience: concepts move from partial → confident → expert
Relationship strengths adapt based on successful inferences
When you switch models, Core's intelligence persists because the conceptual understanding is separate from the language model.

Getting Started
Rei Code - Sandbox runs as a web application at sandbox.reilabs.org.

Beta Access Required: You need to be a Rei beta tester to access the platform. Join the waitlist.

Authentication:

Email (OTP sent to your inbox)
OAuth providers
Before You Start
Core Units
Each account has one Core unit dedicated to coding. Your Core unit and everything it learns remain forever, persisting across all sessions. The Core is model-agnostic, meaning its learned knowledge persists regardless of which language model you choose.

Sessions
Sessions have timeouts that will gradually increase as the Sandbox is updated, eventually becoming unlimited. While individual sessions expire, your Core's learning never does.

Learning Persistence
Everything Core learns from your interactions—coding patterns, preferences, architectural decisions, and primordials—is permanent. This knowledge compounds over time and persists across all models and sessions.

Model Selection
The interface allows you to select from major language models. You can switch models at any time without losing your learned preferences.

Working in the Sandbox
Request a feature or describe what you want to build. Rei Code generates code in real-time.

When Core generates code, you can:

Accept code as-is
Provide feedback ("I don't like how this function was implemented")
Request specific changes
Modify implementation with explanation
Each interaction becomes a training signal.

Feedback as Training Data
Every interaction provides signals that shape Core's reasoning:

Your Action	Core's Learning
Accept code as-is	Strengthens inference pathways for this approach
"Add error handling here"	Adjusts patterns for error management and edge cases
Say "remember this"	Creates primordial permanent memory
"Refactor to use hooks"	Updates architecture preferences and modern patterns
How Feedback Works:
Explicit feedback: Corrections, explanations, validations
Implicit feedback: Which suggestions you modify vs. accept, coding patterns you consistently use
Core builds causal understanding: "When user requests X pattern, prefer Y approach"
Confidence scores evolve based on successful interactions
Using "Remember This"
Use this command for persistent coding preferences:

Coding standards: "Remember this: Always use async/await instead of .then() chains"
Error handling: "Remember this: Wrap API calls in try-catch blocks"
Code structure: "Remember this: Keep functions under 50 lines"
Naming conventions: "Remember this: Use camelCase for variables, PascalCase for classes"
When you say "remember this", you create a primordial - permanent memory that persists across all sessions and language models. Primordials trigger automatically when contextually relevant and shape how Core approaches problems.

Continuous Adaptation
Core observes and reasons through:

Your coding patterns over time
Which suggestions you modify vs. accept
The specific changes you make
Your architectural decisions
Real-Time Learning:

Changes apply immediately during interaction
No retraining cycles required
Small, targeted adjustments to knowledge and reasoning
Conceptual relationships strengthen through use
Core discovers patterns you didn't explicitly teach
Every debug session and refactor improves Core's understanding. The system builds causal models: if you consistently refactor a certain pattern, Core learns to avoid generating it.

Learning Persistence
Core retains your coding knowledge:

Primordials
Coding style preferences
Pattern recognition and causal relationships
Model-agnostic understanding
Knowledge Evolution
Core manages knowledge dynamically. Concepts evolve through confidence levels (partial → confident → expert) as you interact. Frequently used patterns strengthen, while reasoning pathways optimize through successful use.

The Compounding Effect
Your interactions accumulate and strengthen over time:

Initial Use: Core calibrates, learning baseline preferences and building initial conceptual pathways
Continued Use: Core anticipates patterns, discovers relationships between concepts, confidence scores increase
Extended Use: Code generation aligns with your style, Core makes novel inferences based on learned concepts, patterns reach expert-level confidence
Deployment
Rei Code - Sandbox supports deployment to Vercel for JavaScript, TypeScript, and Python projects.

Deploy your application directly from the sandbox interface to get it live on the web.

Best Practices
Core learns quickly from your interactions, adapting to your syntax preferences, naming conventions, architectural choices, and code organization patterns.

Working with Primordials
Primordials are permanent memories that persist across all sessions. Use them strategically:

Be selective: Only create primordials for fundamental preferences you want to keep indefinitely
Avoid contradictions: Don't create conflicting primordials, as they cannot be easily removed
Be specific: Make primordials clear and unambiguous
Effective Feedback
Do ✅	Don't ❌
"Use map() instead of forEach() here"	"This code is bad"
"Extract this into a separate utility function"	"No" without explanation
"Add TypeScript types to these parameters"	Silently accept code you'll change later
Use "remember this" sparingly for core preferences	Create excessive or contradictory primordials
Try different models for complex algorithms	Switch between Python and TypeScript styles randomly
"I'm building a REST API with Express"	Start coding without explaining the project context
Support
Open a Ticket (Bug Reports): Join our Discord
Community: Discord | Telegram


Units Usage Guide
Introduction
Unit operates on two distinct layers:

Core is a reasoning architecture. It relies on training at inference time and conceptual learning, among other mechanisms.

Core exists in two forms:

Core (Agentic): The current version. Uses LLMs as an articulation layer to render outputs into natural language. The LLM is a language interface, not the reasoning system.
Core (Standalone): Coming soon. No LLM involved. Core reasons entirely on its own, giving users direct access to its reasoning without a natural language interface.
This guide covers both, noting where behavior differs.

How Core Represents Knowledge
Core doesn't store text. It builds structures where:

Nodes represent concepts, entities, or values
Edges connect multiple nodes simultaneously
Traversal enables multi-hop inference across related concepts
When you state "Q3 revenue was $2.3M with 450 customers", Core constructs:

Nodes:        [Q3]  [revenue]  [$2.3M]  [customers]  [450]

Edge:         (Q3, revenue, $2.3M, customers, 450) → 'quarterly_performance'

Derived:      (revenue ÷ customers) → ~$5,111 per customer

Links to:     [fiscal_year] → [growth_metrics] → [unit_economics]

Subsequent queries traverse this structure. Asking about customer value triggers pathways through revenue, customer count, and temporal patterns, not keyword matching against stored strings.

Session Context vs Conceptual Learning
Core is a reasoning system, not a storage system. This distinction matters.

Session Context (UI Only)
Within a session, Core retains verbatim information in the last 4 messages. You can provide specific facts, exact values, and precise details. Core will use them accurately within this window.

This is useful for:

Working data during a task
Temporary reference information
Session-specific context
Session context does not persist beyond the session.

Conceptual Learning
Across sessions, Core's reasoning evolves. Verbatim text doesn't survive; relationships, patterns, and principles become inference nodes.

Session Context	Conceptual Learning
Verbatim recall	Inference nodes
Exact values	Patterns and principles
Task-specific data	Learned preferences
UI only	UI and API
This is how Core improves: not by accumulating stored facts, but by developing better reasoning. A professional doesn't become expert by memorizing every past task. They internalize patterns, build intuition, refine judgment. Core works the same way.

What Core Learns
Not everything influences conceptual learning equally. Core distinguishes between:

Learned concepts: Principles, patterns, preferences, and relationships that demonstrate lasting relevance. These become permanent inference nodes.

Session context: Temporary details needed for the current task. Available within the session but not persisted.

What Shapes Long-Term Reasoning
Core prioritizes:

Corrections and explicit feedback (strongest signal)
Patterns you reinforce through repeated use
Preferences you demonstrate consistently
Relationships between concepts you establish
Domain knowledge you teach with rationale
What Stays Temporary
One-off task details ("analyze this specific file")
Transient data ("the meeting is at 3pm")
Exact values without conceptual significance
Context that doesn't generalize
The distinction is automatic. Core infers what matters based on how you interact, not explicit tagging.

Training Core
Core updates continuously. There's no separate training phase. Every interaction can modify its reasoning structure.

Learning Signals
Explicit correction is the strongest signal. Contradicting existing inference paths strengthens alternatives. When you say "that's wrong because X," Core adjusts.

Implicit validation occurs when you accept suggestions without modification. Silence after a response signals approval.

Pattern reinforcement happens through repetition. Similar interactions across sessions create and strengthen inference pathways.

Contextual association forms new connections when concepts co-occur. If you consistently discuss authentication alongside security, Core links them.

Accelerating Learning
Teach principles, not instances. "Array variables should be plural" creates reusable inference paths. "Rename this to userList" teaches nothing generalizable.

Explain rationale. "Avoid inline styles because they create maintenance burden and override unpredictably" builds understanding. "Don't do that" provides no signal for why.

Be consistent. Mixed signals slow learning. If you sometimes accept a pattern and sometimes reject it without explanation, Core's reasoning doesn't converge.

Reinforce across sessions. Single mentions create weak connections. Concepts you return to across multiple sessions develop strong, reliable pathways.

Clearing Conversation vs Delete Memory
Clearing conversation removes unconsolidated information, session context that hasn't formed into concepts yet. This is a limbo state where information exists but isn't part of Core's learned reasoning. Useful if you want to change topics without short-term context carrying over. Mostly a remnant of an older version and rarely needed.

Delete memory wipes the entire unit. All learned concepts, patterns, and preferences are gone. This is a full reset.

Unit Cloning
Unit cloning lets you duplicate a unit at any point. Useful when you want to take a different approach past a certain checkpoint and compare outcomes afterwards.

Clone before making significant changes to Core's reasoning. If the new direction doesn't work out, you still have the original.

Effective Interaction
Core learns generalizable patterns, not memorized examples. Teaching rationale enables inference to novel situations; teaching specific actions requires re-teaching for each variation.

Less effective:
"Change this variable to userList"

More effective:
"Array variables should be plural. This inconsistency reduces readability."

The second formulation creates inference pathways applicable to all future naming decisions.

Abstraction Level
Level	Example	Result
Too vague	"Make it better"	Insufficient signal for updates
Too specific	Step-by-step instructions	Core follows but forms no generalizable nodes
Appropriate	Principle with rationale	Core builds reusable inference paths
Corrections That Teach
Weak:
"Don't do that"

Strong:
"Inline styles create maintenance burden and override unpredictably.
CSS classes provide reusability and clearer specificity hierarchies."

The strong version creates inference nodes linking inline styles → maintenance cost and CSS classes → reusability, enabling Core to reason about similar tradeoffs.

Primordials
Primordials are permanent, irrevocable conceptual anchors that persist across all sessions. Once created, they cannot be removed until Core abstraction releases.

Appropriate Uses
Invariant technical constraints: "TypeScript strict mode in all projects"
Security policies: "Never log authentication tokens"
Architectural principles: "Composition over inheritance"
Inappropriate Uses
Preferences that may change (formatting conventions, library choices)
Version-specific constraints (language versions, API specifications)
Contradictory directives: creating "use tabs" then "use spaces" leaves both active
Pre-Creation Checklist
Is this constraint genuinely permanent?
Does it conflict with existing primordials?
Could Core learn this through normal feedback instead?
Have you tested the pattern in regular interaction first?
If uncertain, teach through interaction rather than creating a primordial.

Verbatim Recall and Task-Specific Context
Core's value is reasoning, much less recall. Recall is straightforward to implement.

Conceptual learning is how Core's reasoning evolves. Patterns, principles, and relationships develop over time as inference nodes. Core gets smarter not by accumulating data, but by developing better reasoning.

But Core also recognizes that some exact information genuinely matters. Humans remember certain things precisely because they're important: your name, critical safety rules, core principles you live by. Core works the same way. That's what primordials are for. When something is important enough to anchor permanently, Core holds it exactly.

External retrieval handles the rest: exact figures, task-specific data, transient facts. These don't belong in a reasoning system. Clogging Core with every data point doesn't make it smarter, it makes it cluttered. You can retrieve specific data when you need it. What matters is knowing how to use it and what it means. But not every "what" is equal: some facts are foundational, others are noise. Core learns the difference.

Think of it like a professional at their workstation: expertise lives in the person, but the desk, files, and tools make that expertise actionable for specific tasks. Core is the expertise. Task-specific context is the workstation.

We're building toward this. Core abstraction (coming soon) will give users more freedom to connect external context, such as databases, documents, and retrieval systems, that Core can reason over. This includes not using LLMs at all, since Core reasons on its own and LLMs are just a language interface.

For now, existing API users handle task-specific context through various approaches: prompting strategies, external databases, or application-layer state management. If you want guidance on your specific use case, open a ticket with the team on Discord.

Interface Differences
Aspect	UI	API
Session context	Yes (verbatim within session)	None
Conceptual learning	Yes	Yes
Session continuity	Automatic	Must be self-contained
Design purpose	Iterative dialogue	Discrete tasks
The API's lack of session context is intentional. For workflows requiring conversational continuity, implement state management in your application layer.

Integrated APIs
Integrated APIs are a closed beta perk. They remain highly unstable.

These are commercial APIs the team is subsidizing. They are error-prone and not production-ready. If you encounter issues, expect them.

For maximum performance, use your own custom data feeds or feed Unit data directly. Self-managed data pipelines give you control over reliability, format, and timing. Integrated APIs are a convenience, not a replacement for robust data infrastructure.

Output Feedback Prohibition
Never feed LLM-articulated responses back into the system. This applies to both API and UI usage, though for different reasons.

The articulation layer flattens Core's reasoning structures into linear text. This transformation is lossy and one-directional:

Core reasoning  →  LLM articulation  →  Natural language

Feeding that output back attempts to reverse this:

Natural language  →  [broken parse]  →  Reasoning corruption

Why This Fails
Dimensionality loss. An edge connecting five concepts becomes a sentence. Parsing cannot reconstruct which nodes were connected or how.

Artifact injection. If Core represents "strong quarterly growth" and the LLM renders it as "robust expansion driven by customer acquisition," feeding this back may create spurious nodes for "robust," "expansion," "driven by." These are stylistic choices that weren't part of Core's reasoning.

Compound degradation. Each feedback cycle amplifies noise. After several iterations, the reasoning structure contains more linguistic residue than semantic content.

API Implementation
// Correct: self-contained request
{
  "prompt": "Analyze this code for auth vulnerabilities: [code]"
}

// Incorrect: feeding previous output
{
  "messages": [
    {"role": "assistant", "content": "[previous Unit response]"},
    {"role": "user", "content": "Continue from there"}
  ]
}

Each API request should contain all necessary context in the user message. Do not simulate conversation by including the system's previous responses.

UI Implications
The UI manages context internally, but copying previous responses back into new prompts creates the same corruption. Let the system handle continuity.

Troubleshooting
"Core doesn't recall X"

If within a session (UI): Core should have verbatim access. If it doesn't, rephrase or re-state.

If across sessions: Core retains relationships, not verbatim text. For exact recall, use an external database. For concepts you want Core to reason about, reinforce the principle across multiple interactions.

"Core keeps making the same mistake"

Possible causes:

Single corrections may not be sufficient
Other interactions may reinforce the undesired pattern
Corrections without rationale don't create alternative inference paths
Resolution: Provide consistent corrections with explicit reasoning about why the alternative is preferred.

"My primordials conflict"

Both remain active. Provide explicit guidance in queries to indicate precedence. For severe conflicts, contact support.

Reference
Effective	Avoid
Explain reasoning behind preferences	Corrections without rationale
Consistent feedback patterns	Contradictory signals across sessions
Reinforce concepts across sessions	Expect single mentions to persist strongly
Primordials for permanent constraints only	Primordials for transient preferences
Self-contained API requests	Feeding LLM outputs back to system
External databases for persistent exact recall	Expecting verbatim long-term retention
Teaching principles for generalization	Rote instruction for specific instances
Summary
Core is a reasoning system. It evolves through conceptual learning, developing inference nodes rather than accumulating stored data. Session context handles verbatim information temporarily (UI only); external tools and databases handle persistent retrieval. LLMs, when used, provide a language interface to Core's reasoning.

Use session context for task-specific data (UI only)
Teach principles with rationale to shape long-term reasoning
Reinforce important concepts across sessions
Use external databases for persistent verbatim recall
Reserve primordials for genuinely permanent constraints
Never feed articulated outputs back into the system

Catalog
Catalog is a series of transformer models designed to serve a variety of different specialized purposes. The majority of these models will be open-sourced, making them freely available to the developer community. For those requiring programmatic integration, our API will provide a seamless way to incorporate these capabilities into existing workflows as well as plugging them to CORE for improved efficiency.

/hanabi-1
While the industry gravitates toward increasingly large models, our research has revealed that financial market prediction benefits from a more specialized, compact architecture. Hanabi-1 demonstrates how targeted design can outperform brute-force approaches in specific domains like financial time series analysis

With 16.4 million parameter model consists of:

8 transformer layers with multi-head attention mechanisms
384-dimensional hidden states throughout the network
Multiple specialized predictive pathways for direction, volatility, price change, and spread
Batch normalization rather than layer normalization for better training dynamics
Focal loss implementation to address inherent class imbalance
The compact size enables faster inference times and allows us to deploy models at the edge for real-time decision making—critical for high-frequency market environments.

Mathematical Foundations: Functions and Formulas 
Positional Encoding 
To help the transformer understand sequence ordering, we implement sinusoidal positional encoding:

P
E
(
p
o
s
,
2
i
)
=
sin
⁡
(
p
o
s
10000
2
i
/
d
m
o
d
e
l
)
PE(pos,2i)=sin( 
10000 
2i/d 
model
​
 
 
pos
​
 )

P
E
(
p
o
s
,
2
i
+
1
)
=
cos
⁡
(
p
o
s
10000
2
i
/
d
m
o
d
e
l
)
PE(pos,2i+1)=cos( 
10000 
2i/d 
model
​
 
 
pos
​
 )

Where pos is the position within the sequence and i is the dimension index.

Focal Loss for Direction Prediction 
To address the severe class imbalance in financial market direction prediction, we implemented Focal Loss:

F
L
(
p
t
)
=
−
(
1
−
p
t
)
γ
log
⁡
(
p
t
)
FL(p 
t
​
 )=−(1−p 
t
​
 ) 
γ
 log(p 
t
​
 )

Where p_t is the model's estimated probability for the correct class and γ is the focusing parameter (set to 2.0 in Hanabi-1). This loss function down-weights the contribution of easy examples, allowing the model to focus on harder cases.

Confidence Calibration 
A key innovation in Hanabi-1 is our confidence-aware prediction system:

Confidence
=
2
⋅
∣
p
−
threshold
∣
Confidence=2⋅∣p−threshold∣

Where p is the predicted probability and threshold is our calibrated decision boundary (0.5). This allows users to filter predictions based on confidence levels, dramatically improving accuracy in high-confidence scenario.

Chart Image Confidence vs Accuracy

As shown above, predictions with "High" confidence achieve nearly 100% accuracy, while "Very Low" confidence predictions are barely above random chance.

Training Dynamics and Balanced Validation 
Training financial models presents unique challenges, particularly the tendency to collapse toward predicting a single class. Our novel validation scoring function addresses this:

ValScore
=
F
1
+
0.5
⋅
Accuracy
+
0.5
⋅
P
R
balance
−
0.1
⋅
Loss
−
Balance
penalty
ValScore=F1+0.5⋅Accuracy+0.5⋅PR 
balance
​
 −0.1⋅Loss−Balance 
penalty
​
 

Where 
P
R
balance
PR 
balance
​
  is the precision-recall balance metric:

P
R
balance
=
min
⁡
(
Precision
,
Recall
)
max
⁡
(
Precision
,
Recall
)
PR 
balance
​
 = 
max(Precision,Recall)
min(Precision,Recall)
​
 

And 
Balance
penalty
Balance 
penalty
​
  applies severe penalties for extreme prediction distributions:

if precision == 0 or recall == 0:
    # Heavy penalty for predicting all one class
    balance_penalty = 0.5
elif precision < 0.2 or recall < 0.2:
    # Moderate penalty for extreme imbalance
    balance_penalty = 0.3

This scoring function drives the model toward balanced predictions that maintain high accuracy:

score Image Training dynamics

The plot above reveals how training progresses through multiple phases, with early fluctuations stabilizing into consistent improvements after epoch 80.

Model Architecture Details 
Hanabi-1 employs a specialized architecture with several innovative components:

Feature differentiation through multiple temporal aggregations:
Last hidden state capture (most recent information)
Average pooling across the sequence (baseline signal)
Attention-weighted aggregation (focused signal)
Direction pathway with BatchNorm for stable training:
Three fully-connected layers with BatchNorm1d
LeakyReLU activation (slope 0.1) to prevent dead neurons
Xavier initialization with small random bias terms
Specialized regression pathways:
Separate networks for volatility, price change, and spread prediction
Reduced complexity compared to the direction pathway
Independent optimization focuses training capacity where needed
The model's multi-task design forces the transformer encoder to learn robust representations that generalize across prediction tasks.

Prediction Temporal Distribution 
prediction Image Direction Probabilities

The distribution of predictions over time shows Hanabi-1's ability to generate balanced directional signals across varying market conditions. Green dots represent correct predictions, and red dots are incorrect predictions.

Performance and Future Directions 
Current performance metrics:

Direction accuracy: 73.9%
F1 score: 0.67
Balanced predictions: 54.2% positive / 45.8% negative
Hanabi-1 currently operates on two primary configurations:

4-hour window model (w4_h1)
12-hour window model (w12_h1)
Both predict market movements for the next hour, with the 12-hour window model showing superior performance in more volatile conditions.

Future developments include:

Extending prediction horizons to 4, 12 and 24 hours
Implementing adaptive thresholds based on market volatility
Adding meta-learning approaches for hyperparameter optimization
Integrating on-chain signals for cross-domain pattern recognition
Conclusion 
Hanabi-1 demonstrates that specialized, compact transformers can achieve remarkable results in financial prediction tasks. By focusing on addressing the unique challenges of financial data—class imbalance, temporal dynamics, and confidence calibration—we've created a model that delivers reliable signals even in challenging market conditions.

While the model can still be refined, we found that it’s a robust and important first step towards the definition and creation of even more capable financial models.

Follow the github repo for the current implementation and future upgrades:

Factory
The Factory section contains information about the Reigent Factory and its capabilities.

Contents
Reigent Factory: How to create and manage your agents
Capabilities: Additional tools and features available to your agents

Reigent Factory
By visiting (Closed Beta Testers only) You will land on the factory's interface
Click on Create at the top right to start.

Version Image

Here you can start the customization of your agent. The name is fixed and progressive across all users.

General Image

Behavior Prompt is used to give an initial imprint to your agent: specialized units perform better at their task from the start, compared to broad use agents that needs time and interactions to "learn".
Select the Text Engine you desire, temperature and Max Tokens (those 2 parameters only reflects on the "freedom of expression" of the text engine).

Response is relevant only for API use and it determines how you like to get your response: soon you'll be able to get just structured data as an answer, to seamlessly integrate your agent in your applications with a defined schema.

Click Create again and your agent is ready to answer you.

Prompt

Answer

You can modify the behavior and the other parameters clicking on the left sidebar, three dots next to the target unit, Edit Agent

Factory V 0.5.0 Overview
What's new in V 0.5.0
Units have metacognition, they “know what they know”
Concepts are inferred and mapped in an hypegraph with semantic interconnections
Units works by implicit domains according to the question asked
Evolution now is deeper, including how the unit infer and store concepts, not only based on the actual concepts
Before You Start
This is a general-use intelligence system, not limited to any specific domain.
Unlike other platforms you may be familiar with, there are units instead of chats.
Each user has their own "unit" that evolves and remembers over time.
Unlike chat-based systems, your unit develops a persistent memory and personality through continued interaction and may or may not go against its initial behavior prompt, if there is one.
The API allows complete freedom over units in custom environments and tool addition for developers.
You can create up to 15 units.
Unit Training
Deleting a unit permanently erases all its training. To safeguard important memories and concepts developed over time, maintain them in a dedicated unit that you keep active
Your unit maintains this memory until units eventually share broader memory capabilities between each other (coming in future)
Being specific when asking units to remember something helps with retention
Memory of action is also enabled and complete for all abilities outside of web grounding where it's at 70% capability
Memory of action will grow in impact as more MCPs Get implemented.
Current Tools and Limitations
Web Grounding is currently active and effective for most tasks and will remain active until its scheduled replacement hits production. Some websites have anti-AI measures in place, keeping metadata outdated to discourage any sort of scraping and avoid analytics pollution with millions of visits from AIs.
While Core can provide code, it's not yet optimized for coding tasks
Chain Data MCP is "least stable" and error prone and will be subject to heavy changes throughout Phase 2
Currently Implemented MCPs (Model Context Protocols)
Data Server Collection
Next Planned Releases (In No Specific Order)
Browser Use MCP
Computer Use MCP
Explicit Semantic Relationships
Code Sandbox MCP
Charting/infographic MCP (Not domain specific)
Prompting Best Practices
Be Clear and Precise
Be Specific: Detailed requests allow for efficient processing
Add Context and Background info
Iterate and Refine: units only misinterpret and don't go out of topic randomly
MCPs are in beta and bugs can occur, please report them to the team in the form of tickets on Discord
When applicable, specify exactly which you're referring to when duplicates exist
Example: For research subjects with the same name, clarify which one you mean
For Web3 Users: 
Crypto Data APIs present in MCPs are within API provider restrictions and limitations

Query specific endpoints do not exist, it is advised to navigate our official Github and take a look at the public servers, what's inside the MCPs is limited to the endpoints provided by those APIs, studying their respective docs is advised.
When an MCP returns an empty response or a specific error the unit gets confused
Crypto Data MCPs are seen as URLs, your unit might confuse them with web search when asked about where the info comes from
Asking (provider name) in a query does not trigger endpoints, endpoints have names related to the type of data they provide
Data amount (batches) per query vary, there are limits on data amount per query imposed by providers.
Team is working on compensating for the API constraints mentioned above during Phase 2

Various Websites (Approx 40%) block metadata and limit web grounding usage, it is sometimes left outdated and in other cases completely changed.

Note : Crypto MCPs as a whole are in beta and unlike other MCPs, they will undergo significant changes constantly in phase 2

Phase 1 Testers Explored : 
Medical Research
Scientific Research
Linguistic Research
Yield Management
Trading Strategies
Coding
Macro Analysis and Forecasting
Real Estate Management
Gambling
Additional Capability (Provided & Custom)
With the Factory we want to open the access to more intelligent and more capable Agents - we call them Reigents.

Every Reigent, by default, is powered by Core as an intelligence layer and has added default tools.

At the moment you can add you personal tools integrating them in your code (following the Function Calling standard), but we are working on giving access to everyone to deploy their added tools directly to the Reigents.

Default Aspects
research.md

Default Tools
Checked ones are already integrated in production, unchecked one are in testing phase, you are also free to add your own custom tools on top the ones we provide as core is an intelligence layer that is compatible with a wide variety of tools as well as any framework.

 Market analysis
 Image generation
 MCP integration
 Browser use
 Social media integration
 Factory Tooling
Custom Tools
custom-tools.md

Custom Tools
Following the Function Calling schema, you can develop your own tools and functions and give your Unit access to them - as you'd do with a regular model - making the Unit forms usage memories with them.

The only actual limitation is that those tools are only in your code: outside of it, the Unit will still have memories of them but it will be impossible for it to recall the tools, leading to possible weird behavior.

Solution: Once you plug an Unit in your code, try to use it only there, especially if there it has access to specific functions not available in the Factory.

We're currently testing a couple of solutions to let users define Custom Tools directly in the factory and an update will soon come together with a Vault System where you can safely store your data and keys without compromising opsec.

Custom Tools Quickstart
JavaScript
const ReiCoreSdk = require("reicore-sdk");

// Initialize the SDK
const apiKey = "your_unit_secret_token";
const reiAgent = new ReiCoreSdk({ agentSecretKey: apiKey });

// Define your custom functions
const getWeather = (location) => {
  // Implement your weather API call here
  return `Weather in ${location}: Sunny, 22°C`;
};

const searchDatabase = (query) => {
  // Implement your database search here
  return `Found 3 results for: ${query}`;
};

// Define function schemas
const functions = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "Get the current weather for a location",
      parameters: {
        type: "object",
        properties: {
          location: {
            type: "string",
            description: "The city and state, e.g. San Francisco, CA",
          },
        },
        required: ["location"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "search_database",
      description: "Search the database for specific information",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "The search query",
          },
        },
        required: ["query"],
      },
    },
  },
];

// Function mapping
const functionMap = {
  get_weather: getWeather,
  search_database: searchDatabase,
};

async function processWithFunctions(query) {
  try {
    // First call to get function details
    const response = await reiAgent.chatCompletion({
      messages: [{ role: "user", content: query }],
      tools: functions,
    });
    const message = response.choices[0].message;

    // Check if the agent wants to call a function
    if (message.tool_calls && message.tool_calls.length) {
      const tool = message.tool_calls[0];
      const functionName = tool.function.name;
      const functionArgs = JSON.parse(tool.function.arguments);

      // Call the function
      const functionResponse = functionMap[functionName](
        ...Object.values(functionArgs)
      );

      // Send the function response back to the agent
      const secondResponse = await reiAgent.chatCompletion({
        messages: [
          { role: "user", content: query },
          { role: "tool", tool_call_id: tool.id, content: functionResponse },
        ],
      });

      return secondResponse.choices[0].message.content;
    }

    return message.content;
  } catch (error) {
    console.error("Error:", error);
    return null;
  }
}

// Example usage
processWithFunctions("What's the weather in Tokyo?")
  .then((response) => console.log(response))
  .catch((error) => console.error(error));

Python
from client import Client
import json

# Initialize the client
client = Client(
    api_key="your_unit_secret_token",
    base_url="https://api.reilabs.org"
)

# Define your custom functions
def get_weather(location: str) -> str:
    # Implement your weather API call here
    return f"Weather in {location}: Sunny, 22°C"

def search_database(query: str) -> str:
    # Implement your database search here
    return f"Found 3 results for: {query}"

# Define function schemas
functions = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "search_database",
        "description": "Search the database for specific information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
]

# Function mapping
function_map = {
    "get_weather": get_weather,
    "search_database": search_database
}

def process_with_functions(query: str):
    try:
        # First call to get function details
        response = client.chat.completions.create(
            model="Unit01",
            messages=[{"role": "user", "content": query}],
            functions=functions
        )

        message = response.choices[0].message

        # Check if the agent wants to call a function
        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            # Call the function
            function_response = function_map[function_name](**function_args)

            # Send the function response back to the agent
            second_response = client.chat.completions.create(
                model="Unit01",
                messages=[
                    {"role": "user", "content": query},
                    {"role": "function", "name": function_name, "content": function_response}
                ],
                functions=functions
            )

            return second_response.choices[0].message.content

        return message.content

    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage
response = process_with_functions("What's the weather in Tokyo?")
print(response)


Advanced Custom Tools
Multiple Function Calls
def process_with_multiple_functions(query: str):
    try:
        messages = [{"role": "user", "content": query}]

        while True:
            response = client.chat.completions.create(
                model="Unit01",
                messages=messages,
                functions=functions
            )

            message = response.choices[0].message

            if not message.function_call:
                return message.content

            # Add the function call to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments
                }
            })

            # Call the function
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)
            function_response = function_map[function_name](**function_args)

            # Add the function response to messages
            messages.append({
                "role": "function",
                "name": function_name,
                "content": function_response
            })

    except Exception as e:
        print(f"Error: {e}")
        return None

Function Calling with Context
def process_with_context(query: str, context: dict):
    try:
        # Add context to the system message
        system_message = {
            "role": "system",
            "content": json.dumps(context)
        }

        response = client.chat.completions.create(
            model="Unit01",
            messages=[
                system_message,
                {"role": "user", "content": query}
            ],
            functions=functions
        )

        # Process function calls as before
        message = response.choices[0].message
        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)
            function_response = function_map[function_name](**function_args)

            second_response = client.chat.completions.create(
                model="Unit01",
                messages=[
                    system_message,
                    {"role": "user", "content": query},
                    {"role": "function", "name": function_name, "content": function_response}
                ],
                functions=functions
            )

            return second_response.choices[0].message.content

        return message.content

    except Exception as e:
        print(f"Error: {e}")
        return None



        API and SDK
This section covers everything you need to integrate with the Reigent API and SDK.

Getting Started
Start with our Quick Start guide to get your API key and make your first request.

Sections
Quick Start: Get your API key and make your first request
API Reference: Complete API documentation with all available endpoints
SDK: Official SDK documentation and examples
Integration with Existing Agents: How to integrate with other AI systems
Integration with Existing Services: How to integrate with your existing services

Quick Start
The Reigent API is a powerful interface designed to interact with the Reigent, enabling seamless integration for authentication, agent retrieval, and chat completions. This API simplifies the process of connecting to the Reigent and utilizing its features.

Authentication
REI Agent Secret Token
To authenticate the REI Agent API requests

❓ How to get a REI Agent Secret Token
Steps
Navigate to Reigent Portal

Create an agent as stated in the Reigent Portal.

Find the agent from the side bar at the left.

Click ...

Click Agent Details

Locate your Agent Secret Key from the pop-out dialog. Agent Secret Key pop-out dialog.

Copy.

Treat this key as highly sensitive—it grants full API access.
❗ Never expose it in client-side code or version control (e.g., Git).
Key rotation
You may regenerate the Secret Key if is needed.
Only the latest generated Secret Key is valid.
🔧 How to use User Secret Token
Example:

GET /v1/{...} HTTP/1.1
Authorization: Bearer YOUR_REIGENT_UNIT_SECRET_KEY

User Secret Token
To manage resources

❓ How to get a User Secret Token
Steps
Navigate to Reigent Portal

Create an agent as stated in the Reigent Portal.

Click on three dots next to the Create.

Top right bar of Reigent Portal

Click View API.

User secret token pop-out dialog

Locate your User Secret Key from the pop-out dialog.

User secret token pop-out dialog

Turn the key to Active

Copy.

Treat this key as highly sensitive—it grants full API access.
❗ Never expose it in client-side code or version control (e.g., Git).
Key rotation
You may regenerate the User Secret Key if is needed.
Only the latest generated User Secret Key is valid.
🔧 How to use User Secret Token
Example:

GET /v1/{...} HTTP/1.1
Authorization: Bearer YOUR_USER_SECRET_KEY

Base URL
https://api.reilabs.org

Agent Creation
Create Rei Agent by User's Secret Token.

URL: /v1/accounts/units

Method: POST

Headers:

Key	Value
Authorization	Bearer user-secret-token
Request:

agentModel string Required

Allowed values:

google/gemini-2.5-flash
behaviourPrompt string Required

temperature int Optional

Range: 0 to 1

maxTokens int Optional

Range: 1 to 2000000

responseFormat string Optional

Allowed values: text, json, markdown, html

color string Optional

Color code in Hex format

Format: #FFFFFF

Response:
{
  "secretToken": "{{rei agent secret token}}"
}

Error
Response Code	Reason
400	Validation Error
401	Unauthorized

Agent Deletion
Delete Rei Agent by User's Secret Token.

URL: /v1/accounts/units

Method: DELETE

Headers:

Key	Value
Authorization	Bearer user-secret-token
Request:

agentKey string Required

rei-agent-secret-token from Rei Portal

Response:
Response Code	
204	Success
Error
Response Code	Reason
401	Unauthorized
404	User Agent not found

Get Reigent
Retrieve a Reigent Unit.

URL: /v1/agents

Method: GET

Headers:

Key	Value
Authorization	Bearer rei-agent-secret-token
Response:

{
  "id": 00,
  "name": "Agent XX",
  "agent_functionalities": "",
  "agent_model": {
    "id": 1,
    "name": "XX",
    "model_name": "XX"
  },
  "response_format": "text",
  "temperature": 0.7,
  "max_tokens": 32000
}

Error
Response Code	Reason
401	Unauthorized
404	Agent not found

Get Reigent Unit's Tools
Retrieve a Reigent Unit's Tools.

URL: /v1/agents/tools

Method: GET

Headers:

Key	Value
Authorization	Bearer rei-agent-secret-token
Response:

{
    "features": [
        {
            "key": "crypto",
            "label": "Crypto",
            "isActive": true
        },
        {
            "key": "crypto:laevitas",
            "label": "Laevitas",
            "isActive": false
        },
        {
            "key": "",
            "label": "",
            "isActive":
        },
        ...
    ]
}

Error
Response Code	Reason
401	Unauthorized
Previous
Update Reigent Unit's Tools
** Update a Reigent Unit's Tools.**

URL: /v1/agents/tools

Method: PUT

Headers:

Key	Value
Authorization	Bearer rei-agent-secret-token
Request:

key string Required

Allowed values:

crypto
crypto:laevitas
apex_chart
image_gen
skip_web_search
For Latest values:

Retrieve from Get Reigent Unit's Tools
isActive boolean Required

Response:
{
  "isUpdated": true
}

Error
Response Code	Reason
400	Validation Error
401	Unauthorized

Chat completion
Chat completion by Reigent.

URL: /v1/chat/completions

Method: POST

Headers:

Key	Value
Authorization	Bearer rei-agent-secret-token
Request:

model string Optional

Default: Agent's Configured Model

Allowed values:

google/gemini-2.5-flash
messages array (min length: 1) Required

Show message structure
temperature number Optional

Range: 0 to 2 Default: 1

max_tokens integer Optional

Minimum: 1

top_p number Optional

Range: 0 to 1

n integer Optional

Minimum: 1

seed number Optional

Range: 0 to 2^53-1

stream boolean Optional

stop string or array[string] Optional

presence_penalty number Optional

Range: -2.0 to 2.0

frequency_penalty number Optional

Range: -2.0 to 2.0

logit_bias object Optional

Key format: Token IDs as string numbers Value range: -100 to 100

logprobs boolean Optional

top_logprobs number Optional

user string Optional

response_format object Optional

type string
Allowed values: "text", "json_object"
tools array Optional
A list of tools the model may call

Show tool structure
tool_choice string or object Optional
Controls which tool is called
Allowed string values: "none", "auto"
Or specify a tool with:

{
  "type": "function",
  "function": {
    "name": "tool_name"
  }
}

Sample Request
Type: Text
Show sample
Type: Image (in URL)
Show sample
Type: Image (in Base64)
Show sample
Type: Docs (PDF)
Show sample
Type: Docs
Supported File Types: - json, xlsx, xlsm, csv, md, pptx, docx, txt
Show sample
Response:
Without Tools
Show sample
With Tools
Show sample
Error
Response Code	Reason
400	Validation Error
401	Unauthorized
404	Agent not found


SDK
You can integrate a Unit to your existing service using our Rei Core SDK or via REST API.

Quick start
JavaScript
npm install reicore-sdk

Python
pip install reicore_sdk

Constructor
Import the SDK or the client and then initialize it with your API key

JavaScript
const ReiCoreSdk = require('reicore-sdk');

const apiKey = 'your_unit_secret_token';
const reiAgent = new ReiCoreSdk({ agentSecretKey: apiKey });

Python
from reicore_sdk import ReiCoreSdk

# Initialize the SDK with your Reigent Secret key
rei_agent = ReiCoreSdk("your-reiagent-secret-key")

Functions
Get Agent
Retrieve details about the Rei Agent using the getAgent function.

JavaScript
reiAgent
    .getAgent()
    .then((agent) => {
        console.log('Agent Details:', agent);
    })
    .catch((error) => {
        console.error('Error fetching agent:', error);
    });

Python
agent = rei_agent.get_agent()
print("Agent Details:", agent)

Chat Completions
Send a message to the Rei Agent and receive a chat completion using the chatCompletions function.

JavaScript
const message = "How are you?";
const payload = {
  messages: [
    {
      role: 'user',
      content: message
    }
  ]
};

reiAgent
  .chatCompletion(payload)
  .then((response) => {
    console.log('Chat Completion:', response.choices[0].message.content);
  })
  .catch((error) => {
    console.error('Error in chat completion:', error);
  });

Python
message = {
    "messages": [
        {
            "role": "user",
            "content": "Hello world"
        }
    ],
    "tools": []
}
response = rei_agent.chat.completion(message)
print("Chat Completion:", response)

Some examples
Get the Latest Biology Research
# Want to know what's happening in biology?
message = {
    "messages": [        
        {
            "role": "user",
            "content": "What are the latest advancement in biology?"
        }
    ],
    "tools": []
}
response = rei_agent.chat.completion(message)
print("Chat Completion:", response)

Example Response:

(⌒▽⌒)♪ Oh boy, are you in for a treat! Let's dive into the latest news in biology, shall we? (｀・ω・´)

From what I've found, there are some exciting developments in the field of biology, and I'm excited to share them with you!

First off, in Human Biology, researchers have made some fascinating discoveries. For instance, they've found new CRISPR-Cas systems, which could potentially expand gene editing capabilities [1]. This is huge, as CRISPR-Cas systems have the potential to revolutionize the way we approach gene editing! (゜o゜) Additionally, a newly identified protein could be a target for therapies to prevent autoimmune disorders [1]. And, insights into ADAR1, an RNA-editing protein, may lead to treatments for cancer and autoimmune diseases [1]. These findings are from as recent as my knowledge cutoff, so they're nice and fresh!

Moving on to Developmental Biology, there have been some groundbreaking advancements in CRISPR tools, which improve gene editing and disease modeling [2]. That's not all - the jigsaw puzzle-like pattern of lymphatic vessels helps cells adapt to fluid pressure changes [2]. Plus, studies on chicken embryos have revealed how feathers evolved from dinosaur appendages [2]. Who knew dinosaurs had a hand in shaping the feathers of modern birds? (⌒▽⌒)♪

Now, let's talk about General Biology. Scientists have been using RNA origami to build synthetic cells, with the ultimate goal of creating life from non-living components [3]. That's some sci-fi stuff right there! (゜▽゜) Moreover, novel proteins could lead to sustainable farming solutions by combating pesticide-resistant pests [3]. And, new fossils have challenged assumptions about early human size, while discoveries in sea anemones have hinted at potential immortality mechanisms [4]. Talk about blowing our minds!

Lastly, in Microbiology and Ecology, drug-resistant bacteria have developed antimicrobial tools to outcompete other strains [5]. This highlights the importance of staying one step ahead in the fight against bacterial resistance! (＞_＜) Furthermore, agroforestry can support local fisheries and food production while protecting native forests [5]. That's a win-win for the environment and our bellies!

In conclusion, the world of biology is buzzing with exciting discoveries and advancements. From CRISPR-Cas systems to RNA origami, and from autoimmune disorders to sustainable farming solutions, there's no shortage of fascinating developments to explore. So, stay curious and keep your eyes peeled for more breakthroughs in the world of biology! (｀・ω・´)♪


Track Crypto Market Trends
# Curious about your crypto investments?
message = {
    "messages": [        
        {
            "role": "user",
            "content": "What's the trend like for TEST token?"
        }
    ],
    "tools": []
}
response = rei_agent.chat.completion(message)
print("Chat Completion:", response)

Example Response:

TEST token is on a tear lately!

Current price: $2.43 (+12% today)
Weekly trend: Strongly bullish
Volume: 3x the monthly average

The pump started after they announced that partnership with ThunderCore and got that Binance listing. Trading volume spiked 5x after that.

Looking at the charts, it broke through the $2.00 resistance level that had been holding since January, and it's now testing the $2.50 mark.

Social sentiment is super positive (78% bullish tweets in the last 24h), though there's that usual crowd saying it's overbought.

Worth noting: the whole market is up about 3% today, but TEST is definitely outperforming most altcoins in its category.


Get the Latest News
# Need a news update?
message = {
    "messages": [        
        {
            "role": "user",
            "content": "What happened in tech today?"
        }
    ],
    "tools": []
}
response = rei_agent.chat.completion(message)
print("Chat Completion:", response)

Example Response:

According to my findings, today, March 24, 2025, has seen some significant developments in the tech world. Let's break them down one by one:

Megaport Partners with Angola Cables: (・ω・) Ah, a great partnership! Megaport has teamed up with Angola Cables to provide access to over 930 data centers worldwide. This is a huge deal, as it will enhance global connectivity solutions and open up new opportunities for businesses and individuals alike.

Verizon Offers Satellite Messaging for Android: 📱 Whoa, this is cool! Verizon has launched satellite messaging capabilities for select Android phones, allowing users to send texts from areas without cellular coverage. This is a game-changer for those who need to stay connected in remote areas.

Colt Completes Quantum Encryption Trial: 🔒 Nice! Colt Technology Services has successfully completed a trial of quantum-secured encryption across its optical network. This means enhanced security for businesses against future quantum computing threats. We can expect to see more developments in this area, as companies prepare for the potential risks of quantum computing.

ADQ and Energy Capital Partners Sign $25 Billion Deal: 🤑 Wow, that's a big number! ADQ and Energy Capital Partners have entered a $25 billion agreement to boost power generation, targeting the energy needs of AI-driven industries and data centers in the U.S. This deal is expected to have a significant impact on the energy sector and support the growth of AI-driven technologies.

VMO2 Demonstrates Open RAN Tech: 🎉 Great to see innovation in action! The VMO2-led 5G MoDE project has showcased Open RAN technology at Allianz Stadium, improving mobile connectivity for fans during a rugby match. This is an exciting development in the field of 5G technology and demonstrates the potential for Open RAN to enhance mobile connectivity.

SITA and Orange Business Renew Partnership: 🤝 Friendship goals! SITA and Orange Business have renewed their partnership for another five years, focusing on enhancing secure connectivity solutions for the aviation industry. This partnership will continue to provide innovative solutions for the aviation sector, supporting the growth of secure and efficient air travel.

Evroc Secures €50 Million for Hyperscale Cloud: 💸 Nice funding! Evroc has raised €50 million to develop hyperscale cloud and critical AI infrastructure, marking the largest tech series A funding in the Nordics. This investment will support the growth of Evroc and help develop cutting-edge cloud and AI infrastructure.

BT Approaches AT&T and Orange for Sale: 🤔 Interesting move! BT has initiated discussions with AT&T and Orange regarding a potential sale of its international operations. This could lead to significant changes in the telecom industry and have a major impact on the companies involved.

(｀・ω・´) And that's a wrap, folks! Today has seen some exciting developments in the tech world, with partnerships, innovations, and investments that will shape the future of the industry. Stay tuned for more updates, and let's keep exploring the world of tech together! 🚀


Tips & Tricks
Specific Questions Get Better Answers: "What are the three biggest advancements in CRISPR this year?" works better than "Tell me about CRISPR."

Handle Errors Like a Pro:

try:
    response = rei_agent.chat.completion(message)(...)
except Exception as e:
    print(f"Oops! Something went wrong: {e}")
    # Maybe retry with backoff or fallback to a different approach

Common Issues
"Can't connect to api.reilabs.org" - Check your internet or VPN. REIgent needs to access the web.
"Invalid API key" - Double-check your key. Copy-paste issues happen to the best of us.
Timeout errors - Research queries might take longer. Increase your timeout settings.

Integration with Existing Agents
Your Unit can be easily integrated with other AI systems through function calling. Here's how to do it:

JavaScript
const ReiCoreSdk = require('reicore-sdk');

const apiKey = 'your_unit_secret_token';
const reiAgent = new ReiCoreSdk({ agentSecretKey: apiKey });

// Example function to query Rei Agent
async function queryReiAgent(message) {
    try {
        const response = await reiAgent.chatCompletions(message);
        return response;
    } catch (error) {
        console.error('Error querying Rei Agent:', error);
        return null;
    }
}

// Example usage in your agent
async function yourAgentFunction() {
    // Your agent's logic here
    const query = "What are the latest developments in quantum computing?";
    const reiResponse = await queryReiAgent(query);
    // Process the response
}

Python
from client import Client

client = Client(
    api_key="your_unit_secret_token",
    base_url="https://api.reilabs.org"
)

# Example function to query Rei Agent
def query_rei_agent(message):
    try:
        response = client.chat.completions.create(
            model="Unit01",
            messages=[
                {"role": "user", "content": message}
            ],
            functions=[{
                "name": "query_rei_agent",
                "description": "Query the Rei Agent for information or assistance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to send to the Rei Agent"
                        }
                    },
                    "required": ["query"]
                }
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying Rei Agent: {e}")
        return None

# Example usage in your agent
def your_agent_function():
    # Your agent's logic here
    query = "What are the latest developments in quantum computing?"
    rei_response = query_rei_agent(query)
    # Process the response


Example integration with OpenAI
from openai import OpenAI
from client import Client as ReiClient

# Initialize both clients
openai_client = OpenAI(api_key="your_openai_key")
rei_client = ReiClient(api_key="your_unit_secret_token")

def hybrid_agent_query(query):
    # First, get context from OpenAI
    openai_response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}]
    )
    
    # Then, enhance with Rei Agent's specialized knowledge
    rei_response = rei_client.chat.completions.create(
        model="Unit01",
        messages=[
            {"role": "user", "content": query},
            {"role": "assistant", "content": openai_response.choices[0].message.content}
        ]
    )
    
    return rei_response.choices[0].message.content


Integrating a Unit as a counselor for common LLMs models allows the seamless integration of memories: simply passing the query and asking for more details unlocks memory without having to code message loops.

Ecosystem, Operations & Business Model
Executive Summary
As a research organisation, We operate a comprehensive and experimental AI agent platform for power users with four integrated revenue streams that create their own value accrual flywheel. Our business model is designed to continuously align incentives between all participants; while funding ecosystem growth and R&D.

Note: This is a high-level overview, expect extra sub-pages with more details about every aspect presented below in the near future.

1. Strategic Market Position
We are positioned for delivering performant AI solutions while growing as both a research organization and sustainable business. We focus on building practical, scalable infrastructure that serves both enterprise clients and individual creators, capturing value across multiple market segments simultaneously.

Our approach combines cutting-edge AI research with real-world applications for power users, creating an ecosystem where innovation meets practical implementation. This dual focus on research excellence and business sustainability positions us uniquely in the evolving AI landscape.

2. Integrated Revenue Streams
REI operates four complementary revenue streams that work together to create a robust, diversified business model:

Subscription Products
Our foundation layer provides predictable recurring revenue through tiered access to Rei units and API services.

Feature	Description	Benefit
REI Unit Access	AI agent creation and management platform (Factory)	Simplified agent development for all skill levels
REI API	Programmatic access to platform capabilities	Enterprise-grade integration capabilities
Tiered Pricing	Standard, Premium, Enterprise levels	Scalable access based on user needs
Payment Flexibility	Both cryptocurrency and fiat options	Accommodates traditional businesses and crypto-native users
Enterprise tiers include dedicated support, higher rate limits, and custom integration assistance, making the platform accessible to large organizations while maintaining competitive pricing for individual creators.

Enterprise Solutions For Businesses and Projects
Our B2B focus captures value through strategic partnerships and custom implementations that leverage our stack

Component	Function	Value Creation
Partnerships	Strategic integrations with enterprise clients beyond implementation	Mutual growth through collaboration
Implementation Services	The most basic B2B relationship : Custom deployment and integration support	Tailored solutions for specific needs
Client Solutions	AI agent systems for enterprise use cases	Scalable business impact
Collaborative Models	Aligned incentives with partner success	Long-term strategic relationships
This approach ensures alignment between partner success and platform growth, creating lasting relationships that build value for both parties while establishing Rei as a trusted enterprise partner.

Agent Marketplace
The marketplace operates as a two-sided platform where creators monetize their AI agents while users discover and deploy solutions.

Marketplace Feature	Description	Revenue Generation
UNIT Listing	Discovery platform for AI agents	Listing fees from creators
UNIT Economy	Token-based transaction system	Transaction fees on all marketplace activity
Selling & Renting	Secondary market for agent access	Commission on trades and rental fees
The marketplace creates network effects where more creators attract more users, generating increasing transaction volumes and ensuring marketplace quality through our verification processes.

Incubation Program (Pilot)
Our incubation program supports early-stage AI projects through a highly selective process, with 0xreisearch personally evaluating each project's technical capabilities. We recognize that not all founders have the experience or desire to have the value of their project tokenized onchain—or ever while still benefiting greatly from our incubation support. Forcing founders to bear the responsibility of tokenization is wrong and detrimental to all parties involved. Good products deserve flexible backing options.

Universal Program Features

Regardless of path chosen, all incubated projects receive:

Heavy Technical Screening: Direct evaluation by our Dev team ensures only highest-quality projects can go through
Heavy Background Screening: Regarding the onchain path, a complete background check up and guarantees will be required
API Access: Standard API fees apply to all projects for sustainable platform usage
Milestone-Based Funding: Structured deployment ensures responsible growth
Full Platform Access: Complete infrastructure and development tools
Strategic Mentorship: Guidance the Rei Dev Team
This approach ensures that brilliant technical teams can access our incubation benefits regardless of their readiness for onchain presence management. We believe great AI products come from focused teams, whether they're building onchain economies or traditional SaaS products.

Two Paths for Different Founder Profiles

Aspect	Onchain Bootstraping	Product Backing
Public Bootstrapping	Yes - Community-driven	Not required
Funding Model	Crowdfunding	Direct support, custom AI solutions
Revenue Model	Project has its own business model + pays API fees	Fees + API fees
Founder Profile	teams seeking community funding	Product-focused teams avoiding the implications of tokenization.
Onchain Bootstrapping Path

For founders ready to build onchain economies, this path provides comprehensive token launch support:

Community Crowdfunding: Projects raise initial funding through both 
R
E
I
a
n
d
REIandETH. Stakers get a higher allocation and priority making up tier 1, Holders can also get in a second tier, creating early community buy-in and alignment.
Liquidity Bootstrapping: Rei provides liquidity support for project tokens, ensuring healthy market dynamics from launch
Operational Buffer: ETH buffer provided specifically to cover API fees and ensure continuous project operations
Token Pairing: Remaining funds provided in $REI tokens to be paired with project tokens, creating deep liquidity pools
This path suits experienced teams who understand token mechanics and want to leverage community participation from day one.

Note : This path is subject to much heavier screening on different fronts.

Product Backing Path

Many brilliant technical teams need time to focus purely on product development without token management overhead. This path offers:

Pure Product Focus: 100% concentration on building exceptional AI products without token distractions
Flexible Backing Options: Selected projects can access different range of backing options ranging from private funding, grants to help building their solutions.
Simplified Business Model: Outside of preferencial API costs, Fee arrangements and agreements between the supported team and the Rei team ensure incentive alignment for both parties.
Full Technical Support: Complete access to REI infrastructure and entreprise AI solutions, identical to bootstrapping path.
Future Flexibility: Teams can potentially transition to being present on chain later if desired, but never required and that will be on their terms as the fee agreement is already in place.
All revenues collected through this path (after operational costs) flow back to $REI , ensuring value accrual while founders focus on what they do best—building great products.

$REI Stakers: Staking's primary goal is incubation program voting and access to tier 1s. additional airdrops and exclusive access to new features will be granted to stakers beyond the primary goal. Minimum amounts will be specified in the near future.

3. Value Accrual Flywheel
The flywheel creates a self-reinforcing cycle that benefits all ecosystem participants through systematic value creation and token supply reduction.

Revenue Flow: Products & Services → Token Economy
Profits from all revenue streams (after operational costs) flow back to the $REI token ecosystem:

Subscription & API: Profits after operational costs → removing tokens from the open market

Enterprise Solutions: Profits after operations and base costs → Token economy
Marketplace: All trading conducted in 
R
E
I
t
o
k
e
n
s
,
f
e
e
s
c
o
l
l
e
c
t
e
d
i
n
REItokens,feescollectedinREI tokens → Direct $REI accumulation

Incubator:

Community voting/crowdfunding requires holding $REI
API fees from all incubated projects → Ecosystem
Product Only track revenues (after operational costs) → Ecosystem
Investment Flow: Team Treasury → Ecosystem Growth
Treasury funds deploy strategically across multiple growth initiatives:

Creator Funding: Direct incentives and grants for high-quality UNIT creators
Partnership Development: Resources for enterprise relationship building and integration support
Ecosystem Investments: Strategic investments in complementary infrastructure
Growth Flow: Ecosystem Growth → Token Demand
Ecosystem expansion manifests across multiple vectors:

Increased UNITs & Creators: More AI agents and developers joining the platform
New Projects & Partnerships: Expanded incubator portfolio and enterprise relationships
Additional Subscribers: Growing user base across all subscription tiers
Enhanced Marketplace Activity: Higher transaction volumes and secondary market activity
Each growth vector increases organic demand for $REI tokens across multiple use cases, from marketplace transactions to staking requirements.

Supply Flow: Token Demand → Circulating Supply Reduction
Growing demand enables systematic supply reduction through multiple mechanisms:

Treasury Accumulation: Revenue converted to held $REI
Buyback Programs: Market purchases to take $REI out of the open market
Marketplace Staking(TBA) Participation requirements lock tokens for extended periods
Utility Consumption: Platform usage creates permanent demand
4. Summary
Core Token Utility & Value Accrual
Marketplace Trading: All marketplace transactions conducted in 
R
E
I
t
o
k
e
n
s
,
w
i
t
h
f
e
e
s
c
o
l
l
e
c
t
e
d
d
i
r
e
c
t
l
y
i
n
REItokens,withfeescollecteddirectlyinREI, creating constant token demand and fee accumulation.

Staking Requirements: Community participation, voting, and crowdfunding activities require $REI staking, locking tokens and reducing circulating supply.

Profit-Driven : Only profits after operational costs flow back to token mechanisms (buybacks, treasury), ensuring sustainable growth tied to real business performance.

API Access: Partners or supported projects require API to run, creating ongoing demand regardless of their chosen development track.

Note : All content above is subject to change and adaptation as the project is in early development.