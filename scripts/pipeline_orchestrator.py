#!/usr/bin/env python3
"""AIdentify Pipeline Orchestrator — runs DISCUSS → SELECT → BUILD → PUBLISH."""
import json
import os
import sys
import subprocess
import re
from datetime import datetime
from pathlib import Path

AIDENTIFY_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = AIDENTIFY_DIR / "projects"

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def log(phase, msg):
    print(f"[{now_str()}] [{phase}] {msg}", flush=True)

def load_opportunities(date_str):
    path = AIDENTIFY_DIR / "marketplace/opportunities" / f"{date_str}.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def classify_category(title, text):
    combined = f"{title} {text}".lower()
    keywords = {
        "healthcare": ["healthcare", "medical", "pharma", "clinical", "hipaa", "ehr"],
        "ecommerce": ["ecommerce", "e-commerce", "shopify", "store", "product"],
        "legal": ["legal", "law", "contract", "compliance", "gdpr", "soc2"],
        "hr": ["hr", "hiring", "recruiting", "onboarding", "resume", "candidate"],
        "finance": ["finance", "accounting", "reconciliation", "invoice", "payment"],
        "marketing": ["marketing", "content", "seo", "social media", "outreach", "lead gen"],
        "devtools": ["developer", "ci/cd", "deployment", "monitoring", "devops"],
        "realestate": ["real estate", "property", "listing", "brokerage"],
    }
    best = "devtools"
    best_count = 0
    for cat, kws in keywords.items():
        count = sum(1 for kw in kws if kw in combined)
        if count > best_count:
            best_count = count
            best = cat
    return best

def score_opportunity_detailed(opp):
    """Score on market, feasibility, revenue, stack_fit (1-10 each)."""
    title = opp.get("title", "")
    text = opp.get("text", "")
    combined = f"{title} {text}".lower()
    source = opp.get("source", "")
    
    # Market (demand signals)
    market_signals = ["lead", "outreach", "automation", "saas", "workflow", "scaling", "growth", "demand"]
    market = min(sum(2 for s in market_signals if s in combined), 10)
    market = max(market, 5)  # Floor for HN/GitHub trending items
    
    # Feasibility (can we build this with Python/agents?)
    feasibility_signals = ["python", "api", "bot", "scraping", "dashboard", "monitor", "automate"]
    feasibility = min(sum(2 for s in feasibility_signals if s in combined), 10)
    feasibility = max(feasibility, 6)  # Most things are feasible with our stack
    
    # Revenue potential (business metrics)
    revenue_signals = ["roi", "revenue", "profit", "monetize", "pricing", "subscription", "saas", "enterprise"]
    revenue = min(sum(2 for s in revenue_signals if s in combined), 10)
    revenue = max(revenue, 4)
    
    # Stack fit (agent-based, Python, web)
    stack_fit_signals = ["agent", "ai", "llm", "web", "api", "dashboard", "pipeline", "automation"]
    stack_fit = min(sum(2 for s in stack_fit_signals if s in combined), 10)
    stack_fit = max(stack_fit, 6)
    
    # Source bonus
    if source == "github":
        stack_fit += 1
    
    total = min(market + feasibility + revenue + stack_fit, 40)
    
    return {
        "market": market,
        "feasibility": min(feasibility, 10),
        "revenue": min(revenue, 10),
        "stack_fit": min(stack_fit, 10),
        "total": total
    }

def phase_discuss(opportunities):
    """Simulate agent discussions on top opportunities."""
    log("DISCUSS", f"Running agent discussions on {len(opportunities)} opportunities...")
    
    agents = ["researcher", "planner", "coder", "reviewer", "social", "outreach"]
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    discussions = {}
    for agent in agents:
        agent_opps = []
        for opp in opportunities[:8]:  # Discuss top 8
            scores = score_opportunity_detailed(opp)
            if agent == "researcher":
                analysis = f"Market analysis: {scores['market']}/10 demand. Source: {opp.get('source')}, engagement: {opp.get('score', 0)} pts"
            elif agent == "planner":
                analysis = f"Plan: Build agent pipeline for '{opp.get('title','')[:40]}' with modular stages"
            elif agent == "coder":
                analysis = f"Feasibility: {scores['feasibility']}/10. Stack: Python/agents suitable. Source-type: {opp.get('source')}"
            elif agent == "reviewer":
                analysis = f"Review: Stack fit {scores['stack_fit']}/10, market {scores['market']}/10 — {'viable' if scores['total'] >= 25 else 'risky'}"
            elif agent == "social":
                analysis = f"Social angle: '{opp.get('title','')[:40]}' resonates with indie hacker / SMB audience"
            elif agent == "outreach":
                analysis = f"Outreach: Target HN Show/Dev.to communities, position as 'open-source alternative'"
            
            agent_opps.append({
                "title": opp.get("title"),
                "source": opp.get("source"),
                "opportunity_score": opp.get("opportunity_score"),
                "scores": scores,
                "analysis": analysis
            })
        
        discussion = {
            "agent": agent,
            "date": date_str,
            "opportunities_discussed": len(agent_opps),
            "rankings": agent_opps,
            "top_pick": agent_opps[0]["title"] if agent_opps else None
        }
        
        out_path = AIDENTIFY_DIR / "pipeline" / f"{date_str}-{agent}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(discussion, f, indent=2, ensure_ascii=False)
        discussions[agent] = discussion
        log("DISCUSS", f"  {agent}: {len(agent_opps)} discussed, top pick: {discussion['top_pick'][:40] if discussion['top_pick'] else 'none'}...")
    
    return discussions

def phase_select(opportunities, discussions):
    """Score and pick the highest-scoring opportunity."""
    log("SELECT", "Scoring all opportunities...")
    
    scored = []
    for opp in opportunities:
        scores = score_opportunity_detailed(opp)
        
        # Incorporate agent consensus
        consensus_bonus = 0
        for agent, disc in discussions.items():
            if disc.get("top_pick") == opp.get("title"):
                consensus_bonus += 2
        
        category = classify_category(opp.get("title", ""), opp.get("text", ""))
        final_score = scores["total"] + consensus_bonus
        
        opp["detailed_scores"] = scores
        opp["category"] = category
        opp["consensus_bonus"] = consensus_bonus
        opp["final_score"] = final_score
        scored.append(opp)
    
    scored.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    best = scored[0]
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    selection = {
        "selected": best,
        "all_scores": [{"title": s.get("title", "?")[:60], "scores": s.get("detailed_scores"), "final": s.get("final_score")} for s in scored[:10]],
        "date": date_str,
        "rationale": f"Best market ({best['detailed_scores']['market']}) + feasibility ({best['detailed_scores']['feasibility']}) + stack fit ({best['detailed_scores']['stack_fit']})"
    }
    
    out_path = AIDENTIFY_DIR / "pipeline" / f"{date_str}-selection.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(selection, f, indent=2, ensure_ascii=False)
    
    log("SELECT", f"Winner: {best.get('title', '?')[:60]} (score: {best.get('final_score', 0)}/40)")
    log("SELECT", f"  Market: {best['detailed_scores']['market']}, Feasibility: {best['detailed_scores']['feasibility']}, Revenue: {best['detailed_scores']['revenue']}, Stack: {best['detailed_scores']['stack_fit']}")
    
    return best

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:50]

def phase_build(opportunity):
    """Generate project scaffolding."""
    idea = opportunity.get("title", "AI automation opportunity")
    category = opportunity.get("category", "devtools")
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(idea)
    project_dir = PROJECTS_DIR / slug
    
    log("BUILD", f"Building: {idea[:60]} (category: {category})")
    log("BUILD", f"Project dir: {project_dir}")
    
    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create basic structure
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    (project_dir / "docs").mkdir(exist_ok=True)
    
    # README
    readme = f"""# {_title_case(slug)}

{idea}

**Category:** {category}  
**Built by:** AIdentify Multi-Agent Pipeline  
**Date:** {date_str}

## Quick Start

```bash
pip install -r requirements.txt
python src/main.py
```

## Architecture

This project uses a multi-agent pipeline:
- **Researcher** — Scans for opportunities and trends
- **Planner** — Creates implementation roadmap
- **Coder** — Generates and reviews code
- **Reviewer** — Quality assurance and testing
- **Social** — Community engagement analysis
- **Outreach** — Communication and marketing

## Configuration

Edit `config.yaml` to customize agent behavior.

## License

MIT
"""
    (project_dir / "README.md").write_text(readme, encoding="utf-8")
    
    # requirements.txt
    reqs = """# Core
pytest>=7.0
pyyaml>=6.0
requests>=2.31.0

# AI/Agent support
openai>=1.0
anthropic>=0.20

# Data & APIs
httpx>=0.25
beautifulsoup4>=4.12

# Utilities
python-dotenv>=1.0
click>=8.1
rich>=13.0
"""
    (project_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    
    # config.yaml
    config = f"""project:
  name: "{slug}"
  category: "{category}"
  date: "{date_str}"

agents:
  researcher:
    role: "Market and trend analysis"
    priority: 1
  planner:
    role: "Implementation planning"
    priority: 2
  coder:
    role: "Code generation and refactoring"
    priority: 3
  reviewer:
    role: "Code review and quality assurance"
    priority: 4
  social:
    role: "Community analysis and social media"
    priority: 5
  outreach:
    role: "Marketing and stakeholder communication"
    priority: 6

pipeline:
  stages:
    - scan
    - discuss
    - select
    - build
    - test
    - publish
"""
    (project_dir / "config.yaml").write_text(config, encoding="utf-8")
    
    # src/main.py
    title = _title_case(slug)
    src_category = category
    src_source = opportunity.get("source", "unknown")
    src_score = opportunity.get("opportunity_score", 0)
    main_py = (
        f'"""{title} — Main Entry Point."""\n\n'
        'import click\n'
        'from rich.console import Console\n\n'
        'console = Console()\n\n\n'
        '@click.group()\n'
        'def cli():\n'
        f'    """{title} - Auto-generated by AIdentify."""\n'
        '    pass\n\n\n'
        '@cli.command()\n'
        'def run():\n'
        '    """Run the main pipeline."""\n'
        '    console.print("[bold green]Pipeline starting...[/bold green]")\n'
        f'    console.print("Category: {src_category}")\n'
        f'    console.print("Source: {src_source}")\n'
        f'    console.print("Score: {src_score}")\n'
        '    console.print("[bold]Step 1:[/bold] Scanning for new signals...")\n'
        '    console.print("[bold]Step 2:[/brief] Processing with agent pipeline...")\n'
        '    console.print("[bold]Step 3:[/bold] Generating output...")\n'
        '    console.print("[bold green]Pipeline complete![/bold green]")\n\n\n'
        '@cli.command()\n'
        'def status():\n'
        '    """Show current status."""\n'
        '    console.print("[bold]Status: Ready[/bold]")\n'
        f'    console.print("Project: {{slug}}")\n'
        f'    console.print("Category: {{src_category}}")\n\n\n'
        'if __name__ == "__main__":\n'
        '    cli()\n'
    )
    (project_dir / "src" / "main.py").write_text(main_py, encoding="utf-8")
    
    # tests/test_main.py
    test_py = '"""Tests for main module."""\n\nimport pytest\n\n\ndef test_project_exists():\n    """Verify the project was created correctly."""\n    from src.main import cli\n    assert cli is not None\n\n\ndef test_config_loaded():\n    """Verify config loads."""\n    import yaml\n    with open("config.yaml") as f:\n        config = yaml.safe_load(f)\n    assert config["project"]["name"] == "{}"\n\n\ndef test_category_correct():\n    """Verify category matches."""\n    import yaml\n    with open("config.yaml") as f:\n        config = yaml.safe_load(f)\n    assert config["project"]["category"] == "{}"\n'.format(slug, category)
    (project_dir / "tests" / "test_main.py").write_text(test_py, encoding="utf-8")
    
    # __init__.py
    (project_dir / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")
    
    # Build manifest
    manifest = {
        "project_slug": slug,
        "project_dir": str(project_dir),
        "idea": idea,
        "category": category,
        "date": date_str,
        "built": True,
        "files": {
            "README.md": str(project_dir / "README.md"),
            "requirements.txt": str(project_dir / "requirements.txt"),
            "config.yaml": str(project_dir / "config.yaml"),
            "src/main.py": str(project_dir / "src" / "main.py"),
            "tests/test_main.py": str(project_dir / "tests" / "test_main.py"),
        },
        "agent_pipeline": [
            {"name": "researcher", "role": "Market analysis"},
            {"name": "planner", "role": "Implementation planning"},
            {"name": "coder", "role": "Code generation"},
            {"name": "reviewer", "role": "Quality assurance"},
            {"name": "social", "role": "Community analysis"},
            {"name": "outreach", "role": "Marketing & comms"}
        ],
        "tags": [category.title(), "Multi-Agent", "AI Automation"]
    }
    
    out_path = AIDENTIFY_DIR / "pipeline" / f"{date_str}-build.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    log("BUILD", f"✅ Project built at {project_dir}")
    log("BUILD", f"Build manifest saved to pipeline/{date_str}-build.json")
    
    return {"slug": slug, "project_dir": str(project_dir)}

def _title_case(slug):
    small = {"a", "an", "the", "and", "or", "for", "in", "of", "to", "with", "on"}
    words = slug.replace("-", " ").replace("_", " ").split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in small:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return " ".join(result)

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    log("PIPELINE", f"=== AIdentify Pipeline Orchestrator — {date_str} ===")
    log("PIPELINE", "Phase: SCOUT → DISCUSS → SELECT → BUILD")
    
    # Load opportunities from scout
    opportunities = load_opportunities(date_str)
    if not opportunities:
        log("PIPELINE", "ERROR: No opportunities found. Run scout first.")
        sys.exit(1)
    
    log("SCOUT", f"Loaded {len(opportunities)} opportunities from {date_str}")
    
    # DISCUSS
    discussions = phase_discuss(opportunities)
    log("DISCUSS", f"✅ Agent discussions complete ({len(discussions)} agents)")
    
    # SELECT
    best = phase_select(opportunities, discussions)
    log("SELECT", f"✅ Selected: {best.get('title', '?')[:50]}")
    
    # BUILD
    result = phase_build(best)
    if not result:
        log("BUILD", "❌ Build failed!")
        sys.exit(1)
    log("BUILD", f"✅ Build complete: {result['slug']}")
    
    log("PIPELINE", "")
    log("PIPELINE", f"� Pipeline Summary:")
    log("PIPELINE", f"   Idea: {best.get('title', '?')[:60]}")
    log("PIPELINE", f"   Category: {best.get('category', '?')}")
    log("PIPELINE", f"   Score: {best.get('final_score', 0)}/40")
    log("PIPELINE", f"   Project: projects/{result['slug']}")
    log("PIPELINE", f"   Manifest: pipeline/{date_str}-build.json")
    log("PIPELINE", "")
    log("PIPELICE", "Next tick: PUBLISH (push to GitHub + update marketplace)")

if __name__ == "__main__":
    main()
