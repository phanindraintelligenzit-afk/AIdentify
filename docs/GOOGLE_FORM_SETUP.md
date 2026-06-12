# Google Form Setup Guide for AgentsFactory

## Step 1: Create the Google Form

1. Go to [forms.google.com](https://forms.google.com) → Click **"Blank"** to create a new form
2. Title: **"AgentsFactory — Free Automation Audit"**
3. Description: *"Tell us about your business and we'll show you exactly where AI can save you time and money. No strings attached."*

### Add these fields:

| Field | Type | Required | Options |
|-------|------|----------|---------|
| Full Name | Short answer | ✅ | — |
| Email Address | Short answer (email validation) | ✅ | — |
| Business Type | Dropdown | ✅ | E-Commerce Store, SaaS / Tech Company, Local / Brick-and-Mortar Business, Marketing / Creative Agency, Other |
| Biggest Pain Point | Paragraph | ✅ | — |

## Step 2: Link to Google Sheet

1. In the form, click **"Responses"** tab
2. Click the green Sheets icon → **"Create a new spreadsheet"**
3. Name it: **"AgentsFactory Leads"**
4. Copy the **Sheet ID** from the URL:
   - URL looks like: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Copy the part between `/d/` and `/edit`

## Step 3: Share the Sheet (for sync script)

1. Open the Google Sheet
2. Click **Share** → **Anyone with the link** → **Viewer**
3. This allows the sync script to read responses

## Step 4: Add Sheet ID to Config

Add this line to `~/.hermes/.env`:

```
GOOGLE_FORM_SHEET_ID=YOUR_SHEET_ID_HERE
```

## Step 5: Test the Form

1. Open the form → Click **Send** → Copy the link
2. Fill it out with a test entry
3. Check the Google Sheet — the response should appear
4. Run the sync script:

```bash
cd C:\Users\Admin\Projects\AgentsFactory
python3 src/agents/form_sync.py
```

The lead should appear in the Command Center dashboard (Leads page) and in Notion.

## Step 6: Embed in Landing Page (Optional)

You can also embed the form directly in the landing page:

1. In Google Form → Click **Send** → **Embed HTML**
2. Copy the iframe code
3. Replace the Formspree form in `docs/landing/index.html` with the iframe

## Automation

Once set up, the sync script can be run on a schedule:

```bash
# Add to crontab (every 30 minutes)
*/30 * * * * cd /c/Users/Admin/Projects/AgentsFactory && python3 src/agents/form_sync.py
```

Or use Hermes cron:

```
hermes cron create --schedule "every 30m" --prompt "Run form sync: python3 src/agents/form_sync.py"
```
