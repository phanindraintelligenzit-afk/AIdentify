# Deploy AgentsFactory Landing Page to GitHub Pages

This guide walks you through publishing the landing page at `docs/landing/` to GitHub Pages.

---

## Option 1: Deploy from the `docs/` folder (Recommended)

This is the simplest approach — GitHub Pages serves everything inside a `docs/` folder on the `main` branch.

### Steps

1. **Push the landing page to your repo**

   ```bash
   cd C:\Users\Admin\Projects\AgentsFactory
   git add docs/landing/
   git commit -m "Add AgentsFactory landing page"
   git push origin main
   ```

2. **Enable GitHub Pages**

   - Go to **github.com/phanindraintelligenzit-afk/AgentsFactory**
   - Click **Settings → Pages**
   - Under **Source**, select **Deploy from a branch**
   - Under **Branch**, choose **`main`** and **`/docs`**
   - Click **Save**

3. **Wait 1–2 minutes**, then visit:

   ```
   https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/
   ```

---

## Option 2: Deploy from a `gh-pages` branch

Use this if you don't want to serve the entire `docs/` folder.

### Steps

1. **Create an orphan `gh-pages` branch** with only the landing page:

   ```bash
   cd C:\Users\Admin\Projects\AgentsFactory
   git checkout --orphan gh-pages
   git rm -rf .
   cp -r docs/landing/* .
   git add .
   git commit -m "Deploy landing page to GitHub Pages"
   git push origin gh-pages
   git checkout main
   ```

2. **Enable GitHub Pages**

   - Go to **Settings → Pages**
   - Under **Source**, select **Deploy from a branch**
   - Under **Branch**, choose **`gh-pages`** and **`/(root)`**
   - Click **Save**

3. Your site will be live at:

   ```
   https://phanindraintigenzit-afk.github.io/AgentsFactory/
   ```

---

## Verify the Form

The CTA form submits to **Formspree** (`https://formspree.io/f/xpwzgkby`).

1. Go to [formspree.io](https://formspree.io) and sign up (free tier).
2. Create a new form endpoint and **replace the URL** in `index.html`:
   ```html
   <form action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
   ```
3. Test the form on the live site — you should receive an email notification.

---

## Custom Domain (Optional)

If you want to use a custom domain (e.g., `agentsfactory.com`):

1. Add a `CNAME` file in the `docs/landing/` folder containing:
   ```
   agentsfactory.com
   ```
2. Configure DNS with your domain registrar:
   - **A records** → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - Or a **CNAME record** → `phanindraintelligenzit-afk.github.io`
3. In GitHub, go to **Settings → Pages → Custom domain** and enter your domain.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Page shows 404 | Make sure the repo is public and Pages is enabled in Settings |
| CSS not loading | Check that `style.css` path is relative (`style.css`, not `/style.css`) |
| Form not working | Verify the Formspree endpoint URL; sign up on Formspree to activate it |
| Changes not reflecting | Hard-refresh the page (`Ctrl+Shift+R`) or wait a few minutes for cache |

---

## File Structure

```
AgentsFactory/
└── docs/
    └── landing/
        ├── index.html      ← Landing page
        ├── style.css       ← Stylesheet
        └── DEPLOY.md       ← This file
```
