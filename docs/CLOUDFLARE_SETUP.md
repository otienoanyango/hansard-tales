# Cloudflare Pages Setup Guide

This guide walks you through deploying Hansard Tales to Cloudflare Pages with a custom .ke domain.

## Prerequisites

- GitHub account with hansard-tales repository
- Cloudflare account (free tier is sufficient)
- Custom domain (e.g., hansardtales.ke or hansardtales.co.ke)

## Step 1: Register Your Domain

**Important**: Cloudflare does NOT support registration of .ke domains. You must register with a Kenyan domain registrar and then transfer DNS management to Cloudflare.

### Domain Choice: .co.ke with Safaricom

**Selected Configuration:**
- **Domain Type**: .co.ke (Commercial)
- **Registrar**: Safaricom Digital
- **Cost**: KES 1,200/year (~$9.25 USD / ~£0.77/month)
- **Payment**: M-Pesa or Airtel Money

**Why .co.ke?**
- No special registration requirements (unlike .or.ke which requires NGO documentation)
- Professional appearance suitable for civic transparency platform
- Supports hybrid revenue model (ads, partnerships, grants)
- Widely used by legitimate civic tech and journalism platforms in Kenya
- Immediate registration - no paperwork delays

**Why Safaricom?**
- Most trusted brand in Kenya
- Excellent local customer support
- Reliable infrastructure and uptime
- Easy M-Pesa payment integration
- Strong reputation for domain management

**Alternative Registrars** (if needed):
| Registrar | .co.ke Price | Payment Options | Key Features |
|-----------|--------------|-----------------|--------------|
| **Truehost Kenya** | KES 850/year (~$6.55) | M-Pesa, Card, PayPal | Cheapest option, good reputation |
| **Kenya Web Experts** | KES 999/year (~$7.70) | M-Pesa, Card, Bank | Established since 2003, free WHOIS privacy |

### Registrar Selection Criteria

When choosing a registrar, verify:

1. **DNS Management**: Must allow custom nameserver changes (required for Cloudflare)
2. **Transfer Policy**: Free transfers out, no lock-in periods
3. **Payment Options**: M-Pesa support preferred for Kenyan users
4. **Auto-Renewal**: Optional but recommended, with email reminders
5. **Customer Support**: Local Kenyan support preferred
6. **Domain Privacy**: WHOIS protection to hide personal details
7. **Control Panel**: Easy-to-use, self-service DNS management
8. **Reputation**: Check reviews and uptime history
9. **Hidden Fees**: Verify renewal prices match initial price
10. **Bulk Discounts**: Consider if planning multiple domains

### Domain Registration Process with Safaricom

1. **Visit Safaricom Digital**: Go to [safaricom.co.ke](https://www.safaricom.co.ke/) and navigate to domain services
2. **Search for your domain**: Enter `hansardtales.co.ke` to check availability
3. **Complete registration**:
   - Provide contact details (email, phone number)
   - Choose registration period (1 year recommended for MVP)
   - Add WHOIS privacy if available (protects personal details)
   - Review total cost: KES 1,200/year
4. **Payment via M-Pesa**:
   - Select M-Pesa as payment method
   - Follow prompts to complete payment
   - Save payment confirmation
5. **Save credentials**: Store Safaricom account login details in password manager
6. **Proceed to Step 2**: Add domain to Cloudflare for DNS management

## Step 2: Add Domain to Cloudflare

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Click **"Add a Site"**
3. Enter your domain name (e.g., `hansardtales.ke`)
4. Select **Free plan**
5. Cloudflare will scan your DNS records
6. Click **Continue**
7. Update your domain's nameservers at your registrar to the ones provided by Cloudflare
8. Wait for DNS propagation (can take 24-48 hours, usually faster)

## Step 3: Create Cloudflare Pages Project

1. In Cloudflare Dashboard, go to **Workers & Pages**
2. Click **Create application**
3. Select **Pages** tab
4. Click **Connect to Git**

### Connect GitHub Repository

1. Click **Connect GitHub**
2. Authorize Cloudflare to access your GitHub account
3. Select **otienoanyango/hansard-tales** repository
4. Click **Begin setup**

### Configure Build Settings

**Project name:**
```
hansard-tales
```

**Production branch:**
```
main
```

**Framework preset:**
```
None
```

**Build command:**
```bash
bash scripts/cloudflare-build.sh
```

**Build output directory:**
```
output
```

**Root directory (advanced):**
```
/
```

### Environment Variables

Click **Add variable** and add:

| Variable Name | Value |
|--------------|-------|
| `PYTHON_VERSION` | `3.11` |

### Build Configuration (Advanced)

**Build watch paths (optional):**
```
hansard_tales/**
templates/**
static/**
data/**
pyproject.toml
requirements.txt
scripts/cloudflare-build.sh
```

**Preview deployments:**
- ✅ Enable automatic preview deployments
- ✅ Enable preview comments on pull requests

Click **Save and Deploy**

## Step 4: Configure Custom Domain

### Add Custom Domain to Pages Project

1. Go to your Pages project in Cloudflare Dashboard
2. Click **Custom domains** tab
3. Click **Set up a custom domain**
4. Enter your domain: `hansardtales.ke`
5. Click **Continue**

### Configure DNS Records

Cloudflare will automatically create the necessary DNS records:

**For root domain (hansardtales.ke):**
- Type: `CNAME`
- Name: `@` (or your domain)
- Target: `hansard-tales.pages.dev`
- Proxy status: Proxied (orange cloud)

**For www subdomain (optional):**
- Type: `CNAME`
- Name: `www`
- Target: `hansardtales.ke`
- Proxy status: Proxied (orange cloud)

Click **Activate domain**

### SSL/TLS Configuration

1. Go to **SSL/TLS** in Cloudflare Dashboard
2. Set encryption mode to **Full (strict)**
3. Enable **Always Use HTTPS**
4. Enable **Automatic HTTPS Rewrites**

## Step 5: Configure Caching Rules

1. Go to **Caching** → **Configuration**
2. Set **Browser Cache TTL** to `4 hours`
3. Enable **Always Online**

### Create Cache Rules (Optional)

Go to **Rules** → **Page Rules** and create:

**Rule 1: Cache static assets**
- URL: `hansardtales.ke/static/*`
- Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 week

**Rule 2: Cache MP profiles**
- URL: `hansardtales.ke/mp/*`
- Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 day
  - Browser Cache TTL: 4 hours

## Step 6: Enable Analytics

1. Go to **Analytics & Logs** → **Web Analytics**
2. Click **Enable Web Analytics**
3. Copy the analytics script (optional - for additional insights)
4. Cloudflare automatically tracks basic metrics

## Step 7: Test Your Deployment

1. Wait for initial build to complete (~2-3 minutes)
2. Visit your custom domain: `https://hansardtales.ke`
3. Test key pages:
   - Homepage with search
   - MP profiles
   - Party pages
   - MPs listing
4. Test on mobile devices
5. Check page load times

## Step 8: Update GitHub Workflows (Optional)

Since Cloudflare handles deployments automatically, you can simplify your GitHub workflows:

### Option A: Keep Both (Recommended)
- Keep GitHub Pages for backup/redundancy
- Cloudflare Pages as primary
- Both deploy automatically on push to main

### Option B: Cloudflare Only
- Disable GitHub Pages workflow
- Remove `.github/workflows/deploy-pages.yml`
- Keep weekly update workflow (it commits to Git, Cloudflare auto-deploys)

## Deployment Workflow

### Automatic Deployments

**Production (main branch):**
1. Push to `main` branch (or merge PR)
2. Cloudflare automatically builds and deploys
3. Site updates at `hansardtales.ke` in ~2-3 minutes

**Preview (feature branches):**
1. Push to any feature branch
2. Cloudflare builds preview deployment
3. Preview URL: `<branch-name>.hansard-tales.pages.dev`
4. Comment with preview URL appears on PR

### Manual Deployments

1. Go to Pages project in Cloudflare Dashboard
2. Click **Deployments** tab
3. Click **Create deployment**
4. Select branch and click **Deploy**

## Monitoring and Maintenance

### Check Build Status

1. Go to Pages project → **Deployments**
2. View build logs for any deployment
3. Check for errors or warnings

### Monitor Analytics

1. Go to **Analytics & Logs** → **Web Analytics**
2. View metrics:
   - Page views
   - Unique visitors
   - Top pages
   - Geographic distribution
   - Referrers

### Build Limits (Free Tier)

- 500 builds/month
- 1 concurrent build
- Unlimited bandwidth
- Unlimited requests

With weekly updates + occasional manual deploys, you'll use ~10-20 builds/month.

## Troubleshooting

### Build Fails

**Check build logs:**
1. Go to Deployments → Click failed deployment
2. View build log
3. Common issues:
   - Missing dependencies: Check `requirements.txt`
   - Python version: Ensure `PYTHON_VERSION=3.11` is set
   - Database initialization: Check data files exist

**Solution:**
- Fix issue in code
- Push to GitHub
- Cloudflare automatically retries build

### Domain Not Working

**Check DNS propagation:**
```bash
dig hansardtales.ke
nslookup hansardtales.ke
```

**Verify DNS records:**
1. Go to **DNS** in Cloudflare Dashboard
2. Ensure CNAME record exists and is proxied (orange cloud)

**Wait for propagation:**
- Can take up to 48 hours
- Usually completes in 1-2 hours

### Site Not Updating

**Check deployment status:**
1. Go to Deployments tab
2. Verify latest deployment succeeded
3. Check deployment timestamp

**Clear cache:**
1. Go to **Caching** → **Configuration**
2. Click **Purge Everything**
3. Wait 30 seconds and refresh site

## Cost Breakdown

**Selected Configuration: .co.ke with Safaricom**

| Item | Cost (USD) | Cost (KES) | Frequency |
|------|-----------|------------|-----------|
| .co.ke Domain (Safaricom) | ~$9.25 | 1,200 | Annual |
| Cloudflare Pages | $0 | 0 | Free tier |
| **Total Annual Cost** | **~$9.25/year** | **~1,200 KES/year** | **~£0.77/month** |

**Budget Status**: Well within the £30/month budget - using less than 3% of available budget for infrastructure.

**Cost Comparison** (for reference):
- Truehost Kenya: KES 850/year (~$6.55 / ~£0.55/month) - saves KES 350/year
- Kenya Web Experts: KES 999/year (~$7.70 / ~£0.64/month) - saves KES 201/year
- **Safaricom (selected)**: KES 1,200/year - premium for trusted brand and support

## Security Best Practices

1. **Enable HTTPS only** - Already configured
2. **Enable DNSSEC** - Go to DNS → DNSSEC → Enable
3. **Enable Bot Fight Mode** - Go to Security → Bots → Enable
4. **Review Security Level** - Go to Security → Settings → Medium

## Next Steps

1. ✅ Domain registered and DNS configured
2. ✅ Cloudflare Pages project created
3. ✅ Custom domain connected
4. ✅ SSL/TLS enabled
5. ✅ Analytics enabled
6. 🎯 Launch and share your site!

## Support Resources

- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)
- [Cloudflare Community](https://community.cloudflare.com/)
- [Cloudflare Status](https://www.cloudflarestatus.com/)

### Kenyan Domain Registrar Links

**Selected Registrar:**
- [Safaricom Digital](https://www.safaricom.co.ke/) - Domain registration services

**Alternative Registrars** (if needed):
- [Truehost Kenya](https://truehost.co.ke/) - Cheapest option
- [Kenya Web Experts](https://www.kenyawebexperts.com/) - Established provider

### Domain Registration Tips

1. **Check renewal prices**: Some registrars offer low first-year prices but higher renewals
2. **Enable auto-renewal**: Prevents accidental domain expiration
3. **Set up email reminders**: Get notified 30 days before expiration
4. **Add WHOIS privacy**: Protects your personal contact information
5. **Keep registrar credentials safe**: Store in password manager
6. **Verify DNS propagation**: Use tools like [WhatsMyDNS](https://www.whatsmydns.net/)
7. **Test before launch**: Verify domain works before announcing publicly

## Comparison: GitHub Pages vs Cloudflare Pages

| Feature | GitHub Pages | Cloudflare Pages |
|---------|-------------|------------------|
| **URL** | `username.github.io/repo` | Custom domain |
| **Cost** | Free | Free + domain (~$15/year) |
| **Performance** | Good (Fastly CDN) | Excellent (Cloudflare CDN) |
| **Analytics** | None (need Google Analytics) | Built-in Web Analytics |
| **Caching** | Basic | Advanced control |
| **Preview Deployments** | No | Yes (automatic) |
| **Custom Domain** | Yes (but complex) | Yes (simple) |
| **Build Minutes** | Unlimited | 500/month (sufficient) |
| **Bandwidth** | 100GB soft limit | Unlimited |

---

**Ready to launch?** Follow this guide step-by-step and your site will be live at `hansardtales.ke` in under an hour!
