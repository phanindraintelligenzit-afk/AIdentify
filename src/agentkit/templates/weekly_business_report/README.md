# Weekly Business Report

## What It Does
Pulls simulated data from multiple business sources (orders, revenue, customers, content), generates a formatted markdown report with key insights, saves it to a dated file, and logs all activity.

## Who It's For
- **Founders** who want a weekly snapshot without logging into dashboards
- **Agency owners** tracking client performance metrics
- **Ops teams** automating recurring reporting

## How to Set Up

1. **Install dependencies** — only needs `PyYAML` (`pip install pyyaml`)
2. **Configure** `config.yaml` with your report output directory and data sources
3. **Run dry-run first** to verify:
   ```bash
   python src/agentkit/templates/weekly_business_report/agent.py --dry-run
   ```
4. **Run live** when ready:
   ```bash
   python src/agentkit/templates/weekly_business_report/agent.py
   ```
5. **Custom config path**:
   ```bash
   python src/agentkit/templates/weekly_business_report/agent.py --config /path/to/my_config.yaml
   ```

## Configuration Reference

| Parameter | Description | Default |
|---|---|---|
| `report_output_dir` | Directory for generated reports | `data/reports` |
| `email_recipients` | List of email addresses for report delivery | `[]` |
| `data_sources.orders` | Enable orders data source | `true` |
| `data_sources.revenue` | Enable revenue data source | `true` |
| `data_sources.customers` | Enable customers data source | `true` |
| `data_sources.content` | Enable content performance data source | `true` |

## Report Sections
- **Orders Summary**: Total orders, average order value, order status breakdown
- **Revenue**: Weekly revenue, growth vs previous week, top revenue day
- **Top Products**: Best-selling products by quantity and revenue
- **Customer Insights**: New vs returning, top customers, geographic distribution
- **Content Performance**: Page views, engagement rate, top-performing content

## Activity Logging
All report generation runs are logged to the `agent_activity` table in `agentsfactory_metrics.db`.
