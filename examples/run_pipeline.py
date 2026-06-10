"""
Universal Pipeline Runner
Run any pipeline template with sample data.

Usage:
  uv run python examples/run_pipeline.py --pipeline healthcare
  uv run python examples/run_pipeline.py --pipeline real_estate
  uv run python examples/run_pipeline.py --pipeline ecommerce
  uv run python examples/run_pipeline.py --pipeline legal
  uv run python examples/run_pipeline.py --pipeline hr
  uv run python examples/run_pipeline.py --all
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentkit.llm import LLMClient
from agentkit.observability.metrics import MetricsCollector
from agentkit.orchestrator.yaml_loader import load_pipeline_config


PIPELINE_DIR = Path(__file__).parent / "pipelines"

SAMPLE_DATA = {
    "healthcare": """
Patient: John D. (ID: PT-2026-8847)
Procedure: MRI Brain with contrast (CPT 70553)
Diagnosis: R51.9 (Headache, unspecified)
Insurer: Aetna Better Health
Urgency: Urgent (neurologist suspects MS)
Clinical Notes: 45yo male, 3 weeks progressive headaches, visual changes.
  Neurologist ordered MRI to rule out MS or tumor.
  Previous CT was inconclusive.
Required: Prior auth for MRI brain w/contrast.
""",
    "real_estate": """
Market: Austin, TX — 78701, 78702, 78703 zip codes
Criteria: 3BR/2BA, $400K-$650K, family-friendly, good schools
Target: Young families relocating from CA/NY
Timeline: Sellers want to close in 30-45 days
Source: Expired listings, pre-foreclosure data, probate records
""",
    "ecommerce": """
Product: Ergonomic Lumbar Support Cushion for Office Chairs
Price: $34.99
Category: Home Office > Chair Accessories
Competitors: Everlasting Comfort ($29.99), LoveHome ($24.99), Cushion Lab ($39.99)
Key Features: Memory foam, breathable mesh, adjustable strap, washable cover
Target: Remote workers, gamers, people with back pain
Reviews to handle: 12 recent reviews (mix of 1-5 stars)
""",
    "legal": """
Contract: Master Service Agreement between TechCorp (client) and CloudVendor Inc.
Type: MSA for cloud infrastructure services
Value: $2.4M over 3 years
Key Concerns: Data ownership, SLA penalties, termination for convenience, IP assignment
Governing Law: Delaware
Special Requirements: Must comply with GDPR (EU customers), SOC 2 Type II required
Red flags noticed: Unlimited liability clause, auto-renewal with 90-day notice, broad IP assignment
""",
    "hr": """
Job: Senior Python Developer (Backend)
Requirements: 5+ years Python, FastAPI/Django, AWS, Postgres, Docker
Salary: $140K-$170K
Location: Remote (US)
Resumes received: 8 candidates
Top picks needed: 3 for phone screens
New hire starting: Alex Rivera, starts June 23, needs full onboarding package
""",
}


def print_header(text: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_agent_output(agent_name: str, output: str, elapsed: float) -> None:
    print(f"\n{'─'*60}")
    print(f"  🤖 {agent_name}  ({elapsed:.1f}s)")
    print(f"{'─'*60}")
    preview = output[:600] + ("..." if len(output) > 600 else "")
    print(preview)


async def run_pipeline_demo(pipeline_name: str) -> None:
    """Run a pipeline in demo mode with sample data."""
    yaml_file = PIPELINE_DIR / f"{pipeline_name}.yaml"
    if not yaml_file.exists():
        print(f"❌ Pipeline not found: {yaml_file}")
        return

    config = load_pipeline_config(str(yaml_file))
    sample_input = SAMPLE_DATA.get(pipeline_name, "Sample input data")

    print_header(f"PIPELINE: {config.name}")
    print(f"  Topology:    {config.topology_type}")
    print(f"  Agents:      {len(config.agents)}")
    print(f"  Budget:      ${config.cost_budget_usd}")
    print(f"  Mode:        DEMO (no API key needed)\n")

    start = datetime.now()

    for i, agent in enumerate(config.agents, 1):
        print(f"▶ Agent {i}/{len(config.agents)}: {agent.agent_id}...")
        await asyncio.sleep(0.3)

        demo_output = generate_demo_output(agent.agent_id, sample_input, pipeline_name)
        print_agent_output(agent.agent_id.upper(), demo_output, 0.3)

    elapsed = (datetime.now() - start).total_seconds()
    print_header(f"PIPELINE COMPLETE: {config.name}")
    print(f"  Total time:   {elapsed:.1f}s")
    print(f"  Agents run:   {len(config.agents)}/{len(config.agents)}")
    print(f"  Mode:         Demo (static output)")
    print(f"  Live mode:    uv run python examples/run_pipeline.py --{pipeline_name} --live\n")


def generate_demo_output(agent_id: str, sample_input: str, pipeline_name: str) -> str:
    """Generate realistic demo output for each agent."""
    outputs = {
        # Healthcare
        "auth_intake": json.dumps({
            "patient_id": "PT-2026-8847",
            "procedure_code": "70553",
            "diagnosis_code": "R51.9",
            "insurer_name": "Aetna Better Health",
            "insurer_id": "AET-BH-001",
            "urgency": "urgent",
            "required_documents": ["Neurologist referral", "Prior CT results", "Clinical notes"],
            "clinical_notes_summary": "45yo male, 3 weeks progressive headaches + visual changes. Neuro ordered MRI to rule out MS/tumor. CT inconclusive.",
            "estimated_turnaround_days": 3
        }, indent=2),
        "requirement_checker": """## Aetna Prior Auth Requirements — MRI Brain w/Contrast (70553)

1. **Required Documentation:**
   - Neurologist referral letter with clinical justification
   - Prior CT scan results (must show inconclusive findings)
   - Failed conservative treatment documentation (if applicable)
   - ICD-10: R51.9 (supported by M54.5 if back pain component)

2. **Common Denial Reasons:**
   - "Conservative treatment not attempted" — ensure PT/medication trial is documented
   - "CT sufficient" — must clearly state why CT was inadequate
   - "Not medically necessary" — neurologist letter must be detailed

3. **Approval Tips:**
   - Use specific language: "rule out multiple sclerosis" not just "headache"
   - Include visual changes as a red-flag symptom
   - Reference Aetna Clinical Policy Bulletin #0043 (Neuroimaging)

4. **Alternative Codes:**
   - 70552 (MRI Brain without contrast) — lower denial rate but less diagnostic value
   - 70551 (MRI Brain without + with contrast) — may be approved if 70553 denied

5. **Timeline:** Urgent = 3-5 business days. Standard = 10-14 days.""",

        # Real Estate
        "market_scout": """## Austin, TX Market Brief (78701-78703)

**Current Conditions:** Seller's market, 2.1 months inventory, prices up 4.2% YoY
**Price Trends:** Median $585K (78701), $510K (78702), $620K (78703). Per sq ft: $380-$450.
**Hot Neighborhoods:** East Austin (78702) — gentrifying, strong appreciation. Mueller family area.
**Off-Market Opportunities:** 12 expired listings in target range, 3 pre-foreclosures in 78702.
**Investor Activity:** Moderate — institutional buyers pulling back, opportunity for individual buyers.
**Recommendation:** Focus on 78702 expired listings — motivated sellers, below-market pricing possible.""",
        "lead_qualifier": """## Lead Qualification Results

| Lead | Score | Approach | Est. Value |
|------|-------|----------|------------|
| Expired: 123 Oak St | 9/10 | Call directly, mention listing expired | $520K |
| Expired: 456 Pine Ave | 8/10 | Door knock + market analysis | $485K |
| Pre-foreclosure: 789 Elm | 7/10 | Sensitive approach, cash offer ready | $410K |
| Probate: 321 Maple Dr | 6/10 | Work with estate attorney | $550K |

**Top Pick:** 123 Oak St — seller listed 6 months ago, price dropped twice, highly motivated.""",

        # E-Commerce
        "product_analyst": """## Product Analysis: Ergonomic Lumbar Cushion

**Positioning:** "The last lumbar cushion you'll buy" — premium memory foam for serious remote workers.
**Competitive Gaps:** Everlasting Comfort = budget brand, quality issues. LoveHome = cheap materials. Cushion Lab = overpriced, weak strap.
**Keywords:** "lumbar support cushion", "office chair back support", "memory foam seat cushion", "ergonomic car seat cushion", "back pain relief cushion"
**Pricing:** $34.99 is optimal — undercuts Cushion Lab, premium to budget options. Sweet spot.
**Upsell:** Matching seat cushion ($24.99), travel neck pillow ($19.99). Bundle at $69.99.""",
        "listing_optimizer": """## Optimized Listing

**Title:** Ergonomic Lumbar Support Cushion — Memory Foam Office Chair Back Support for Lower Back Pain Relief, Adjustable Strap, Breathable Mesh Cover (Black)

**Bullets:**
- ✅ ERGONOMIC DESIGN: Contours to your spine's natural curve, reducing lower pressure by up to 40% during long work sessions
- ✅ PREMIUM MEMORY FOAM: High-density, slow-rebound foam that maintains shape after 10,000+ hours of use
- ✅ UNIVERSAL FIT: Adjustable elastic strap fits any office chair, car seat, or gaming chair (up to 38" wide)
- ✅ BREATHABLE & WASHABLE: 3D mesh cover promotes airflow, machine-washable for easy maintenance
- ✅ SATISFACTION GUARANTEE: 30-day money-back guarantee + 2-year warranty — buy with confidence""",

        # Legal
        "contract_parser": json.dumps({
            "parties": [{"name": "TechCorp", "role": "Client"}, {"name": "CloudVendor Inc.", "role": "Vendor"}],
            "contract_type": "MSA",
            "effective_date": "2026-07-01",
            "termination_date": "2029-06-30",
            "financial_terms": {"total_value": "$2.4M", "annual": "$800K", "payment": "Quarterly in advance"},
            "key_obligations": ["Vendor: 99.95% uptime SLA", "Vendor: SOC 2 Type II compliance", "Client: Provide access to technical contacts"],
            "termination": "90-day notice for convenience, immediate for cause",
            "governing_law": "Delaware",
            "special_clauses": ["Unlimited liability for data breaches", "Auto-renewal 1 year", "Broad IP assignment to Vendor"]
        }, indent=2),
        "risk_analyzer": """## Contract Risk Matrix

| Clause | Risk | Severity | Recommendation |
|--------|------|----------|----------------|
| Unlimited liability (data breach) | CRITICAL | 9/10 | Cap at 12 months fees ($800K) |
| Auto-renewal 90-day notice | HIGH | 7/10 | Reduce to 60-day notice, add opt-out |
| Broad IP assignment | HIGH | 8/10 | Limit to project-specific IP only |
| No SLA penalty detail | MEDIUM | 6/10 | Add: 5% credit per 0.1% below 99.95% |
| No data portability clause | MEDIUM | 5/10 | Add: 90-day data export on termination |
| Governing law: Delaware | LOW | 2/10 | Acceptable — standard for tech contracts |

**Overall Risk Score: 7.2/10 — Significant redlines needed before signing.**""",

        # HR
        "resume_screener": """## Candidate Screening Results

| Rank | Candidate | Score | Verdict | Notes |
|------|-----------|-------|---------|-------|
| 1 | Alex M. | 92/100 | ✅ PHONE SCREEN | 6yr Python, AWS, FastAPI. Led team of 4. |
| 2 | Priya K. | 88/100 | ✅ PHONE SCREEN | 5yr, strong Django, Postgres. FAANG exp. |
| 3 | James T. | 81/100 | ✅ PHONE SCREEN | 7yr, Docker expert. Slight overqualify. |
| 4 | Maria S. | 72/100 | 🤔 MAYBE | 4yr, good skills. Job hopper (3 in 2yr). |
| 5 | Chris L. | 65/100 | ❌ SKIP | 3yr exp, missing AWS. Wrong fit. |
| 6-8 | Others | <60 | ❌ SKIP | Insufficient experience or skills mismatch |

**Recommendation:** Phone screen Alex, Priya, James. Skip to Maria if any decline.""",
        "outreach_composer": """## Personalized Outreach

**To Alex M. (Top Candidate):**

*Email:*
Subject: Your FastAPI experience caught our attention — Senior Python Role

Hi Alex,

I noticed you led the API platform team at [Company] and built their FastAPI microservices from scratch. That's exactly the kind of experience we need.

We're a growing team building [product], and we need a senior backend engineer who can own the architecture. Your background in AWS + FastAPI + team leadership is a perfect match.

Would you be open to a 20-minute call this week? No pressure — just a conversation.

Best,
[Hiring Manager]

*LinkedIn:*
"Hi Alex — your work on FastAPI microservices is impressive. We have a senior backend role that matches your profile. Open to a quick chat?"
""",

        # Missing agents — Healthcare
        "submission_drafter": """## Prior Auth Submission Package — READY

**Patient:** John D. (PT-2026-8847)
**Procedure:** MRI Brain w/Contrast (CPT 70553)
**Insurer:** Aetna Better Health

### Documents Prepared:
1. ✅ **Clinical Justification Letter** (neurologist-signed)
   - "45yo male, 3 weeks progressive headaches + visual changes. CT inconclusive. MRI needed to rule out MS or tumor."
   - ICD-10: R51.9, M54.5

2. ✅ **Prior CT Results** (attached — shows inconclusive findings)

3. ✅ **Conservative Treatment Documentation**
   - Physical therapy: 6 weeks, no improvement
   - Medication trial: Sumatriptan, Topiramate — inadequate relief

4. ✅ **Aetna PA Form** (completed electronically)

### Submission Method:
- **Electronic:** Via Aetna Provider Portal (preferred)
- **Backup:** Fax to 1-800-XXX-XXXX
- **Reference:** Aetna CPB #0043 (Neuroimaging)

### Follow-up Schedule:
- Day 3: Check status via portal
- Day 5: If no response, call provider services
- Day 7: Escalate to clinical review if denied

**Estimated approval: 3-5 business days (urgent)""",
        "tracker_setup": """## Auth Tracking — ACTIVE

**Auth ID:** AET-2026-PA-8847-001
**Status:** Submitted → Under Review
**Submitted:** 2026-06-10 14:32 UTC

### Automated Monitoring:
| Check | Date | Action |
|-------|------|--------|
| Status check | Day 3 (Jun 13) | Auto-query portal |
| Follow-up call | Day 5 (Jun 15) | Alert: call provider services |
| Escalation | Day 7 (Jun 17) | Alert: clinical review request |
| Expiry alert | Day 14 (Jun 24) | Alert: auth may expire |

### SLA Tracking:
- **Urgent turnaround:** 3-5 business days
- **Expected decision by:** Jun 13-15
- **Escalation trigger:** No response by Day 5

### Patient Notification:
- ✅ SMS sent to patient: "Your prior auth has been submitted. We'll update you within 3-5 business days."
- ✅ Calendar reminder set for follow-up""",

        # Missing agents — Real Estate
        "listing_creator": """## Listing Draft — 123 Oak St, Austin TX 78702

**Price:** $489,000 (reduced from $520,000)
**Status:** Coming Soon (pre-market)

### Listing Description:
Welcome to this stunning 3BR/2BA in the heart of East Austin's most sought-after neighborhood. Recently renovated with modern finishes, this home features an open-concept kitchen, hardwood floors throughout, and a spacious backyard perfect for entertaining.

**Key Features:**
- 3 Bedrooms / 2 Bathrooms
- 1,650 sq ft living space
- Updated kitchen with quartz countertops
- Original hardwood floors
- Private backyard with deck
- 2-car garage
- Walkable to Mueller amenities

**School District:** Austin ISD — rated 8/10
**HOA:** None
**Year Built:** 1995 (renovated 2023)

### Marketing Plan:
1. Professional photography (schedule: this week)
2. Virtual tour (Matterport)
3. Coming Soon on MLS + Zillow
4. Open house: Saturday 2-4pm
5. Targeted Facebook/Instagram ads ($500 budget)

### Pricing Strategy:
- List at $489K (4% below recent comps)
- Expected offer range: $475K-$495K
- Target close: 30 days""",
        "outreach_automator": """## Outreach Campaign — Austin TX Leads

### Email Sequence (5-touch):

**Email 1 (Day 0):** "Your Austin home — what's it worth in 2026?"
- Personalized with address + estimated value
- CTA: "Get your free home valuation"

**Email 2 (Day 3):** "3 homes just sold on your street"
- Recent comps + market trends
- CTA: "See what buyers are paying"

**Email 3 (Day 7):** "Thinking of selling? Here's your game plan"
- 5-step selling guide
- CTA: "Book a free 15-min call"

**Email 4 (Day 14):** "Austin market update — prices are shifting"
- Monthly market report
- CTA: "Get your personalized report"

**Email 5 (Day 30):** "Last chance — your home valuation expires"
- Urgency + social proof
- CTA: "Claim your valuation"

### LinkedIn Sequence:
- Connection request with personalized note
- Follow-up: Share market insight
- Follow-up: Case study of recent sale

### SMS Sequence:
- Day 1: "Hi [Name], I help Austin homeowners sell fast. Worth a chat?"
- Day 5: "Quick update: 3 homes sold on [Street] this month. Curious about your home's value?"

**Expected response rate:** 8-12%
**Target:** 5 qualified conversations/week""",

        # Missing agents — E-Commerce
        "support_responder": """## Customer Support Response Draft

**Review:** ★★☆☆☆ — "Cushion flattened after 2 weeks, waste of money"

**Response Draft:**

Hi [Customer Name],

Thank you for taking the time to share your feedback, and I'm sorry to hear the cushion didn't meet your expectations. That's definitely not the experience we want for our customers.

Our memory foam is rated for 10,000+ hours of use, so flattening after 2 weeks is unusual. This could be:
1. A defective unit (rare, but it happens)
2. The cushion needs 24-48 hours to fully expand after unboxing
3. The foam may have been compressed during shipping

Here's what I'd like to do:
✅ Send you a replacement cushion — no questions asked
✅ Include a prepaid return label for the original
✅ Add a free seat cushion ($24.99 value) for the trouble

Would that work for you? Just reply "yes" and I'll ship it today.

Best,
[Agent Name]
Customer Experience Team

**Internal Notes:**
- Flag for QA: Check batch # for foam density issues
- Offer: Full refund + keep product (cost: $34.99, saves $15 return shipping)
- Escalation: If customer is VIP, offer 50% off next purchase""",
        "review_manager": """## Review Analysis — Last 30 Days

**Total Reviews:** 12
**Average Rating:** 4.2/5 (down from 4.5 last month)

### Sentiment Breakdown:
| Rating | Count | Trend | Key Themes |
|--------|-------|-------|------------|
| ★★★★★ | 5 | ↑ +2 | "Best cushion ever", "back pain gone" |
| ★★★★☆ | 3 | → | "Good quality, strap could be stronger" |
| ★★★☆☆ | 1 | → | "Decent, but not $35 worth" |
| ★★☆☆☆ | 2 | ↑ +2 | "Flattened quickly", "cover tore" |
| ★☆☆☆☆ | 1 | → | "Wrong color, returning" |

### Action Items:
1. **URGENT:** 2 reports of flattening — check foam supplier batch quality
2. **HIGH:** Strap strength mentioned 3x — consider upgrading to wider strap
3. **MEDIUM:** Color accuracy — update product photos to match actual color
4. **LOW:** Price sensitivity — consider $29.99 entry-level option

### Auto-Generated Responses:
- ★★★★★ → "Thank you! Would you like to share a photo for 20% off your next order?"
- ★★★★☆ → "Thanks! We're working on a stronger strap — stay tuned!"
- ★★★☆☆ → "We appreciate your honesty. Here's a 15% discount code for your next purchase."
- ★★☆☆☆ → [See support_responder output]
- ★☆☆☆☆ → "We're sorry. Full refund + free return shipping. No questions asked."

**Response rate target:** 100% within 24 hours
**Current response rate:** 83% (10/12 responded)""",

        # Missing agents — Legal
        "redline_drafter": """## Redline Recommendations — TechCorp MSA

### Critical Redlines (Must Change):

**1. Unlimited Liability (Section 8.2)**
- **Current:** "Vendor's liability for data breaches is unlimited"
- **Redline:** "Vendor's liability for data breaches shall not exceed 12 months of fees paid under this Agreement ($800,000)"
- **Rationale:** Industry standard is 6-12 months fees. Unlimited liability is a deal-breaker.

**2. Broad IP Assignment (Section 11.4)**
- **Current:** "All IP created during the engagement shall be owned by Vendor"
- **Redline:** "IP created specifically for Client's project shall be owned by Client. Vendor retains rights to pre-existing IP and general-purpose tools."
- **Rationale:** Current clause assigns ALL IP including Client's proprietary work.

**3. Auto-Renewal (Section 14.1)**
- **Current:** "Agreement auto-renews for 1 year with 90-day notice"
- **Redline:** "Agreement auto-renews for 6 months with 60-day notice. Either party may terminate for convenience with 30-day notice after initial term."
- **Rationale:** 90-day notice is excessive. 6-month renewal gives flexibility.

### Suggested Additions:
- **Data Portability (new section):** "Upon termination, Vendor shall provide 90-day data export in standard formats"
- **SLA Penalties (Section 6.3):** "For each 0.1% below 99.95% uptime, Client receives 5% monthly credit"
- **Insurance (new section):** "Vendor shall maintain $5M cyber liability insurance"

### Negotiation Priority:
1. 🔴 Liability cap — non-negotiable
2. 🔴 IP assignment — non-negotiable
3. 🟡 Auto-renewal — flexible on terms
4. 🟢 SLA penalties — nice to have""",
        "compliance_checker": """## Compliance Check — TechCorp MSA

### GDPR Compliance:
| Requirement | Status | Notes |
|-------------|--------|-------|
| Data Processing Agreement | ⚠️ MISSING | Must be signed before processing EU data |
| Right to Erasure | ✅ Covered | Section 9.3 allows data deletion |
| Data Portability | ⚠️ PARTIAL | Export mentioned but no format specified |
| Breach Notification | ✅ Covered | 72-hour notification in Section 8.4 |
| DPO Appointment | ❓ UNKNOWN | Ask Vendor if they have a Data Protection Officer |

### SOC 2 Type II:
| Requirement | Status | Notes |
|-------------|--------|-------|
| SOC 2 Report | ⚠️ PENDING | Vendor claims compliance but report not provided |
| Audit Rights | ✅ Covered | Section 12.1 allows annual audit |
| Subprocessor List | ⚠️ MISSING | No list of subcontractors provided |
| Incident Response Plan | ✅ Covered | Referenced in Section 8.5 |

### HIPAA (if applicable):
| Requirement | Status | Notes |
|-------------|--------|-------|
| BAA Required | ❓ TBD | Only if handling PHI — confirm with Client |
| Encryption at Rest | ✅ Covered | AES-256 mentioned in security docs |
| Encryption in Transit | ✅ Covered | TLS 1.2+ required |
| Access Controls | ✅ Covered | RBAC mentioned in Section 7.2 |

### Overall Compliance Score: 7.5/10
**Blockers:** Missing DPA, no SOC 2 report, no subprocessor list
**Recommendation:** Request these 3 items before signing""",

        # Missing agents — HR
        "interview_prep": """## Interview Prep — Senior Python Developer

### Phone Screen Questions (30 min):

**Technical (15 min):**
1. "Walk me through how you'd design a REST API for a multi-tenant SaaS application"
2. "How do you handle database migrations in a zero-downtime deployment?"
3. "Explain the difference between ASGI and WSGI. When would you use each?"
4. "How do you implement rate limiting in FastAPI?"
5. "Describe your approach to testing async Python code"

**Behavioral (10 min):**
1. "Tell me about a time you had to debug a production issue under pressure"
2. "How do you handle disagreements with teammates about technical decisions?"
3. "Describe a project you're most proud of and your specific contribution"

**Culture Fit (5 min):**
1. "What does your ideal work environment look like?"
2. "What are you looking for in your next role?"

### Evaluation Rubric:
| Criteria | Weight | What to Listen For |
|----------|--------|-------------------|
| Technical depth | 40% | Specific examples, not just theory |
| System design | 25% | Thinks about scale, trade-offs |
| Communication | 20% | Clear, structured answers |
| Culture fit | 15% | Collaborative, growth mindset |

### Red Flags:
- ❌ Can't explain basic Python concepts
- ❌ No experience with async/await
- ❌ Blames others for past failures
- ❌ Uncomfortable with "I don't know"

### Green Flags:
- ✅ Asks clarifying questions
- ✅ Discusses trade-offs, not just solutions
- ✅ Mentions testing and monitoring
- ✅ Shows curiosity about our stack

### Decision Framework:
- **Strong Hire:** 8+ on technical, 7+ on all others
- **Hire:** 7+ on technical, 6+ on all others
- **No Hire:** Below 6 on any category""",
        "onboarding_automator": """## Onboarding Package — Alex Rivera

**Start Date:** June 23, 2026
**Role:** Senior Python Developer (Backend)
**Manager:** [Manager Name]

### Pre-Arrival (June 16-22):
- [ ] Laptop ordered (MacBook Pro 16", M4 Pro)
- [ ] GitHub org access granted
- [ ] AWS IAM account created (dev environment)
- [ ] Slack channels added: #backend, #engineering, #deployments
- [ ] 1Password vault access granted
- [ ] Calendar invites sent for Week 1

### Day 1 (June 23):
| Time | Activity | Owner |
|------|----------|-------|
| 9:00 AM | Welcome + office tour | Manager |
| 10:00 AM | IT setup (laptop, accounts) | IT |
| 11:00 AM | Team introductions | Team |
| 12:00 PM | Lunch with buddy | Buddy |
| 1:00 PM | Codebase walkthrough | Senior Dev |
| 2:00 PM | First issue assigned (good first issue) | Manager |
| 3:00 PM | 1:1 with manager | Manager |
| 4:00 PM | Self-study: Architecture docs | Alex |

### Week 1 Goals:
- [ ] Complete IT setup and access
- [ ] Read architecture documentation
- [ ] Ship first PR (documentation fix or small bug)
- [ ] Meet all team members
- [ ] Understand deployment process

### 30-60-90 Day Plan:
**Days 1-30:** Learn codebase, ship small features, understand team dynamics
**Days 31-60:** Own a feature end-to-end, participate in on-call rotation
**Days 61-90:** Lead a technical discussion, mentor a junior dev, propose an improvement

### Resources:
- 📚 Architecture docs: [Confluence link]
- 🔧 Dev environment setup: [README link]
- 💬 Team Slack: #backend
- 📅 Sprint calendar: [Jira link]
- 🎓 Learning budget: $500/year for courses/books

### Buddy Assignment:
**Name:** [Senior Dev Name]
**Role:** Day-to-day questions, code reviews, culture guide
**Check-ins:** Daily Week 1, then 2x/week""",
    }

    # Return matching output or generic
    for key, value in outputs.items():
        if key in agent_id:
            return value

    return f"[Demo output for {agent_id}]\n\nThis agent would process the input using the configured prompt and model (openrouter/owl-alpha).\n\nWith a live API key, this generates unique, contextual output for each run."

    # Return matching output or generic
    for key, value in outputs.items():
        if key in agent_id:
            return value

    return f"[Demo output for {agent_id}]\n\nThis agent would process the input using the configured prompt and model (openrouter/owl-alpha).\n\nWith a live API key, this generates unique, contextual output for each run."


async def run_all_pipelines() -> None:
    """Run all 5 pipeline demos."""
    pipelines = ["healthcare_prior_auth", "real_estate_lead_gen", "ecommerce_operations", "legal_contract_review", "hr_operations"]
    for p in pipelines:
        await run_pipeline_demo(p)
        print("\n\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--all" in args:
        asyncio.run(run_all_pipelines())
    elif "--healthcare" in args:
        asyncio.run(run_pipeline_demo("healthcare_prior_auth"))
    elif "--real-estate" in args:
        asyncio.run(run_pipeline_demo("real_estate_lead_gen"))
    elif "--ecommerce" in args:
        asyncio.run(run_pipeline_demo("ecommerce_operations"))
    elif "--legal" in args:
        asyncio.run(run_pipeline_demo("legal_contract_review"))
    elif "--hr" in args:
        asyncio.run(run_pipeline_demo("hr_operations"))
    else:
        print("Usage:")
        print("  uv run python examples/run_pipeline.py --healthcare")
        print("  uv run python examples/run_pipeline.py --real-estate")
        print("  uv run python examples/run_pipeline.py --ecommerce")
        print("  uv run python examples/run_pipeline.py --legal")
        print("  uv run python examples/run_pipeline.py --hr")
        print("  uv run python examples/run_pipeline.py --all")
