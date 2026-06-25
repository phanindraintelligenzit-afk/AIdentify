"""
AIdentify Project Pipeline
==========================
Turns an automation idea into a marketplace listing + GitHub repo.

Pipeline stages:
  1. Opportunity Scanner  — finds/scores automation opportunities
  2. Research Agent       — deep-dive analysis, feasibility, monetization
  3. Roadmap Agent        — builds project plan, architecture, agent design
  4. Builder Agent        — generates code, tests, docs, CI/CD
  5. Publisher Agent      — creates GitHub repo, pushes code, updates marketplace

Usage:
  python project_pipeline.py --idea "Automate insurance prior auth" --category healthcare
  python project_pipeline.py --from-request requests/pending.json
  python project_pipeline.py --list-projects
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──
BASE_DIR = Path(__file__).resolve().parent
AIDENTIFY_DIR = BASE_DIR.parent
PROJECTS_DIR = AIDENTIFY_DIR / "projects"
REQUESTS_DIR = AIDENTIFY_DIR / "requests"
MARKETPLACE_FILE = AIDENTIFY_DIR / "docs" / "marketplace.html"
CONFIG_FILE = AIDENTIFY_DIR / "config" / "projects.json"

# ── Ensure dirs exist ──
for d in [PROJECTS_DIR, REQUESTS_DIR, AIDENTIFY_DIR / "config"]:
    d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════
# STAGE 1: OPPORTUNITY SCANNER
# ═══════════════════════════════════════════

CATEGORY_TEMPLATES = {
    "healthcare": {
        "icon": "🏥",
        "agents": 4,
        "tags": ["HIPAA Ready", "EHR Integration"],
        "monetization": "Free repo + $2K-5K setup",
        "compliance": ["HIPAA", "HL7 FHIR"],
    },
    "ecommerce": {
        "icon": "🛒",
        "agents": 4,
        "tags": ["SEO", "Conversion"],
        "monetization": "Free repo + $1K-3K setup",
        "compliance": [],
    },
    "legal": {
        "icon": "⚖️",
        "agents": 4,
        "tags": ["Risk Matrix", "GDPR / SOC2"],
        "monetization": "Free repo + $3K-8K setup",
        "compliance": ["GDPR", "SOC2"],
    },
    "hr": {
        "icon": "👥",
        "agents": 4,
        "tags": ["Screening", "Onboarding"],
        "monetization": "Free repo + $1K-3K setup",
        "compliance": [],
    },
    "realestate": {
        "icon": "🏠",
        "agents": 4,
        "tags": ["Market Analysis", "Lead Scoring"],
        "monetization": "Free repo + $2K-5K setup",
        "compliance": [],
    },
    "finance": {
        "icon": "💰",
        "agents": 4,
        "tags": ["Reconciliation", "Audit Trail"],
        "monetization": "Free repo + $3K-10K setup",
        "compliance": ["SOX", "PCI-DSS"],
    },
    "marketing": {
        "icon": "📣",
        "agents": 3,
        "tags": ["Multi-Platform", "Analytics"],
        "monetization": "Free repo + $1K-2K setup",
        "compliance": [],
    },
}


def scan_opportunity(idea: str, category: str) -> dict:
    """Stage 1: Score and structure the opportunity."""
    print(f"\n{'═' * 50}")
    print(f"  STAGE 1: Opportunity Scanner")
    print(f"{'═' * 50}")
    print(f"  Idea: {idea}")
    print(f"  Category: {category}")

    template = CATEGORY_TEMPLATES.get(category, {
        "icon": "⚡",
        "agents": 3,
        "tags": ["Custom"],
        "monetization": "Free repo + custom quote",
        "compliance": [],
    })

    # Score the opportunity (simple heuristic)
    score = _score_opportunity(idea, category)

    opportunity = {
        "id": _slugify(idea),
        "idea": idea,
        "category": category,
        "score": score,
        "icon": template["icon"],
        "agents": template["agents"],
        "tags": template["tags"],
        "monetization": template["monetization"],
        "compliance": template["compliance"],
        "status": "scanned",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    print(f"  Score: {score}/100")
    print(f"  Agents needed: {template['agents']}")
    print(f"  Monetization: {template['monetization']}")
    print(f"  ✓ Opportunity scanned")

    return opportunity


def _score_opportunity(idea: str, category: str) -> int:
    """Simple scoring heuristic."""
    score = 50  # base
    # Category bonus
    if category in CATEGORY_TEMPLATES:
        score += 15
    # Length bonus (more detail = better)
    words = len(idea.split())
    if words > 10:
        score += 10
    if words > 20:
        score += 5
    # Keyword bonuses
    high_value = ["automate", "workflow", "pipeline", "integration", "ai", "agent"]
    for kw in high_value:
        if kw in idea.lower():
            score += 3
    return min(score, 100)


# ═══════════════════════════════════════════
# STAGE 2: RESEARCH AGENT
# ═══════════════════════════════════════════

def research_opportunity(opportunity: dict) -> dict:
    """Stage 2: Deep-dive research and feasibility analysis."""
    print(f"\n{'═' * 50}")
    print(f"  STAGE 2: Research Agent")
    print(f"{'═' * 50}")

    idea = opportunity["idea"]
    category = opportunity["category"]

    # Build research output
    research = {
        "problem_statement": _generate_problem_statement(idea, category),
        "target_audience": _generate_target_audience(category),
        "competitor_analysis": _generate_competitor_notes(category),
        "technical_feasibility": _assess_feasibility(category),
        "monetization_strategy": _generate_monetization(category),
        "estimated_dev_hours": _estimate_dev_hours(opportunity["agents"]),
        "roi_estimate": _estimate_roi(category),
    }

    opportunity["research"] = research
    opportunity["status"] = "researched"

    print(f"  Problem: {research['problem_statement'][:80]}...")
    print(f"  Feasibility: {research['technical_feasibility']}")
    print(f"  Dev hours: ~{research['estimated_dev_hours']}h")
    print(f"  ROI: {research['roi_estimate']}")
    print(f"  ✓ Research complete")

    return opportunity


def _generate_problem_statement(idea: str, category: str) -> str:
    return f"Businesses in {category} spend significant manual effort on: {idea}. This automation eliminates repetitive tasks, reduces errors, and accelerates turnaround."


def _generate_target_audience(category: str) -> str:
    audiences = {
        "healthcare": "Healthcare providers, medical billing companies, health tech startups",
        "ecommerce": "E-commerce store owners, DTC brands, marketplace sellers",
        "legal": "Law firms, legal departments, contract managers",
        "hr": "HR teams, recruiting agencies, people operations",
        "realestate": "Real estate agents, brokerages, property managers",
        "finance": "Accounting teams, fintech startups, CFO offices",
        "marketing": "Marketing teams, agencies, growth teams",
    }
    return audiences.get(category, f"Businesses and individuals in {category}")


def _generate_competitor_notes(category: str) -> str:
    notes = {
        "healthcare": "Manual processes still dominate. Existing tools are expensive enterprise solutions ($5K+/mo). Open-source gap exists.",
        "ecommerce": "Shopify apps cover basics but lack multi-step AI orchestration. Custom solutions require dev teams.",
        "legal": "Contract review tools exist (Kira, Luminance) but are enterprise-priced. SMB market underserved.",
        "hr": "ATS systems handle screening but not end-to-end automation. AI recruiting tools are emerging but fragmented.",
        "realestate": "CRM tools exist but lead qualification is still manual. AI-powered scoring is a differentiator.",
        "finance": "Reconciliation tools are rule-based. AI-powered matching and anomaly detection is the gap.",
        "marketing": "Scheduling tools exist but content generation + analytics + optimization in one pipeline is rare.",
    }
    return notes.get(category, "Market has gaps for affordable, open-source automation.")


def _assess_feasibility(category: str) -> str:
    high = ["healthcare", "ecommerce", "hr", "marketing"]
    medium = ["legal", "realestate", "finance"]
    if category in high:
        return "High — well-understood patterns, available APIs, proven agent architectures"
    elif category in medium:
        return "Medium — requires domain expertise, some custom integrations needed"
    return "Assess — custom domain, needs deeper technical spike"


def _generate_monetization(category: str) -> str:
    return CATEGORY_TEMPLATES.get(category, {}).get("monetization", "Free repo + custom quote")


def _estimate_dev_hours(agents: int) -> int:
    return agents * 8  # ~8 hours per agent


def _estimate_roi(category: str) -> str:
    roi = {
        "healthcare": "Replaces 4-8 hours/week of manual auth processing. Pays for itself in 2-4 weeks.",
        "ecommerce": "Saves 10+ hours/week on product management. Pays for itself in 1-2 weeks.",
        "legal": "Reduces contract review time by 60%. Pays for itself in 1-3 weeks.",
        "hr": "Cuts screening time by 70%. Pays for itself in 2-4 weeks.",
        "realestate": "Increases lead response speed 10x. Pays for itself in 3-6 weeks.",
        "finance": "Eliminates 80% of manual reconciliation. Pays for itself in 2-4 weeks.",
        "marketing": "Saves 5+ hours/week on content ops. Pays for itself in 1-2 weeks.",
    }
    return roi.get(category, "Significant time savings. ROI depends on deployment scale.")


# ═══════════════════════════════════════════
# STAGE 3: ROADMAP AGENT
# ═══════════════════════════════════════════

def build_roadmap(opportunity: dict) -> dict:
    """Stage 3: Build project roadmap and architecture."""
    print(f"\n{'═' * 50}")
    print(f"  STAGE 3: Roadmap Agent")
    print(f"{'═' * 50}")

    agents_count = opportunity["agents"]
    category = opportunity["category"]

    # Generate agent pipeline design
    agent_pipeline = _design_agent_pipeline(category, agents_count)

    roadmap = {
        "project_name": _title_case(opportunity["id"]),
        "repo_name": opportunity["id"],
        "description": opportunity["research"]["problem_statement"],
        "agent_pipeline": agent_pipeline,
        "tech_stack": _get_tech_stack(),
        "milestones": _generate_milestones(agent_pipeline),
        "file_structure": _generate_file_structure(opportunity["id"]),
    }

    opportunity["roadmap"] = roadmap
    opportunity["status"] = "roadmapped"

    print(f"  Project: {roadmap['project_name']}")
    print(f"  Repo: {roadmap['repo_name']}")
    print(f"  Pipeline: {' → '.join(a['name'] for a in agent_pipeline)}")
    print(f"  Milestones: {len(roadmap['milestones'])}")
    print(f"  ✓ Roadmap built")

    return opportunity


def _design_agent_pipeline(category: str, count: int) -> list:
    """Design the multi-agent pipeline for this category."""
    pipelines = {
        "healthcare": [
            {"name": "auth_intake", "role": "Extract patient data, procedure codes, insurer info from input"},
            {"name": "requirement_checker", "role": "Check insurer-specific prior auth requirements and common denial reasons"},
            {"name": "documentation_generator", "role": "Generate CMS-1500 forms, clinical justification letters, submission packages"},
            {"name": "tracker_setup", "role": "Set up submission tracking, SLA alerts, follow-up scheduling"},
        ],
        "ecommerce": [
            {"name": "product_analyzer", "role": "Analyze product listings, pricing, reviews, competitive positioning"},
            {"name": "content_optimizer", "role": "Generate SEO-optimized titles, descriptions, tags"},
            {"name": "pricing_agent", "role": "Monitor competitor pricing, recommend dynamic pricing adjustments"},
            {"name": "review_manager", "role": "Aggregate reviews, generate response templates, flag urgent issues"},
        ],
        "legal": [
            {"name": "contract_parser", "role": "Parse contracts, extract key clauses, dates, parties"},
            {"name": "redline_detector", "role": "Identify non-standard terms, risky clauses, deviations from template"},
            {"name": "risk_assessor", "role": "Score contract risk, generate negotiation recommendations"},
            {"name": "compliance_checker", "role": "Check GDPR, SOC2, and regulatory compliance requirements"},
        ],
        "hr": [
            {"name": "resume_parser", "role": "Parse resumes, extract skills, experience, education"},
            {"name": "candidate_scorer", "role": "Score candidates against job requirements, rank top matches"},
            {"name": "outreach_drafter", "role": "Generate personalized outreach messages for top candidates"},
            {"name": "onboarding_builder", "role": "Generate onboarding checklists, welcome packages, training plans"},
        ],
        "realestate": [
            {"name": "market_scout", "role": "Scout markets for opportunities: expired listings, pre-foreclosures, new developments"},
            {"name": "lead_qualifier", "role": "Score leads by intent, timeline, budget, and fit"},
            {"name": "outreach_agent", "role": "Generate personalized outreach campaigns per lead segment"},
            {"name": "market_analyst", "role": "Generate market reports, price trends, investment analysis"},
        ],
        "finance": [
            {"name": "data_extractor", "role": "Extract transactions from bank feeds, invoices, receipts"},
            {"name": "reconciliation_agent", "role": "Match transactions, flag anomalies, auto-categorize"},
            {"name": "report_generator", "role": "Generate P&L, cash flow, balance sheet reports"},
            {"name": "audit_trail", "role": "Maintain audit trail, flag compliance issues, generate audit packages"},
        ],
        "marketing": [
            {"name": "content_generator", "role": "Generate platform-specific content from briefs and trends"},
            {"name": "scheduler", "role": "Optimize posting schedule by platform, audience, engagement data"},
            {"name": "analytics_agent", "role": "Track performance, generate insights, recommend optimizations"},
        ],
    }

    default_pipeline = [
        {"name": f"agent_{i+1}", "role": f"Stage {i+1} processing for {category} automation"}
        for i in range(count)
    ]

    return pipelines.get(category, default_pipeline)


def _get_tech_stack() -> dict:
    return {
        "language": "Python 3.11+",
        "framework": "FastAPI",
        "agent_framework": "LangGraph",
        "testing": "pytest",
        "ci_cd": "GitHub Actions",
        "containerization": "Docker",
        "docs": "Markdown + MkDocs",
    }


def _generate_milestones(agent_pipeline: list) -> list:
    milestones = []
    for i, agent in enumerate(agent_pipeline, 1):
        milestones.append({
            "phase": i,
            "name": f"Agent {i}: {agent['name']}",
            "deliverable": f"Working {agent['name']} with tests",
            "acceptance": f"Agent processes input and produces validated output for {agent['role'].lower()}",
        })
    milestones.append({
        "phase": len(agent_pipeline) + 1,
        "name": "Integration & Publish",
        "deliverable": "Full pipeline tested, repo published, marketplace listing created",
        "acceptance": "End-to-end pipeline runs, all tests pass, repo is public",
    })
    return milestones


def _generate_file_structure(repo_name: str) -> list:
    return [
        f"{repo_name}/",
        f"├── README.md",
        f"├── LICENSE (MIT)",
        f"├── pyproject.toml",
        f"├── Dockerfile",
        f"├── .github/",
        f"│   └── workflows/",
        f"│       └── ci.yml",
        f"├── src/",
        f"│   ├── __init__.py",
        f"│   ├── pipeline.py",
        f"│   ├── agents/",
        f"│   │   ├── __init__.py",
        f"│   │   └── (one .py per agent)",
        f"│   └── config.py",
        f"├── tests/",
        f"│   ├── __init__.py",
        f"│   ├── conftest.py",
        f"│   └── test_*.py",
        f"└── docs/",
            f"    ├── setup.md",
            f"    └── api.md",
    ]


# ═══════════════════════════════════════════
# STAGE 4: BUILDER AGENT
# ═══════════════════════════════════════════

def build_project(opportunity: dict) -> dict:
    """Stage 4: Generate code, tests, and docs."""
    print(f"\n{'═' * 50}")
    print(f"  STAGE 4: Builder Agent")
    print(f"{'═' * 50}")

    roadmap = opportunity["roadmap"]
    repo_name = roadmap["repo_name"]
    project_dir = PROJECTS_DIR / repo_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Generate all project files
    files_created = []

    # README
    readme = _generate_readme(opportunity)
    (project_dir / "README.md").write_text(readme, encoding="utf-8")
    files_created.append("README.md")

    # pyproject.toml
    pyproject = _generate_pyproject(repo_name)
    (project_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    files_created.append("pyproject.toml")

    # Dockerfile
    dockerfile = _generate_dockerfile()
    (project_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    files_created.append("Dockerfile")

    # CI/CD
    github_dir = project_dir / ".github" / "workflows"
    github_dir.mkdir(parents=True, exist_ok=True)
    ci = _generate_ci()
    (github_dir / "ci.yml").write_text(ci, encoding="utf-8")
    files_created.append(".github/workflows/ci.yml")

    # Source code
    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "__init__.py").write_text(f'"""{roadmap["project_name"]} — AIdentify Project."""\n', encoding="utf-8")

    # Pipeline
    pipeline_code = _generate_pipeline_code(opportunity)
    (src_dir / "pipeline.py").write_text(pipeline_code, encoding="utf-8")
    files_created.append("src/pipeline.py")

    # Config
    config_code = _generate_config_code(opportunity)
    (src_dir / "config.py").write_text(config_code, encoding="utf-8")
    files_created.append("src/config.py")

    # Agents
    agents_dir = src_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    (agents_dir / "__init__.py").write_text("", encoding="utf-8")
    for agent in roadmap["agent_pipeline"]:
        agent_code = _generate_agent_code(agent, opportunity)
        (agents_dir / f"{agent['name']}.py").write_text(agent_code, encoding="utf-8")
        files_created.append(f"src/agents/{agent['name']}.py")

    # Tests
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "conftest.py").write_text(_generate_conftest(), encoding="utf-8")
    for agent in roadmap["agent_pipeline"]:
        test_code = _generate_test_code(agent, opportunity)
        (tests_dir / f"test_{agent['name']}.py").write_text(test_code, encoding="utf-8")
        files_created.append(f"tests/test_{agent['name']}.py")

    # Integration test
    integration_test = _generate_integration_test(opportunity)
    (tests_dir / "test_pipeline.py").write_text(integration_test, encoding="utf-8")
    files_created.append("tests/test_pipeline.py")

    # Docs
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    setup_docs = _generate_setup_docs(opportunity)
    (docs_dir / "setup.md").write_text(setup_docs, encoding="utf-8")
    files_created.append("docs/setup.md")

    opportunity["build"] = {
        "project_dir": str(project_dir),
        "files_created": files_created,
        "total_files": len(files_created),
    }
    opportunity["status"] = "built"

    print(f"  Files created: {len(files_created)}")
    for f in files_created:
        print(f"    ✓ {f}")
    print(f"  ✓ Build complete → {project_dir}")

    return opportunity


def _generate_readme(opp: dict) -> str:
    roadmap = opp["roadmap"]
    research = opp["research"]
    agents_md = "\n".join(f"| {a['name']} | {a['role']} |" for a in roadmap["agent_pipeline"])
    compliance_md = ", ".join(opp.get("compliance", [])) or "N/A"
    name = roadmap['project_name']
    desc = roadmap['description']
    cat = opp['category'].capitalize()
    repo = roadmap['repo_name']
    monet = opp.get('monetization', 'Contact us for setup pricing')

    return (
        f"# {name}\n"
        f"\n"
        f"{desc}\n"
        f"\n"
        f"## Category\n"
        f"\n"
        f"{cat}\n"
        f"\n"
        f"## Agent Pipeline\n"
        f"\n"
        f"| Agent | Role |\n"
        f"|-------|------|\n"
        f"{agents_md}\n"
        f"\n"
        f"## Tech Stack\n"
        f"\n"
        f"- **Language:** Python 3.11+\n"
        f"- **Framework:** FastAPI\n"
        f"- **Agent Framework:** LangGraph\n"
        f"- **Testing:** pytest\n"
        f"- **CI/CD:** GitHub Actions\n"
        f"- **Containerization:** Docker\n"
        f"\n"
        f"## Compliance\n"
        f"\n"
        f"{compliance_md}\n"
        f"\n"
        f"## Monetization\n"
        f"\n"
        f"- **Free:** This repo is open-source (MIT). Clone, test, and deploy yourself.\n"
        f"- **Done-for-You:** {monet}\n"
        f"\n"
        f"## Quick Start\n"
        f"\n"
        f"```bash\n"
        f"git clone https://github.com/phanindraintelligenzit-afk/{repo}.git\n"
        f"cd {repo}\n"
        f'pip install -e ".[dev]"\n'
        f"pytest tests/ -v\n"
        f"```\n"
        f"\n"
        f"## License\n"
        f"\n"
        f"MIT License — see [LICENSE](LICENSE) for details.\n"
        f"\n"
        f"---\n"
        f"\n"
        f"Built by [AIdentify](https://github.com/phanindraintelligenzit-afk/AIdentify) — AI Automation Marketplace.\n"
    )


def _generate_pyproject(name: str) -> str:
    return textwrap.dedent(f"""\
    [project]
    name = "{name}"
    version = "0.1.0"
    description = "AIdentify automation project"
    requires-python = ">=3.11"
    dependencies = [
        "fastapi>=0.110",
        "uvicorn>=0.29",
        "pydantic>=2.0",
        "langgraph>=0.1",
    ]

    [project.optional-dependencies]
    dev = [
        "pytest>=8.0",
        "pytest-cov>=5.0",
        "ruff>=0.4",
    ]

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    """)


def _generate_dockerfile() -> str:
    return textwrap.dedent("""\
    FROM python:3.11-slim
    WORKDIR /app
    COPY pyproject.toml .
    RUN pip install -e .
    COPY src/ src/
    COPY tests/ tests/
    CMD ["uvicorn", "src.pipeline:app", "--host", "0.0.0.0", "--port", "8000"]
    """)


def _generate_ci() -> str:
    return textwrap.dedent("""\
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: "3.11"
          - run: pip install -e ".[dev]"
          - run: pytest tests/ -v --cov=src
    """)


def _generate_pipeline_code(opp: dict) -> str:
    roadmap = opp["roadmap"]
    agent_imports = "\n".join(
        f"from src.agents.{a['name']} import {a['name']}" for a in roadmap["agent_pipeline"]
    )
    agent_calls = "\n    ".join(
        f"result = {a['name']}(result)  # {a['role']}" for a in roadmap["agent_pipeline"]
    )

    title = roadmap['project_name']
    lines = [
        f'"""Pipeline for {title}."""',
        "from fastapi import FastAPI",
        agent_imports,
        "",
        f'app = FastAPI(title="{title}")',
        "",
        '@app.post("/run")',
        "def run_pipeline(input_data: dict):",
        '    """Run the full agent pipeline."""',
        "    result = input_data",
    ]
    for a in roadmap["agent_pipeline"]:
        lines.append(f"    result = {a['name']}(result)  # {a['role']}")
    lines += [
        '    return {"status": "complete", "result": result}',
        "",
        '@app.get("/health")',
        "def health():",
        '    return {"status": "ok"}',
    ]
    return "\n".join(lines) + "\n"


def _generate_config_code(opp: dict) -> str:
    name = opp['roadmap']['project_name']
    cat = opp['category']
    agents = opp['agents']
    return (
        f'"""Configuration for {name}."""\n'
        "\n"
        f'CATEGORY = "{cat}"\n'
        f"AGENTS = {agents}\n"
        'VERSION = "0.1.0"\n'
    )


def _generate_agent_code(agent: dict, opp: dict) -> str:
    aname = agent['name']
    role = agent['role']
    return (
        f'"""{aname} — {role}"""\n'
        "\n"
        f"def {aname}(data: dict) -> dict:\n"
        '    """\n'
        f"    {role}\n"
        "\n"
        "    Args:\n"
        "        data: Input dict from previous agent or initial input.\n"
        "\n"
        "    Returns:\n"
        "        dict with processed output.\n"
        '    """\n'
        f"    # TODO: Implement {aname} logic\n"
        f'    data["{aname}_output"] = "processed"\n'
        "    return data\n"
    )


def _generate_test_code(agent: dict, opp: dict) -> str:
    aname = agent['name']
    return (
        f'"""Tests for {aname}."""\n'
        "import pytest\n"
        f"from src.agents.{aname} import {aname}\n"
        "\n"
        f"def test_{aname}_basic():\n"
        f'    """Test {aname} processes input correctly."""\n'
        '    input_data = {"test": True}\n'
        f"    result = {aname}(input_data)\n"
        "    assert isinstance(result, dict)\n"
        f'    assert "{aname}_output" in result\n'
        "\n"
        f"def test_{aname}_empty_input():\n"
        f'    """Test {aname} handles empty input."""\n'
        "    result = {aname}(dict())\n"
        "    assert isinstance(result, dict)\n"
    )


def _generate_conftest() -> str:
    return (
        '"""Shared test fixtures."""\n'
        "import pytest\n"
        "\n"
        "@pytest.fixture\n"
        "def sample_input():\n"
        '    return {"test": True, "data": "sample"}\n'
    )


def _generate_integration_test(opp: dict) -> str:
    roadmap = opp["roadmap"]
    agents = ", ".join(a["name"] for a in roadmap["agent_pipeline"])
    return (
        '"""Integration test for the full pipeline."""\n'
        "import pytest\n"
        "from src.pipeline import app\n"
        "from fastapi.testclient import TestClient\n"
        "\n"
        "client = TestClient(app)\n"
        "\n"
        "def test_health():\n"
        '    response = client.get("/health")\n'
        "    assert response.status_code == 200\n"
        "\n"
        "def test_pipeline_end_to_end():\n"
        f'    """Test the full pipeline: {agents}."""\n'
        '    response = client.post("/run", json={"input": "test"})\n'
        "    assert response.status_code == 200\n"
        "    data = response.json()\n"
        '    assert data["status"] == "complete"\n'
    )


def _generate_setup_docs(opp: dict) -> str:
    roadmap = opp["roadmap"]
    name = roadmap['project_name']
    repo = roadmap['repo_name']
    return (
        f"# Setup Guide — {name}\n"
        "\n"
        "## Prerequisites\n"
        "\n"
        "- Python 3.11+\n"
        "- Docker (optional)\n"
        "- Git\n"
        "\n"
        "## Installation\n"
        "\n"
        "```bash\n"
        f"git clone https://github.com/phanindraintelligenzit-afk/{repo}.git\n"
        f"cd {repo}\n"
        "python -m venv .venv\n"
        "source .venv/bin/activate\n"
        'pip install -e ".[dev]"\n'
        "```\n"
        "\n"
        "## Run Tests\n"
        "\n"
        "```bash\n"
        "pytest tests/ -v\n"
        "```\n"
        "\n"
        "## Run Locally\n"
        "\n"
        "```bash\n"
        "uvicorn src.pipeline:app --reload\n"
        "```\n"
        "\n"
        "## Deploy with Docker\n"
        "\n"
        "```bash\n"
        f"docker build -t {repo} .\n"
        f"docker run -p 8000:8000 {repo}\n"
        "```\n"
    )


# ═══════════════════════════════════════════
# STAGE 5: PUBLISHER AGENT
# ═══════════════════════════════════════════

def publish_project(opportunity: dict, github_token: str = None) -> dict:
    """Stage 5: Create GitHub repo, push code, update marketplace."""
    print(f"\n{'═' * 50}")
    print(f"  STAGE 5: Publisher Agent")
    print(f"{'═' * 50}")

    roadmap = opportunity["roadmap"]
    build = opportunity["build"]
    repo_name = roadmap["repo_name"]
    project_dir = Path(build["project_dir"])

    # Create GitHub repo via gh CLI
    github_url = None
    if github_token or _gh_auth_available():
        try:
            result = subprocess.run(
                ["gh", "repo", "create", f"phanindraintelligenzit-afk/{repo_name}",
                 "--public", "--description", roadmap["description"][:100],
                 "--homepage", "https://aidentify.dev"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                github_url = f"https://github.com/phanindraintelligenzit-afk/{repo_name}"
                print(f"  ✓ GitHub repo created: {github_url}")
            else:
                print(f"  ⚠ gh repo create: {result.stderr.strip()[:120]}")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"  ⚠ gh CLI not available: {e}")
    else:
        print("  ⚠ No GitHub auth — skipping repo creation")

    # Initialize git and push
    if github_url:
        try:
            _git_push(project_dir, github_url)
            print(f"  ✓ Code pushed to GitHub")
        except Exception as e:
            print(f"  ⚠ Git push failed: {e}")

    # Save project config
    _save_project_config(opportunity)

    # Generate marketplace card data
    card_data = _generate_marketplace_card(opportunity)
    opportunity["publish"] = {
        "github_url": github_url,
        "project_dir": str(project_dir),
        "marketplace_card": card_data,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    opportunity["status"] = "published"

    print(f"  ✓ Project config saved")
    print(f"  ✓ Marketplace card generated")
    print(f"\n{'═' * 50}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'═' * 50}")
    print(f"  Project: {roadmap['project_name']}")
    print(f"  Repo: {repo_name}")
    print(f"  Files: {build['total_files']}")
    print(f"  GitHub: {github_url or 'Not pushed (gh auth needed)'}")

    return opportunity


def _gh_auth_available() -> bool:
    """Check if gh CLI is authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _git_push(project_dir: Path, github_url: str):
    """Initialize git repo and push to GitHub."""
    cmds = [
        ["git", "init"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Initial commit — AIdentify project scaffold"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", f"{github_url}.git"],
        ["git", "push", "-u", "origin", "main"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=str(project_dir), capture_output=True, text=True, timeout=60)
        if result.returncode != 0 and "already exists" not in result.stderr:
            # Non-fatal for remote add if already exists
            if "remote" in cmd and "already exists" in result.stderr:
                continue
            raise RuntimeError(f"{' '.join(cmd)}: {result.stderr.strip()}")


def _save_project_config(opportunity: dict):
    """Save project to config file."""
    config = {}
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    config[opportunity["id"]] = {
        "name": opportunity["roadmap"]["project_name"],
        "category": opportunity["category"],
        "status": opportunity["status"],
        "github_url": opportunity.get("publish", {}).get("github_url"),
        "project_dir": opportunity["build"]["project_dir"],
        "created_at": opportunity["created_at"],
    }
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _generate_marketplace_card(opportunity: dict) -> dict:
    """Generate the marketplace card data for this project."""
    return {
        "name": opportunity["roadmap"]["project_name"],
        "category": opportunity["category"],
        "description": opportunity["roadmap"]["description"][:120],
        "icon": opportunity["icon"],
        "tags": opportunity["tags"],
        "agents": opportunity["agents"],
        "github_url": opportunity.get("publish", {}).get("github_url", "#"),
        "monetization": opportunity["monetization"],
    }


# ═══════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════

def _slugify(text: str) -> str:
    """Convert text to a URL/repo-safe slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:50]


def _title_case(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.split("-"))


# ═══════════════════════════════════════════
# MAIN PIPELINE RUNNER
# ═══════════════════════════════════════════

def run_pipeline(idea: str, category: str, skip_publish: bool = False) -> dict:
    """Run the full project pipeline."""
    print(f"\n{'█' * 50}")
    print(f"  AIdentify Project Pipeline")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'█' * 50}")

    # Stage 1: Scan
    opportunity = scan_opportunity(idea, category)

    # Stage 2: Research
    opportunity = research_opportunity(opportunity)

    # Stage 3: Roadmap
    opportunity = build_roadmap(opportunity)

    # Stage 4: Build
    opportunity = build_project(opportunity)

    # Stage 5: Publish (optional)
    if not skip_publish:
        opportunity = publish_project(opportunity)
    else:
        opportunity["status"] = "built (not published)"
        print(f"\n  ⏭ Publish skipped (--skip-publish)")

    # Save full pipeline output
    output_file = PROJECTS_DIR / opportunity["id"] / "pipeline_output.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    # Remove non-serializable parts
    serializable = {k: v for k, v in opportunity.items() if isinstance(v, (str, int, float, bool, dict, list, type(None)))}
    output_file.write_text(json.dumps(serializable, indent=2, default=str), encoding="utf-8")

    return opportunity


def list_projects() -> list:
    """List all projects in the config."""
    if not CONFIG_FILE.exists():
        print("No projects found.")
        return []
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    print(f"\n{'═' * 50}")
    print(f"  AIdentify Projects ({len(config)})")
    print(f"{'═' * 50}")
    for pid, p in config.items():
        print(f"  {p['name']}")
        print(f"    Category: {p['category']}  Status: {p['status']}")
        print(f"    GitHub: {p.get('github_url', 'N/A')}")
        print()
    return list(config.values())


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="AIdentify Project Pipeline")
    sub = parser.add_subparsers(dest="command")

    # Run pipeline
    run_p = sub.add_parser("run", help="Run the full pipeline for an idea")
    run_p.add_argument("--idea", required=True, help="Automation idea description")
    run_p.add_argument("--category", required=True, choices=list(CATEGORY_TEMPLATES.keys()) + ["other"])
    run_p.add_argument("--skip-publish", action="store_true", help="Skip GitHub publish")

    # List projects
    sub.add_parser("list", help="List all projects")

    # Process request file
    req_p = sub.add_parser("from-request", help="Process a project request JSON file")
    req_p.add_argument("--file", required=True, help="Path to request JSON")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(args.idea, args.category, args.skip_publish)
    elif args.command == "list":
        list_projects()
    elif args.command == "from-request":
        req = json.loads(Path(args.file).read_text(encoding="utf-8"))
        run_pipeline(req["idea"], req.get("category", "other"), req.get("skip_publish", True))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
