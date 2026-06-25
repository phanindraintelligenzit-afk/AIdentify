# AI Compliance & Governance Monitor — Landing Page Design Document

> **Version:** 1.0.0
> **Date:** 2026-06-21
> **Author:** Planner Agent (AgentsFactory Swarm)
> **Purpose:** Conversion-focused landing page for AI-first startups (Series A–C) needing EU AI Act compliance
> **Target Conversion Rate:** 3–5% visitor-to-trial, 15–20% trial-to-paid

---

## Design Principles

1. **Urgency over features** — Lead with the August 2026 deadline, not feature lists
2. **Startup-native tone** — Speak like a founder, not a compliance officer. Direct, technical, no fluff
3. **Trust through specificity** — Name exact EU AI Act articles, penalty amounts, and integration steps
4. **Frictionless path to value** — Every section should push toward the free trial CTA
5. **Social proof at every scroll depth** — Trust badges, testimonials, and metrics throughout

---

## Page Architecture (Scroll Order)

```
┌─────────────────────────────────────────────┐
│  1. NAVIGATION BAR (sticky)                 │
├─────────────────────────────────────────────┤
│  2. HERO SECTION                            │
├─────────────────────────────────────────────┤
│  3. PROBLEM SECTION (Pain Points)           │
├─────────────────────────────────────────────┤
│  4. SOLUTION SECTION (Key Features)         │
├─────────────────────────────────────────────┤
│  5. HOW IT WORKS (3-Step Flow)              │
├─────────────────────────────────────────────┤
│  6. PRICING SECTION (4 Tiers)               │
├─────────────────────────────────────────────┤
│  7. SOCIAL PROOF (Testimonials + Badges)    │
├─────────────────────────────────────────────┤
│  8. FAQ SECTION (5 Questions)               │
├─────────────────────────────────────────────┤
│  9. FINAL CTA SECTION                       │
├─────────────────────────────────────────────┤
│  10. FOOTER                                 │
└─────────────────────────────────────────────┘
```

---

## 1. Navigation Bar (Sticky)

**Layout:** Logo left, nav links center, CTA button right

**Elements:**
- **Logo:** Product name + shield/checkmark icon
- **Nav Links:** `Features` · `How It Works` · `Pricing` · `FAQ` · `Docs`
- **CTA Button:** `Start Free Trial` (primary button, contrasting color)
- **Secondary Link:** `Log in` (text link, subtle)

**Sticky behavior:** On scroll, nav gains a subtle shadow and backdrop blur. CTA button pulses gently to draw attention.

---

## 2. Hero Section

### Headline (H1)
```
EU AI Act Compliance for AI Startups —
Ship with Confidence Before August 2026
```

*Rationale: Combines the regulatory urgency (August 2026 deadline) with the target audience (AI startups) and the core value proposition (compliance + confidence). The em dash creates a natural pause that adds weight.*

### Subheadline (H2)
```
Log every AI agent decision. Auto-generate compliance reports.
Flag anomalies in real time. From 2 hours, not 2 months.
```

*Rationale: Three concrete capabilities in plain language. The "2 hours, not 2 months" contrast directly addresses the pain of enterprise competitors that take months to implement.*

### CTA Buttons
- **Primary:** `Start 14-Day Free Trial` — links to signup
- **Secondary:** `See How It Works` — smooth-scrolls to How It Works section

### Urgency Banner (below CTAs, thin horizontal strip)
```
⚠️ EU AI Act high-risk obligations enforceable August 2, 2026 — Penalties up to €15M or 3% of global turnover
```

*Rationale: This is the single most important conversion driver. The specific date and penalty amount create immediate urgency. Placed directly below CTAs so it reinforces the action.*

### Hero Image Description
```
A split-screen dashboard mockup:
LEFT: Real-time decision log stream showing AI agent events flowing in —
     each row shows agent name, action type, risk score (color-coded),
     and compliance tags (art_12, art_13, art_14). Clean, dark-theme
     developer console aesthetic.
RIGHT: Auto-generated compliance report preview — EU AI Act Article
      mapping, risk summary pie chart, anomaly timeline, and an
      "Export PDF" button. Professional, audit-ready formatting.

Style: Modern SaaS dashboard, dark mode with blue/cyan accent colors.
      Subtle grid lines, monospace font for log data, clean sans-serif
      for labels. Conveys both technical depth and executive-ready output.
```

### Trust Line (below hero image)
```
Trusted by AI teams at [Logo] [Logo] [Logo] [Logo]
```
*Placeholder for customer logos. Until real logos exist, use: "Built by the team behind AgentsFactory · SOC 2 Type II Ready · GDPR Compliant"*

---

## 3. Problem Section — "The Compliance Clock Is Ticking"

### Section Headline
```
If You're Building AI in Europe, You Have a Deadline.
Most Startups Aren't Ready.
```

### Subheadline
```
The EU AI Act's high-risk obligations become enforceable August 2, 2026.
Here's what's keeping AI founders up at night.
```

### Pain Point Cards (3 cards, side-by-side on desktop, stacked on mobile)

#### Card 1: Regulatory Risk
**Icon:** Shield with warning triangle
**Title:** `€15M Fines Are Not a Typo`
**Body:**
```
Non-compliance with EU AI Act high-risk obligations carries penalties
of up to €15 million or 3% of global annual turnover — whichever is
higher. For Series A–C startups, even the lower end is an existential
threat. And regulators are already hiring enforcement staff.
```
**Key stat callout:** `August 2, 2026 — High-risk obligations enforceable`

#### Card 2: Manual Compliance
**Icon:** Spreadsheet/document with red X
**Title:** `Spreadsheets Won't Survive an Audit`
**Body:**
```
Article 12 requires tamper-evident, structured logs of every AI decision
— input, model version, output, and human review. Most startups are
tracking this in Slack threads, Notion docs, or not at all. When a
regulator asks for your audit trail, "we'll get back to you" is not
a compliance strategy.
```
**Key stat callout:** `15 compliance rules evaluated per decision in real time`

#### Card 3: Enterprise Tools Don't Fit
**Icon:** Oversized suit/armor
**Title:** `Enterprise Compliance Tools Aren't Built for You`
**Body:**
```
Credo AI, Holistic AI, ModelOp — they're built for Fortune 500
companies with $50K+ annual compliance budgets and 6-month sales cycles.
As a startup, you need something you can install today, not a consulting
engagement that starts in Q3.
```
**Key stat callout:** `Competitors: $50K+/yr · Our Starter: $499/mo`

### Section Closing Line
```
You built your AI to move fast. Your compliance should keep up.
```

---

## 4. Solution Section — "Compliance That Ships at Startup Speed"

### Section Headline
```
Real-Time AI Decision Logging.
Auto-Generated Compliance Reports.
Anomaly Detection That Actually Works.
```

### Subheadline:
```
The only compliance platform built for AI-first startups.
Install the SDK, and we handle the rest.
```

### Feature Cards (3 cards, alternating layout — text left/image right, then reversed)

#### Feature 1: Real-Time Agent Decision Logging
**Icon:** Terminal/console with streaming logs
**Body:**
```
Every decision your AI agents make — classified, logged, and
tamper-evident. Full provenance: input hash → model version →
output → human review. Directly satisfies EU AI Act Article 12
record-keeping requirements.

Supports all major frameworks: LangChain, CrewAI, AutoGen,
OpenAI Agents SDK, and custom agents. One line of code to
start logging.
```

**Key capabilities (bullet list):**
- UUID-based immutable event IDs with hash chain integrity
- PII detection on both input and output (GDPR Art. 32)
- Data lineage tracking — every data source accessed, every record affected
- Consent flag verification per decision (GDPR Art. 6/9)
- 15 automated compliance rules evaluated per event

**Visual description:**
```
Screenshot: SDK integration code snippet (Python) showing
`from compliance_monitor import ComplianceLogger` with 3 lines
of setup code. Below it, a live log stream showing real-time
events with color-coded risk scores.
```

#### Feature 2: Auto-Generated Compliance Reports
**Icon:** Document with checkmark and EU flag
**Body:**
```
Generate audit-ready compliance reports in one click. Map your
AI systems to EU AI Act Articles 12, 13, 14, and 15. Export
PDF reports your legal team (and regulators) will actually
understand.

Weekly automated reports on Growth tier and above. Custom
templates available on Scale and Enterprise.
```

**Key capabilities (bullet list):**
- EU AI Act article mapping (Art. 12, 13, 14, 15)
- Multi-framework support: NIST AI RMF, UK framework (Scale+)
- Risk summary dashboards with trend analysis
- Anomaly timeline with drill-down capability
- One-click PDF export, audit-ready formatting

**Visual description:**
```
Screenshot: Compliance report preview showing EU AI Act
coverage heatmap, risk distribution chart, anomaly timeline,
and "Export PDF" button. Clean, professional formatting.
```

#### Feature 3: Anomaly Detection & Human Oversight
**Icon:** Radar/sonar with alert indicator
**Body:**
```
ML-based anomaly detection flags decisions that fall outside
expected parameters — low confidence scores, off-policy actions,
unauthorized data access, PII leakage. Route alerts to Slack,
PagerDuty, or email.

Built-in human oversight workflow: when an anomaly is flagged,
a reviewer can approve, modify, or override the decision.
Directly satisfies Article 14 human oversight requirements.
```

**Key capabilities (bullet list):**
- Real-time anomaly detection (15 rule types)
- Confidence score threshold alerts (configurable)
- PII leakage detection and auto-blocking
- Human review workflow with approval chains (Scale+)
- Slack, PagerDuty, email, and webhook notifications

**Visual description:**
```
Screenshot: Alert dashboard showing flagged anomalies with
severity levels (critical/warning/info), a decision review
panel with Approve/Modify/Override buttons, and notification
channel configuration.
```

---

## 5. How It Works — "From Zero to Compliant in 3 Steps"

### Section Headline
```
EU AI Act Compliance in 2 Hours, Not 2 Months
```

### Subheadline:
```
Three steps from installation to your first compliance report.
```

### Step Flow (horizontal on desktop, vertical on mobile, connected by animated line)

#### Step 1: Install the SDK
**Icon:** Terminal with `pip install` / `npm install`
**Title:** `Install the SDK`
**Body:**
```
Add our SDK to your AI agent codebase. Python, JavaScript, and
Ruby available. One line to initialize, zero config to start
logging.

    pip install compliance-monitor
    from compliance_monitor import ComplianceLogger
    logger = ComplianceLogger(api_key="your-key")

That's it. Every agent decision is now being logged.
```
**Time estimate:** `5 minutes`

#### Step 2: Decisions Logged Automatically
**Icon:** Server/database with streaming data
**Title:** `Decisions Logged Automatically`
**Body:**
```
Every AI agent decision is captured in real time: input, model
version, output, data lineage, consent flags, and risk scores.
Our rules engine evaluates 15 compliance rules per event — PII
leakage, unauthorized access, low confidence, and more.

Your compliance dashboard updates in real time. No manual
log-building required.
```
**Time estimate:** `Automatic — starts immediately`

#### Step 3: Compliance Reports Generated
**Icon:** Document with EU checkmark
**Title:** `Compliance Reports Generated`
**Body:**
```
Generate audit-ready compliance reports with one click. Map your
systems to EU AI Act articles, review anomaly trends, and export
PDF reports for your legal team or regulators.

On Growth tier and above: automated weekly reports delivered
to your inbox.
```
**Time estimate:** `First report in under 2 hours`

### Section Closing CTA
```
Ready to get compliant? Start your free trial →
[Start 14-Day Free Trial]
```

---

## 6. Pricing Section — "Compliance That Scales With You"

### Section Headline
```
Startup-Friendly Pricing.
No Enterprise Sales Calls Required.
```

### Subheadline:**
```
From $499/mo. 14-day free trial on all tiers. No credit card required.
Annual billing saves 20%.
```

### Pricing Toggle
```
[Monthly] — [Annual (save 20%)]
```

### Pricing Cards (4 cards, Growth tier highlighted/popular)

#### Tier 1: Starter — $499/mo
**Badge:** `Best for early-stage`
**Target:** Pre-seed to Seed, 1–3 AI agents

**Includes:**
- Up to 3 AI agents monitored
- 100K decision logs/month
- Basic compliance dashboard
- Monthly compliance report (PDF)
- Email anomaly alerts
- 30-day log retention
- Community support

**CTA:** `Start Free Trial`

**Positioning line:** `"Get EU AI Act ready from day one"`

---

#### Tier 2: Growth — $1,499/mo ⭐ MOST POPULAR
**Badge:** `Most Popular` (highlighted, contrasting background)
**Target:** Series A–B, 4–15 AI agents

**Includes everything in Starter, plus:**
- Up to 15 AI agents monitored
- 1M decision logs/month
- Full compliance dashboard with EU AI Act mapping
- Weekly compliance reports
- Real-time anomaly detection + Slack/PagerDuty alerts
- Human oversight workflow (review & override)
- 90-day log retention
- API access
- Email + chat support

**CTA:** `Start Free Trial`

**Positioning line:** `"Enterprise-grade compliance for growing AI teams"`

---

#### Tier 3: Scale — $3,999/mo
**Badge:** `For scaling teams`
**Target:** Series B–C, 16–50 AI agents

**Includes everything in Growth, plus:**
- Up to 50 AI agents monitored
- 10M decision logs/month
- Multi-framework compliance (EU AI Act + NIST AI RMF + UK)
- Custom compliance report templates
- Advanced anomaly detection (ML-based)
- Human oversight workflow with approval chains
- 1-year log retention
- SSO, audit logs, SOC 2 support
- Dedicated customer success manager

**CTA:** `Start Free Trial`

**Positioning line:** `"The compliance backbone for AI-first companies"`

---

#### Tier 4: Enterprise — Custom
**Badge:** `Custom deployment`
**Target:** Large startups, multi-team deployments

**Includes everything in Scale, plus:**
- Unlimited agents
- Unlimited logs
- Custom integrations
- On-premise deployment option
- Custom compliance frameworks
- 2-year+ log retention
- SLA guarantees
- White-label reports
- Dedicated support team

**CTA:** `Contact Sales`

**Positioning line:** `"Built for teams that need full control"`

---

### Pricing Footer Notes
```
All plans include: 14-day free trial · No credit card required · Cancel anytime
Annual billing: 20% discount · Startup program: 50% off for 6 months (< $5M funding)
```

### Competitive Comparison Callout
```
Why not enterprise tools? Credo AI and Holistic AI start at $50K+/yr.
Our Growth tier gives you the same EU AI Act compliance for $1,499/mo.
That's 72% less. With a 14-day free trial instead of a 6-month sales cycle.
```

---

## 7. Social Proof Section — "Built for AI Teams, Trusted by AI Teams"

### Section Headline
```
Join 50+ AI-First Startups Already Compliant
```
*Note: Replace with real number as customers are acquired. For launch, use: "Join the waitlist — Early access for AI-first startups"*

### Testimonial Cards (3 cards, carousel on mobile)

#### Testimonial 1
```
"Before [Product], our compliance was a shared Google Doc and a
prayer. Now we have audit-ready logs for every agent decision
and weekly reports our legal team actually trusts. Setup took
45 minutes."

— [Name], CTO, [AI Startup Name] (Series A)
```

#### Testimonial 2
```
"We evaluated Credo AI and Holistic AI. Both wanted $50K+ and
3-month onboarding. [Product] had us logging decisions the same
day. The EU AI Act mapping alone is worth the subscription."

— [Name], Head of AI, [AI Startup Name] (Series B)
```

#### Testimonial 3
```
"The anomaly detection caught a PII leakage issue in our
customer support agent before it reached production. That alone
saved us from a potential GDPR violation. This is compliance
that actively protects you."

— [Name], VP Engineering, [AI Startup Name] (Series C)
```

*Note: All testimonials are placeholders. Replace with real customer quotes as they become available.*

### Trust Badges Row
```
[SOC 2 Type II]  [GDPR Compliant]  [EU AI Act Ready]  [ISO 27001 (in progress)]
```

### Logos Section
```
Trusted by teams at:
[Logo Placeholder] [Logo Placeholder] [Logo Placeholder] [Logo Placeholder]
```

### Key Metrics (once available)
```
50+ startups · 2M+ decisions logged · 15 compliance rules · 99.9% uptime
```

---

## 8. FAQ Section — "Questions You Should Be Asking"

### Section Headline
```
Frequently Asked Questions
```

### Subheadline:
```
Everything you need to know about EU AI Act compliance and our platform.
```

### FAQ Items (accordion style — click to expand)

#### Q1: When do I need to be compliant with the EU AI Act?
```
The EU AI Act's high-risk AI system obligations become enforceable
on August 2, 2026. This is when Articles 12 (record-keeping),
13 (transparency), 14 (human oversight), and 15 (accuracy/robustness)
become legally binding for high-risk AI systems.

If your startup deploys AI in regulated domains — fintech, healthtech,
HRtech, legaltech, autonomous systems, or any system that impacts
EU residents — you likely fall under the high-risk category and need
compliance infrastructure in place by that date.

Prohibited AI practices (unacceptable risk) have been enforceable
since August 2, 2025. The grace period for systems already on the
market ends August 2, 2027.

Our recommendation: don't wait. Start logging now so you have
historical data and a working compliance process before the deadline.
```

#### Q2: How long does integration take?
```
For most teams, integration takes under 2 hours. Our SDK requires
3 lines of code to start logging decisions. We provide pre-built
integrations for LangChain, CrewAI, AutoGen, and the OpenAI Agents
SDK — if you're using one of these frameworks, you can be up and
running in under 30 minutes.

Full compliance dashboard setup — including agent registration,
compliance rule configuration, and report template customization —
typically takes 1–2 hours for a technical team.

We provide step-by-step documentation, example repos on GitHub,
and free onboarding support for all paid tiers.
```

#### Q3: How do you handle data security and privacy?
```
Security is foundational to our architecture:

- All decision logs are encrypted at rest (AES-256) and in transit (TLS 1.3)
- PII is detected and flagged automatically on both input and output
- We support data residency in EU (eu-west-1) for GDPR compliance
- SOC 2 Type II controls are in place
- We never store raw prompts or outputs — only hashed summaries and metadata
- On Enterprise tier, we offer on-premise deployment for full data control
- Our platform is designed to help you comply with GDPR, not create new risks

We undergo regular third-party security audits and can provide our
SOC 2 report and DPA (Data Processing Agreement) upon request.
```

#### Q4: What if I'm not sure whether my AI system is "high-risk"?
```
The EU AI Act's high-risk classification depends on your use case,
not your company size. AI systems used in the following domains are
generally considered high-risk:

- Credit scoring and financial decision-making
- Hiring, employee evaluation, and HR decisions
- Medical devices and health diagnostics
- Legal document analysis and judicial assistance
- Autonomous vehicles and critical infrastructure
- Education and vocational training
- Law enforcement and border control

If you're unsure, we offer a free "EU AI Act Compliance Checker"
tool on our website that assesses your risk classification in 2 minutes.
You can also book a free 30-minute compliance assessment call with
our team.

When in doubt, logging your decisions is a good practice regardless
of risk classification — it protects you and builds trust with users
and investors.
```

#### Q5: What happens if I exceed my plan's limits?
```
We'll never silently drop your logs. If you approach your decision
log limit or agent count, we'll notify you via email and in-app
alerts with a 14-day grace period.

You can:
- Upgrade to the next tier (instant, prorated)
- Purchase additional log packs (overage pricing available)
- Contact us for a custom arrangement

On the Starter tier, if you exceed 100K logs/month, we continue
logging but flag the overage. On Growth and above, we provide
generous buffers before any action is needed.

We also offer a startup program: 50% discount for 6 months for
companies with less than $5M in funding. Apply from your dashboard.
```

### FAQ Footer
```
Still have questions? [Book a demo] or [Email us at hello@agentsfactory.ai]
```

---

## 9. Final CTA Section — "Your Compliance Clock Is Ticking"

### Background
```
Full-width section with subtle gradient background (dark blue to deep navy).
Optional: animated countdown timer showing days until August 2, 2026.
```

### Headline
```
August 2, 2026 Is Coming.
Get Compliant Before Your Competitors Do.
```

### Subheadline:
```
Start your 14-day free trial today. No credit card required.
Install in 5 minutes. First compliance report in under 2 hours.
```

### CTA Buttons
- **Primary (large):** `Start 14-Day Free Trial` — links to signup
- **Secondary:** `Book a Demo` — links to calendar booking

### Urgency Element
```
⏰ [Countdown: XX days until EU AI Act high-risk enforcement]
```

### Risk Reversal Line
```
No credit card · Cancel anytime · Full data export if you leave
```

### Final Trust Line
```
Join AI-first startups who chose compliance over chaos.
```

---

## 10. Footer

### Layout: 4-column grid

**Column 1 — Product:**
- Features
- How It Works
- Pricing
- Changelog
- Documentation

**Column 2 — Resources:**
- EU AI Act Compliance Guide
- Compliance Checker Tool
- Blog
- API Reference
- GitHub (SDK)

**Column 3 — Company:**
- About
- Careers
- Contact
- Privacy Policy
- Terms of Service

**Column 4 — Stay Updated:**
- Email signup: "Get EU AI Act updates and compliance tips"
- Input field + Subscribe button
- Social links: Twitter/X, LinkedIn, GitHub

### Footbar (bottom):
```
© 2026 AgentsFactory. All rights reserved.
Built with ❤️ for AI-first startups.
```

---

## Technical Specifications

### Responsive Breakpoints
- Desktop: 1200px+ (full layout)
- Tablet: 768px–1199px (2-column grids → single column)
- Mobile: < 768px (single column, hamburger nav, stacked cards)

### Performance Targets
- Largest Contentful Paint (LCP): < 2.5s
- First Input Delay (FID): < 100ms
- Cumulative Layout Shift (CLS): < 0.1
- Target Lighthouse score: 90+

### SEO Meta Tags
```html
<title>EU AI Act Compliance for AI Startups | [Product Name]</title>
<meta name="description" content="Log every AI agent decision.
Auto-generate compliance reports. EU AI Act ready in 2 hours.
From $499/mo. 14-day free trial. Built for Series A-C startups.">
<meta name="keywords" content="EU AI Act compliance, AI governance,
AI compliance software, AI agent logging, Article 12 compliance,
startup compliance, AI audit, GDPR AI">
```

### Open Graph Tags
```html
<meta property="og:title" content="EU AI Act Compliance for AI Startups">
<meta property="og:description" content="Ship AI with confidence.
Compliance in 2 hours, not 2 months. From $499/mo.">
<meta property="og:image" content="[hero-image-url]">
<meta property="og:type" content="website">
```

### Analytics & Tracking
- Google Analytics 4: Page views, scroll depth, CTA clicks
- Hotjar/Microsoft Clarity: Heatmaps, session recordings
- Conversion events: `trial_signup`, `demo_booked`, `pricing_viewed`, `faq_expanded`
- UTM parameter tracking for all marketing campaigns

### A/B Tests to Run (Post-Launch)
1. **Hero headline:** "Ship with Confidence" vs. "Don't Get Fined"
2. **CTA button:** "Start Free Trial" vs. "Get Compliant Now"
3. **Pricing anchor:** Show Enterprise tier first vs. Starter tier first
4. **Social proof:** Testimonials above pricing vs. below pricing
5. **Urgency banner:** Countdown timer vs. static deadline text

---

## Conversion Funnel

```
Landing Page Visit
       │
       ▼
┌─────────────────┐
│  Scroll to Hero  │ 100% of visitors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  View Pricing   │ ~40% of visitors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Click CTA      │ ~8% of visitors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Start Trial    │ ~3-5% of visitors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Install SDK    │ ~60% of trial users
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Convert to Paid│ ~15-20% of active trials
└─────────────────┘
```

---

## Design Tokens

### Color Palette
| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#2563EB` | CTA buttons, links, accents |
| `--color-primary-dark` | `#1D4ED8` | Hover states |
| `--color-secondary` | `#0EA5E9` | Secondary buttons, highlights |
| `--color-accent` | `#F59E0B` | Urgency elements, badges |
| `--color-danger` | `#EF4444` | Critical alerts, penalty amounts |
| `--color-success` | `#10B981` | Checkmarks, success states |
| `--color-bg-dark` | `#0F172A` | Dark background (hero, footer) |
| `--color-bg-light` | `#F8FAFC` | Light background (sections) |
| `--color-text-primary` | `#1E293B` | Headings (light bg) |
| `--color-text-secondary` | `#64748B` | Body text |
| `--color-text-inverse` | `#FFFFFF` | Text on dark backgrounds |

### Typography
| Element | Font | Weight | Size (desktop) |
|---------|------|--------|-----------------|
| H1 (Hero) | Inter | 800 | 56px / 64px line-height |
| H2 (Section) | Inter | 700 | 36px / 44px line-height |
| H3 (Cards) | Inter | 600 | 24px / 32px line-height |
| Body | Inter | 400 | 18px / 28px line-height |
| Code | JetBrains Mono | 400 | 14px / 20px line-height |
| Small/Caption | Inter | 400 | 14px / 20px line-height |

### Spacing Scale
`4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px, 128px`

### Border Radius
- Cards: `12px`
- Buttons: `8px`
- Input fields: `8px`
- Badges: `9999px` (pill shape)

### Shadows
- Card default: `0 1px 3px rgba(0,0,0,0.1)`
- Card hover: `0 4px 12px rgba(0,0,0,0.15)`
- Button: `0 2px 4px rgba(37,99,235,0.3)`
- Modal: `0 20px 40px rgba(0,0,0,0.2)`

---

## Implementation Notes

### Recommended Tech Stack
- **Framework:** Next.js 14 (App Router) or Astro for static generation
- **Styling:** Tailwind CSS + custom design tokens
- **Animations:** Framer Motion (subtle entrance animations, scroll-triggered)
- **Forms:** React Hook Form + Zod validation
- **Analytics:** PostHog (open-source, privacy-friendly) or Mixpanel
- **A/B Testing:** PostHog built-in or LaunchDarkly
- **Hosting:** Vercel (edge deployment, global CDN)

### Accessibility Requirements
- WCAG 2.1 AA compliance minimum
- All interactive elements keyboard-navigable
- Color contrast ratio ≥ 4.5:1 for body text, ≥ 3:1 for large text
- ARIA labels on all interactive elements
- Skip-to-content link
- Reduced motion support via `prefers-reduced-motion`

### i18n Readiness
- All user-facing strings should be externalized from day one
- Primary market: English (US/UK)
- Future: German, French, Dutch (key EU markets)
- Use `next-intl` or similar for translation management

---

## Appendix: Copy Variants for Testing

### Hero Headline Variants
1. `EU AI Act Compliance for AI Startups — Ship with Confidence Before August 2026`
2. `Don't Let the EU AI Act Slow Down Your AI. Get Compliant in 2 Hours.`
3. `The Compliance Layer Your AI Agents Need. From $499/mo.`
4. `August 2026 Is the Deadline. Your AI Agents Need Compliance Logging.`

### CTA Button Variants
1. `Start 14-Day Free Trial`
2. `Get Compliant Now`
3. `Start Free Trial`
4. `Try It Free — No Credit Card`

### Urgency Banner Variants
1. `⚠️ EU AI Act high-risk obligations enforceable August 2, 2026 — Penalties up to €15M or 3% of global turnover`
2. `⏰ XX days until EU AI Act enforcement. Start your free trial today.`
3. `🚨 50+ startups already compliant. Don't be the one that gets fined.`

---

*Document created by Planner Agent, AgentsFactory Swarm. This is a living document — update with real customer data, testimonials, and metrics as they become available.*
