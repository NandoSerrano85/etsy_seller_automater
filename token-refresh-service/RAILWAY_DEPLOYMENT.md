# Railway Deployment Guide - Token Refresh Service

Complete guide to deploy the Token Refresh Service on Railway.

## Prerequisites

- Railway account (free tier works fine)
- Railway CLI installed (optional but recommended)
- Access to your main database connection string

## Deployment Steps

### Option 1: Deploy via Railway Dashboard (Easiest)

#### Step 1: Create New Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"** (if you've pushed to GitHub)
   - OR select **"Empty Project"** to deploy manually

#### Step 2: Add Service from GitHub (If using GitHub)

1. Click **"New"** → **"GitHub Repo"**
2. Select your repository: `etsy_seller_automater`
3. Set **Root Directory**: `token-refresh-service`
4. Railway will auto-detect the Dockerfile

#### Step 3: Configure Environment Variables

Click on your service → **"Variables"** tab → Add the following:

```
DATABASE_URL=postgresql://user:password@host:port/database
ETSY_CLIENT_ID=your_etsy_client_id
ETSY_CLIENT_SECRET=your_etsy_client_secret
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
REFRESH_INTERVAL_MINUTES=3
LOG_LEVEL=INFO
```

**Important:**

- Use the **same DATABASE_URL** as your main backend service
- Get the DATABASE_URL from your existing Railway database service
- To reference existing database: Click your Postgres service → "Connect" → Copy the connection string

#### Step 4: Deploy

1. Railway will automatically build and deploy
2. Check the **"Deployments"** tab for build progress
3. View logs in the **"Logs"** tab

### Option 2: Deploy via Railway CLI

#### Step 1: Install Railway CLI

```bash
# macOS/Linux
brew install railway

# Windows
scoop install railway

# Or use npm
npm i -g @railway/cli
```

#### Step 2: Login to Railway

```bash
railway login
```

#### Step 3: Initialize Project

```bash
# Navigate to the token-refresh-service directory
cd /Users/fserrano/Documents/Projects/etsy_seller_automater/token-refresh-service

# Link to Railway (creates new project or links to existing)
railway link

# OR create a new project
railway init
```

#### Step 4: Set Environment Variables

```bash
# Set each variable
railway variables set DATABASE_URL="postgresql://user:password@host:port/database"
railway variables set ETSY_CLIENT_ID="your_etsy_client_id"
railway variables set ETSY_CLIENT_SECRET="your_etsy_client_secret"
railway variables set SHOPIFY_API_KEY="your_shopify_api_key"
railway variables set SHOPIFY_API_SECRET="your_shopify_api_secret"
railway variables set REFRESH_INTERVAL_MINUTES="3"
railway variables set LOG_LEVEL="INFO"
```

**Or set them all at once using a .env file:**

```bash
# Create .env file with your variables
cat > .env.railway << EOF
DATABASE_URL=postgresql://user:password@host:port/database
ETSY_CLIENT_ID=your_etsy_client_id
ETSY_CLIENT_SECRET=your_etsy_client_secret
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
REFRESH_INTERVAL_MINUTES=3
LOG_LEVEL=INFO
EOF

# Upload variables to Railway
railway variables set --file .env.railway
```

#### Step 5: Deploy

```bash
# Deploy to Railway
railway up

# Watch logs
railway logs
```

## Connecting to Existing Database

### Method 1: Use Existing Railway Postgres

If your main backend already uses a Railway Postgres database:

1. Go to your Railway dashboard
2. Click on your **Postgres service**
3. Go to **"Connect"** tab
4. Copy the **"Postgres Connection URL"**
5. Use this as your `DATABASE_URL` in the token-refresh-service

### Method 2: Reference Database Service Variable

In Railway, you can reference another service's variables:

1. In the token-refresh-service, go to **Variables**
2. Click **"Add Reference"**
3. Select your Postgres service
4. Choose `DATABASE_URL` variable
5. This automatically uses the same database connection

## Verifying Deployment

### Check Service is Running

```bash
# Via CLI
railway logs

# Via Dashboard
# Go to service → "Logs" tab
```

You should see:

```
🚀 Token Refresh Service starting...
⏱️  Refresh interval: 3 minutes
✅ Etsy refresher initialized
✅ Shopify refresher initialized
🎯 Token Refresh Service is running...
```

### Monitor Token Refreshes

Look for log entries every 3 minutes:

```
================================================================================
🔄 Starting refresh cycle at 2025-10-08T10:00:00
================================================================================
🔵 Processing Etsy tokens...
🟢 Processing Shopify tokens...
================================================================================
📊 REFRESH CYCLE SUMMARY
================================================================================
```

## Troubleshooting

### Service Crashes on Startup

**Error: `DATABASE_URL environment variable is required`**

- Make sure all environment variables are set
- Check spelling and formatting

**Error: `Failed to connect to database`**

- Verify DATABASE_URL is correct
- Ensure the database allows connections from Railway IPs
- Check database service is running

### No Tokens Being Refreshed

**If you see: `No Etsy tokens need refreshing`**

- This is normal if tokens aren't expiring soon
- Etsy tokens are only refreshed within 10 minutes of expiry
- Check `platform_connections` table for expiration times

**If you see: `No active Shopify connections found`**

- Check `platform_connections` table has Shopify entries
- Verify `is_active = true` in the database
- Check legacy `shopify_stores` table if using old schema

### High Memory Usage

Railway free tier has memory limits:

- Service uses ~50-100MB normally
- Increase `pool_size` in `database.py` if needed (currently 5)
- Monitor memory in Railway dashboard

### Timezone Issues

All timestamps use UTC. If you need different timezone:

- Update logs to show local time
- Keep database timestamps in UTC

## Updating the Service

### Via GitHub (Automatic)

If connected to GitHub:

1. Push changes to your repository
2. Railway auto-deploys on push to main branch
3. Monitor deployment in Railway dashboard

### Via CLI

```bash
cd token-refresh-service
railway up
```

### Restart Service

```bash
# Via CLI
railway restart

# Via Dashboard
# Click service → "Settings" → "Restart"
```

## Configuration Options

### Adjust Refresh Interval

Change how often tokens are refreshed:

```bash
# Every 5 minutes
railway variables set REFRESH_INTERVAL_MINUTES="5"

# Every 1 minute (not recommended - rate limits)
railway variables set REFRESH_INTERVAL_MINUTES="1"

# Every 10 minutes
railway variables set REFRESH_INTERVAL_MINUTES="10"
```

After changing, restart the service.

### Adjust Log Level

```bash
# More verbose
railway variables set LOG_LEVEL="DEBUG"

# Less verbose
railway variables set LOG_LEVEL="WARNING"

# Production (recommended)
railway variables set LOG_LEVEL="INFO"
```

## Cost Considerations

### Railway Free Tier

- $5 free credit per month
- Service uses minimal resources
- Should run entirely on free tier
- No external ports needed (service only connects to database)

### Estimated Usage

- CPU: Very low (runs every 3 minutes)
- Memory: ~50-100MB
- Network: Minimal (only API calls for token refresh)

## Monitoring & Alerts

### View Logs

```bash
# Real-time logs via CLI
railway logs --tail

# Filter logs
railway logs | grep "ERROR"
railway logs | grep "Etsy"
```

### Set Up Alerts (Optional)

Railway doesn't have built-in alerting, but you can:

1. Use an external monitoring service
2. Add webhook notifications to the service
3. Check logs periodically

## Advanced Configuration

### Connect to Private Database

If your database is in a private network:

1. Use Railway Private Networking
2. Or use database proxy/tunnel
3. Update DATABASE_URL accordingly

### Multiple Environments

Deploy separate services for dev/staging/production:

```bash
# Create production service
railway up --service token-refresh-prod

# Create staging service
railway up --service token-refresh-staging
```

Set different environment variables for each.

## Maintenance

### Check Service Health

```bash
# View recent logs
railway logs --tail 100

# Check if service is running
railway status
```

### Manual Token Refresh

The service runs automatically, but you can trigger manually:

```bash
# Restart triggers immediate refresh
railway restart
```

### Database Maintenance

- Service doesn't create tables
- No migrations needed
- Only reads/writes to existing tables

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use Railway's secret variables** for sensitive data
3. **Rotate OAuth secrets** periodically
4. **Monitor failed authentication** attempts in logs
5. **Keep service updated** with latest code

## Getting Help

- **Railway Docs**: https://docs.railway.app
- **Service Logs**: Railway Dashboard → Your Service → Logs
- **Database Access**: Railway Dashboard → Postgres → Data

## Quick Reference

### Essential Commands

```bash
# Deploy
railway up

# View logs
railway logs

# Restart
railway restart

# Set variable
railway variables set KEY="value"

# Shell access (debugging)
railway shell

# Open in browser
railway open
```

### Service URLs

- No public URL needed (background service)
- Connects to database internally
- Check Railway dashboard for service status

---

## Complete Setup Example

Here's a complete end-to-end setup:

```bash
# 1. Navigate to service directory
cd /Users/fserrano/Documents/Projects/etsy_seller_automater/token-refresh-service

# 2. Login to Railway
railway login

# 3. Create new project
railway init

# 4. Get your database URL from main backend service
# Go to Railway Dashboard → Your Postgres → Connect → Copy URL

# 5. Set all environment variables
railway variables set DATABASE_URL="postgresql://postgres:password@containers-us-west-123.railway.app:1234/railway"
railway variables set ETSY_CLIENT_ID="abc123xyz"
railway variables set ETSY_CLIENT_SECRET="secret123"
railway variables set SHOPIFY_API_KEY="shopify_key"
railway variables set SHOPIFY_API_SECRET="shopify_secret"
railway variables set REFRESH_INTERVAL_MINUTES="3"
railway variables set LOG_LEVEL="INFO"

# 6. Deploy
railway up

# 7. Watch logs to verify it's working
railway logs --tail

# Done! Service is now running and will refresh tokens every 3 minutes
```

You should see output like:

```
🚀 Token Refresh Service starting...
⏱️  Refresh interval: 3 minutes
✅ Etsy refresher initialized
✅ Shopify refresher initialized
🎯 Token Refresh Service is running...
⏰ Next refresh at: 2025-10-08T10:03:00

🔄 Starting refresh cycle at 2025-10-08T10:00:00
🔵 Processing Etsy tokens...
Found 2 Etsy connections with expiring/expired tokens
✅ Refreshed token for Etsy connection: uuid-here
📊 REFRESH CYCLE SUMMARY
Etsy:    2/2 refreshed, 0 failed
Shopify: 3/3 validated, 0 failed
✅ Refresh cycle completed
💤 Sleeping for 3 minutes...
```

Your tokens are now being automatically refreshed! 🎉
