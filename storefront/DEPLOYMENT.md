# Multi-Tenant Storefront Deployment Guide

## Table of Contents

1. [Vercel Free Tier Deployment](#vercel-free-tier-deployment)
2. [Multi-Tenancy Approaches](#multi-tenancy-approaches)
3. [Custom Domain Strategy](#custom-domain-strategy)
4. [Monetization Models](#monetization-models)
5. [Scaling Path](#scaling-path)

---

## Vercel Free Tier Deployment

### Prerequisites

- GitHub repository with your code
- Vercel account (free)
- Railway backend running

### Step 1: Prepare Your Project

1. **Ensure `vercel.json` is configured** (already done)
2. **Update environment variables in `.env.local`**:

```bash
NEXT_PUBLIC_API_URL=https://printer-automation-backend-production.up.railway.app
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=your_stripe_public_key
```

### Step 2: Deploy to Vercel

**Option A: Via Vercel Dashboard (Recommended)**

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Select the `storefront` directory as root
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_STRIPE_PUBLIC_KEY`
5. Click "Deploy"

**Option B: Via Vercel CLI**

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to storefront
cd storefront

# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Step 3: Configure Domain

1. In Vercel dashboard, go to your project settings
2. Add your custom domain (e.g., `craftflow.com`)
3. Follow DNS instructions to point your domain to Vercel

---

## Multi-Tenancy Approaches

### Current Setup: Path-Based Multi-Tenancy (FREE)

**How it works:**

- Each store gets a unique URL path
- Example: `yourdomain.com/store/customer1`

**Pros:**
✅ Works on Vercel free tier
✅ No per-customer configuration
✅ Unlimited stores
✅ Simple to manage
✅ Great for MVP

**Cons:**
❌ Not as branded (customers see `/store/` in URL)
❌ Can't use customer's own domain

**Perfect for:**

- Getting started
- Testing your platform
- Customers who don't need custom branding

---

### Future: Subdomain Multi-Tenancy (PRO - $20/month)

**How it works:**

- Each store gets a subdomain
- Example: `customer1.craftflow.com`

**Requirements:**

- Vercel Pro plan ($20/month)
- Wildcard DNS (\*.craftflow.com)
- Middleware is ready (already created)

**Setup:**

1. Upgrade to Vercel Pro
2. Add wildcard domain: `*.craftflow.com`
3. Point DNS: `*.craftflow.com` CNAME to `cname.vercel-dns.com`
4. Middleware automatically routes subdomains

---

### Advanced: Custom Domains (PRO + Additional Features)

**How it works:**

- Each customer uses their own domain
- Example: `customershop.com` → your store

**Requirements:**

- Vercel Pro plan ($20/month)
- Custom domain setup per customer
- Domain verification system

**Cost:**

- Vercel Pro: $20/month (100 domains included)
- Each additional 100 domains: +$20/month

---

## Custom Domain Strategy

### Hybrid Approach (Best for Growth)

Offer **tiered plans** to customers:

#### **Free/Basic Plan**

- Path-based URL: `yourplatform.com/store/customername`
- Vercel Free tier: $0/month
- Unlimited stores

#### **Pro Plan**

- Subdomain URL: `customername.yourplatform.com`
- Vercel Pro: $20/month (covers up to 100 stores)
- Charge customers: $10-15/month

#### **Enterprise Plan**

- Custom domain: `customershop.com`
- Per-domain setup on Vercel
- Charge customers: $30-50/month

### Revenue Math Example:

**Free Tier (0-50 stores):**

- Cost: $0/month
- Revenue: $0/month
- Use path-based routing

**10 Pro Plan Customers:**

- Cost: $20/month (Vercel Pro)
- Revenue: $100/month ($10/customer × 10)
- Profit: $80/month
- Use subdomain routing

**5 Enterprise Customers:**

- Cost: $20/month (included in Pro)
- Revenue: $150/month ($30/customer × 5)
- Additional profit: $150/month

**Total with 15 customers:**

- Cost: $20/month
- Revenue: $250/month
- Profit: $230/month

---

## Monetization Models

### Model 1: Usage-Based (Recommended)

**Tier 1: Free**

- Path-based URL
- Up to 100 products
- Basic themes
- Perfect for: Testing, small shops

**Tier 2: Professional - $15/month**

- Subdomain URL
- Unlimited products
- Custom branding
- Priority support
- Perfect for: Growing businesses

**Tier 3: Enterprise - $49/month**

- Custom domain
- Advanced analytics
- API access
- White-label options
- Perfect for: Established brands

### Model 2: Transaction Fee

Instead of monthly fees:

- Free path-based URL
- Take 1-2% transaction fee
- Upgrade to subdomain: 0.5% fee
- Custom domain: 0% fee (flat $29/month)

---

## Scaling Path

### Phase 1: MVP (Current - FREE)

**Setup:**

- Vercel Free tier
- Path-based routing
- Your domain: `craftflow.com`

**Capacity:**

- Unlimited stores
- All on `/store/[slug]`

**Cost:** $0/month

---

### Phase 2: Growth (PRO - $20/month)

**When:** You get 3+ paying customers

**Setup:**

- Upgrade to Vercel Pro
- Enable subdomain routing
- Add wildcard DNS

**Capacity:**

- 100 custom domains
- Unlimited subdomains
- Unlimited path-based

**Cost:** $20/month (break even at 2 customers × $10/month)

---

### Phase 3: Scale (PRO + Add-ons)

**When:** You have 100+ domains or need more features

**Setup:**

- Vercel Pro + additional domain packs
- Consider enterprise features
- May need custom infrastructure

**Capacity:**

- 100 domains per $20/month
- Or move to custom solution

---

## Quick Start Checklist

For launching on **Vercel Free tier TODAY**:

- [x] `vercel.json` configured
- [x] Middleware created (ready for future)
- [x] Environment variables set
- [ ] Push code to GitHub
- [ ] Connect GitHub to Vercel
- [ ] Deploy
- [ ] Test `/store/[slug]` routes
- [ ] Add your custom domain
- [ ] Update DNS records
- [ ] Launch! 🚀

---

## Next Steps

1. **Deploy to Vercel Free** (today)

   ```bash
   cd storefront
   vercel --prod
   ```

2. **Test with sample stores**
   - Create test stores in admin panel
   - Visit: `yourdomain.com/store/test-shop`

3. **Onboard first customers**
   - They get: `yourdomain.com/store/their-name`
   - Free for you until you need Pro

4. **Upgrade to Pro when:**
   - You have 3+ paying customers ($10/mo each = $30 revenue > $20 cost)
   - Customers want branded subdomains
   - You're ready to scale

---

## Support Resources

- **Vercel Docs**: https://vercel.com/docs
- **Next.js Multi-Tenancy**: https://nextjs.org/docs/app/building-your-application/routing/middleware
- **Vercel Pricing**: https://vercel.com/pricing

---

## Frequently Asked Questions

**Q: Can I use Vercel free tier forever?**
A: Yes! Path-based routing works perfectly on the free tier with unlimited stores.

**Q: When should I upgrade to Pro?**
A: When you want subdomains or custom domains, OR when you have enough paying customers to cover the $20/month cost.

**Q: Can I mix path-based and subdomain routing?**
A: Yes! You can offer both. Free customers get path-based, paying customers get subdomains.

**Q: What about my own domain on free tier?**
A: You can use ONE custom domain (e.g., craftflow.com) on the free tier. All stores will be under that domain as paths.

**Q: How many stores can I host on free tier?**
A: Unlimited! Vercel free tier has no limit on the number of `/store/[slug]` routes you can have.
