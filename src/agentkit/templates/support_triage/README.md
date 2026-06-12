# Customer Support Triage

## What It Does
Reads incoming support emails/messages, classifies urgency (low/medium/high/critical) using keyword matching and heuristics, drafts response templates based on category, queues items for human review, and tracks response time metrics.

## Who It's For
- **E-commerce stores** drowning in support tickets (Growth tier — $1–3K/mo)
- **SaaS startups** without a dedicated support team
- **Agencies** managing support for multiple clients
- **Scale tier** clients needing 24/7 AI operations

## How to Set Up

1. **No extra dependencies** — uses stdlib only
2. **Configure** `config.yaml` with your urgency keywords and response templates
3. **Run dry-run first**:
   ```bash
   python src/agentkit/templates/support_triage/agent.py --dry-run
   ```
4. **Run live** to write to the review queue:
   ```bash
   python src/agentkit/templates/support_triage/agent.py
   ```

## Urgency Classification
| Level | Keywords | Response SLA |
|---|---|---|
| **Critical** | "urgent", "down", "broken", "can't access", "emergency", "refund", "chargeback" | 1 hour |
| **High** | "issue", "problem", "not working", "error", "complaint", "cancel" | 4 hours |
| **Medium** | "question", "help", "how to", "when", "status" | 24 hours |
| **Low** | "feedback", "suggestion", "feature request", "thanks" | 72 hours |

## Categories
- `order_issue` — Order status, shipping, delivery
- `billing` — Charges, refunds, invoices
- `technical` — Bugs, errors, integration issues
- `account` — Login, access, settings
- `general` — Everything else

## Activity Logging
All triage actions, classifications, and response drafts are logged to `agent_activity` table in `agentsfactory_metrics.db`.
