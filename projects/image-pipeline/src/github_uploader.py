"""Image uploader — uploads generated images to GitHub for hosting.

Uses git + gh CLI (already authenticated) to push images to a dedicated repo,
then returns the raw URL for use in social media posts.
"""
import subprocess
import os
from pathlib import Path

GITHUB_REPO = "phanindraintelligenzit-afk/social-assets"
REPO_URL = f"https://github.com/{GITHUB_REPO}.git"
REPO_DIR = Path(__file__).resolve().parent / ".social-assets-repo"


def ensure_repo_cloned():
    """Clone the repo if not already present."""
    if not REPO_DIR.exists():
        subprocess.run(
            ["git", "clone", "--depth", "1", str(REPO_URL), str(REPO_DIR)],
            check=True, capture_output=True,
        )
        # Create images directory
        (REPO_DIR / "images").mkdir(exist_ok=True)


def upload_image(local_path: str) -> str:
    """Upload an image to GitHub and return the raw URL.

    Args:
        local_path: Path to local image file

    Returns:
        Raw GitHub URL for the image
    """
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {local_path}")

    ensure_repo_cloned()

    # Copy image to repo
    dest = REPO_DIR / "images" / path.name
    dest.write_bytes(path.read_bytes())

    # Git add, commit, push
    subprocess.run(["git", "add", "images/"], cwd=REPO_DIR, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"Add {path.name}"],
        cwd=REPO_DIR, check=True, capture_output=True,
    )
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True, capture_output=True)

    # Return raw URL
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/images/{path.name}"


if __name__ == "__main__":
    print("Testing image upload...")
    url = upload_image("../../promotion-engine/src/output/twitter_youtube-channel-manager.png")
    print(f"Uploaded: {url}")
