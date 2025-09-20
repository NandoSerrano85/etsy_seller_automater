# Railway Redis Setup Guide

Complete step-by-step guide to set up Redis caching on Railway for dramatic performance improvements.

## 🚀 Expected Performance Improvements

After setup, you should see:

- **`verify-connection`**: 1.5 min → 100ms (99.9% faster)
- **`analytics`**: 1 min → 200ms (99.7% faster)
- **`gallery`**: 1.5 min → 300ms (99.7% faster)
- **Overall load time**: 30+ seconds → 2-5 seconds

## 📋 Step-by-Step Setup

### **Step 1: Add Redis Service in Railway**

1. **Open your Railway dashboard**
   - Go to [railway.app](https://railway.app)
   - Navigate to your project

2. **Add Redis service**
   - Click **"+ New Service"**
   - Select **"Database"**
   - Choose **"Redis"**
   - Click **"Add Redis"**

3. **Wait for deployment**
   - Redis service will deploy automatically
   - Should take 1-2 minutes

### **Step 2: Configure Environment Variables**

1. **Go to your main API service**
   - Click on your main API service (not Redis)
   - Go to **"Variables"** tab

2. **Add Redis URL variable**
   - Click **"+ New Variable"**
   - **Name**: `REDIS_URL`
   - **Value**: Get from Redis service (see Step 3)

### **Step 3: Get Redis Connection URL**

1. **Click on your Redis service**
2. **Go to "Connect" tab**
3. **Copy the "Private URL"** (should look like):
   ```
   redis://default:password@redis-service.railway.internal:6379
   ```
4. **Paste this URL as the `REDIS_URL` variable** in your API service

### **Step 4: Deploy Updated Code**

1. **Make sure your code is up to date**
   - The Redis caching code is already implemented
   - Push any remaining changes to your git repository

2. **Trigger deployment**
   - Railway will automatically redeploy when you push changes
   - Or manually redeploy via Railway dashboard

### **Step 5: Verify Setup**

1. **Check service logs**
   - Go to your main API service
   - Click on **"Deployments"** tab
   - Click on latest deployment
   - Look for these messages in logs:

   ```
   ✅ Redis cache service connected successfully
   🚀 Cache service initialized
   ```

2. **Test cache endpoints**
   - Visit: `https://your-app.railway.app/api/platform-connections/cache/stats`
   - Should return:
   ```json
   {
     "cache_status": "enabled",
     "stats": {
       "enabled": true,
       "connected_clients": 1,
       "hit_rate": 0.0
     }
   }
   ```

## 🔧 Service Configuration

Your Railway project should now have these services:

### **1. Main API Service**

```yaml
Environment Variables:
  - DATABASE_URL: (your existing PostgreSQL URL)
  - REDIS_URL: redis://default:password@redis-service.railway.internal:6379
  - RAILWAY_ENVIRONMENT: production
  - (your other existing variables)
```

### **2. Migration Service**

```yaml
Environment Variables:
  - DATABASE_URL: (same as API)
  - QNAP_HOST: (your NAS host)
  - QNAP_USERNAME: (your NAS username)
  - QNAP_PASSWORD: (your NAS password)
  - MIGRATION_MODE: all
  - NAS_USE_BATCHED: true
```

### **3. Redis Service**

```yaml
Automatically configured by Railway
- No additional setup required
- Provides caching for API service
```

### **4. PostgreSQL Database**

```yaml
Existing database service
- Shared by API and Migration services
```

## 🔍 Monitoring & Troubleshooting

### **Cache Statistics**

Monitor cache performance:

- **URL**: `/api/platform-connections/cache/stats`
- **Check**: Hit rate should increase over time
- **Expected**: >70% hit rate after users start using cached endpoints

### **Common Issues**

**1. Cache not connecting**

```
❌ Redis connection failed, caching disabled
```

**Solution**:

- Verify `REDIS_URL` environment variable
- Check Redis service is running
- Ensure URL format is correct

**2. Cache disabled in logs**

```
⚠️ REDIS_URL not found, caching will be disabled
```

**Solution**:

- Add `REDIS_URL` environment variable to API service
- Redeploy API service

**3. Performance not improving**

- Check logs for cache hits: `Cache hit for verify-connection`
- Verify TTL values are appropriate
- Monitor cache stats endpoint

### **Cache Invalidation**

**Automatic invalidation happens when:**

- User reconnects Etsy account (clears connection cache)
- User uploads new designs (clears gallery cache)
- Cache TTL expires naturally

**Manual cache clearing:**

- Redis service restart (clears all cache)
- API service restart (reconnects to Redis)

## 📊 Cache Configuration

Current cache TTL (Time To Live) settings:

| Endpoint            | Cache Duration | Reasoning                             |
| ------------------- | -------------- | ------------------------------------- |
| `verify-connection` | 5 minutes      | Connection status changes rarely      |
| `analytics`         | 1 hour         | Analytics data updates daily          |
| `gallery`           | 30 minutes     | Gallery changes when designs uploaded |
| `orders`            | 10 minutes     | Orders update frequently              |

## 🚀 Expected Results

After successful setup:

### **Before Redis (Current)**

```
verify-connection: 1.5 min ❌
analytics: 1 min ❌
gallery: 1.5 min ❌
Total page load: 30+ seconds ❌
```

### **After Redis (With Caching)**

```
verify-connection: 100ms ✅ (first hit: 1.5 min, subsequent: 100ms)
analytics: 200ms ✅ (first hit: 1 min, subsequent: 200ms)
gallery: 300ms ✅ (first hit: 1.5 min, subsequent: 300ms)
Total page load: 2-5 seconds ✅
```

## 🔄 Testing the Setup

1. **First page load** (cache miss):
   - Should take normal time (30+ seconds)
   - Endpoints populate cache

2. **Refresh page** (cache hit):
   - Should be dramatically faster (2-5 seconds)
   - Most data served from cache

3. **Monitor cache stats**:

   ```bash
   curl https://your-app.railway.app/api/platform-connections/cache/stats
   ```

4. **Check hit rate improvement**:
   - Initial: 0% hit rate
   - After usage: 70%+ hit rate

## 🎯 Next Steps

After Redis is working:

1. **Monitor performance** using cache stats endpoint
2. **Adjust TTL values** if needed for your use case
3. **Add more caching** to other slow endpoints
4. **Consider background job processing** for even better performance

## 🆘 Support

If you encounter issues:

1. **Check service logs** in Railway dashboard
2. **Verify environment variables** are set correctly
3. **Test cache stats endpoint** for connectivity
4. **Restart services** if needed (API service, then Redis)

---

**After completing this setup, your users should experience dramatically faster page loads with most content loading in under 5 seconds instead of 30+ seconds!**
