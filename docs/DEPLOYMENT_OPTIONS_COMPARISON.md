# Deployment Options Comparison for Hansard Tales MVP

## Executive Summary

**Recommended**: GitHub Actions (build) + Cloudflare Pages (deploy) with SQLite in Git

**Cost**: ~$0.75/month (domain only)
**Complexity**: Low
**Scalability**: High (clear migration path)

## Option 1: Local DB Updates + Manual Commits ❌

### How It Works
```
Developer Machine → Update DB → Commit Everything → Push to Git → Deploy
```

### Pros
- ✅ Simple mental model
- ✅ No CI/CD complexity
- ✅ Full control over updates

### Cons
- ❌ **Manual workflow** - defeats automation purpose
- ❌ **Large commits** - 953 HTML files + DB = 2-3 MB per update
- ❌ **Git bloat** - repository grows ~150 MB/year
- ❌ **No automation** - requires developer intervention weekly
- ❌ **Error prone** - manual steps can be forgotten
- ❌ **Not scalable** - doesn't work for team collaboration

### Cost
- **FREE** (no CI/CD costs)

### Verdict
**Not Recommended** - Defeats the purpose of weekly automation. Only suitable for one-off projects.

---

## Option 2: GitHub Actions Build + Cloudflare Deploy ✅ **RECOMMENDED**

### How It Works
```
GitHub Actions (Weekly) → Scrape → Update DB → Generate Site → Deploy to Cloudflare
```

### Pros
- ✅ **Fully automated** - runs weekly without intervention
- ✅ **Clean Git history** - only commits DB + PDFs (~500 KB)
- ✅ **No SQLite issues** - GitHub Actions has full Python support
- ✅ **Free tier sufficient** - both services have generous limits
- ✅ **Fast deployment** - 2-3 minutes from commit to live
- ✅ **PR workflow** - review changes before deployment
- ✅ **Scalable** - can handle 10,000+ daily visitors
- ✅ **Reliable** - no database connection failures

### Cons
- ⚠️ **Two services** - GitHub + Cloudflare (but both free)
- ⚠️ **Initial setup** - requires API tokens and secrets (one-time)

### Cost
| Service | Usage | Cost |
|---------|-------|------|
| GitHub Actions | ~40 min/month | **FREE** (2,000 min limit) |
| Cloudflare Pages | ~4 deploys/month | **FREE** (500 deploys limit) |
| Domain (.co.ke) | Annual | **KES 1,200/year** |
| **TOTAL** | | **~$0.75/month** |

### Implementation
1. Weekly workflow scrapes and updates DB
2. Creates PR with changes
3. On merge, deploys to Cloudflare via Wrangler CLI
4. Site updates within 2-3 minutes

### Scalability Path
- **Current**: 433 MPs, ~1,500 statements, 500 KB DB
- **1 year**: ~2,000 statements, ~1 MB DB
- **3 years**: ~6,000 statements, ~3 MB DB
- **5 years**: ~10,000 statements, ~5 MB DB

**Verdict**: Can run on free tier for 5+ years before needing external database.

### Verdict
**RECOMMENDED** - Best balance of cost, simplicity, and scalability for MVP.

---

## Option 3: External Database (Supabase/DynamoDB) ❌

### How It Works
```
GitHub Actions → Update External DB → Generate Site → Deploy
```

### Pros
- ✅ **Dynamic updates** - can update without rebuilding site
- ✅ **Scalable storage** - no Git size concerns
- ✅ **API access** - can build mobile apps, third-party integrations
- ✅ **Real-time features** - comments, ratings, live updates

### Cons
- ❌ **Overkill for MVP** - data updates weekly, not real-time
- ❌ **Added complexity** - need API layer, authentication, CORS
- ❌ **Cost** - free tiers have limits, then $25+/month
- ❌ **Latency** - extra network hop vs static files
- ❌ **Maintenance** - database backups, migrations, monitoring
- ❌ **Vendor lock-in** - harder to migrate later

### Cost Comparison

#### Supabase
| Tier | Storage | Bandwidth | Requests | Cost |
|------|---------|-----------|----------|------|
| Free | 500 MB | 2 GB/month | Unlimited | **FREE** |
| Pro | 8 GB | 50 GB/month | Unlimited | **$25/month** |

**Estimate**: Free tier sufficient for 2-3 years, then $25/month.

#### DynamoDB
| Resource | Free Tier | Cost After |
|----------|-----------|------------|
| Storage | 25 GB | $0.25/GB/month |
| Reads | 25 RCU | $0.00013/RCU |
| Writes | 25 WCU | $0.00065/WCU |

**Estimate**: ~$5-15/month depending on traffic.

### When to Consider
- ✅ Database > 100 MB (years away)
- ✅ Need real-time updates (not weekly batch)
- ✅ User-generated content (comments, ratings)
- ✅ Advanced search (full-text, complex filters)
- ✅ Mobile app or API access

### Verdict
**Not Recommended for MVP** - Adds cost and complexity with no immediate benefit. Consider when you hit scalability limits (years away).

---

## Alternative Scenarios

### Scenario A: Hybrid Static + Dynamic

**Architecture**:
```
Static Site (Cloudflare Pages) + Cloudflare Workers (API) + Supabase (DB)
```

**Use Case**: 
- Static pages for performance
- Dynamic search/filters via API
- User comments/ratings

**Cost**: $0-25/month (depending on usage)

**When**: When you need dynamic features but want to keep static site performance.

---

### Scenario B: Incremental Static Regeneration (ISR)

**Architecture**:
```
Next.js on Vercel + Supabase
```

**Use Case**:
- Static pages with on-demand regeneration
- Best of both worlds: static performance + dynamic updates

**Cost**: 
- Vercel: FREE (100 GB bandwidth/month)
- Supabase: FREE (500 MB storage)

**Pros**:
- ✅ Better DX (Next.js ecosystem)
- ✅ ISR for dynamic pages
- ✅ API routes built-in

**Cons**:
- ⚠️ Vendor lock-in (Vercel)
- ⚠️ Bandwidth limits (100 GB/month)
- ⚠️ More complex than pure static

**When**: When you need dynamic features and prefer Next.js ecosystem.

---

### Scenario C: Serverless Functions + Edge Caching

**Architecture**:
```
Cloudflare Workers + Cloudflare KV + Cloudflare Pages
```

**Use Case**:
- API endpoints at the edge
- Key-value storage for frequently accessed data
- Static site for everything else

**Cost**: 
- Workers: FREE (100k requests/day)
- KV: FREE (100k reads/day, 1k writes/day)
- Pages: FREE

**Pros**:
- ✅ All on Cloudflare (single vendor)
- ✅ Edge computing (low latency)
- ✅ Generous free tier

**Cons**:
- ⚠️ KV is key-value only (not relational)
- ⚠️ Workers have 50ms CPU time limit
- ⚠️ More complex than static site

**When**: When you need API endpoints but want to stay on Cloudflare.

---

### Scenario D: Self-Hosted VPS

**Architecture**:
```
DigitalOcean Droplet + Nginx + PostgreSQL + Python
```

**Use Case**:
- Full control over infrastructure
- Custom server configuration
- No vendor lock-in

**Cost**: $5-10/month (basic VPS)

**Pros**:
- ✅ Full control
- ✅ No vendor lock-in
- ✅ Can run any software

**Cons**:
- ❌ Maintenance burden (updates, security, backups)
- ❌ Uptime responsibility (no SLA)
- ❌ Scaling complexity (manual)
- ❌ Ongoing cost (even with zero traffic)

**When**: When you need full control and have DevOps expertise.

---

## Decision Matrix

| Criteria | Option 1 (Local) | Option 2 (GH Actions) | Option 3 (External DB) |
|----------|------------------|----------------------|------------------------|
| **Cost** | ⭐⭐⭐⭐⭐ FREE | ⭐⭐⭐⭐⭐ ~$1/month | ⭐⭐⭐ $0-25/month |
| **Simplicity** | ⭐⭐⭐ Manual | ⭐⭐⭐⭐⭐ Automated | ⭐⭐ Complex |
| **Automation** | ⭐ Manual | ⭐⭐⭐⭐⭐ Full | ⭐⭐⭐⭐ Full |
| **Scalability** | ⭐⭐ Limited | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Performance** | ⭐⭐⭐⭐ Static | ⭐⭐⭐⭐⭐ Static+CDN | ⭐⭐⭐ Dynamic |
| **Maintenance** | ⭐⭐ High | ⭐⭐⭐⭐⭐ Low | ⭐⭐⭐ Medium |
| **Reliability** | ⭐⭐⭐ Manual | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐⭐ High |

## Recommendation

### For MVP (Now)
**Option 2: GitHub Actions + Cloudflare Pages**

**Rationale**:
1. ✅ Essentially free (~$1/month for domain)
2. ✅ Fully automated weekly updates
3. ✅ No SQLite issues (GitHub Actions has full support)
4. ✅ Fast performance (static files on CDN)
5. ✅ Reliable (no database connection failures)
6. ✅ Scalable (can handle 10,000+ daily visitors)
7. ✅ Clean Git history (only commits source data)

### For Scale (Future)
**Migrate to Option 3 when**:
1. Database > 50 MB (years away at current rate)
2. Need real-time updates (not weekly batch)
3. Want user-generated content (comments, ratings)
4. Need advanced search (full-text, complex filters)
5. Building mobile app or API access

**Migration Path**:
1. Export SQLite to PostgreSQL (Supabase)
2. Add API layer (Cloudflare Workers or Next.js)
3. Keep static site for performance (ISR)
4. Estimated effort: 2-3 weeks

## Implementation Plan

### Phase 1: MVP (Current)
- ✅ GitHub Actions builds everything
- ✅ Commit only DB + PDFs to Git
- ✅ Deploy to Cloudflare Pages via Wrangler
- ✅ Cost: ~$1/month

### Phase 2: Analytics (Month 2-3)
- Add Cloudflare Web Analytics (free)
- Monitor traffic patterns
- Identify popular MPs/parties

### Phase 3: Optimization (Month 4-6)
- Implement caching strategies
- Optimize image delivery
- Add service worker for offline support

### Phase 4: Dynamic Features (Month 7-12)
- Evaluate need for external database
- Add search filters via Cloudflare Workers
- Consider user accounts (if needed)

### Phase 5: Scale (Year 2+)
- Migrate to Supabase if database > 50 MB
- Add API for mobile app
- Implement ISR for dynamic pages

## Conclusion

**Start with Option 2** (GitHub Actions + Cloudflare Pages) for MVP:
- Minimal cost (~$1/month)
- Fully automated
- Scalable for years
- Clear migration path when needed

**Avoid Option 3** (External Database) until you have:
- Proven traffic (1,000+ daily visitors)
- Need for real-time updates
- Budget for ongoing costs ($25+/month)

The beauty of Option 2 is that it's not a dead-end. You can migrate to Option 3 later with minimal effort when you actually need it.
