# AgentsFactory Autonomous Agency Launch Plan

> **For Hermes:** Execute this plan task-by-task. Spawn subagents for parallel workstreams.

**Goal:** Launch AgentsFactory as a fully autonomous AI automation agency — with real clients, real revenue, and real automations running — managed by Hermes subagents.

**Architecture:** Hermes (orchestrator) → Subagents (specialist workers) → External tools (Gmail, LinkedIn, Notion, Streamlit dashboard). All business data flows into the Command Center dashboard.

**Tech Stack:** Hermes Agent, Python, Streamlit, SQLite, Notion API, Gmail API, LinkedIn (browser automation), GitHub

---

## Phase 1: Foundation — Business Identity & Infrastructure
*Timeline: Day 1-2*

### Task 1.1: Define AgentsFactory Service Offerings
**Objective:** Lock down exactly what services AgentsFactory sells, at what price, for whom.

**Files:**
- Create: `C:\Users\Admin\Projects\AgentsFactory\docs\services.md`

**Action:** Write the service catalog:
- **Tier 1 — Starter ($500-1K/mo):** Single automation (e.g., Shopify order alerts, email triage, lead capture)
- **Tier 2 — Growth ($1-3K/mo):** Multi-step workflow (e.g., customer support bot + CRM sync + weekly reports)
- **Tier 3 — Scale ($3-5K/mo):** Full autonomous agent (e.g., AI operations manager handling support + orders + escalations)
- **Custom:** Enterprise / bespoke builds

**Target clients:** E-commerce stores (Shopify/WooCommerce), SaaS startups, local businesses (dentists, gyms, restaurants), solopreneurs.

**Deliverable:** `docs/services.md` with pricing, target personas, and example automations per tier.

---

### Task 1.2: Set Up Business Infrastructure
**Objective:** Create the operational backbone — email, CRM, project tracking.

**Actions:**
1. Create a dedicated AgentsFactory Gmail label/filter (via Hermes Gmail connector)
2. Create a Notion workspace for AgentsFactory (separate from IntelligenzIT):
   - Leads database
   - Projects database
   - Content calendar
   - Automation runbook
3. Update the Command Center dashboard to connect to Notion as a data source (not just SQLite)

**Files:**
- Modify: `src/agentkit/observability/command_center.py` (add Notion sync)
- Create: `src/agentkit/observability/notion_sync.py`

---

### Task 1.3: Clean Dashboard — Remove Seed Data, Add Real Data Entry
**Objective:** Replace all fake seed data with a clean slate + easy data entry.

**Actions:**
1. Remove `seed_data.py` or make it optional (flag: `--seed`)
2. Add a "Quick Add" sidebar to the Command Center for fast manual entry
3. Pre-populate with Phani as the sole team member
4. Set up the database schema to support multi-agent tracking (which subagent handled what)

**Files:**
- Modify: `src/agentkit/observability/command_center.py`
- Modify: `src/agentkit/observability/seed_data.py`

---

## Phase 2: Lead Generation Engine
*Timeline: Day 3-5*

### Task 2.1: Build Outbound Lead Finder
**Objective:** Automatically find potential clients and populate the leads database.

**Approach:** Hermes subagent scans:
- LinkedIn (local business owners, e-commerce founders, SaaS founders in Hyderabad/India + US)
- Twitter/X (people complaining about manual workflows, hiring for ops roles)
- Reddit (r/ecommerce, r/smallbusiness, r/shopify — people asking for automation help)
- Google Maps (local businesses with poor online presence = automation opportunity)

**Files:**
- Create: `src/agentkit/agents/lead_finder.py`
- Create: `src/agentkit/agents/lead_scorer.py` (score 0-100 based on fit)

**Output:** Auto-populate the Leads table in the Command Center with real prospects.

---

### Task 2.2: Build Outbound Outreach Agent
**Objective:** Automatically send personalized first-contact messages to scored leads.

**Approach:**
1. Lead finder identifies prospect → Lead scorer ranks them → Outreach agent drafts personalized message
2. Channels: LinkedIn DM, email (via Gmail), Twitter reply
3. Message template: "I noticed [specific thing about their business]. I built an AI automation that [specific benefit]. Worth a 10-min chat?"
4. All outreach logged in the Command Center

**Files:**
- Create: `src/agentkit/agents/outreach_agent.py`
- Create: `templates/outreach/` (message templates per persona)

**Safety:** Max 20 outreach messages/day to avoid spam flags. Human approval for first 50.

---

### Task 2.3: Build Inbound Capture — Landing Page
**Objective:** Create a simple landing page that captures leads who find AgentsFactory.

**Approach:**
- Single-page site (HTML/CSS, GitHub Pages free hosting)
- Headline: "AI Automations That Run Your Business While You Sleep"
- CTA: "Get a Free Automation Audit" → captures name + email + business type
- Form writes directly to the Command Center database

**Files:**
- Create: `docs/landing/index.html`
- Create: `docs/landing/style.css`
- Create: `docs/landing/form_handler.py` (or use Formspree free tier)

---

## Phase 3: Content Engine (Build in Public)
*Timeline: Day 5-10, then ongoing*

### Task 3.1: Content Calendar & Production
**Objective:** Publish 3-5 pieces of content per week to attract clients.

**Content pillars:**
1. **Automation case studies** — "How I built an AI agent that handles X"
2. **Behind-the-scenes** — "Building an autonomous agency in public" (your journey)
3. **Tips & tutorials** — "3 automations every e-commerce store needs"
4. **Social proof** — Client results, metrics, testimonials (once you have them)

**Channels:** LinkedIn (primary), Twitter/X, YouTube (optional)

**Files:**
- Create: `src/agentkit/agents/content_writer.py`
- Create: `docs/content-calendar.md`
- Create: `templates/content/` (post templates)

**Workflow:** Hermes drafts content → Phani reviews/approves → Hermes publishes (via browser automation)

---

### Task 3.2: LinkedIn Automation
**Objective:** Build a Hermes-managed LinkedIn presence that generates leads.

**Actions:**
1. Optimize Phani's LinkedIn headline: "Building AgentsFactory — AI Automations for E-commerce & SaaS | Autonomous Agency in Public"
2. Daily: Hermes drafts 1 LinkedIn post → Phani approves → auto-publish
3. Daily: Hermes identifies 10 relevant people to engage with (comment on their posts)
4. Weekly: Hermes sends 5 personalized connection requests to target personas

**Files:**
- Create: `src/agentkit/agents/linkedin_agent.py`

---

## Phase 4: Delivery Engine (Build & Deploy Automations)
*Timeline: Day 7+*

### Task 4.1: Automation Templates Library
**Objective:** Build a library of reusable automation templates so new client projects are fast.

**Starter templates:**
1. **Shopify Order Monitor** — Track orders, flag anomalies, send daily summary
2. **Lead Capture & Qualify** — Web form → AI qualification → CRM entry → Slack alert
3. **Customer Support Triage** — Email/chat → classify urgency → draft response → human review
4. **Weekly Business Report** — Pull data from multiple sources → generate PDF → email
5. **Social Media Scheduler** — Content calendar → auto-post → engagement tracking

**Files:**
- Create: `src/agentkit/templates/` (one folder per template)
- Each template: `config.yaml` + `agent.py` + `README.md`

---

### Task 4.2: Client Onboarding Workflow
**Objective:** Standardize how new clients are onboarded.

**Workflow:**
1. Lead signs up (landing page or outreach reply)
2. Hermes sends intro email + scheduling link
3. Discovery call (Phani leads, Hermes takes notes)
4. Hermes generates SOW from call notes
5. Phani approves → Hermes sends proposal
6. Client signs → Hermes creates project in Command Center
7. Subagent starts building

**Files:**
- Create: `src/agentkit/agents/onboarding_agent.py`
- Create: `templates/proposal_template.md`
- Create: `templates/sow_template.md`

---

## Phase 5: Autonomous Operations (The Flywheel)
*Timeline: Day 14+*

### Task 5.1: Daily Operations Cron
**Objective:** Hermes runs daily business operations without Phani's input.

**Daily cron job (8:00 AM IST):**
1. Check all client automations → report health
2. Scan for new leads → add to database
3. Draft content for the day
4. Check email for client communications → draft responses
5. Update Command Center dashboard
6. Send Phani a morning briefing (Telegram)

**Files:**
- Create: `src/agentkit/cron/daily_briefing.py`
- Cron: `cronjob create — daily 8:00 AM IST`

---

### Task 5.2: Weekly Review & Strategy
**Objective:** Hermes analyzes business performance and suggests improvements.

**Weekly cron job (Monday 9:00 AM IST):**
1. Revenue this week vs last week
2. Lead pipeline health (new, converted, lost)
3. Content performance (views, engagement, leads generated)
4. Automation uptime across all clients
5. Top 3 recommendations for the week
6. Send Phani a weekly report (Telegram)

---

### Task 5.3: Subagent Team Structure
**Objective:** Define the "org chart" of Hermes subagents that run AgentsFactory.

**Subagent roster:**
1. **Lead Finder** — Scans for prospects, populates database
2. **Outreach Agent** — Sends personalized first contact
3. **Content Writer** — Drafts LinkedIn posts, blogs, case studies
4. **LinkedIn Agent** — Manages daily LinkedIn activity
5. **Builder Agent** — Builds client automations from templates
6. **Monitor Agent** — Watches all client automations, alerts on failures
7. **Reporter Agent** — Generates daily/weekly business reports

**Files:**
- Create: `src/agentkit/agents/` (one file per agent)
- Create: `docs/org-chart.md`

---

## Immediate Next Steps (Do Now)

| Priority | Task | Time |
|----------|------|------|
| 🔴 P0 | Define services & pricing (Task 1.1) | 30 min |
| 🔴 P0 | Clean dashboard, remove seed data (Task 1.3) | 30 min |
| 🟡 P1 | Set up Notion workspace (Task 1.2) | 1 hr |
| 🟡 P1 | Build landing page (Task 2.3) | 2 hr |
| 🟢 P2 | Build lead finder (Task 2.1) | 2 hr |
| 🟢 P2 | Build content writer (Task 3.1) | 2 hr |
| ⚪ P3 | Outreach agent (Task 2.2) | 2 hr |
| ⚪ P3 | LinkedIn agent (Task 3.2) | 2 hr |
| ⚪ P4 | Automation templates (Task 4.1) | 4 hr |
| ⚪ P5 | Daily cron (Task 5.1) | 1 hr |

---

## Key Decisions Needed from Phani

1. **Services & Pricing** — Do the tiers above match what you want to sell?
2. **Target market** — India-first? US-first? Both?
3. **Content voice** — Technical/deep? Casual/business? Educational?
4. **Outreach comfort** — How aggressive? (20/day is conservative, 100/day is aggressive)
5. **First client strategy** — Do you have any warm contacts who'd be an early customer?
6. **Brand name** — "AgentsFactory" locked in, or still open to change?

---

## Success Metrics (Track in Command Center)

| Metric | Month 1 Target | Month 3 Target |
|--------|---------------|----------------|
| Leads in pipeline | 20 | 100 |
| Outreach sent | 100 | 500 |
| Content published | 12 posts | 50 posts |
| Clients signed | 1 | 5 |
| Monthly revenue | $500 | $5,000 |
| Automations running | 1 | 10 |
| LinkedIn followers | +50 | +500 |
