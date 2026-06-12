# Lead Capture & Qualifier

## What It Does
Captures leads from web forms or email, scores them using AI qualification (budget, timeline, company size), creates entries in a local SQLite CRM, and sends Slack alerts for hot leads (score >= 70).

## Who It's For
- **SaaS startups** that need automated lead qualification (Growth tier — $1–3K/mo)
- **E-commerce brands** capturing wholesale inquiries
- **Agencies** managing inbound leads for multiple clients
- **Local businesses** with web forms that go unanswered

## How to Set Up

1. **No extra dependencies** — uses stdlib only
2. **Configure** `config.yaml` with your scoring weights and Slack webhook
3. **Run dry-run first**:
   ```bash
   python src/agentkit/templates/lead_qualifier/agent.py --dry-run
   ```
4. **Run live** to actually write to CRM:
   ```bash
   python src/agentkit/templates/lead_qualifier/agent.py
   ```
5. **Custom config**:
   ```bash
   python src/agentkit/templates/lead_qualifier/agent.py --config /path/to/config.yaml
   ```

## Scoring Model
| Factor | Weight | Criteria |
|---|---|---|
| Budget | 30 pts | >$5K = 30, $1-5K = 15, <$1K = 5 |
| Timeline | 25 pts | Immediate = 25, 1-3 mo = 15, 3+ mo = 5 |
| Company size | 20 pts | 50+ = 20, 10-49 = 12, <10 = 5 |
| Industry fit | 15 pts | Perfect = 15, Partial = 8, Poor = 0 |
| Engagement | 10 pts | Referred = 10, Inbound = 7, Cold = 3 |

**Hot lead threshold**: >= 70 points → Slack alert

## Configuration Reference
| Parameter | Description | Default |
|---|---|---|
| `scoring.hot_threshold` | Score to trigger hot lead alert | `70` |
| `scoring.budget.tier1_min` | Min budget for max points | `5000` |
| `scoring.timeline.immediate_months` | Months considered "immediate" | `1` |
| `notifications.slack_webhook` | Slack webhook for hot lead alerts | `''` |
| `notifications.slack_channel` | Slack channel | `#leads` |
| `crm.table_name` | SQLite table for leads | `leads` |

## Activity Logging
All lead captures, scores, and alerts are logged to `agent_activity` table in `agentsfactory_metrics.db`.
