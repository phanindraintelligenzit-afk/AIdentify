"""Image Pipeline — generates branded social media images for AIdentify posts.

Creates platform-optimized images with:
- Project name overlay
- AIdentify branding
- Platform-specific dimensions
- Gradient backgrounds

Uses PIL (no external API needed).
"""
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Platform dimensions
DIMENSIONS = {
    "twitter": (1200, 675),    # 16:9
    "linkedin": (1200, 627),   # 1.91:1
    "instagram": (1080, 1080), # 1:1
    "facebook": (1200, 630),   # 1.91:1
}

# Brand colors (gradient pairs)
GRADIENTS = [
    (("#667eea", "#764ba2"), "purple-blue"),
    (("#f093fb", "#f5576c"), "pink-red"),
    (("#4facfe", "#00f2fe"), "cyan-blue"),
    (("#43e97b", "#38f9d7"), "green-teal"),
    (("#fa709a", "#fee140"), "pink-yellow"),
    (("#a18cd1", "#fbc2eb"), "lavender-pink"),
    (("#ffecd2", "#fcb69f"), "peach"),
    (("#667eea", "#43e97b"), "blue-green"),
]

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_social_image(
    project_name: str,
    description: str,
    platform: str = "twitter",
    output_path: str = None,
) -> str:
    """Generate a branded social media image.

    Args:
        project_name: Name of the project
        description: Short description (1 line)
        platform: twitter, linkedin, instagram, facebook
        output_path: Optional custom output path

    Returns:
        Path to generated image
    """
    width, height = DIMENSIONS.get(platform, (1200, 675))

    # Pick a gradient
    gradient, _ = random.choice(GRADIENTS)

    # Create image with gradient
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw, width, height, gradient)

    # Add subtle pattern overlay
    _add_pattern(img, width, height)

    # Draw text
    _draw_text(img, width, height, project_name, description)

    # Add AIdentify branding
    _add_branding(img, width, height)

    # Save
    if not output_path:
        safe_name = project_name.lower().replace(" ", "-")[:30]
        output_path = str(OUTPUT_DIR / f"{platform}_{safe_name}.png")

    img.save(output_path, "PNG")
    return output_path


def _draw_gradient(draw, width, height, colors):
    """Draw a diagonal gradient."""
    start_color = _hex_to_rgb(colors[0])
    end_color = _hex_to_rgb(colors[1])

    for y in range(height):
        for x in range(width):
            # Diagonal gradient factor
            factor = (x + y) / (width + height)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)
            draw.point((x, y), fill=(r, g, b))


def _add_pattern(img, width, height):
    """Add subtle geometric pattern overlay."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Subtle dots
    for x in range(0, width, 40):
        for y in range(0, height, 40):
            draw.ellipse([x, y, x+2, y+2], fill=(255, 255, 255, 15))

    img.paste(Image.alpha_composite(Image.new("RGBA", img.size, (0,0,0,0)), overlay).convert("RGB"), (0, 0))


def _draw_text(img, width, height, project_name, description):
    """Draw project name and description."""
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        desc_font = ImageFont.truetype("arial.ttf", 28)
    except (IOError, OSError):
        try:
            title_font = ImageFont.truetype("/c/Windows/Fonts/arial.ttf", 48)
            desc_font = ImageFont.truetype("/c/Windows/Fonts/arial.ttf", 28)
        except (IOError, OSError):
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()

    # Title (centered, upper-middle)
    title_text = _truncate_text(project_name, 25)
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (width - title_w) // 2
    title_y = height // 3

    # Draw title with shadow
    draw.text((title_x+2, title_y+2), title_text, font=title_font, fill=(0, 0, 0, 100))
    draw.text((title_x, title_y), title_text, font=title_font, fill=(255, 255, 255))

    # Description (below title)
    desc_text = _truncate_text(description, 50)
    desc_bbox = draw.textbbox((0, 0), desc_text, font=desc_font)
    desc_w = desc_bbox[2] - desc_bbox[0]
    desc_x = (width - desc_w) // 2
    desc_y = title_y + 80

    draw.text((desc_x, desc_y), desc_text, font=desc_font, fill=(255, 255, 255, 220))


def _add_branding(img, width, height):
    """Add AIdentify logo/branding."""
    draw = ImageDraw.Draw(img)

    try:
        brand_font = ImageFont.truetype("arial.ttf", 20)
    except (IOError, OSError):
        try:
            brand_font = ImageFont.truetype("/c/Windows/Fonts/arial.ttf", 20)
        except (IOError, OSError):
            brand_font = ImageFont.load_default()

    # Bottom-left branding
    brand_text = "AIdentify • AI Agent Swarm"
    draw.text((30, height - 40), brand_text, font=brand_font, fill=(255, 255, 255, 180))

    # Top-right robot emoji indicator
    draw.text((width - 150, 20), "🤖", font=brand_font, fill=(255, 255, 255))


def _hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _truncate_text(text, max_chars):
    """Truncate text with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars-3] + "..."


def generate_all_platforms(project_name: str, description: str) -> dict:
    """Generate images for all platforms at once.

    Returns:
        dict mapping platform -> image path
    """
    results = {}
    for platform in DIMENSIONS:
        path = generate_social_image(project_name, description, platform)
        results[platform] = path
    return results


if __name__ == "__main__":
    # Demo
    print("Generating social media images...")

    result = generate_all_platforms(
        project_name="YouTube Channel Manager",
        description="AI content engine for creators",
    )

    for platform, path in result.items():
        size = os.path.getsize(path)
        print(f"  ✅ {platform}: {path} ({size/1024:.1f} KB)")

    print(f"\nAll images saved to: {OUTPUT_DIR}")
