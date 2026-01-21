# Hansard Tales - Deployment Architecture

## Overview
Hansard Tales uses a **static site generation** approach with **GitHub Actions** as the build system and **Cloudflare Pages** as the CDN/hosting platform.

## Architecture Decision

### Why Static Site + GitHub Actions?

**For MVP (Current State)**:
- ✅ **Zero cost** (both GitHub Actions and Cloudflare Pages are free)
- ✅ **No database hosting needed** (SQLite committed to Git)
- ✅ **Fast performance** (static HTML served from CDN)
- ✅ **Simple deployment** (no backend to manage)
- ✅ **Reliable** (no database connection failures)

**For Scale (Future State)**:
- ✅ **Easy migration path** to Supabase/PostgreSQL when needed
- ✅ **Can add dynamic features** incrementally
- ✅ **Database size manageable** (433 MPs × ~3 years = ~50 MB max)

## Deployment Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ Weekly Update (Every Sunday 2 AM EAT)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Scrape new Hansard PDFs from parliament.go.ke               │
│  2. Process PDFs → Extract statements                           │
│  3. Update SQLite database (data/hansard.db)                    │
│  4. Generate search index (output/search-index.json)            │
│  5. Generate static site (output/*.html)                        │
│  6. Create Pull Request with DB + PDF changes                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                    (User reviews and merges PR)
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Deployment (On merge to main)                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. GitHub Actions builds site from updated database            │
│  2. Deploys to GitHub Pages (hansard-tales.github.io)           │
│  3. Deploys to Cloudflare Pages (hansard.co.ke)                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## What Gets Committed to Git

### Committed (Small, Essential Data)
- ✅ `data/hansard.db` (~500 KB, grows slowly)
- ✅ `data/pdfs/*.pdf` (~5-10 MB, weekly additions)
- ✅ Source code and templates

### NOT Committed (Generated, Large)
- ❌ `output/` directory (~2-3 MB, 953 files)
- ❌ `output/search-index.json` (~300 KB)
- ❌ Generated HTML files

**Rationale**: Database is source of truth (small), generated files are artifacts (large, reproducible).

## Cloudflare Pages Configuration

### Current Setup (Needs Change)
```yaml
Build command: bash scripts/cloudflare-build.sh
Build output directory: output
Root directory: (default)
```

**Problem**: Cloudflare tries to build, but Python SQLite support is missing.

### Recommended Setup (Deploy Only)
```yaml
Build command: (empty)
Build output directory: output
Root directory: (default)
Framework preset: None
```

**Solution**: GitHub Actions builds, Cloudflare just deploys the artifacts.

## Deployment Methods

### Method 1: Wrangler CLI (Recommended)
Deploy from GitHub Actions using Cloudflare's official CLI:

```yaml
- name: Deploy to Cloudflare Pages
  uses: cloudflare/wrangler-action@v3
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    command: pages deploy output --project-name=hansard-tales
```

**Pros**: 
- Direct deployment from CI/CD
- No build step in Cloudflare
- Full control over deployment

### Method 2: GitHub Integration (Current)
Connect Cloudflare Pages to GitHub repository:

**Pros**: 
- Automatic deployments on push
- Preview deployments for PRs

**Cons**: 
- Cloudflare tries to build (causes SQLite errors)
- Need to disable build step

### Method 3: Direct Upload
Manual upload via Cloudflare dashboard:

**Pros**: 
- Simple for testing

**Cons**: 
- Not automated
- Not suitable for production

## Cost Analysis

### Current Architecture (Static Site)
| Service | Usage | Cost |
|---------|-------|------|
| GitHub Actions | ~10 min/week build time | **FREE** (2,000 min/month) |
| GitHub Pages | Static hosting | **FREE** |
| Cloudflare Pages | CDN + hosting | **FREE** (500 builds/month) |
| Domain (.co.ke) | Annual registration | **KES 1,200/year** (~$9) |
| **TOTAL** | | **~$0.75/month** |

### Alternative: External Database
| Service | Usage | Cost |
|---------|-------|------|
| Supabase | 500 MB DB, 2 GB bandwidth | **FREE** (then $25/month) |
| DynamoDB | 25 GB storage, 200M requests | **FREE** (then pay-per-use) |
| API Hosting | Cloudflare Workers | **FREE** (100k req/day) |
| **TOTAL** | | **$0-25/month** |

**Verdict**: External DB adds complexity and cost with no MVP benefit.

## Migration Path (When to Scale)

### Triggers to Consider External Database:
1. **Database size** > 100 MB (years away at current rate)
2. **Need real-time updates** (not weekly batch)
3. **User-generated content** (comments, ratings)
4. **Advanced search** (full-text, filters beyond static)
5. **API access** (mobile app, third-party integrations)

### Migration Strategy:
1. Export SQLite to PostgreSQL (Supabase)
2. Add API layer (Cloudflare Workers or Next.js API routes)
3. Keep static site for performance
4. Use ISR (Incremental Static Regeneration) for dynamic pages
5. Estimated effort: 2-3 weeks

## Recommended Implementation

### Immediate Changes (This PR):
1. ✅ Remove build logic from Cloudflare
2. ✅ Deploy pre-built artifacts from GitHub Actions
3. ✅ Use Wrangler CLI for deployment

### Future Enhancements:
1. Add Cloudflare Workers for dynamic search (when needed)
2. Implement caching strategies (Cloudflare Cache API)
3. Add analytics (Cloudflare Web Analytics - free)
4. Consider Supabase when database > 50 MB

## Alternative Architectures Considered

### Option A: Vercel + Supabase
**Cost**: Vercel free tier + Supabase free tier
**Pros**: Better DX, serverless functions
**Cons**: Vercel bandwidth limits (100 GB/month), vendor lock-in

### Option B: Netlify + PostgreSQL
**Cost**: Netlify free tier + Hosted PostgreSQL
**Pros**: Similar to Cloudflare
**Cons**: Netlify build minutes limited (300/month), DB costs

### Option C: AWS S3 + CloudFront + RDS
**Cost**: ~$15-30/month
**Pros**: Full AWS ecosystem
**Cons**: Overkill for MVP, complex setup, ongoing costs

### Option D: Self-hosted (VPS)
**Cost**: $5-10/month (DigitalOcean, Linode)
**Pros**: Full control
**Cons**: Maintenance burden, uptime responsibility

## Conclusion

**Recommended Architecture**: 
- **Build**: GitHub Actions (free, reliable, SQLite support)
- **Deploy**: Cloudflare Pages via Wrangler (free, fast CDN)
- **Database**: SQLite in Git (simple, sufficient for MVP)
- **Future**: Migrate to Supabase when needed (clear path)

**Total Cost**: ~$0.75/month (domain only)
**Scalability**: Can handle 10,000+ daily visitors on free tier
**Maintenance**: Minimal (automated weekly updates)

This architecture optimizes for:
1. ✅ **Cost** (essentially free)
2. ✅ **Simplicity** (no backend to manage)
3. ✅ **Performance** (static files on CDN)
4. ✅ **Reliability** (no database connection issues)
5. ✅ **Scalability** (clear migration path when needed)
