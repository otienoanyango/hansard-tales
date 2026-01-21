# Quick Deployment Guide - Hansard Tales

## TL;DR

**Architecture**: GitHub Actions (build) → Cloudflare Pages (deploy)
**Cost**: ~$0.75/month (domain only)
**Setup Time**: 15 minutes

## Setup Checklist

### 1. Cloudflare Setup (5 minutes)

- [ ] Create Cloudflare account (free)
- [ ] Create Pages project: `hansard-tales`
- [ ] Get API Token (Profile → API Tokens → Create Token)
- [ ] Get Account ID (Dashboard → Copy from sidebar)
- [ ] Disable automatic builds (Settings → Builds & deployments)

### 2. GitHub Secrets (2 minutes)

- [ ] Go to repo Settings → Secrets → Actions
- [ ] Add `CLOUDFLARE_API_TOKEN`
- [ ] Add `CLOUDFLARE_ACCOUNT_ID`

### 3. Test Deployment (5 minutes)

- [ ] Merge `fix/cloudflare-spacy-download` to main
- [ ] Go to Actions → Deploy to Cloudflare Pages
- [ ] Run workflow manually
- [ ] Verify site at `https://hansard-tales.pages.dev/`

### 4. Custom Domain (3 minutes)

- [ ] Cloudflare Pages → Custom domains
- [ ] Add `hansard.co.ke`
- [ ] Configure DNS (automatic if domain on Cloudflare)
- [ ] Wait for SSL certificate (~5 minutes)

## How It Works

### Weekly Automation (Every Sunday 2 AM)

```
1. Scrape new Hansard PDFs
2. Update database
3. Create PR with changes
   ↓
4. You review and merge PR
   ↓
5. GitHub Actions builds site
6. Deploys to Cloudflare
7. Live in 2-3 minutes
```

### Manual Deployment

```bash
# Trigger deployment manually
# Go to: Actions → Deploy to Cloudflare Pages → Run workflow
```

## Troubleshooting

### "Project not found"
→ Check project name in Cloudflare matches workflow: `hansard-tales`

### "Authentication failed"
→ Verify `CLOUDFLARE_API_TOKEN` is correct and has Pages:Edit permission

### "Database not found"
→ Ensure `data/hansard.db` is committed to Git

### "Site shows 404"
→ Check `--base-path /` in site generation command

## Cost Breakdown

| Service | Usage | Cost |
|---------|-------|------|
| GitHub Actions | ~40 min/month | FREE |
| Cloudflare Pages | ~4 deploys/month | FREE |
| Domain (.co.ke) | Annual | KES 1,200/year |
| **TOTAL** | | **~$0.75/month** |

## URLs

- **Production**: `https://hansard.co.ke/` (after domain setup)
- **Preview**: `https://hansard-tales.pages.dev/`
- **GitHub Actions**: `https://github.com/<username>/hansard-tales/actions`
- **Cloudflare Dashboard**: `https://dash.cloudflare.com/`

## Key Files

- `.github/workflows/deploy-cloudflare.yml` - Deployment workflow
- `.github/workflows/weekly-update.yml` - Weekly scraper
- `data/hansard.db` - SQLite database (committed)
- `output/` - Generated site (not committed)

## Support

- **Architecture**: `docs/DEPLOYMENT_ARCHITECTURE.md`
- **Comparison**: `docs/DEPLOYMENT_OPTIONS_COMPARISON.md`
- **Full Setup**: `docs/CLOUDFLARE_DEPLOYMENT_SETUP.md`
- **Migration**: `docs/CLOUDFLARE_MIGRATION_SUMMARY.md`

## Next Steps After Setup

1. Monitor first automated weekly update (next Sunday)
2. Add Cloudflare Web Analytics (free)
3. Configure caching rules (optional)
4. Set up monitoring/alerts (optional)

## Emergency Rollback

If deployment fails:

```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Or rollback in Cloudflare Dashboard
# Pages → Deployments → Select previous → Rollback
```

## Performance Expectations

- **Build Time**: 2-3 minutes
- **Deploy Time**: 30 seconds
- **Total**: ~3 minutes from commit to live
- **Page Load**: < 1 second (static files on CDN)
- **Uptime**: 99.99% (Cloudflare SLA)

## Scaling

Current setup can handle:
- ✅ 10,000+ daily visitors
- ✅ 100,000+ page views/month
- ✅ 10+ years of data growth
- ✅ All on free tier

## Questions?

See detailed documentation in `docs/` folder or open an issue.
