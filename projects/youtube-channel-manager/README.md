# YouTube Channel Manager

AI-powered content engine that manages your YouTube channel's pre-production workflow.

## What it does

```
Niche Input → Trend Research → Scripts → SEO → Thumbnails → Calendar
```

### Agents

| Agent | Function |
|-------|----------|
| **Trend Researcher** | Generates video ideas with search volume & competition scoring |
| **Script Writer** | Full scripts with hooks, timestamps, visual cues, CTAs |
| **SEO Agent** | 5 title options, description, tags, hashtags |
| **Thumbnail Brief** | Visual concept, text, composition, color guidance |
| **Content Calendar** | Weekly schedule with optimal posting times |

## Usage

```python
from src.pipeline import run_content_engine

result = run_content_engine(
    niche="AI automation tools",
    duration_minutes=8,
    style="educational",
    num_videos=5,
)

# Access results
for idea in result["ideas"]:
    print(f"[{idea['trending_score']}] {idea['title']}")

print(result["calendar"])
```

## Quick ideas only

```python
from src.pipeline import quick_ideas
ideas = quick_ideas("coding", count=10)
```

## Styles

- `educational` — tutorials, how-tos, guides
- `entertainment` — challenges, experiments, reactions
- `review` — honest reviews, comparisons
- `vlog` — behind the scenes, personal

## Future

- YouTube Data API integration (real search volume, competitor analysis)
- OpenRouter LLM for script/title generation
- YouTube Analytics reporting
- Comment management & reply drafting
- Shorts/TikTok repurposing from long-form
