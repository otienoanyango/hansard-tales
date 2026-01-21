# Cloudflare Pages Deployment Setup

## Overview
This guide explains how to deploy Hansard Tales to Cloudflare Pages using GitHub Actions for building and Wrangler CLI for deployment.

## Architecture

```
GitHub Actions (Build) → Wrangler CLI → Cloudflare Pages (Deploy)
```

**Key Principle**: Cloudflare Pages does NOT build anything. It only serves pre-built static files from GitHub Actions.

## Prerequisites

1. Cloudflare account (free tier is sufficient)
2. GitHub repository with Hansard Tales code
3. Domain registered (optional, can use `*.pages.dev` subdomain)

## Step 1: Create Cloudflare Pages Project

### Option A: Via Dashboard (Recommended for Initial Setup)

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Workers & Pages** → **Pages**
3. Click **Create application** → **Pages**
4. Click **Connect to Git** → Select your GitHub repository
5. Configure build settings:
   ```
   Build command: (leave empty)
   Build output directory: output
   Root directory: (leave empty)
   Framework preset: None
   ```
6. Click **Save and Deploy**
7. **Important**: Go to **Settings** → **Builds & deployments** → **Disable automatic deployments**
   - We'll deploy via GitHub Actions instead

### Option B: Via Wrangler CLI

```bash
# Install Wrangler globally
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create Pages project
wrangler pages project create hansard-tales
```

## Step 2: Get Cloudflare Credentials

### Get API Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Click on your profile → **API Tokens**
3. Click **Create Token**
4. Use template: **Edit Cloudflare Workers**
5. Or create custom token with permissions:
   - **Account** → **Cloudflare Pages** → **Edit**
6. Copy the token (you'll only see it once!)

### Get Account ID

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select any domain or go to **Workers & Pages**
3. Copy **Account ID** from the right sidebar

## Step 3: Add Secrets to GitHub

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

   **Secret 1:**
   ```
   Name: CLOUDFLARE_API_TOKEN
   Value: <paste your API token>
   ```

   **Secret 2:**
   ```
   Name: CLOUDFLARE_ACCOUNT_ID
   Value: <paste your account ID>
   ```

## Step 4: Configure Custom Domain (Optional)

### If Using .co.ke Domain

1. Go to your Cloudflare Pages project
2. Navigate to **Custom domains**
3. Click **Set up a custom domain**
4. Enter your domain: `hansard.co.ke`
5. Follow DNS configuration instructions:

   **If domain is on Cloudflare:**
   - DNS records are added automatically
   - Wait for SSL certificate (usually < 5 minutes)

   **If domain is on Safaricom/other registrar:**
   - Add CNAME record:
     ```
     Type: CNAME
     Name: @ (or hansard)
     Value: hansard-tales.pages.dev
     ```
   - Wait for DNS propagation (up to 24 hours)
   - SSL certificate will be issued automatically

## Step 5: Test Deployment

### Manual Test

1. Go to **Actions** tab in GitHub
2. Select **Deploy to Cloudflare Pages** workflow
3. Click **Run workflow** → Select `main` branch
4. Wait for completion (~2-3 minutes)
5. Check deployment at: `https://hansard-tales.pages.dev`

### Verify Deployment

Check these URLs work:
- Homepage: `https://hansard-tales.pages.dev/`
- MP Profile: `https://hansard-tales.pages.dev/mp/1/`
- Party Page: `https://hansard-tales.pages.dev/party/uda/`
- Search: `https://hansard-tales.pages.dev/search/`

## Step 6: Automated Workflow

Once setup is complete, deployments happen automatically:

1. **Weekly Update** (Every Sunday 2 AM EAT):
   - Scrapes new Hansard PDFs
   - Updates database
   - Creates PR with changes

2. **On PR Merge to Main**:
   - GitHub Actions builds site from updated database
   - Deploys to Cloudflare Pages via Wrangler
   - Site updates within 2-3 minutes

## Troubleshooting

### Issue: "Project not found"

**Solution**: Ensure project name in workflow matches Cloudflare:
```yaml
command: pages deploy output --project-name=hansard-tales
```

Check project name in Cloudflare Dashboard → Workers & Pages.

### Issue: "Authentication failed"

**Solution**: 
1. Verify `CLOUDFLARE_API_TOKEN` is correct
2. Check token has **Cloudflare Pages:Edit** permission
3. Token might have expired - create a new one

### Issue: "Account ID invalid"

**Solution**: 
1. Copy Account ID from Cloudflare Dashboard
2. Ensure no extra spaces in GitHub secret
3. Account ID should be 32 characters (hex)

### Issue: "Build failed - database not found"

**Solution**: 
1. Ensure `data/hansard.db` is committed to Git
2. Run weekly update workflow first to create database
3. Check `.gitignore` doesn't exclude database

### Issue: "Site shows 404 errors"

**Solution**: 
1. Check `--base-path` in site generation:
   ```bash
   hansard-generate-site --base-path /
   ```
2. Verify `output/` directory structure is correct
3. Check Cloudflare Pages build output directory is set to `output`

## Monitoring

### Cloudflare Analytics

1. Go to your Pages project
2. Navigate to **Analytics** tab
3. View:
   - Page views
   - Unique visitors
   - Bandwidth usage
   - Top pages

### GitHub Actions Logs

1. Go to **Actions** tab
2. Click on workflow run
3. View build logs and deployment status

## Cost Breakdown

| Service | Free Tier | Usage | Cost |
|---------|-----------|-------|------|
| Cloudflare Pages | 500 builds/month, Unlimited bandwidth | ~4 builds/month | **FREE** |
| GitHub Actions | 2,000 minutes/month | ~40 minutes/month | **FREE** |
| Custom Domain | N/A | .co.ke domain | **KES 1,200/year** |
| **TOTAL** | | | **~$0.75/month** |

## Comparison: Cloudflare Build vs GitHub Actions Build

### Cloudflare Build (Current - Broken)
```
❌ Pros: Simple configuration
❌ Cons: No SQLite support, build failures, limited control
```

### GitHub Actions Build (Recommended)
```
✅ Pros: Full Python/SQLite support, more build time, better control
✅ Cons: Slightly more complex setup (one-time)
```

## Migration from GitHub Pages

If you were using GitHub Pages before:

1. Keep GitHub Pages workflow for backup/testing
2. Update DNS to point to Cloudflare Pages
3. Both can run simultaneously (different domains)

**GitHub Pages URL**: `https://<username>.github.io/hansard-tales/`
**Cloudflare Pages URL**: `https://hansard.co.ke/`

## Next Steps

1. ✅ Complete this setup guide
2. ✅ Test manual deployment
3. ✅ Verify custom domain works
4. ✅ Wait for first automated weekly update
5. ✅ Monitor analytics and performance

## Support

- **Cloudflare Docs**: https://developers.cloudflare.com/pages/
- **Wrangler Docs**: https://developers.cloudflare.com/workers/wrangler/
- **GitHub Actions**: https://docs.github.com/en/actions

## Alternative: Keep Cloudflare Build (Not Recommended)

If you must use Cloudflare's build system:

1. Use Python buildpack with SQLite compiled in (complex)
2. Or commit pre-built `output/` directory to Git (defeats purpose)
3. Or use external database (adds cost and complexity)

**Verdict**: GitHub Actions build is simpler and more reliable.
