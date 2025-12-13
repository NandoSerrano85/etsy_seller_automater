# Railway Deployment Guide - Ecommerce Platform

**Complete guide for deploying both backend and storefront as separate Railway services**

---

## 🎯 Overview

Your ecommerce platform consists of **two separate services**:

1. **Backend API** (FastAPI + Python) - Port 8080
2. **Storefront** (Next.js + Node) - Port 3001

Both will be deployed as separate services in Railway.

---

## 📋 Prerequisites

- GitHub repository with your code
- Railway account (free tier works)
- Stripe account (test mode is fine)
- PostgreSQL database (Railway provides this)

---

## 🚀 Deployment Steps

### Step 1: Deploy Backend API (if not already deployed)

1. **Login to Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add PostgreSQL Database:**
   - Click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will provision and connect it automatically

4. **Configure Backend Service:**
   - Click on the service
   - Go to "Settings" → Set root directory: `.` (or leave empty)
   - Go to "Variables"

5. **Add Environment Variables:**

   ```bash
   # Database (auto-filled by Railway)
   DATABASE_URL=postgresql://...

   # JWT
   JWT_SECRET_KEY=your_secure_random_string_min_64_chars

   # Stripe
   STRIPE_API_KEY=sk_test_your_stripe_secret_key
   STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

   # Optional: Existing Etsy/Shopify keys
   ETSY_CLIENT_ID=...
   SHOPIFY_API_KEY=...
   ```

6. **Deploy:**
   - Backend will auto-deploy
   - Note the URL: `https://your-project.up.railway.app`

7. **Run Migration (One-time):**
   - After first deployment
   - SSH into service or use Railway CLI
   - Run: `python migration-service/run_migration.py create_ecommerce_tables`

---

### Step 2: Deploy Storefront (NEW SERVICE)

1. **Add New Service to Same Project:**
   - In your Railway project dashboard
   - Click "+ New" → "GitHub Repo"
   - Select the **same repository**
   - Railway will create a new service

2. **Configure Storefront Service:**
   - Click on the new service
   - Go to "Settings"
   - **IMPORTANT:** Set **Root Directory** to `storefront`
   - Railway will detect the Dockerfile

3. **Add Environment Variables:**

   ```bash
   # Backend API URL (from Step 1)
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app

   # Stripe Public Key (client-side, safe to expose)
   NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key

   # Site Info
   NEXT_PUBLIC_SITE_NAME=Your Store Name
   NEXT_PUBLIC_SITE_URL=https://your-storefront.up.railway.app
   ```

   **Note:** Railway auto-generates a URL. Copy it and paste into `NEXT_PUBLIC_SITE_URL`

4. **Deploy:**
   - Click "Deploy"
   - Build takes ~3-5 minutes
   - Storefront will be available at generated URL

---

### Step 3: Configure Stripe Webhooks

1. **Go to Stripe Dashboard:**
   - [https://dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks)

2. **Add Endpoint:**
   - Click "Add endpoint"
   - URL: `https://your-backend.up.railway.app/api/storefront/checkout/webhook`

3. **Select Events:**
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`

4. **Copy Webhook Secret:**
   - After creating, click "Reveal signing secret"
   - Copy the `whsec_...` value
   - Add to backend environment variables as `STRIPE_WEBHOOK_SECRET`
   - Redeploy backend

---

### Step 4: Test Deployment

1. **Test Backend API:**

   ```bash
   curl https://your-backend.up.railway.app/api/storefront/products
   ```

2. **Test Storefront:**
   - Open `https://your-storefront.up.railway.app`
   - Should see homepage
   - Try adding featured product to cart

3. **Test Stripe:**
   - Get Stripe config:
   ```bash
   curl https://your-backend.up.railway.app/api/storefront/checkout/config
   ```

   - Should return your public key

---

## 🔧 Custom Domains (Optional)

### Backend Custom Domain

1. **In Railway (Backend Service):**
   - Settings → Domains
   - Click "Custom Domain"
   - Enter: `api.yourstore.com`

2. **Update DNS:**
   - Add CNAME record:
     - Name: `api`
     - Value: (Railway provides this)

3. **Update Storefront:**
   - Update `NEXT_PUBLIC_API_URL` to `https://api.yourstore.com`
   - Redeploy storefront

### Storefront Custom Domain

1. **In Railway (Storefront Service):**
   - Settings → Domains
   - Click "Custom Domain"
   - Enter: `shop.yourstore.com` or `yourstore.com`

2. **Update DNS:**
   - Add CNAME (subdomain) or A record (apex domain)
   - Follow Railway's instructions

3. **Update Environment:**
   - Update `NEXT_PUBLIC_SITE_URL` to your domain
   - Update Stripe webhook URL if needed

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────┐
│           Railway Project                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Backend API    │  │  PostgreSQL     │ │
│  │  (FastAPI)      │◄─┤  Database       │ │
│  │  Port: 8080     │  │                 │ │
│  └────────┬────────┘  └─────────────────┘ │
│           │                                 │
│           │ HTTP/JSON                       │
│           │                                 │
│  ┌────────▼────────┐                       │
│  │  Storefront     │                       │
│  │  (Next.js)      │                       │
│  │  Port: 3001     │                       │
│  └─────────────────┘                       │
│                                             │
└─────────────────────────────────────────────┘
           ▲
           │
       Customer
```

---

## 🔒 Security Checklist

Before going live:

- [ ] Change JWT_SECRET_KEY to strong random value
- [ ] Switch Stripe keys from test to live mode
- [ ] Enable HTTPS (Railway does this automatically)
- [ ] Set DISABLE_REGISTRATION=true (if needed)
- [ ] Review CORS settings
- [ ] Secure webhook endpoints
- [ ] Set up database backups
- [ ] Enable Railway project protection
- [ ] Review environment variables (no secrets exposed)

---

## 💰 Railway Pricing

**Free Tier:**

- $5 free credit per month
- Suitable for development/testing
- May need to upgrade for production

**Starter Plan ($5/month):**

- $5 credit included
- Pay only for usage beyond credit
- Recommended for small stores

**Estimate:**

- Backend: ~$3-5/month
- Storefront: ~$3-5/month
- Database: ~$2-3/month
- **Total: ~$8-13/month** for both services

---

## 🔄 CI/CD (Auto-Deployment)

Railway automatically deploys when you push to GitHub:

1. **Make changes** locally
2. **Commit** to git
3. **Push** to GitHub main branch
4. **Railway auto-detects** changes
5. **Builds & deploys** automatically

**To disable auto-deploy:**

- Service Settings → Deployments → Turn off "Auto-deploy"

---

## 📝 Environment Variables Reference

### Backend (FastAPI Service)

| Variable                | Required | Example                        |
| ----------------------- | -------- | ------------------------------ |
| `DATABASE_URL`          | ✅       | Auto-provided by Railway       |
| `JWT_SECRET_KEY`        | ✅       | `64_char_random_string`        |
| `STRIPE_API_KEY`        | ✅       | `sk_test_...` or `sk_live_...` |
| `STRIPE_PUBLIC_KEY`     | ✅       | `pk_test_...` or `pk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | ✅       | `whsec_...`                    |

### Storefront (Next.js Service)

| Variable                        | Required | Example                      |
| ------------------------------- | -------- | ---------------------------- |
| `NEXT_PUBLIC_API_URL`           | ✅       | `https://api.yourstore.com`  |
| `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` | ✅       | `pk_test_...`                |
| `NEXT_PUBLIC_SITE_NAME`         | Optional | `Your Store Name`            |
| `NEXT_PUBLIC_SITE_URL`          | Optional | `https://shop.yourstore.com` |

---

## 🐛 Troubleshooting

### Issue: Storefront can't connect to backend

**Solution:**

- Verify `NEXT_PUBLIC_API_URL` matches backend URL exactly
- Check backend is deployed and running
- Test backend API directly with curl
- Check Railway logs for errors

### Issue: Database migration fails

**Solution:**

- Ensure `DATABASE_URL` is set
- Check PostgreSQL service is running
- Try running migration manually via Railway CLI

### Issue: Stripe webhook not working

**Solution:**

- Verify webhook URL is correct
- Check `STRIPE_WEBHOOK_SECRET` matches Stripe dashboard
- Test webhook with Stripe CLI: `stripe listen`

### Issue: Build fails for storefront

**Solution:**

- Check Dockerfile syntax
- Verify root directory is set to `storefront`
- Check Railway build logs
- Ensure all dependencies in package.json

### Issue: Environment variables not updating

**Solution:**

- After changing variables, redeploy service
- Click "Deploy" → "Redeploy"
- Or push a commit to trigger redeploy

---

## 📚 Useful Railway Commands

### Railway CLI (optional but helpful)

**Install:**

```bash
npm install -g @railway/cli
```

**Login:**

```bash
railway login
```

**Link to project:**

```bash
railway link
```

**View logs:**

```bash
railway logs
```

**Run migration:**

```bash
railway run python migration-service/run_migration.py create_ecommerce_tables
```

**Open service:**

```bash
railway open
```

---

## ✨ Post-Deployment Checklist

After both services are deployed:

- [ ] Test homepage loads
- [ ] Test product API endpoint
- [ ] Test cart functionality
- [ ] Test Stripe config endpoint
- [ ] Create test order with Stripe test card
- [ ] Verify order appears in database
- [ ] Test customer registration
- [ ] Test customer login
- [ ] Set up monitoring/alerts
- [ ] Configure custom domains (optional)
- [ ] Set up backup strategy
- [ ] Document your deployment

---

## 🎉 Success!

Your ecommerce platform is now live with:

- ✅ Customer-facing storefront
- ✅ Backend API with database
- ✅ Stripe payment processing
- ✅ Secure authentication
- ✅ Separate services for scalability
- ✅ Auto-deployment from GitHub

**Next Steps:**

- Complete remaining frontend pages (catalog, checkout, account)
- Add products to your store
- Test with real customers
- Monitor performance and errors
- Scale as needed

---

**Questions?** Check the detailed guides:

- `ECOMMERCE_STOREFRONT_GUIDE.md`
- `ECOMMERCE_STRIPE_INTEGRATION.md`
- `ECOMMERCE_IMPLEMENTATION_STATUS.md`
