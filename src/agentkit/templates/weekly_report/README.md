# Weekly Business Report

## What It Does
Pulls data from multiple sources (simulated with sample data), generates a formatted markdown report with orders summary, revenue, top products, and customer insights. Saves to file or sends via email.

## Who It's For
- **E-commerce store owners** who need weekly pulse checks (Starter+ tier)
- **SaaS startups** tracking MRR and growth metrics
- **Agencies** generating client reports automatically
- **Scale tier** clients needing automated reporting pipelines

## How to Set Up

1. **No extra dependencies** — uses stdlib only (jinja2 optional for advanced templates)
2. **Configure** `config.yaml` with your report sections and email settings
3. **Generate a dry-run report**:
   ```bash
   python src/agentkit/templates/weekly_report/agent.py --dry-run
   ```
4. **Generate and save**:
   ```bash
   python src/agentkit/templates/weekly_report/agent.py
   ```
5. **Output as JSON** for integration with other tools:
   ```bash
   python src/agentkit/templates/weekly_report/agent.py --json
   ```

## Report Sections
| Section | Description |
|---|---|
| Executive Summary | Key metrics at a glance |
| Orders Summary | Total orders, avg order value, growth |
| Revenue | Total revenue, MoM comparison, breakdown by channel |
| Top Products | Best sellers by units and revenue |
| Customer Insights | New vs returning, top customers, NPS |
| Recommendations | AI-generated suggestions based on trends |

## Configuration Reference
| Parameter | Description | Default |
|---|---|---|
| `report.title` | Report title | `Weekly Business Report` |
| `report.brand_name` | Your brand name | `Your Company` |
| `report.sections` | List of sections to include | All enabled |
| `notifications.email` | Email to send report | `''` |
| `notifications.email_subject` | Email subject template | `Weekly Report — {date}` |
| `output.save_path` | File path template | `data/reports/weekly_report_{date}.md` |
