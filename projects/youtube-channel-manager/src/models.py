"""Data models for YouTube Channel Manager."""
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class VideoType(str, Enum):
    LONG_FORM = "long_form"
    SHORT = "short"
    LIVE = "live"


class VideoIdea(BaseModel):
    """A researched video idea."""
    title: str
    niche: str
    search_volume: str  # high, medium, low
    competition: str  # high, medium, low
    trending_score: float  # 0-100
    description: str
    target_audience: str
    estimated_views: str  # rough estimate category


class Script(BaseModel):
    """A full video script."""
    video_id: str
    title: str
    hook: str  # First 30 seconds
    intro: str
    body: list[dict]  # [{"timestamp": "0:30", "content": "...", "visual": "..."}]
    cta: str  # Call to action
    outro: str
    estimated_duration: str  # e.g., "8:30"
    b_roll_notes: list[str] = []
    sound_music_notes: list[str] = []


class SEOPackage(BaseModel):
    """SEO metadata for a video."""
    titles: list[str]  # 5 options
    description: str
    tags: list[str]
    hashtags: list[str]
    thumbnail_text: str  # Short text overlay suggestion


class ThumbnailBrief(BaseModel):
    """Visual brief for thumbnail creation."""
    concept: str
    main_text: str  # 3-5 words max
    background: str  # colors, style
    subject: str  # what/who is shown
    emotion: str  # what feeling to evoke
    composition: str  # layout description
    reference_style: str  # "like MrBeast" / "like MKBHD" etc.


class ContentCalendarItem(BaseModel):
    """A scheduled piece of content."""
    date: str
    video_id: str
    title: str
    status: str  # idea, scripting, filming, editing, ready, published
    platform: str = "youtube"
    notes: str = ""


class WeeklyPlan(BaseModel):
    """A full week of content."""
    niche: str
    week_start: str
    videos: list[dict]  # Combined idea + script + seo + thumbnail
    posting_schedule: list[ContentCalendarItem]
    content_pillars: list[str]  # 3-5 themes for the week
