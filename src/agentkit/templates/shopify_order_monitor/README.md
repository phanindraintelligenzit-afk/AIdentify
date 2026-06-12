# Shopify Order Monitor

## What It Does
Monitors a Shopify store for new orders, flags anomalies (high-value orders, bulk quantities, risk-country shipments), and sends a daily summary report via Slack or email.

## Who It's For
- **E-commerce store owners** who need automated order surveillance
- **Growing brands** processing 50+ orders/day
- **Agencies** managing multiple client stores

## How to Set Up

1. **Install dependencies** — only needs `PyYAML` (`pip install pyyaml`)
2. **Configure** `config.yaml` with your Shopify store URL and alert thresholds
3. **Run dry-run first** to verify:
   ```bash
   python src/agentkit/templates/shopify_order_monitor/agent.py --dry-run
   ```
4. **Run live** when ready:
   ```bash
   python src/agentkit/templates/shopify_order_monitor/agent.py
   ```
5. **Custom config path**:
   ```bash
   python src/agentkit/templates/shopify_order_monitor/agent.py --config /path/to/my_config.yaml
   ```

## Configuration Reference

| Parameter | Description | Default |
|---|---|---|
| `shopify_store_url` | Your Shopify store URL | `your-store.myshopify.com` |
| `slack_webhook` | Slack incoming webhook URL | `""` |
| `email_recipients` | List of email addresses for summaries | `[]` |
| `anomaly_thresholds.high_value_order` | Flag orders above this value | `5000` |
| `anomaly_thresholds.bulk_quantity` | Flag line items with qty >= this | `10` |
| `anomaly_thresholds.risk_countries` | Country codes flagged for review | `["NG", "PK", "BD", "VN"]` |

## Anomaly Detection Rules
- **High value**: Order total exceeds `high_value_order` threshold
- **Bulk quantity**: Any line item has quantity >= `bulk_quantity`
- **Risk country**: Shipping address is in a flagged country code
- **Suspiciously low**: Order total is below $0.50 (likely a test order)

## Activity Logging
All monitoring runs and flagged orders are logged to the `agent_activity` table in `agentsfactory_metrics.db`.
