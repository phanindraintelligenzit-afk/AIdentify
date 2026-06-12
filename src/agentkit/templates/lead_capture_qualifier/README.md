# Lead Capture & Qualifier

## What It Does
Captures incoming leads from web forms, scores them using AI qualification criteria, stores them in a local SQLite CRM, and sends Slack alerts when hot leads (score >= 70) are detected.

## Who It's For
- **B2B SaaS teams** automating their inbound lead pipeline
- **Agencies** qualifying prospects before sales handoff
- **Solo founders** who need lead triage without a full CRM

## How to Set Up

1. **Install dependencies** — only needs `PyYAML` (`pip install pyyaml`)
2. **Configure** `config.yaml` with your Slack webhook and CRM path
3. **Run dry-run first** to verify:
   ```bash
   python src/agentkit/templates/lead_capture_qualifier/agent.py --dry-run
   ```
4. **Run live** when ready:
   ```bash
   python src/agentkit/templates/lead_capture_qualifier/agent.py
   ```
5. **Custom config path**:
   ```bash
   python src/agentkit/templates/lead_capture_qualifier/agent.py --config /path/to/my_config.yaml
   ```

## Configuration Reference

| Parameter | Description | Default |
|---|---|---|
| `slack_webhook` | Slack incoming webhook for hot lead alerts | `""` |
| `hot_leader_threshold` | Score threshold for "hot lead" alerts | `70` |
| `crm_db_path` | Path to SQLite CRM database | `data/leads.db` |

## Scoring Criteria (0–100)
- **Budget** (0–30 pts): Higher budget = higher score
- **Timeline** (0–25 pts): Shorter timeline = higher score
- **Company size** (0–20 pts): Larger company = higher score
- **Industry fit** (0–15 pts): Target industries score higher
- **Engagement source** (0–10 pts): Referrals and inbound calls score highest

## Activity Logging
All lead processing runs and hot-lead alerts are logged to the `agent_activity` table in `agentsfactory_metrics.db`.
