# 🚂 Railway Redis Caching Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Railway Redis caching system that has been implemented throughout the backend. The caching system provides significant performance improvements with Redis primary storage and memory fallback.

---

## 🛠️ Implementation Summary

### ✅ What's Been Implemented

1. **Railway-Optimized Cache Manager** (`server/src/utils/railway_cache.py`)
   - Redis connection with Railway configuration
   - Memory fallback for development/Redis failures
   - JSON serialization with datetime support
   - Performance monitoring and statistics
   - LRU eviction for memory cache

2. **Cache Service** (`server/src/services/cache_service.py`)
   - Centralized cache management
   - Health monitoring with periodic checks
   - Automatic initialization and cleanup
   - User and template cache invalidation

3. **Caching Integration** - Added to key services:
   - **Design Queries** - 5-minute cache for design lists, 10-minute for individual designs
   - **Template Operations** - 10-minute cache for template lists, 30-minute for individual templates
   - **User/Auth Data** - 15-minute cache for user token lookups
   - **Mockup Operations** - 5-minute cache for mockup lists, 10-minute for individual mockups

4. **Cache Endpoints** (`server/src/routes/cache/controller.py`)
   - `/api/cache/health` - Cache system health status
   - `/api/cache/stats` - Performance statistics
   - `/api/cache/clear/user/{user_id}` - Clear user cache
   - `/api/cache/clear/template/{template_id}` - Clear template cache

5. **Main App Integration** (`server/main.py`)
   - Automatic cache service initialization on startup
   - Graceful cache shutdown on app termination

---

## 🚀 Railway Deployment Steps

### Step 1: Add Redis Service to Railway

#### Option A: Railway CLI

```bash
# Login to Railway
railway login

# Add Redis service
railway add redis

# Check services
railway status
```

#### Option B: Railway Dashboard

1. Go to your Railway project dashboard
2. Click "Add Service"
3. Select "Redis" from add-ons
4. Configure memory size (recommend 1GB minimum)

### Step 2: Configure Environment Variables

Set these environment variables in Railway dashboard or via CLI:

```bash
# Cache configuration
railway variables set ENABLE_CACHING="true"
railway variables set CACHE_TTL_SECONDS="300"
railway variables set CACHE_MAX_MEMORY_ITEMS="1000"

# Redis will automatically set REDIS_URL when service is added
# Format: redis://redis:6379

# Optional: Performance monitoring
railway variables set DEBUG_LOGGING="false"
railway variables set PERFORMANCE_MONITORING="true"
```

### Step 3: Deploy the Updated Application

```bash
# Deploy the application with caching
railway up

# Monitor deployment logs
railway logs --follow
```

### Step 4: Verify Cache System

#### Check Health Status

```bash
curl https://your-app.railway.app/api/cache/health
```

Expected response:

```json
{
  "status": "healthy",
  "last_check": "2024-09-30T...",
  "cache_health": {
    "redis": "healthy",
    "memory": "healthy",
    "overall": "healthy"
  },
  "performance_stats": {
    "hits": 0,
    "misses": 0,
    "hit_rate_percent": 0,
    "redis_available": true,
    "enabled": true
  }
}
```

#### Check Performance Statistics

```bash
curl https://your-app.railway.app/api/cache/stats
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable                 | Default  | Description                               |
| ------------------------ | -------- | ----------------------------------------- |
| `ENABLE_CACHING`         | `true`   | Enable/disable caching system             |
| `REDIS_URL`              | Auto-set | Redis connection URL (Railway auto-sets)  |
| `CACHE_TTL_SECONDS`      | `300`    | Default cache TTL in seconds              |
| `CACHE_MAX_MEMORY_ITEMS` | `1000`   | Max items in memory fallback cache        |
| `DEBUG_LOGGING`          | `false`  | Enable debug logging for cache operations |

### Cache TTL Settings by Service

- **Design Lists**: 300 seconds (5 minutes)
- **Individual Designs**: 600 seconds (10 minutes)
- **Template Lists**: 600 seconds (10 minutes)
- **Individual Templates**: 1800 seconds (30 minutes)
- **User Token Data**: 900 seconds (15 minutes)
- **Mockup Lists**: 300 seconds (5 minutes)
- **Individual Mockups**: 600 seconds (10 minutes)

---

## 📊 Performance Monitoring

### Cache Health Monitoring

The cache system includes comprehensive health monitoring:

```python
# Automatic health checks every 5 minutes
# Manual health check endpoint: /api/cache/health
```

### Performance Metrics

Monitor these key metrics:

- **Hit Rate**: Percentage of cache hits vs misses
- **Memory Usage**: Items in memory fallback cache
- **Redis Status**: Connection health to Redis
- **Error Rates**: Redis and memory cache errors

### Logging

Cache operations are logged with these patterns:

```
INFO: 📊 Cache health: healthy | Hit rate: 85.2% | Memory items: 150
INFO: ✅ Cache service initialized successfully
INFO: 🧹 Cleared cache for user: user123
```

---

## 🛡️ Error Handling and Fallbacks

### Redis Connection Failures

The system gracefully handles Redis failures:

1. **Automatic Fallback**: Falls back to memory cache if Redis fails
2. **Connection Retry**: Attempts to reconnect to Redis
3. **Graceful Degradation**: Application continues without caching if needed

### Memory Cache Limits

When memory cache reaches capacity:

1. **LRU Eviction**: Removes least recently used items
2. **Expired Item Cleanup**: Automatically removes expired items
3. **Configurable Limits**: Set via `CACHE_MAX_MEMORY_ITEMS`

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Errors

```
⚠️ Redis connection failed, using memory cache: Connection refused
```

**Solution:**

- Verify Redis service is running in Railway dashboard
- Check `REDIS_URL` environment variable
- Ensure network connectivity between services

#### 2. Cache Initialization Failures

```
❌ Cache service initialization failed: Module not found
```

**Solution:**

- Check Redis package installation: `pip install redis`
- Verify import paths are correct
- Check Railway deployment logs

#### 3. High Memory Usage

```
⚠️ Memory cache at capacity, evicting items
```

**Solution:**

- Increase `CACHE_MAX_MEMORY_ITEMS`
- Reduce cache TTL values
- Verify Redis is working properly

### Debug Commands

```bash
# Check Redis service logs
railway logs --service redis

# Check application logs
railway logs --service api

# Test cache endpoints
curl https://your-app.railway.app/api/cache/health
curl https://your-app.railway.app/api/cache/stats
```

---

## 📈 Expected Performance Improvements

With the caching system properly deployed, expect:

- **70-90% reduction** in database query load
- **50-80% faster** response times for cached operations
- **Reduced API latency** for repeated requests
- **Better user experience** with faster page loads
- **Lower resource usage** on database servers

---

## 🔄 Cache Management

### Manual Cache Operations

```bash
# Clear user cache
curl -X POST https://your-app.railway.app/api/cache/clear/user/USER_ID \
  -H "Authorization: Bearer YOUR_TOKEN"

# Clear template cache
curl -X POST https://your-app.railway.app/api/cache/clear/template/TEMPLATE_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Automated Cache Invalidation

The system automatically invalidates cache when:

- **Designs**: Created, updated, or deleted
- **Templates**: Created, updated, or deleted
- **Users**: Profile updated or deleted
- **Mockups**: Created, updated, or deleted

---

## ✅ Deployment Checklist

- [ ] Redis service added to Railway project
- [ ] Environment variables configured
- [ ] Application deployed with caching code
- [ ] Cache health endpoint responding
- [ ] Performance monitoring active
- [ ] Error handling tested
- [ ] Documentation updated

---

## 🆘 Support

For issues with the caching system:

1. Check Railway dashboard for service status
2. Review application logs for cache errors
3. Test cache endpoints for connectivity
4. Verify environment variable configuration
5. Monitor performance metrics for anomalies

The caching system is designed to fail gracefully - if Redis is unavailable, the application will continue to function using memory cache or no cache, ensuring uptime is maintained.
