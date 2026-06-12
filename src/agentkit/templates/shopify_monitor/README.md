# Shopify Order Monitor

## What It Does
Monitors a Shopify store for new orders, flags anomalies (unusual order values, bulk orders, high-risk shipping countries), and sends a daily summary to Slack or email.

## Who It's For
- **E-commerce store owners** (Starter tier — $500–1K/mo)
- **Growing brands** that need automated order surveillance (Growth tier)
- **Agencies** managing multiple client stores

## How to Set Up

1. **Install dependencies** (stdlib only — no pip installs needed)
2. **Configure** `config.yaml` with your Shopify credentials and thresholds
3. **Run dry-run first** to verify:
   ```bash
   python src/agentkit/templates/shopify_monitor/agent.py --dry-run
   ```
4. **Run live** when ready:
   ```bash
   python src/agentkit/templates/shopify_monitor/agent.py
   ```
5. **Custom config path**:
   ```bash
   python src/agentkit/templates/shopify_monitor/agent.py --config /path/to/my_config.yaml
   ```

## Configuration Reference
| Parameter | Description | Default |
|---|---|---|
| `shopify.store_url` | Your Shopify store URL | `your-store.myshopify.com` |
| `shopify.api_key` | Admin API key | `YOUR_API_KEY` |
| `shopify.api_secret` | Admin API secret | `YOUR_API_SECRET` |
| `thresholds.max_order_value` | Flag orders above this value | `5000` |
| `thresholds.bulk_quantity` | Flag line items with quantity >= this | `10` |
| `thresholds.high_risk_countries` | List of country codes to flag | `['NG', 'PK', 'BD', 'VN']` |
| `notifications.slack_webhook` | Slack incoming webhook URL | `''` |
| `notifications.email` | Email address for summaries | `''` |
| `notifications.daily_summary_hour` | Hour (0–23) to send daily summary | `9` |

## Anomaly Detection Rules
- **Unusual order value**: Total order value exceeds `max_order_value` threshold
- **Bulk order**: Any line item has quantity >= `bulk_quantity`
- **High-risk country**: Shipping address is in a flagged country code
- **Rapid fire**: >5 orders from same IP in 10 minutes (simulated)

## Activity Logging
All checks and flagged orders are logged to the `agent_activity` table in `agentsfactory_metrics.db`.
