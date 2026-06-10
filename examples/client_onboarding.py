"""
Client Onboarding Pipeline — Runner
Demonstrates the full 4-agent onboarding workflow.

Usage:
  uv run python examples/client_onboarding.py              # Demo mode (no API key needed)
  uv run python examples/client_onboarding.py --live       # Live mode (needs OPENROUTER_API_KEY)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentkit.core.context import ContextManager
from agentkit.llm import LLMClient
from agentkit.observability.metrics import MetricsCollector


SAMPLE_CLIENT_INPUT = """
Company: MedVantage Health Solutions
Contact: Sarah Chen, VP of Operations (sarah@medvantage.com)
Industry: Healthcare / HealthTech
Size: ~200 employees, Series B
Problem: "We're drowning in prior authorization requests. Our team of 12 spends
  60% of their time on paperwork — faxing, calling insurers, following up.
  We need to automate this entire workflow. We've tried basic RPA but it
  breaks when insurers change their forms. We need something smarter."
Budget: $8,000-$12,000/month for the right solution
Timeline: Need Phase 1 live in 6 weeks
Stakeholders: Sarah (sponsor), Dr. Patel (CMO), Mike Torres (IT Lead)
Notes: Currently using Epic EHR. Must be HIPAA compliant. Competitor
  AuthAuto just raised $40M — board is pushing for AI adoption.
"""


def print_header(text: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_agent_output(agent_name: str, output: str, elapsed: float) -> None:
    print(f"\n{'─'*60}")
    print(f"  🤖 {agent_name}  ({elapsed:.1f}s)")
    print(f"{'─'*60}")
    # Print first 800 chars of output
    preview = output[:800] + ("..." if len(output) > 800 else "")
    print(preview)


async def run_demo_pipeline() -> None:
    """Run the pipeline in demo mode — shows structure without LLM calls."""
    print_header("CLIENT ONBOARDING PIPELINE — DEMO MODE")
    print("  (No API key — showing pipeline structure and sample output)\n")

    start = datetime.now()

    # ── Agent 1: INTAKE ──
    print("▶ Agent 1/4: INTAKE — Extracting structured data from raw input...")
    await asyncio.sleep(0.5)

    intake_output = {
        "company_name": "MedVantage Health Solutions",
        "industry": "Healthcare / HealthTech",
        "company_size": "~200 employees, Series B",
        "primary_contact": {"name": "Sarah Chen", "role": "VP of Operations", "email": "sarah@medvantage.com"},
        "stated_problem": "Automating prior authorization workflow — currently 60% of 12-person team spent on paperwork, faxing, insurer follow-ups. Previous RPA attempt failed due to form changes.",
        "budget_range": "$8,000-$12,000/month",
        "timeline": "Phase 1 live in 6 weeks",
        "key_stakeholders": ["Sarah Chen (VP Ops, sponsor)", "Dr. Patel (CMO)", "Mike Torres (IT Lead)"],
        "raw_notes": "Uses Epic EHR. Must be HIPAA compliant. Competitor AuthAuto raised $40M. Board pushing AI adoption."
    }

    print_agent_output("INTAKE", json.dumps(intake_output, indent=2), 0.5)

    # ── Agent 2: RESEARCH ──
    print("\n▶ Agent 2/4: RESEARCH — Industry analysis and opportunity mapping...")
    await asyncio.sleep(0.5)

    research_output = """## Industry Overview
HealthTech prior authorization is a $4.2B market growing at 18% CAGR. CMS final rules (2026) now require electronic prior auth for Medicare Advantage, accelerating adoption. 73% of providers still use fax/phone as primary method.

## Key Challenges
1. **Form variability**: Each insurer has unique prior auth forms that change quarterly — breaks traditional RPA
2. **HIPAA compliance**: Any automation must handle PHI securely, requiring BAA with cloud providers
3. **EHR integration**: Epic's FHIR API is powerful but complex; most teams lack in-house expertise

## Competitive Landscape
- AuthAuto ($40M raised): Rules-based + basic ML, strong in payer-side, weak on provider workflow
- Cohere Health: Clinical AI approach, expensive ($15K+/mo), long implementation
- Olive AI: Shut down — cautionary tale about over-promising on autonomous agents

## Opportunity Areas
1. **Intelligent document processing**: LLM-based form understanding that adapts to changes (no retraining)
2. **Payer communication automation**: Auto-detect insurer requirements, submit via API or fax fallback
3. **Status tracking dashboard**: Real-time visibility into all pending auths — biggest pain point for staff

## Risks & Considerations
- HIPAA: Must use AWS GovCloud or Azure Healthcare with BAA
- Epic integration: Need Epic App Orchard approval or FHIR R4 API access
- Change management: Staff may resist — need training plan
- Regulatory: CMS interoperability rules evolving — build for flexibility"""

    print_agent_output("RESEARCH", research_output, 0.5)

    # ── Agent 3: BRIEF WRITER ──
    print("\n▶ Agent 3/4: BRIEF WRITER — Generating project brief...")
    await asyncio.sleep(0.5)

    brief_output = """# Project Brief: Prior Authorization Automation
## MedVantage Health Solutions

### Executive Summary
MedVantage Health Solutions seeks to automate their prior authorization workflow, currently consuming 60% of a 12-person operations team. This engagement will deploy an AI-powered agent pipeline that intelligently processes auth requests, adapts to insurer form changes, and integrates with their Epic EHR — targeting 70% reduction in manual processing time.

### Client Background
- **Company**: MedVantage Health Solutions (~200 employees, Series B)
- **Industry**: Healthcare / HealthTech
- **Tech Stack**: Epic EHR, cloud infrastructure (TBD)
- **Sponsor**: Sarah Chen, VP of Operations
- **Urgency**: Board-level pressure following competitor AuthAuto's $40M raise

### Problem Statement
Prior authorization is the #1 operational bottleneck. The team manually processes auth requests across 15+ insurers, each with unique and frequently changing forms. A previous RPA attempt failed because it couldn't adapt to form changes. Staff spend ~4 hours/day on faxing, calling, and follow-ups that could be automated.

### Proposed Solution
A multi-agent AI pipeline:
- **Intake Agent**: Extracts auth request data from any source (fax, email, portal)
- **Classifier Agent**: Identifies insurer, procedure code, required documentation
- **Submission Agent**: Completes and submits via insurer API or fax fallback
- **Tracker Agent**: Monitors status, escalates denials, alerts on SLA breaches
- **Dashboard**: Real-time visibility for operations team

### Scope of Work
**Phase 1 (Weeks 1-6)**: Core pipeline for top 3 insurers, Epic FHIR integration, HIPAA-compliant deployment
**Phase 2 (Weeks 7-12)**: Expand to all 15+ insurers, add denial management workflow
**Phase 3 (Weeks 13-16)**: Analytics dashboard, staff training, optimization

### Deliverables
- Deployed agent pipeline (staging + production)
- Epic EHR integration module
- HIPAA compliance documentation + BAA
- Admin dashboard (Streamlit)
- Staff training materials
- 30-day post-launch support

### Timeline Estimate
16 weeks total (4 weeks per phase + 4 weeks buffer)

### Investment Range
- Phase 1: $24,000 ($8,000/mo x 3 months)
- Phase 2: $21,000 ($7,000/mo x 3 months)
- Phase 3: $12,000 ($6,000/mo x 2 months)
- **Total: $57,000** (within stated $8K-$12K/mo budget)

### Next Steps
1. Schedule technical discovery call with Mike Torres (IT Lead) — Epic API access assessment
2. Sign BAA and initiate HIPAA compliance review
3. Begin Phase 1 sprint planning with Sarah's team"""

    print_agent_output("BRIEF WRITER", brief_output, 0.5)

    # ── Agent 4: OUTREACH ──
    print("\n▶ Agent 4/4: OUTREACH — Welcome email + kickoff agenda...")
    await asyncio.sleep(0.5)

    outreach_output = """## Welcome Email

**Subject:** Welcome to the team — your prior authorization automation journey starts now

Hi Sarah,

Thank you for choosing us to tackle MedVantage's prior authorization challenge. We've reviewed your situation and we're confident we can help your team reclaim those lost hours.

Here's what happens next:
1. This week: We'll schedule a 30-minute technical discovery call with Mike to assess your Epic integration points
2. Next week: We'll share a detailed Phase 1 project plan for your sign-off
3. Week 3: Development kicks off

In the meantime, if you have any questions, just reply to this email or book a slot on my calendar: [calendly link]

Looking forward to helping MedVantage lead the way in healthcare automation.

Best,
[Agency Name]

---

## Kickoff Meeting Agenda (60 minutes)

1. **Introductions & Roles** (5 min) — Who's who on both teams
2. **Project Vision Alignment** (10 min) — Confirm goals, success metrics, constraints
3. **Technical Deep-Dive** (20 min) — Epic EHR access, insurer list, current workflow walkthrough
4. **Compliance & Security** (10 min) — HIPAA requirements, BAA, data handling
5. **Phase 1 Plan Review** (10 min) — Timeline, milestones, deliverables
6. **Q&A and Next Steps** (5 min) — Action items, communication cadence

---

## Internal Pre-Kickoff Checklist

- [ ] Create project in AgentsFactory dashboard
- [ ] Set up HIPAA-compliant AWS environment (GovCloud)
- [ ] Prepare Epic FHIR API documentation request
- [ ] Draft BAA for legal review
- [ ] Build insurer form sample library (top 3 insurers)
- [ ] Prepare demo environment with sample auth request
- [ ] Assign team: 1 PM, 1 backend, 1 ML engineer
- [ ] Set up Slack channel: #medvantage-onboarding"""

    print_agent_output("OUTREACH", outreach_output, 0.5)

    # ── Summary ──
    elapsed = (datetime.now() - start).total_seconds()
    print_header("PIPELINE COMPLETE")
    print(f"  Total time:     {elapsed:.1f}s")
    print(f"  Agents run:     4/4")
    print(f"  Output files:   3 (brief, email, checklist)")
    print(f"  Est. value:     $57,000 project")
    print(f"  Time saved:     ~15 hours of manual onboarding work")
    print(f"\n  💡 With a real OpenRouter API key, this pipeline runs live")
    print(f"     and generates unique output for each new client.\n")


async def run_live_pipeline() -> None:
    """Run the pipeline with real LLM calls."""
    print_header("CLIENT ONBOARDING PIPELINE — LIVE MODE")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set. Run with --demo or set the key.")
        sys.exit(1)

    client = LLMClient(api_key=api_key)
    metrics = MetricsCollector()

    print("▶ Running 4-agent pipeline with live LLM calls...\n")
    print("  (This will take 30-60 seconds)\n")

    start = datetime.now()

    # Agent 1: Intake
    print("▶ Agent 1/4: INTAKE...")
    r1 = await client.chat(
        messages=[{"role": "user", "content": f"Extract structured client data from this input. Output ONLY valid JSON with fields: company_name, industry, company_size, primary_contact, stated_problem, budget_range, timeline, key_stakeholders, raw_notes.\n\n{SAMPLE_CLIENT_INPUT}"}],
        model="openrouter/owl-alpha",
    )
    print(f"  ✓ {r1.usage.output_tokens} tokens, ${r1.cost:.4f}")

    # Agent 2: Research
    print("▶ Agent 2/4: RESEARCH...")
    r2 = await client.chat(
        messages=[{"role": "user", "content": f"Based on this client data, produce a research brief covering: Industry Overview, Key Challenges, Competitive Landscape, Opportunity Areas, Risks & Considerations.\n\n{r1.text}"}],
        model="openrouter/owl-alpha",
    )
    print(f"  ✓ {r2.usage.output_tokens} tokens, ${r2.cost:.4f}")

    # Agent 3: Brief
    print("▶ Agent 3/4: BRIEF WRITER...")
    r3 = await client.chat(
        messages=[{"role": "user", "content": f"Generate a professional project brief (Executive Summary, Client Background, Problem Statement, Proposed Solution, Scope of Work with 3 phases, Deliverables, Timeline, Investment Range, Next Steps) based on:\n\nClient Data: {r1.text}\n\nResearch: {r2.text}"}],
        model="openrouter/owl-alpha",
    )
    print(f"  ✓ {r3.usage.output_tokens} tokens, ${r3.cost:.4f}")

    # Agent 4: Outreach
    print("▶ Agent 4/4: OUTREACH...")
    r4 = await client.chat(
        messages=[{"role": "user", "content": f"Based on this project brief, generate: 1) Welcome email (subject + body), 2) Kickoff meeting agenda (6 items, 60 min), 3) Internal pre-kickoff checklist.\n\n{r3.text}"}],
        model="openrouter/owl-alpha",
    )
    print(f"  ✓ {r4.usage.output_tokens} tokens, ${r4.cost:.4f}")

    elapsed = (datetime.now() - start).total_seconds()
    total_cost = r1.cost + r2.cost + r3.cost + r4.cost
    total_tokens = r1.usage.output_tokens + r2.usage.output_tokens + r3.usage.output_tokens + r4.usage.output_tokens

    print_header("LIVE PIPELINE COMPLETE")
    print(f"  Total time:     {elapsed:.1f}s")
    print(f"  Total tokens:   {total_tokens:,}")
    print(f"  Total cost:     ${total_cost:.4f}")
    print(f"  Agents run:     4/4")

    # Save outputs
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    (output_dir / f"intake_{ts}.json").write_text(r1.text)
    (output_dir / f"research_{ts}.md").write_text(r2.text)
    (output_dir / f"brief_{ts}.md").write_text(r3.text)
    (output_dir / f"outreach_{ts}.md").write_text(r4.text)

    print(f"\n  📁 Outputs saved to: {output_dir}/\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--live" in args:
        asyncio.run(run_live_pipeline())
    else:
        asyncio.run(run_demo_pipeline())
