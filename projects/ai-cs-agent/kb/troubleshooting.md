# AIdentify Troubleshooting Guide

## Agent won't deploy
- Check that your account has available agent quota (Settings → Usage)
- Verify all required API keys are configured in Integrations
- Ensure the agent template is compatible with your plan tier
- Try refreshing the page and deploying again
- If the error persists, check the deployment logs for specific error messages

## Integration connection failures
- Verify the third-party service is operational (check their status page)
- Re-authenticate the integration (Settings → Integrations → Reconnect)
- Check that you have admin/owner permissions on the third-party account
- Some integrations require specific OAuth scopes — grant all requested permissions
- For custom API connectors: verify the endpoint URL and auth headers are correct

## Agent returns incorrect responses
- Check the agent's prompt configuration — it may need more context
- Review the knowledge base sources attached to the agent
- Try adding more specific examples to the agent's system prompt
- If using RAG mode, ensure your documents are properly uploaded
- Consider adjusting the temperature setting (lower = more deterministic)

## High latency / slow responses
- Complex multi-agent workflows may take 30-60 seconds
- Check service status at https://status.aidentify.ai
- Free tier requests may be deprioritized during peak hours
- Consider upgrading to Pro for dedicated compute resources

## "Rate limit exceeded" error
- Each plan tier has rate limits:
  - Free: 10 requests/minute
  - Pro: 100 requests/minute  
  - Enterprise: Custom limits
- Implement request queuing in your agent workflow
- If you're hitting limits consistently, consider upgrading your plan

## Billing issues
- Verify your payment method is current (Settings → Billing → Payment Methods)
- Check for failed invoices in your billing history
- Failed payment attempts will trigger email notifications
- After 3 failed attempts, the account is downgraded to Free tier
- Contact billing@aidentify.ai for invoice questions or refund requests

## Data not syncing
- Check the integration connection status
- Some platforms have sync delays (up to 15 minutes for Google Workspace)
- Verify the agent has the correct data source permissions
- Try manually triggering a sync from the agent's history panel
