# CORS & 502 Error Troubleshooting Guide

## Current Error

```
Access to fetch at 'https://printer-automation-backend-production.up.railway.app/api/orders/create-print-files?format=PNG'
from origin 'https://printer-automation-frontend-production.up.railway.app'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present

502 (Bad Gateway)
```

## Root Cause

The **502 Bad Gateway** error means your backend is crashing or not responding properly. When this happens, **NO CORS headers are sent**, which triggers the CORS error as a side effect.

## Fixes Applied

### 1. Enhanced CORS Configuration

✅ Updated `server/main.py` to:

- Allow all Railway, Vercel, and Netlify apps
- Add `PATCH` method support
- Add preflight cache (1 hour)
- Support regex patterns for all deployment platforms

### 2. Better Error Handling

✅ Added try-catch to `/api/orders/create-print-files` endpoint

- Now returns proper 500 errors instead of crashing
- Logs full traceback for debugging

### 3. Debug Endpoints

✅ Added health check endpoints:

- `GET /health` - Check if backend is running
- `GET /api/cors-test` - Verify CORS is configured

---

## How to Debug

### Step 1: Check Backend Health

Open in your browser:

```
https://printer-automation-backend-production.up.railway.app/health
```

**Expected response:**

```json
{
  "status": "healthy",
  "environment": "production",
  "cors_enabled": true,
  "multi_tenant": "true"
}
```

If this doesn't work, your backend is **not running** on Railway.

---

### Step 2: Test CORS Configuration

Open in your browser:

```
https://printer-automation-backend-production.up.railway.app/api/cors-test
```

**Expected response:**

```json
{
  "message": "CORS is working correctly",
  "frontend_url": "...",
  "timestamp": "..."
}
```

---

### Step 3: Check Railway Logs

1. Go to Railway dashboard
2. Open your backend service
3. Click "Deployments" → Latest deployment
4. Click "View Logs"

**Look for:**

- ❌ `Error in create_print_files:` (shows the actual error)
- ❌ `502 Bad Gateway` (backend crashed)
- ❌ `Out of memory` (Railway needs more RAM)
- ❌ `Timeout` (process taking too long)

---

### Step 4: Common Fixes

#### If backend is not running:

```bash
# Redeploy to Railway
git add .
git commit -m "Fix CORS and error handling"
git push origin main
```

Railway should auto-deploy.

#### If backend is running but endpoint fails:

The `/api/orders/create-print-files` endpoint might be:

- Trying to access files that don't exist
- Running out of memory
- Taking too long (Railway timeout: 300 seconds)

**Check the logs for specific errors.**

---

## Railway Configuration Checklist

### Environment Variables (Set in Railway)

Make sure these are set:

```bash
# Required
DATABASE_URL=postgresql://...
FRONTEND_URL=https://printer-automation-frontend-production.up.railway.app

# Optional but recommended
DEBUG_LOGGING=true  # Enable for troubleshooting
RAILWAY_ENVIRONMENT=production
ENABLE_MULTI_TENANT=true

# API Keys
ETSY_API_KEY=...
STRIPE_SECRET_KEY=...
```

### Railway Service Settings

1. **Memory**: Increase if getting OOM errors
   - Settings → Resources → Memory: 512MB or 1GB

2. **Timeout**: Increase for long-running requests
   - Settings → Deploy → Build timeout: 10 minutes

3. **Auto-deploy**: Enable for automatic deployments
   - Settings → Source → Auto-deploy: ON

---

## Testing CORS Locally

### Test from browser console

Open your frontend in browser, then in console:

```javascript
// Test CORS
fetch(
  "https://printer-automation-backend-production.up.railway.app/api/cors-test",
)
  .then((r) => r.json())
  .then(console.log)
  .catch(console.error);

// Test the actual endpoint
fetch("https://printer-automation-backend-production.up.railway.app/health")
  .then((r) => r.json())
  .then(console.log)
  .catch(console.error);
```

**Expected:** Both should return JSON without CORS errors.

---

## If Still Getting CORS Errors

### Quick Fix: Add Specific Origin

If the regex isn't working, add your frontend URL explicitly:

**In `server/main.py`, line 204-213:**

```python
allow_origins=[
    "https://printer-automation-frontend-production.up.railway.app",  # <-- Make sure this exact URL is here
    "https://comforting-cocada-88dd8c.netlify.app",
    "https://printer-automater.netlify.app",
    "https://store-front-production-bddf.up.railway.app",
    frontend_url,
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001"
],
```

---

## Alternative: Use Railway Internal URLs

Instead of public URLs, use Railway's internal networking:

1. Go to Railway dashboard
2. Click on frontend service
3. Under "Settings" → "Networking" → Enable "Private Networking"
4. Use internal URL: `backend.railway.internal`

**Update frontend .env:**

```bash
NEXT_PUBLIC_API_URL=https://backend.railway.internal
```

---

## Emergency Bypass (Development Only)

**⚠️ NOT for production:**

Temporarily allow all origins for testing:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DANGER: Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If this works, the issue is your origin list. Revert and add the correct origins.

---

## Next Steps

1. ✅ **Deploy the updated code** to Railway
2. ✅ **Test `/health` endpoint** in browser
3. ✅ **Test `/api/cors-test` endpoint** in browser
4. ✅ **Check Railway logs** for any errors
5. ✅ **Test from frontend**

If still failing, share:

- Railway logs
- Browser console output
- Response from `/health` endpoint

---

## Quick Commands

### Deploy to Railway

```bash
cd server
git add .
git commit -m "Fix CORS and add error handling"
git push origin main
```

### View logs

```bash
# If Railway CLI installed
railway logs --service backend
```

### Test endpoints

```bash
# Health check
curl https://printer-automation-backend-production.up.railway.app/health

# CORS test
curl https://printer-automation-backend-production.up.railway.app/api/cors-test

# With credentials (like browser)
curl -H "Origin: https://printer-automation-frontend-production.up.railway.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     --verbose \
     https://printer-automation-backend-production.up.railway.app/api/orders/create-print-files?format=PNG
```

---

## Still Having Issues?

If you're still seeing 502 errors, the endpoint itself might be broken. Check:

1. **Do you have active orders?** The endpoint needs orders to process
2. **Are your NAS/file paths configured?** The endpoint accesses files
3. **Is the database connection working?** Check Railway DB status

Most likely, the endpoint is trying to access resources that don't exist or are misconfigured on Railway.
