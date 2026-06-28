"""Autonomous Idea Loop — End-to-End Autonomous Business Idea Pipeline.

This module implements a fully autonomous agent loop that:
1. Generates business ideas from multiple perspectives (agents)
2. Deduplicates and scores ideas
3. Selects top ideas based on score
4. Builds, tests, pushes to GitHub
5. Publishes to marketplace
9. Posts to social media

The loop runs autonomously on a schedule or can be triggered manually.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"
MARKETPLACE_HTML = BASE_DIR / "docs" / "marketplace.html"
SCRIPTS_DIR = BASE_DIR / "scripts"

IST = timezone(timedelta(hours=5, minutes=30))

# Import existing modules
sys.path.insert(0, str(SCRIPTS_DIR))
from opportunity_scanner import run_scan
from tool_scanner import analyze_tool

# Add project directories to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "projects" / "promotion-engine" / "src"))
sys.path.insert(0, str(BASE_DIR / "projects" / "image-pipeline" / "src"))

from promoter import generate_posts, schedule_post
from image_gen import generate_all_platforms
from github_uploader import upload_image
from autonomous_pipeline import run_full_cycle


class IdeaGenerator:
    """Generates business ideas from multiple sources and perspectives."""

    def __init__(self, seen_ideas: set):
        self.seen_ideas = seen_ideas

    def _generate_signature(self, idea: dict) -> str:
        title = idea.get("title", "").lower()
        text = idea.get("text", "").lower()
        words = re.findall(r"[a-z]{3,}", title + " " + text)
        stop_words = {"the", "and", "for", "with", "using", "tool", "app", "ai", "agent", "auto", "system", "platform", "service"}
        key_words = [w for w in words if w not in stop_words]
        return "|".join(sorted(set(key_words))[:10])

    def generate_from_scanner(self) -> list[dict]:
        """Generate ideas from the opportunity scanner."""
        items, _ = run_scan(enable_llm=False, enable_js=True)
        ideas = []

        for item in items:
            if item.get("opportunity_score", 0) < 30:
                continue
            sig = self._generate_signature(item)
            if sig in self.seen_ideas:
                continue
            ideas.append({
                "title": item.get("title", ""),
                "text": item.get("text", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "score": item.get("opportunity_score", 0),
                "category": item.get("category", ""),
                "signals": item.get("signals", []),
                "origin": "scanner",
            })
            self.seen_ideas.add(sig)
        return ideas

    def generate_from_tool_sites(self) -> list[dict]:
        """Generate ideas from tool discovery sites."""
        ideas = []
        try:
            from tool_scanner import (
                fetch_futuretools_newest, fetch_appsumo_new,
                fetch_futurepedia_recent, analyze_tool
            )
            tool_items = []
            tool_items.extend(fetch_appsumo_new(limit=5))
            tool_items.extend(fetch_futuretools_newest(limit=5))
            tool_items.extend(fetch_futurepedia_recent(limit=5))
            for item in tool_items:
                if item.get("opportunity_score", 0) < 30:
                    continue
                sig = self._generate_signature(item)
                if sig in self.seen_ideas:
                    continue
                analyze_tool(item)
                ideas.append({
                    "title": item.get("title", ""),
                    "text": item.get("text", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "score": item.get("opportunity_score", 0),
                    "analysis_score": item.get("analysis_score", 0),
                    "replication": item.get("replication_feasibility", ""),
                    "sentiment": item.get("customer_sentiment", ""),
                    "category": item.get("category", ""),
                    "signals": item.get("signals", []),
                    "origin": "tool_scanner",
                })
                self.seen_ideas.add(sig)
        except Exception as e:
            print(f"  ⚠️ Tool scanner error: {e}")
        return ideas

    def generate_synthetic(self) -> list[dict]:
        """Generate ideas from business patterns."""
        templates = [
            # Content/Marketing automation
            ("AI Content Repurposer", "Turn long-form content into social posts, emails, scripts across platforms",
             "marketing", "marketing", "HIGH"),
            ("AI SEO Content Pipeline", "Automated keyword research → content brief → article → SEO optimization → publish",
             "marketing", "marketing", "HIGH"),
            ("Social Media Content Calendar", "AI generates, schedules, optimizes posts based on engagement data",
             "marketing", "marketing", "HIGH"),
            # Lead Gen / Sales
            ("AI Lead Qualification Bot", "Qualifies inbound leads via email/chat, enriches data, routes to CRM",
             "marketing", "marketing", "HIGH"),
            ("Cold Outreach Personalizer", "Researches prospects, writes hyper-personalized cold emails at scale",
             "marketing", "marketing", "HIGH"),
            ("AI Sales Call Analyzer", "Records, transcribes, analyzes sales calls, extracts insights, updates CRM",
             "marketing", "marketing", "MEDIUM"),
            # Operations / Productivity
            ("AI Invoice Processor", "Extracts data from invoices/receipts, categorizes, syncs to accounting",
             "finance", "finance", "HIGH"),
            ("Meeting Intelligence Agent", "Joins calls, transcribes, summarizes, extracts action items, updates docs",
             "marketing", "marketing", "HIGH"),
            ("AI Document Processor", "Classifies, extracts, routes documents (contracts, invoices, HR forms)",
             "other", "marketing", "HIGH"),
            # Development / Engineering
            ("Code Review Assistant", "Auto-reviews PRs for bugs, style, security, suggests fixes",
             "marketing", "marketing", "HIGH"),
            ("Test Generator", "Analyzes codebase, writes unit/integration tests for uncovered code",
             "marketing", "marketing", "MEDIUM"),
            ("API Documentation Generator", "Generates OpenAPI specs, SDKs, examples from code",
             "marketing", "marketing", "MEDIUM"),
            # Customer Support
            ("AI Support Triage", "Classifies tickets, drafts replies, routes to right team, learns from responses",
             "marketing", "marketing", "HIGH"),
            ("Knowledge Base Builder", "Analyzes tickets, creates/updates help articles, keeps KB current",
             "marketing", "marketing", "HIGH"),
            # Data / Analytics
            ("Competitor Monitor", "Tracks competitor pricing, features, content, alerts on changes",
             "marketing", "marketing", "MEDIUM"),
            ("User Feedback Synthesizer", "Aggregates reviews, tickets, NPS, identifies themes, prioritizes roadmap",
             "marketing", "marketing", "MEDIUM"),
        ]

        ideas = []
        for title, desc, cat, industry, replication in templates:
            sig = f"{title.lower()}|{cat}|{industry}"
            if sig in self.seen_ideas:
                continue
            self.seen_ideas.add(sig)
            ideas.append({
                "title": title,
                "text": desc,
                "source": "synthetic",
                "url": "",
                "score": 50,
                "category": cat,
                "industry": industry,
                "replication": replication,
                "origin": "synthetic",
            })
        return ideas

    def generate_all(self) -> list[dict]:
        """Generate ideas from all sources."""
        all_ideas = []
        all_ideas.extend(self.generate_from_scanner())
        all_ideas.extend(self.generate_from_tool_sites())
        all_ideas.extend(self.generate_synthetic())
        return all_ideas


class IdeaScorer:
    """Scores and ranks ideas based on multiple criteria."""

    def score(self, ideas: list[dict]) -> list[dict]:
        for idea in ideas:
            score = idea.get("score", 30)

            # Origin bonus
            if idea.get("origin") == "scanner":
                score += 10
            elif idea.get("origin") == "tool_scanner":
                score += 15

            # Signals
            signals = idea.get("signals", [])
            if any("🔥" in s for s in signals):
                score += 10
            if any("💡" in s for s in signals):
                score += 5
            if any("📈" in s for s in signals):
                score += 8

            # Replication feasibility
            replication = idea.get("replication", "").upper()
            if "HIGH" in replication:
                score += 15
            elif "MEDIUM" in replication:
                score += 5

            # Customer validation
            if idea.get("reviews", 0) > 50 and idea.get("rating", 0) >= 4.5:
                score += 10

            idea["final_score"] = min(score, 100)

        # Sort descending
        ideas.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return ideas


class IdeaSelector:
    """Selects top ideas based on score."""

    def __init__(self, max_per_run: int = 2):
        self.max_per_run = max_per_run

    def select(self, ideas: list[dict], count: int = None) -> list[dict]:
        count = count or self.max_per_run
        return ideas[:count]


class ProjectBuilder:
    """Builds a project using the autonomous pipeline."""

    def build(self, idea: dict) -> Optional[str]:
        print(f"\n🏗️  Building: {idea['title']}")

        try:
            result = run_full_cycle(
                idea_override=idea["title"],
                category_override=idea.get("category", "marketing"),
                dry_run=False,
            )
            if result != 0:
                print(f"  ❌ Build failed (exit code: {result})")
                return None

            slug = re.sub(r"[^a-z0-9]+", "-", idea["title"].lower()).strip("-")
            project_dir = PROJECTS_DIR / slug

            if not project_dir.exists():
                for d in PROJECTS_DIR.iterdir():
                    if d.is_dir() and slug[:20] in d.name:
                        project_dir = d
                        break

            if not project_dir.exists():
                print(f"  ❌ Project directory not found")
                return None

            print(f"  ✅ Built: {project_dir.name}")
            return str(project_dir)

        except Exception as e:
            print(f"  ❌ Build error: {e}")
            return None


class ImageGenerator:
    """Generates branded images for all platforms."""

    def generate(self, project_name: str, description: str) -> Dict[str, str]:
        try:
            return generate_all_platforms(project_name, description)
        except Exception as e:
            print(f"  ⚠️ Image generation failed: {e}")
            return {}


class SocialPoster:
    """Schedules social media posts via Ocaya."""

    def schedule(self, idea: dict, image_urls: Dict[str, str]) -> Dict[str, Any]:
        results = {}
        try:
            posts = generate_posts({
                "name": idea["title"],
                "description": idea.get("text", "")[:200],
                "github_url": idea.get("url", ""),
                "category": idea.get("category", "marketing"),
                "agents": idea.get("signals", []),
            })

            schedule = [
                ("linkedin", "08:00"),
                ("twitter", "09:00"),
                ("instagram", "10:00"),
                ("facebook", "11:00"),
            ]

            for platform, time_ist in schedule:
                content = posts.get(platform, "")
                if isinstance(content, list):
                    content = "\n\n".join(content)

                image_url = image_urls.get(platform)

                if platform == "instagram" and not image_url:
                    print(f"    ⏭️  Skipping Instagram (no image)")
                    continue

                result = schedule_post(
                    platform=platform,
                    content=content,
                    post_time_ist=time_ist,
                    media_url=image_url,
                    project_name=idea["title"],
                )
                results[platform] = result
                print(f"    ✅ {platform}: {result.get('postGroupId', result.get('error', 'scheduled'))[:30]}")

        except Exception as e:
            print(f"    ❌ Scheduling failed: {e}")

        return results


class MarketplacePublisher:
    """Updates the marketplace with new projects."""

    def publish(self, idea: dict, project_dir: str) -> bool:
        try:
            from autonomous_pipeline import phase_update_marketplace

            agents = []
            pipeline_file = Path(project_dir) / "pipeline_output.json"
            if pipeline_file.exists():
                data = json.loads(pipeline_file.read_text())
                for agent in data.get("roadmap", {}).get("agent_pipeline", []):
                    agents.append(f"{agent.get('name', '')} — {agent.get('role', '')}")

            phase_update_marketplace(
                name=idea["title"],
                repo_url=f"https://github.com/phanindraintelligenzit-afk/{Path(project_dir).name}",
                category=idea.get("category", "marketing"),
                description=idea.get("text", "")[:200],
                agents=agents,
                tags=[idea.get("category", "marketing"), "ai-agent", "automation"],
            )
            print(f"  ✅ Marketplace updated")
            return True
        except Exception as e:
            print(f"  ❌ Marketplace update failed: {e}")
            return False


class IdeaLoopAgent:
    """Main autonomous agent orchestrating the full pipeline."""

    def __init__(
        self,
        min_score: int = 50,
        max_projects_per_run: int = 2,
    ):
        self.min_score = min_score
        self.max_projects_per_run = max_projects_per_run
        self.seen_ideas: set[str] = self._load_seen_ideas()

        # Components
        self.generator = IdeaGenerator(set())
        self.scorer = IdeaScorer()
        self.selector = IdeaSelector(max_per_run=max_projects_per_run)
        self.builder = ProjectBuilder()
        self.image_gen = ImageGenerator()
        self.poster = SocialPoster()
        self.publisher = MarketplacePublisher()

    def _load_seen_ideas(self) -> set[str]:
        seen_file = SCRIPTS_DIR / "seen_ideas.json"
        if seen_file.exists():
            try:
                return set(json.loads(seen_file.read_text()))
            except Exception:
                pass
        return set()

    def _save_seen_ideas(self):
        seen_file = SCRIPTS_DIR / "seen_ideas.json"
        seen_file.write_text(json.dumps(list(self.seen_ideas)))

    def _generate_signature(self, idea: dict) -> str:
        title = idea.get("title", "").lower()
        text = idea.get("text", "").lower()
        words = re.findall(r"[a-z]{3,}", title + " " + text)
        stop_words = {"the", "and", "for", "with", "using", "tool", "app", "ai", "agent", "auto", "system", "platform", "service"}
        key_words = [w for w in words if w not in stop_words]
        return "|".join(sorted(set(key_words))[:10])

    def run_cycle(self) -> dict:
        """Run one full cycle of the autonomous idea loop."""
        print(f"\n{'='*60}")
        print(f"🤖 IDEA LOOP AGENT — {datetime.now(IST).strftime('%Y-%m-%d %I:%M %p IST')}")
        print(f"{'='*60}")

        # 1. Generate ideas from all sources
        generator = IdeaGenerator(self.seen_ideas)
        ideas = generator.generate_all()
        print(f"  💡 Generated {len(ideas)} unique ideas")

        # 2. Score and rank
        scored = IdeaScorer().score(ideas)

        # 3. Select top ideas
        top_ideas = IdeaSelector(self.max_projects_per_run).select(scored)

        if not top_ideas:
            print("  ⚠️ No ideas above threshold")
            return {"built": 0, "ideas": []}

        print(f"\n🎯 Top {len(top_ideas)} ideas selected:")
        for i, idea in enumerate(top_ideas, 1):
            print(f"  {i}. [{idea.get('final_score', 0)}/100] {idea['title']}")

        # 4. Build each project
        results = {"built": 0, "ideas": []}

        for idea in top_ideas:
            # Skip if project directory already exists (already built)
            slug = re.sub(r"[^a-z0-9]+", "-", idea["title"].lower()).strip("-")
            existing_dir = PROJECTS_DIR / slug
            if existing_dir.exists():
                print(f"  ⏭️  Skipping '{idea['title']}' — already built at {existing_dir}")
                continue

            # Build
            project_dir = ProjectBuilder().build(idea)
            if not project_dir:
                continue

            # Generate images
            image_urls = ImageGenerator().generate(idea["title"], idea.get("text", "")[:100])

            # Schedule social posts
            SocialPoster().schedule(idea, image_urls)

            # Update marketplace
            MarketplacePublisher().publish(idea, project_dir)

            results["built"] += 1
            results["ideas"].append({
                "title": idea["title"],
                "score": idea.get("final_score", 0),
                "project_dir": project_dir,
                "image_urls": image_urls,
            })

        return results


def run_idea_loop(min_score: int = 30, max_projects: int = 2) -> dict:
    """Run one cycle of the autonomous idea loop."""
    agent = IdeaLoopAgent(min_score=min_score, max_projects_per_run=max_projects)
    return agent.run_cycle()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Idea Loop Agent")
    parser.add_argument("--min-score", type=int, default=50, help="Minimum score to build")
    parser.add_argument("--max-projects", type=int, default=2, help="Max projects per run")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually build/publish")
    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY RUN — generating ideas only")
        gen = IdeaGenerator(set())
        ideas = gen.generate_all()
        scored = IdeaScorer().score(ideas)
        top = IdeaSelector(args.max_projects).select(scored)
        for i, idea in enumerate(top, 1):
            print(f"  {i}. [{idea.get('final_score', 0)}/100] {idea['title']} ({idea.get('origin', '')})")
    else:
        results = run_idea_loop(min_score=args.min_score, max_projects=args.max_projects)
        print(f"\n✅ Cycle complete: built {results['built']} projects")

# Make sure the file can be run as a script
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Generate ideas only")
    parser.add_argument("--min-score", type=int, default=30, help="Minimum score threshold")
    parser.add_argument("--max-projects", type=int, default=2, help="Max projects per cycle")
    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY RUN — generating ideas only")
        gen = IdeaGenerator(set())
        ideas = gen.generate_all()
        scored = IdeaScorer().score(ideas)
        top = IdeaSelector(args.max_projects).select(scored)
        for i, idea in enumerate(top, 1):
            print(f"  {i}. [{idea.get('final_score', 0)}/100] {idea['title']} ({idea.get('origin', '')})")
    else:
        results = run_idea_loop(min_score=args.min_score, max_projects=args.max_projects)
        print(f"\n✅ Cycle complete: built {results['built']} projects")