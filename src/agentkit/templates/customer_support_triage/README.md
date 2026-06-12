# Customer Support Triage

## What It Does
Reads incoming customer emails/messages, classifies urgency using keyword matching, drafts response templates, queues ambiguous or critical items for human review, and tracks response time metrics.

## Who It's For
- **Support teams** drowning in inbound tickets
- **Solo founders** who need automated triage before responding
- **Agencies** managing support for multiple clients

## How to Set Up

1. **Install dependencies** — only needs `PyYAML` (`pip install pyyaml`)
2. **Configure** `config.yaml` with your urgency keywords and review queue path
3. **Run dry-run first** to verify:
   ```bash
   python src/agentkit/templates/customer_support_triage/agent.py --dry-run
   ```
4. **Run live** when ready:
   ```bash
   python src/agentkit/templates/customer_support_triage/agent.py
   ```
5. **Custom config path**:
   ```bash
   python src/agentkit/templates/customer_support_triage/agent.py --config /path/to/my_config.yaml
   ```

## Configuration Reference

| Parameter | Description | Default |
|---|---|---|
| `email_check_interval_minutes` | How often to check for new messages | `15` |
| `urgency_keywords.critical` | Keywords triggering critical priority | `["down", "outage", "data loss", "security breach"]` |
| `urgency_keywords.high` | Keywords triggering high priority | `["refund", "cancel", "broken", "urgent"]` |
| `urgency_keywords.medium` | Keywords triggering medium priority | `["question", "help", "issue", "bug"]` |
| `urgency_keywords.low` | Keywords triggering low priority | `["feedback", "suggestion", "feature request"]` |
| `response_templates_dir` | Directory for response template files | `data/support_templates` |
| `human_review_queue_path` | Path to JSON file for human review queue | `data/human_review_queue.json` |

## Urgency Classification
Messages are scored by keyword match count per urgency tier. The highest tier with any match wins. Ties are broken by match count. Unmatched messages default to **low** priority.

## Activity Logging
All triage runs, classifications, and human-review queue actions are logged to the `agent_activity` table in `agentsfactory_metrics.db`.
