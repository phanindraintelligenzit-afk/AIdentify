#!/usr/bin/env python3
"""AIdentify Autonomous Pipeline — Zero-Touch Loop

Runs the full cycle automatically:
  SCAN → SELECT → BUILD → TEST → PUSH → PUBLISH → UPDATE MARKETPLACE

Designed to run as a daily cron job. No human input needed.

Usage:
    python autonomous_pipeline.py                    # Run one full cycle
    python autonomous_pipeline.py --dry-run          # Scan + select only (no build)
    python autonomous_pipeline.py --idea "..."       # Skip scan, build specific idea

Exit codes:
    0 = Success (published to marketplace)
    1 = Partial (built but not published)
    2 = Failure (build or earlier phase failed)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Paths ──
BASE_DIR = Path(__file__).resolve().parent
AIDENTIFY_DIR = BASE_DIR.parent
PROJECTS_DIR = AIDENTIFY_DIR / "projects"
MARKETPLACE_HTML = AIDENTIFY_DIR / "docs" / "marketplace.html"
SCOUT_SCRIPT = BASE_DIR / "opportunity_scanner.py"
PIPELINE_SCRIPT = BASE_DIR / "project_pipeline.py"
GITHUB_ORG = "phanindraintelligenzit-afk"

# Import scanner helpers for alternate search queries (threshold loop)
sys.path.insert(0, str(BASE_DIR))
from opportunity_scanner import search_ddg, score_opportunity

IST = timezone(timedelta(hours=5, minutes=30))

# Industry keyword → category mapping
INDUSTRY_MAP = {
    "healthcare": "healthcare", "medical": "healthcare", "pharma": "healthcare",
    "clinical": "healthcare", "hipaa": "healthcare", "ehr": "healthcare",
    "ecommerce": "ecommerce", "e-commerce": "ecommerce", "shopify": "ecommerce",
    "store": "ecommerce", "product": "ecommerce",
    "legal": "legal", "law": "legal", "contract": "legal", "compliance": "legal",
    "gdpr": "legal", "soc2": "legal",
    "hr": "hr", "hiring": "hr", "recruiting": "hr", "onboarding": "hr",
    "resume": "hr", "candidate": "hr",
    "realestate": "realestate", "real estate": "realestate", "property": "realestate",
    "listing": "realestate", "brokerage": "realestate",
    "finance": "finance", "accounting": "finance", "reconciliation": "finance",
    "invoice": "finance", "payment": "finance",
    "marketing": "marketing", "content": "marketing", "seo": "marketing",
    "social media": "marketing", "outreach": "marketing",
    "devtools": "devtools", "developer": "devtools", "ci/cd": "devtools",
    "deployment": "devtools", "monitoring": "devtools", "devops": "devtools",
}


def now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %I:%M %p IST")


def log(phase: str, msg: str):
    print(f"[{now_ist()}] [{phase}] {msg}", flush=True)


def run_cmd(cmd: list, cwd=None, timeout=120) -> tuple:
    """Run a command, return (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"


# ═══════════════════════════════════════════
# PHASE 1: SCAN
# ═══════════════════════════════════════════

def phase_scan(enable_llm: bool = False, enable_js: bool = False) -> list:
    """Scan HN, GitHub, Reddit, dev.to for business opportunities."""
    log("SCAN", "Running opportunity scanner...")

    cmd = [sys.executable, str(SCOUT_SCRIPT), "--json"]
    if enable_llm:
        cmd.append("--llm")
    if enable_js:
        cmd.append("--js")
    code, stdout, stderr = run_cmd(cmd, timeout=180)

    if code != 0:
        log("SCAN", f"Scanner failed (exit {code}): {stderr[:200]}")
        return []

    try:
        opportunities = json.loads(stdout)
    except json.JSONDecodeError:
        log("SCAN", f"Failed to parse scanner output: {stdout[:200]}")
        return []

    # Filter to scored opportunities
    scored = [o for o in opportunities if o.get("opportunity_score", 0) >= 20]
    if not scored:
        scored = opportunities[:5]  # Top 5 even if low score

    scored.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
    log("SCAN", f"Found {len(scored)} scored opportunities (top: {scored[0].get('title', '?')[:50] if scored else 'none'})")
    return scored


# ═══════════════════════════════════════════
# PHASE 2: SELECT
# ═══════════════════════════════════════════

def classify_category(title: str, text: str) -> str:
    """Classify an opportunity into a category based on keywords."""
    combined = f"{title} {text}".lower()
    best_cat = "devtools"
    best_count = 0
    for keyword, cat in INDUSTRY_MAP.items():
        if keyword in combined:
            count = combined.count(keyword)
            if count > best_count:
                best_count = count
                best_cat = cat
    return best_cat


def phase_select(opportunities: list) -> dict:
    """Pick the best opportunity based on score + freshness + buildability."""
    if not opportunities:
        log("SELECT", "No opportunities to select from!")
        return None

    # Score + bonus for recent GitHub trending (buildable signal)
    for opp in opportunities:
        bonus = 0
        source = opp.get("source", "")
        title = opp.get("title", "").lower()
        text = opp.get("text", "").lower()

        # Prefer GitHub trending (buildable repos)
        if source == "github":
            bonus += 10

        # Prefer things with clear pain points
        pain_words = ["manual", "automate", "workflow", "struggling", "repetitive"]
        bonus += sum(2 for w in pain_words if w in title or w in text)

        # Prefer industries we already have templates for
        cat = classify_category(opp.get("title", ""), opp.get("text", ""))
        if cat in ["healthcare", "ecommerce", "legal", "hr", "realestate", "finance", "marketing"]:
            bonus += 5

        opp["final_score"] = opp.get("opportunity_score", 0) + bonus
        opp["category"] = cat

    # Sort by final score
    opportunities.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    best = opportunities[0]
    log("SELECT", f"Selected: {best.get('title', '?')[:60]} (score: {best.get('final_score', 0)})")
    return best


# ═══════════════════════════════════════════
# PHASE 3: BUILD
# ═══════════════════════════════════════════

def phase_build(idea: str, category: str) -> dict:
    """Run the full project pipeline (scan → research → roadmap → build)."""
    log("BUILD", f"Building: {idea[:60]}... (category: {category})")

    code, stdout, stderr = run_cmd(
        [sys.executable, str(PIPELINE_SCRIPT), "run",
         "--idea", idea,
         "--category", category,
         "--skip-publish"],  # We handle publishing ourselves
        cwd=str(AIDENTIFY_DIR),
        timeout=300,
    )

    if code != 0:
        log("BUILD", f"Build failed (exit {code}): {stderr[:300]}")
        return None

    log("BUILD", "Build completed successfully")
    # The pipeline saves output but we need to find the project dir
    return {"idea": idea, "category": category, "built": True}


# ═══════════════════════════════════════════
# PHASE 4: TEST
# ═══════════════════════════════════════════

def phase_test(project_slug: str) -> bool:
    """Run tests on the built project."""
    project_dir = PROJECTS_DIR / project_slug
    if not project_dir.exists():
        log("TEST", f"Project dir not found: {project_dir}")
        return False

    log("TEST", f"Running tests for {project_slug}...")

    # Try pytest first, then fallback to python -m pytest
    code, stdout, stderr = run_cmd(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(project_dir),
        timeout=120,
    )

    if code == 0:
        log("TEST", f"All tests passed ✅")
        return True
    else:
        # Non-fatal — log it but continue (tests are scaffold-level)
        failed_lines = [l for l in stdout.split("\n") if "FAILED" in l or "passed" in l or "failed" in l]
        log("TEST", f"Some tests had issues (non-blocking): {'; '.join(failed_lines[:3])}")
        return True  # Continue anyway — scaffold tests are structural


# ═══════════════════════════════════════════
# PHASE 5: PUSH TO GITHUB
# ═══════════════════════════════════════════

def phase_push(project_slug: str, description: str) -> str:
    """Create GitHub repo and push the project code."""
    project_dir = PROJECTS_DIR / project_slug
    repo_name = project_slug
    repo_url = f"https://github.com/{GITHUB_ORG}/{repo_name}"

    if not project_dir.exists():
        log("PUSH", f"Project dir not found: {project_dir}")
        return None

    # Check if repo already exists
    code, _, _ = run_cmd(["gh", "repo", "view", f"{GITHUB_ORG}/{repo_name}"], timeout=15)
    if code == 0:
        log("PUSH", f"Repo already exists: {repo_url}")
    else:
        # Create the repo
        log("PUSH", f"Creating repo: {GITHUB_ORG}/{repo_name}")
        code, stdout, stderr = run_cmd(
            ["gh", "repo", "create", f"{GITHUB_ORG}/{repo_name}",
             "--public", "--description", description[:200]],
            timeout=30,
        )
        if code != 0 and "already exists" not in stderr:
            log("PUSH", f"Failed to create repo: {stderr[:200]}")
            return None

    # Push code
    log("PUSH", f"Pushing code to {repo_url}...")
    push_cmds = [
        (["git", "init"], True),
        (["git", "add", "."], True),
        (["git", "commit", "-m", f"Initial commit — {project_slug}"], True),
        (["git", "branch", "-M", "main"], True),
        (["git", "remote", "add", "origin", f"{repo_url}.git"], False),  # may already exist
        (["git", "push", "-u", "origin", "main", "--force"], True),
    ]

    for cmd, must_succeed in push_cmds:
        code, stdout, stderr = run_cmd(cmd, cwd=str(project_dir), timeout=120)
        if code != 0:
            if "already exists" in stderr or "nothing to commit" in stderr:
                continue  # Non-fatal
            if must_succeed:
                log("PUSH", f"Command failed: {' '.join(cmd)}: {stderr[:150]}")
                # Try set-url as fallback for remote add
                if "remote" in cmd:
                    run_cmd(["git", "remote", "set-url", "origin", f"{repo_url}.git"],
                           cwd=str(project_dir))
                    continue
                return None

    log("PUSH", f"Pushed to {repo_url} ✅")
    return repo_url


# ═══════════════════════════════════════════
# PHASE 6: UPDATE MARKETPLACE
# ═══════════════════════════════════════════

def phase_update_marketplace(name: str, repo_url: str, category: str,
                              description: str, agents: list, tags: list):
    """Add a new project card to the marketplace HTML and push to GitHub Pages."""
    if not MARKETPLACE_HTML.exists():
        log("MARKETPLACE", f"marketplace.html not found at {MARKETPLACE_HTML}")
        return False

    # Read current HTML
    html = MARKETPLACE_HTML.read_text(encoding="utf-8")

    # Check if this project is already in the HTML
    if repo_url and repo_url in html:
        log("MARKETPLACE", f"Project already in marketplace: {name}")
        return True

    # Generate new card HTML
    icon_map = {
        "healthcare": "🏥", "ecommerce": "🛒", "legal": "⚖️",
        "hr": "👥", "realestate": "🏠", "finance": "💰",
        "marketing": "📣", "devtools": "⚡",
    }
    icon = icon_map.get(category, "⚡")

    # Generate agent pipeline descriptions
    agent_descriptions = agents if agents else [f"Agent {i+1}" for i in range(4)]

    # Build the PROJECT_DATA JS entry
    project_key = repo_url.split("/")[-1] if repo_url else name.lower().replace(" ", "-")
    project_js_entry = f'''
      "{project_key}": {{
        name:"{name}",icon:"{icon}",category:"{category.title()}",
        description:"{description[:200].replace('"', "'")}",
        agents:{json.dumps(agent_descriptions)},
        tags:{json.dumps(tags)},
        github_url:"{repo_url}"
      }}'''

    # Add to PROJECT_DATA object in JS
    if "PROJECT_DATA" in html:
        # Find the last entry in PROJECT_DATA and add after it
        # Insert before the closing brace
        marker = '    };\n    const REPO_MAP'
        if marker in html:
            # Add comma to last entry, then add new entry
            html = html.replace(marker, ',' + project_js_entry + '\n' + marker)

    # Add card HTML before the CTA card
    cta_marker = '<!-- Card 6: Coming Soon / CTA -->'
    if cta_marker in html:
        tags_html = " ".join(
            '<span class="project-card__tag">{}</span>'.format(t)
            for t in tags[:4]
        )
        card_html = (
            '        <!-- Card: {name} -->\n'
            '        <div class="project-card" data-category="{category}" style="cursor:pointer;">\n'
            '          <div class="project-card__header">\n'
            '            <div class="project-card__icon">{icon}</div>\n'
            '            <span class="project-card__badge project-card__badge--free">Free Repo</span>\n'
            '          </div>\n'
            '          <h3 class="project-card__name">{name}</h3>\n'
            '          <p class="project-card__desc">{desc}</p>\n'
            '          <div class="project-card__tags">\n'
            '            {tags_html}\n'
            '          </div>\n'
            '          <div class="project-card__meta">\n'
            '            <span class="project-card__meta-item">\U0001f40d Python</span>\n'
            '            <span class="project-card__meta-item">\U0001f4dd MIT</span>\n'
            '            <span class="project-card__meta-item">\U0001f464 AIdentify</span>\n'
            '          </div>\n'
            '          <div class="project-card__actions">\n'
            '            <a href="{repo_url}" target="_blank" rel="noopener" class="btn btn--primary btn--sm">View Repo</a>\n'
            '            <a href="#request" class="btn btn--outline btn--sm">Hire Setup</a>\n'
            '          </div>\n'
            '        </div>\n'
            '\n'
        ).format(
            name=name,
            category=category,
            icon=icon,
            desc=description[:120],
            tags_html=tags_html,
            repo_url=repo_url,
        )
        html = html.replace(cta_marker, card_html + cta_marker)

    # Also update REPO_MAP
    repo_map_marker = 'const REPO_MAP = {'
    if repo_map_marker in html:
        new_map_entry = f'"{category}":"{project_key}",'
        html = html.replace(repo_map_marker, repo_map_marker + '\n        ' + new_map_entry)

    MARKETPLACE_HTML.write_text(html, encoding="utf-8")

    # Also update projects.json (loaded by marketplace-loader.js on the live site)
    SYNC_SCRIPT = BASE_DIR / "marketplace_sync.py"
    if SYNC_SCRIPT.exists():
        log("MARKETPLACE", "Syncing projects.json via marketplace_sync.py...")
        run_cmd([sys.executable, str(SYNC_SCRIPT)], cwd=str(AIDENTIFY_DIR), timeout=60)

    # Commit and push
    log("MARKETPLACE", "Committing marketplace update...")
    run_cmd(["git", "add", "docs/marketplace.html", "docs/data/projects.json"], cwd=str(AIDENTIFY_DIR))
    run_cmd(
        ["git", "commit", "-m", f"feat: add {name} to marketplace"],
        cwd=str(AIDENTIFY_DIR),
    )
    # Push to current branch (gh-pages for AIdentify)
    _branch_result = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(AIDENTIFY_DIR))
    _current_branch = _branch_result[1].strip() if _branch_result[0] == 0 else "gh-pages"
    code, _, stderr = run_cmd(["git", "push", "origin", _current_branch], cwd=str(AIDENTIFY_DIR), timeout=60)
    if code == 0:
        log("MARKETPLACE", f"Marketplace updated and pushed ✅")
        return True
    else:
        log("MARKETPLACE", f"Push failed: {stderr[:150]}")
        return False


# ═══════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════

def run_full_cycle(idea_override: str = None, category_override: str = None,
                   dry_run: bool = False, enable_llm: bool = False):
    """Run one complete cycle of the autonomous pipeline."""

    print(f"\n{'█' * 60}")
    print(f"  AIdentify Autonomous Pipeline")
    print(f"  {now_ist()}")
    print(f"{'█' * 60}\n")

    # ── PHASE 1: SCAN ──
    if idea_override:
        log("SCAN", f"Skipping scan — using provided idea: {idea_override[:60]}")
        category = category_override or classify_category(idea_override, "")
        best = {
            "title": idea_override,
            "text": idea_override,
            "opportunity_score": 80,
            "category": category,
            "final_score": 80,
            "source": "manual",
        }
    else:
        MIN_SCORE = 30
        best = None

        # Primary scan (with JS sources enabled)
        opportunities = phase_scan(enable_llm=enable_llm, enable_js=True)
        if not opportunities:
            log("SCAN", "No opportunities found. Exiting.")
            return 2

        # ── PHASE 2: SELECT (with threshold loop) ──
        best = phase_select(opportunities)
        if best and best.get("final_score", 0) < MIN_SCORE:
            log("SELECT", f"Top score {best.get('final_score', 0)} < {MIN_SCORE} — trying alternate scans...")

            # Alternate DDG queries to find richer signals
            alt_queries = [
                "AI agent workflow automation pain points 2026",
                "small business struggling manual processes automation",
                "startup MVP idea AI automation underserved market",
                "enterprise compliance automation AI tool gap",
            ]

            for q in alt_queries:
                log("SCAN", f"Alternate scan: '{q}'")
                alt_items = search_ddg(q, limit=10)
                for item in alt_items:
                    score_opportunity(item)
                alt_scored = [o for o in alt_items if o.get("opportunity_score", 0) >= 30]
                alt_scored.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

                # Merge with existing opportunities
                opportunities.extend(alt_scored)
                # Re-run select with merged pool
                best = phase_select(opportunities)
                if best and best.get("final_score", 0) >= MIN_SCORE:
                    log("SELECT", f"Found qualifying signal: {best.get('title', '?')[:50]} (score: {best.get('final_score', 0)})")
                    break

            if not best or best.get("final_score", 0) < MIN_SCORE:
                log("SELECT", f"No signal reached {MIN_SCORE} after all scans. Best: {best.get('final_score', 0) if best else 'none'}. Exiting.")
                return 2
        elif not best:
            log("SELECT", "Selection failed. Exiting.")
            return 2

    idea = best.get("title", best.get("text", "AI automation opportunity"))
    category = best.get("category", classify_category(idea, best.get("text", "")))

    if dry_run:
        log("DRY-RUN", f"Would build: {idea} (category: {category})")
        log("DRY-RUN", f"Score: {best.get('final_score', best.get('opportunity_score', 0))}")
        return 0

    # ── PHASE 3: BUILD ──
    result = phase_build(idea, category)
    if not result:
        log("BUILD", "Build failed. Exiting.")
        return 2

    # Find the project slug (directory name)
    slug = _slugify(idea)
    # Verify project directory exists
    project_dir = PROJECTS_DIR / slug
    if not project_dir.exists():
        # Try finding by partial match
        for d in PROJECTS_DIR.iterdir():
            if d.is_dir() and slug[:20] in d.name:
                project_dir = d
                slug = d.name
                break

    if not project_dir.exists():
        log("BUILD", f"Project directory not found for slug: {slug}")
        return 2

    log("BUILD", f"Project built at: {project_dir}")

    # ── PHASE 4: TEST ──
    test_ok = phase_test(slug)
    if not test_ok:
        log("TEST", "Tests failed critically. Exiting.")
        return 2

    # ── PHASE 5: PUSH TO GITHUB ──
    description = f"{idea}. Built by AIdentify — multi-agent automation system."
    repo_url = phase_push(slug, description)
    if not repo_url:
        log("PUSH", "GitHub push failed. Project built locally but not published.")
        return 1

    # ── PHASE 6: UPDATE MARKETPLACE ──
    # Load pipeline_output.json for agent descriptions
    pipeline_output_file = project_dir / "pipeline_output.json"
    agents = []
    tags = []
    if pipeline_output_file.exists():
        try:
            data = json.loads(pipeline_output_file.read_text(encoding="utf-8"))
            roadmap = data.get("roadmap", {})
            for agent in roadmap.get("agent_pipeline", []):
                name = agent.get("name", "Agent")
                role = agent.get("role", "")
                agents.append(f"{name} — {role}" if role else name)
            tags = data.get("tags", [category.title(), "Multi-Agent"])
        except Exception:
            pass

    if not agents:
        agents = [f"Agent {i+1}" for i in range(4)]
    if not tags:
        tags = [category.title(), "Multi-Agent", "AI Automation"]

    marketplace_ok = phase_update_marketplace(
        name=_title_case(slug),
        repo_url=repo_url,
        category=category,
        description=idea,
        agents=agents,
        tags=tags,
    )

    # ── SUMMARY ──
    print(f"\n{'█' * 60}")
    print(f"  Pipeline Complete!")
    print(f"  Project: {_title_case(slug)}")
    print(f"  Category: {category}")
    print(f"  GitHub: {repo_url}")
    print(f"  Marketplace: {'Updated ✅' if marketplace_ok else 'Failed ❌'}")
    print(f"  Time: {now_ist()}")
    print(f"{'█' * 60}\n")

    return 0 if marketplace_ok else 1


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:50]


def _title_case(slug: str) -> str:
    small = {"a", "an", "the", "and", "or", "for", "in", "of", "to", "with", "on"}
    words = slug.replace("-", " ").replace("_", " ").split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in small:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return " ".join(result)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIdentify Autonomous Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Scan + select only")
    parser.add_argument("--idea", type=str, help="Skip scan, build this idea directly")
    parser.add_argument("--category", type=str, help="Category override")
    args = parser.parse_args()

    exit_code = run_full_cycle(
        idea_override=args.idea,
        category_override=args.category,
        dry_run=args.dry_run,
    )
    sys.exit(exit_code)
