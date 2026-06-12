"""
Ocoya API Client for AgentsFactory
Base URL: https://app.ocoya.com/api/_public/v1
"""
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Optional

API_KEY = "1e1ed3a3-a319-4340-975d-6e9a901846a0"
BASE_URL = "https://app.ocoya.com/api/_public/v1"
WORKSPACE_ID = "clapmus480dwb5vzyghnv5dku"

# Social Profile IDs
LINKEDIN_PROFILE_ID = "cll7ytoyz002wl70fnxk0tjwr"
TWITTER_PROFILE_ID = "cmdftz3un00187n0rrzbjc8o4"
INSTAGRAM_PROFILE_ID = "cmdftzne6005l1hrgeacfi8sx"
FACEBOOK_PROFILE_ID = "cmdftypmk005e1hrg1b7ow01b"


def _request(method: str, path: str, data: dict = None, params: dict = None) -> dict:
    """Make an authenticated request to the Ocoya API."""
    url = BASE_URL + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-API-Key", API_KEY)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": True, "status": e.code, "message": error_body}


def get_me() -> dict:
    """Get current user info."""
    return _request("GET", "/me")


def get_workspaces() -> list:
    """List all workspaces."""
    return _request("GET", "/workspaces")


def get_social_profiles() -> list:
    """List all connected social profiles."""
    return _request("GET", "/social-profiles", params={"workspaceId": WORKSPACE_ID})


def create_post(
    caption: str,
    social_profile_ids: list[str],
    scheduled_at: str = None,
    media_urls: list[str] = None,
    post_template_id: str = None,
    ai_template: str = None,
    language: str = "en"
) -> dict:
    """
    Create a post (draft or scheduled).
    
    Args:
        caption: Post text content
        social_profile_ids: List of social profile IDs to post to
        scheduled_at: ISO 8601 datetime (e.g., "2025-01-15T10:00:00Z"). None = draft.
        media_urls: Optional list of image/video URLs
        post_template_id: Optional post template ID
        ai_template: Optional AI template name for copy generation
        language: Language code (default "en")
    """
    data = {
        "caption": caption,
        "socialProfileIds": social_profile_ids,
        "language": language,
    }
    if scheduled_at:
        data["scheduledAt"] = scheduled_at
    if media_urls:
        data["mediaUrls"] = media_urls
    if post_template_id:
        data["postTemplateId"] = post_template_id
    if ai_template:
        data["aiTemplate"] = ai_template

    return _request("POST", "/post", data=data, params={"workspaceId": WORKSPACE_ID})


def schedule_post(
    caption: str,
    social_profile_ids: list[str],
    scheduled_at: str,
    media_urls: list[str] = None,
) -> dict:
    """Schedule a post for a specific time."""
    return create_post(
        caption=caption,
        social_profile_ids=social_profile_ids,
        scheduled_at=scheduled_at,
        media_urls=media_urls,
    )


def list_posts(status: str = None, limit: int = 20) -> list:
    """List posts. Optional status filter: DRAFT, SCHEDULED, POSTED, ERROR."""
    params = {"workspaceId": WORKSPACE_ID, "page": "0", "perPage": str(limit)}
    if status:
        params["statuses"] = status
    return _request("GET", "/post", params=params)


def delete_post(post_group_id: str) -> dict:
    """Delete a post by its group ID."""
    return _request("DELETE", f"/post/{post_group_id}", params={"workspaceId": WORKSPACE_ID})


def generate_ai_copy(topic: str, tone: str = "professional", platform: str = "linkedin") -> str:
    """Generate AI copy using Ocoya's AI templates."""
    result = _request("POST", "/ai/copy", data={
        "topic": topic,
        "tone": tone,
        "platform": platform,
        "workspaceId": WORKSPACE_ID,
    })
    return result.get("caption", result.get("content", ""))


# Convenience functions for posting to specific platforms
def post_to_linkedin(caption: str, scheduled_at: str = None, media_urls: list[str] = None) -> dict:
    """Post to LinkedIn."""
    return create_post(
        caption=caption,
        social_profile_ids=[LINKEDIN_PROFILE_ID],
        scheduled_at=scheduled_at,
        media_urls=media_urls,
    )


def post_to_twitter(caption: str, scheduled_at: str = None, media_urls: list[str] = None) -> dict:
    """Post to X/Twitter."""
    return create_post(
        caption=caption,
        social_profile_ids=[TWITTER_PROFILE_ID],
        scheduled_at=scheduled_at,
        media_urls=media_urls,
    )


def post_to_all(caption: str, scheduled_at: str = None, media_urls: list[str] = None) -> dict:
    """Post to all connected platforms."""
    return create_post(
        caption=caption,
        social_profile_ids=[LINKEDIN_PROFILE_ID, TWITTER_PROFILE_ID, INSTAGRAM_PROFILE_ID, FACEBOOK_PROFILE_ID],
        scheduled_at=scheduled_at,
        media_urls=media_urls,
    )


def schedule_linkedin_post(caption: str, hours_from_now: float = 1) -> dict:
    """Schedule a LinkedIn post for X hours from now."""
    dt = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    return post_to_linkedin(caption, scheduled_at=dt.strftime("%Y-%m-%dT%H:%M:%SZ"))


if __name__ == "__main__":
    # Test: verify connection
    me = get_me()
    print(f"Connected as: {me.get('name')} ({me.get('email')})")

    # Test: list scheduled posts
    posts = list_posts()
    print(f"Total posts: {len(posts)}")
