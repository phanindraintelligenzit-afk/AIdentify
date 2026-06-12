# Social Media Scheduler

## What It Does
Reads a content calendar from the AgentsFactory metrics database, schedules posts across platforms (LinkedIn, Twitter/X), tracks simulated engagement metrics, and automatically reshare top-performing content after a configurable threshold.

## Who It's For
- **Content creators** automating multi-platform posting
- **Marketing teams** managing a recurring content calendar
- **Agencies** scheduling social media for multiple clients

## How to Set Up

1. **Install dependencies** — only needs `PyYAML` (`pip install pyyaml`)
2. **Configure** `config.yaml` with your platforms and scheduling preferences
3. **Run dry-run first** to verify:
   ```bash
   python src/agentkit/templates/social_media_scheduler/agent.py --dry-run
   ```
4. **Run live** when ready:
   ```bash
   python src/agentkit/templates/social_media_scheduler/agent.py
   ```
5. **Custom config path**:
   ```bash
   python src/agentkit/templates/social_media_scheduler/agent.py --config /path/to/my_config.yaml
   ```

## Configuration Reference

| Parameter | Description | Default |
|---|---|---|
| `platforms` | List of platforms to schedule on | `["linkedin", "twitter"]` |
| `max_posts_per_day` | Maximum posts per platform per day | `3` |
| `content_calendar_db_path` | Path to SQLite DB with content calendar | `agentsfactory_metrics.db` |
| `reshare_threshold_days` | Days after which top content is reshared | `7` |

## Reshare Logic
Posts with engagement rate above the 75th percentile are flagged as "top-performing." If `reshare_threshold_days` have passed since the original post, the agent schedules an automatic reshare.

## Activity Logging
All scheduling runs, posts queued, and reshare actions are logged to the `agent_activity` table in `agentsfactory_metrics.db`.
