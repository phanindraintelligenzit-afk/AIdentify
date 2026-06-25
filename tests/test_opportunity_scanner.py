#!/usr/bin/env python3
"""Tests for opportunity_scanner.py — scoring engine and briefing generator."""

import sys
import json
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from opportunity_scanner import score_opportunity, generate_briefing


def test_score_opportunity_pain_signals():
    """Items with pain keywords should score higher."""
    item = {
        "title": "Struggling with manual work, need automation",
        "text": "We are overwhelmed by repetitive tasks and looking for a solution",
        "source": "hackernews",
        "score": 5,
        "comments": 2,
    }
    result = score_opportunity(item)
    assert result["opportunity_score"] >= 30, f"Expected >= 30, got {result['opportunity_score']}"
    assert any("pain" in s.lower() for s in result["signals"]), "Should detect pain signals"


def test_score_opportunity_no_signals():
    """Items with no relevant keywords should score low."""
    item = {
        "title": "My vacation photos from Iceland",
        "text": "Here are some pictures I took last summer",
        "source": "search",
    }
    result = score_opportunity(item)
    assert result["opportunity_score"] < 25, f"Expected < 25, got {result['opportunity_score']}"


def test_score_opportunity_github_source():
    """GitHub source should get source quality bonus."""
    item_no_source = {"title": "AI agent framework", "text": "", "source": "search"}
    item_github = {"title": "AI agent framework", "text": "", "source": "github"}
    score_no = score_opportunity(item_no_source)["opportunity_score"]
    score_gh = score_opportunity(item_github)["opportunity_score"]
    assert score_gh > score_no, f"GitHub ({score_gh}) should score higher than search ({score_no})"


def test_score_opportunity_industry_match():
    """Items matching industries should have industry signals."""
    item = {
        "title": "Healthcare compliance automation for HIPAA",
        "text": "Medical records audit trail for clinics",
        "source": "hackernews",
    }
    result = score_opportunity(item)
    assert any("healthcare" in s.lower() for s in result["signals"]), "Should detect healthcare industry"


def test_score_opportunity_engagement():
    """High engagement items should get engagement signals."""
    item = {
        "title": "AI automation workflow",
        "text": "",
        "source": "hackernews",
        "score": 50,
        "comments": 25,
    }
    result = score_opportunity(item)
    assert any("engagement" in s.lower() for s in result["signals"]), "Should detect high engagement"


def test_score_opportunity_max_100():
    """Score should never exceed 100."""
    item = {
        "title": "AI agent automation workflow LLM SaaS no-code API integration bot scraping monitoring analytics dashboard lead gen outreach CRM email marketing compliance audit security observability",
        "text": " ".join(["manual struggling overwhelmed hiring help needed automate automation too much work bottleneck time-consuming repetitive tedious need help looking for solution frustrated waste of time inefficient streamline optimize"] * 3),
        "source": "hackernews",
        "score": 100,
        "comments": 100,
    }
    result = score_opportunity(item)
    assert result["opportunity_score"] <= 100, f"Score should be <= 100, got {result['opportunity_score']}"


def test_generate_briefing_empty():
    """Briefing with no opportunities should not crash."""
    briefing = generate_briefing([])
    assert "Opportunity Scanner" in briefing
    assert "0 opportunities" in briefing


def test_generate_briefing_sorting():
    """Briefing should sort opportunities by score descending."""
    items = [
        {"title": "Low score item", "opportunity_score": 30, "source": "search", "text": "", "url": ""},
        {"title": "High score item", "opportunity_score": 80, "source": "hackernews", "text": "", "url": ""},
        {"title": "Mid score item", "opportunity_score": 45, "source": "devto", "text": "", "url": ""},
    ]
    briefing = generate_briefing(items)
    # High score should appear before low score
    high_pos = briefing.index("High score item")
    low_pos = briefing.index("Low score item")
    assert high_pos < low_pos, "High score item should appear before low score item"


def test_generate_briefing_filters_low_scores():
    """Briefing should filter out items with score < 20."""
    items = [
        {"title": "Good item", "opportunity_score": 50, "source": "hackernews", "text": "", "url": ""},
        {"title": "Terrible item", "opportunity_score": 5, "source": "search", "text": "", "url": ""},
    ]
    briefing = generate_briefing(items)
    assert "Good item" in briefing
    # Low score item should not appear (below threshold)
    assert "Terrible item" not in briefing


def test_generate_briefing_includes_url():
    """Briefing should include URLs when available."""
    items = [
        {"title": "Item with URL", "opportunity_score": 60, "source": "hackernews", "text": "Some text", "url": "https://example.com"},
    ]
    briefing = generate_briefing(items)
    assert "https://example.com" in briefing


def test_generate_briefing_max_10():
    """Briefing should show at most 10 opportunities."""
    import re
    items = [
        {"title": f"Item number {i:02d}", "opportunity_score": 50 + i, "source": "hackernews", "text": "", "url": ""}
        for i in range(15)
    ]
    briefing = generate_briefing(items)
    # Count occurrences of numbered items — should be at most 10
    matches = re.findall(r"Item number \d+", briefing)
    assert len(matches) <= 10, f"Expected at most 10 items, got {len(matches)}: {matches}"


if __name__ == "__main__":
    tests = [
        test_score_opportunity_pain_signals,
        test_score_opportunity_no_signals,
        test_score_opportunity_github_source,
        test_score_opportunity_industry_match,
        test_score_opportunity_engagement,
        test_score_opportunity_max_100,
        test_generate_briefing_empty,
        test_generate_briefing_sorting,
        test_generate_briefing_filters_low_scores,
        test_generate_briefing_includes_url,
        test_generate_briefing_max_10,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    if failed > 0:
        sys.exit(1)
