"""
Tests for scripts/weekly_social_report.py
"""
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is on sys.path so we can import scripts
PROJECT_ROOT = Path("C:/Users/Admin/Projects/AgentsFactory")
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import weekly_social_report as wsr


# ── helpers ────────────────────────────────────────────────────
# Use real profile IDs so PROFILE_NAME_MAP resolves correctly
LN_ID = "cll7ytoyz002wl70fnxk0tjwr"
TW_ID = "cmdftz3un00187n0rrzbjc8o4"
IG_ID = "cmdftzne6005l1hrgeacfi8sx"
FB_ID = "cmdftypmk005e1hrg1b7ow01b"


def _make_post(profile_id, caption="Test post", created_hours_ago=1, eng=None):
    """Build a fake Ocoya post dict."""
    created = (datetime.now(timezone.utc) - timedelta(hours=created_hours_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return {
        "id": f"post_{profile_id}_{created_hours_ago}",
        "caption": caption,
        "createdAt": created,
        "socialProfiles": [{"id": profile_id}],
        "engagement": eng or {"likes": 0, "comments": 0, "shares": 0},
    }


# ── fetch_posts ────────────────────────────────────────────────
class TestFetchPosts:
    @patch("scripts.weekly_social_report.list_posts")
    def test_filters_by_date(self, mock_list):
        """Only posts within the last N days are returned."""
        mock_list.return_value = [
            _make_post(LN_ID, created_hours_ago=2),    # within 7 days
            _make_post(LN_ID, created_hours_ago=200),  # too old
        ]
        posts = wsr.fetch_posts(days=7)
        assert len(posts) == 1

    @patch("scripts.weekly_social_report.list_posts")
    def test_empty_on_api_error(self, mock_list):
        """Returns empty list when Ocoya API fails."""
        mock_list.side_effect = Exception("API down")
        posts = wsr.fetch_posts(days=7)
        assert posts == []

    @patch("scripts.weekly_social_report.list_posts")
    def test_includes_all_platforms(self, mock_list):
        """Posts from multiple platforms are all returned."""
        mock_list.return_value = [
            _make_post(LN_ID, created_hours_ago=1),
            _make_post(TW_ID, created_hours_ago=2),
            _make_post(IG_ID, created_hours_ago=3),
        ]
        posts = wsr.fetch_posts(days=7)
        assert len(posts) == 3


# ── analyse ────────────────────────────────────────────────────
class TestAnalyse:
    def test_groups_by_platform(self):
        posts = [
            _make_post(LN_ID, "Post A", eng={"likes": 10, "comments": 2, "shares": 1}),
            _make_post(LN_ID, "Post B", eng={"likes": 5, "comments": 0, "shares": 0}),
            _make_post(TW_ID, "Post C", eng={"likes": 20, "comments": 5, "shares": 3}),
        ]
        result = wsr.analyse(posts)
        assert "LinkedIn" in result
        assert "Twitter" in result
        assert result["LinkedIn"]["posts"] == 2
        assert result["Twitter"]["posts"] == 1

    def test_avg_engagement(self):
        posts = [
            _make_post(LN_ID, eng={"likes": 10, "comments": 0, "shares": 0}),
            _make_post(LN_ID, eng={"likes": 20, "comments": 0, "shares": 0}),
        ]
        result = wsr.analyse(posts)
        assert result["LinkedIn"]["avg_eng"] == 15.0

    def test_best_post(self):
        posts = [
            _make_post(LN_ID, "Low eng", eng={"likes": 1, "comments": 0, "shares": 0}),
            _make_post(LN_ID, "High eng", eng={"likes": 50, "comments": 10, "shares": 5}),
        ]
        result = wsr.analyse(posts)
        assert result["LinkedIn"]["best_post"] == "High eng"
        assert result["LinkedIn"]["best_eng"] == 65

    def test_empty_posts(self):
        result = wsr.analyse([])
        assert result == {}


# ── format_report ──────────────────────────────────────────────
class TestFormatReport:
    def test_basic_format(self):
        current = {
            "LinkedIn": {"posts": 5, "avg_eng": 12.3, "total_eng": 61, "engaged": 4,
                         "best_post": "Great post", "best_eng": 30},
        }
        previous = {
            "LinkedIn": {"posts": 4, "avg_eng": 10.0, "total_eng": 40, "engaged": 3,
                         "best_post": "Old post", "best_eng": 20},
        }
        report = wsr.format_report(current, previous, days=7)
        assert "📊" in report
        assert "LinkedIn" in report
        assert "5 posts" in report
        assert "📈" in report or "📉" in report or "🆕" in report

    def test_no_previous_data(self):
        current = {
            "Twitter": {"posts": 3, "avg_eng": 5.0, "total_eng": 15, "engaged": 2,
                        "best_post": "Tweet", "best_eng": 10},
        }
        previous = {}
        report = wsr.format_report(current, previous, days=7)
        assert "🆕 first week" in report

    def test_empty_both_periods(self):
        report = wsr.format_report({}, {}, days=7)
        assert "No posts found" in report

    def test_insight_generated(self):
        current = {
            "LinkedIn": {"posts": 5, "avg_eng": 20.0, "total_eng": 100, "engaged": 5,
                         "best_post": "Viral", "best_eng": 50},
        }
        previous = {}
        report = wsr.format_report(current, previous, days=7)
        assert "💡" in report
        assert "Insight" in report

    def test_wow_decline(self):
        current = {
            "LinkedIn": {"posts": 3, "avg_eng": 10.0, "total_eng": 30, "engaged": 2,
                         "best_post": "Post", "best_eng": 15, "engaged": 2},
        }
        previous = {
            "LinkedIn": {"posts": 6, "avg_eng": 15.0, "total_eng": 90, "engaged": 5,
                         "best_post": "Old", "best_eng": 40, "engaged": 5},
        }
        report = wsr.format_report(current, previous, days=7)
        assert "📉" in report


# ── _generate_insight ──────────────────────────────────────────
class TestGenerateInsight:
    def test_no_data(self):
        insight = wsr._generate_insight({}, {})
        assert "No posts" in insight or "cron" in insight.lower()

    def test_best_platform(self):
        current = {
            "LinkedIn": {"posts": 3, "avg_eng": 25.0},
            "Twitter":  {"posts": 3, "avg_eng": 5.0},
        }
        insight = wsr._generate_insight(current, {})
        assert "LinkedIn" in insight

    def test_low_volume(self):
        current = {
            "LinkedIn": {"posts": 1, "avg_eng": 0},
        }
        insight = wsr._generate_insight(current, {})
        assert "Low post volume" in insight or "2+" in insight


# ── _slack_post (dry-run safe) ─────────────────────────────────
class TestSlackPost:
    @patch.dict(os.environ, {"SLACK_BOT_TOKEN": ""})
    def test_no_token_returns_false(self):
        assert wsr._slack_post("test") is False

    @patch("scripts.weekly_social_report.urllib.request.urlopen")
    @patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test"})
    def test_successful_post(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True}).encode()
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        assert wsr._slack_post("test") is True
