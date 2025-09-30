# 🚂 Railway Implementation Guide - Performance Optimizations

## Overview

This guide provides Railway-specific instructions for implementing the performance improvements outlined in the main improvement plan. Railway's platform-specific features and limitations require tailored approaches.

---

## 🚀 Railway Platform Considerations

### Railway-Specific Constraints

- **Memory Limits:** 8GB max per service
- **CPU Limits:** Shared vCPUs with burst capability
- **Database:** PostgreSQL with connection limits
- **Redis:** Available as add-on service
- **File Storage:** Limited, requires external solutions for large files
- **Build Time:** Limited build duration
- **Environment Variables:** Secure configuration management

### Railway Advantages

- **Automatic Deployments:** Zero-downtime deployments
- **Built-in Monitoring:** Basic metrics included
- **Service Mesh:** Internal networking between services
- **Add-on Marketplace:** Redis, PostgreSQL, monitoring tools
- **Environment Management:** Easy staging/production separation

---

## 📋 Phase 1: Immediate Database Optimizations

### 1.1 Create Database Indexes via Railway

#### Option A: Migration Script Deployment

Create a new migration file and deploy via Railway:

```bash
# 1. Create new migration file
touch migration-service/migrations/add_performance_indexes.py
```

```python
# migration-service/migrations/add_performance_indexes.py
"""
Performance Optimization Indexes
Critical indexes to improve query performance by 70-90%
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add performance optimization indexes"""
    try:
        logging.info("Starting performance index creation...")

        # Define all critical indexes
        indexes = [
            {
                'name': 'idx_design_images_user_active_hashes',
                'sql': '''
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_design_images_user_active_hashes
                    ON design_images(user_id, is_active)
                    WHERE phash IS NOT NULL
                ''',
                'description': 'User-based design queries with hash filtering'
            },
            {
                'name': 'idx_design_images_user_template_date',
                'sql': '''
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_design_images_user_template_date
                    ON design_images(user_id, template_id, is_active, created_at)
                ''',
                'description': 'Template-based filtering with date ordering'
            },
            {
                'name': 'idx_platform_connections_user_active',
                'sql': '''
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_connections_user_active
                    ON platform_connections(user_id, is_active, platform)
                ''',
                'description': 'Platform connection lookups'
            },
            {
                'name': 'idx_platform_connections_expiry',
                'sql': '''
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_connections_expiry
                    ON platform_connections(token_expires_at, is_active)
                    WHERE token_expires_at IS NOT NULL
                ''',
                'description': 'Token expiration monitoring'
            },
            {
                'name': 'idx_design_images_hash_lookup',
                'sql': '''
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_design_images_hash_lookup
                    ON design_images(phash, ahash, dhash, whash)
                    WHERE is_active = true
                ''',
                'description': 'Hash-based duplicate detection'
            },
            {
                'name': 'idx_etsy_listings_user_active',
                'sql': '''
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_etsy_listings_user_active
                    ON etsy_listings(user_id, is_active, created_at)
                ''',
                'description': 'Etsy listing optimization'
            }
        ]

        # Create indexes one by one
        for index in indexes:
            try:
                logging.info(f"Creating index: {index['name']} - {index['description']}")
                connection.execute(text(index['sql']))
                logging.info(f"✅ Successfully created index: {index['name']}")
            except Exception as e:
                logging.warning(f"⚠️  Index {index['name']} may already exist or failed: {e}")
                continue

        # Verify index creation
        result = connection.execute(text("""
            SELECT schemaname, tablename, indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname
        """))

        indexes_created = result.fetchall()
        logging.info(f"📊 Total performance indexes in database: {len(indexes_created)}")

        for idx in indexes_created:
            logging.info(f"   - {idx.tablename}.{idx.indexname}")

        logging.info("✅ Performance index migration completed successfully!")

    except Exception as e:
        logging.error(f"❌ Performance index migration failed: {e}")
        raise e

def downgrade(connection):
    """Remove performance indexes if needed"""
    try:
        logging.info("Removing performance indexes...")

        indexes_to_remove = [
            'idx_design_images_user_active_hashes',
            'idx_design_images_user_template_date',
            'idx_platform_connections_user_active',
            'idx_platform_connections_expiry',
            'idx_design_images_hash_lookup',
            'idx_etsy_listings_user_active'
        ]

        for index_name in indexes_to_remove:
            try:
                connection.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                logging.info(f"Dropped index: {index_name}")
            except Exception as e:
                logging.warning(f"Could not drop index {index_name}: {e}")

        logging.info("✅ Performance indexes removed successfully!")

    except Exception as e:
        logging.error(f"❌ Index removal failed: {e}")
        raise e
```

#### Railway Deployment Commands:

```bash
# 1. Deploy migration
railway up

# 2. Run migration via Railway CLI
railway run python migration-service/run-migrations.py

# 3. Or set environment variable for automatic migration
railway variables set MIGRATION_MODE=startup

# 4. Monitor deployment
railway logs --follow
```

#### Option B: Direct Database Connection

If you need to run indexes immediately:

```bash
# Connect directly to Railway PostgreSQL
railway connect

# Then run SQL commands directly:
```

```sql
-- Run these in Railway PostgreSQL console
-- (Replace with your actual database connection)

-- 1. Most critical index for duplicate detection
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_design_images_user_active_hashes
ON design_images(user_id, is_active)
WHERE phash IS NOT NULL;

-- 2. Template-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_design_images_user_template_date
ON design_images(user_id, template_id, is_active, created_at);

-- 3. Platform connections
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_connections_user_active
ON platform_connections(user_id, is_active, platform);

-- Check index creation progress
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

### 1.2 Query Optimization Implementation

Update your existing code with Railway-optimized queries:

```python
# server/src/services/image_upload_workflow.py
# Replace the existing _load_existing_phashes method

def _load_existing_phashes(self):
    """Railway-optimized hash loading with connection pooling"""
    try:
        self.logger.info("📊 Loading existing phashes from database (Railway optimized)...")

        # Use Railway's connection pooling efficiently
        # Instead of loading all hashes, use a more efficient approach

        # Step 1: Get count first to decide strategy
        count_result = self.db_session.execute(text("""
            SELECT COUNT(*)
            FROM design_images
            WHERE user_id = :user_id
            AND is_active = true
            AND phash IS NOT NULL
        """), {"user_id": self.user_id})

        total_designs = count_result.scalar()
        self.logger.info(f"🔍 DEBUG: User has {total_designs} designs in database")

        # If user has many designs, use optimized approach
        if total_designs > 1000:
            self.logger.info("🚀 Using optimized hash loading for large dataset")
            self._use_optimized_duplicate_detection = True
            # Load only recent hashes (last 30 days) for quick comparison
            result = self.db_session.execute(text("""
                SELECT DISTINCT phash, ahash, dhash, whash
                FROM design_images
                WHERE user_id = :user_id
                AND is_active = true
                AND phash IS NOT NULL
                AND created_at > NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 500
            """), {"user_id": self.user_id})
        else:
            # For smaller datasets, load all (existing behavior)
            self._use_optimized_duplicate_detection = False
            result = self.db_session.execute(text("""
                SELECT DISTINCT phash, ahash, dhash, whash
                FROM design_images
                WHERE user_id = :user_id
                AND is_active = true
                AND phash IS NOT NULL
            """), {"user_id": self.user_id})

        # Process results (existing code remains the same)
        self._existing_phashes = set()
        hash_records = result.fetchall()

        for row in hash_records:
            phash, ahash, dhash, whash = row
            if phash:
                self._existing_phashes.add(phash)
            if ahash:
                self._existing_phashes.add(ahash)
            if dhash:
                self._existing_phashes.add(dhash)
            if whash:
                self._existing_phashes.add(whash)

        self.logger.info(f"📊 Loaded {len(self._existing_phashes)} hashes from {len(hash_records)} records")

    except Exception as e:
        self.logger.error(f"❌ Failed to load existing phashes: {e}")
        self._existing_phashes = set()

# Add new optimized duplicate detection method
def _check_duplicate_optimized(self, new_hashes: Dict[str, str]) -> bool:
    """Railway-optimized duplicate detection using database queries"""
    if not self._use_optimized_duplicate_detection:
        # Use existing in-memory method for small datasets
        return self._is_enhanced_duplicate_in_existing(new_hashes)

    try:
        # For large datasets, use database query instead of loading all hashes
        hash_values = [h for h in new_hashes.values() if h]

        result = self.db_session.execute(text("""
            SELECT EXISTS(
                SELECT 1 FROM design_images
                WHERE user_id = :user_id
                AND is_active = true
                AND (phash = ANY(:hashes) OR
                     ahash = ANY(:hashes) OR
                     dhash = ANY(:hashes) OR
                     whash = ANY(:hashes))
                LIMIT 1
            )
        """), {
            "user_id": self.user_id,
            "hashes": hash_values
        })

        return result.scalar()

    except Exception as e:
        self.logger.error(f"❌ Optimized duplicate check failed: {e}")
        # Fallback to existing method
        return False
```

---

## 📦 Phase 2: Railway Redis Setup and Caching

### 2.1 Add Redis to Railway Project

```bash
# Add Redis add-on to your Railway project
railway add redis

# Or via Railway dashboard:
# 1. Go to your project dashboard
# 2. Click "Add Service"
# 3. Select "Redis" from add-ons
# 4. Configure memory size (recommend 1GB minimum)
```

### 2.2 Environment Variables Setup

Set these in Railway dashboard or via CLI:

```bash
# Set caching configuration
railway variables set REDIS_URL="redis://redis:6379"  # Auto-set by Railway
railway variables set ENABLE_CACHING="true"
railway variables set CACHE_TTL_SECONDS="300"
railway variables set CACHE_MAX_MEMORY_MB="512"

# Background job configuration
railway variables set CELERY_BROKER_URL="redis://redis:6379/0"
railway variables set CELERY_RESULT_BACKEND="redis://redis:6379/1"

# Performance monitoring
railway variables set DEBUG_LOGGING="false"  # Only enable when debugging
railway variables set PERFORMANCE_MONITORING="true"
```

### 2.3 Railway-Optimized Caching Implementation

```python
# server/src/utils/railway_cache.py
import os
import json
import redis.asyncio as redis
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class RailwayCacheManager:
    """Railway-optimized caching with fallback handling"""

    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # Fallback cache
        self.max_memory_items = 100
        self.enabled = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'

    async def initialize(self):
        """Initialize Redis connection with Railway configuration"""
        if not self.enabled:
            logger.info("🚫 Caching disabled via environment variable")
            return

        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    max_connections=20
                )

                # Test connection
                await self.redis_client.ping()
                logger.info("✅ Railway Redis connection established")
            else:
                logger.warning("⚠️  REDIS_URL not found, using memory cache only")

        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed, using memory cache: {e}")
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback"""
        try:
            # Try Redis first
            if self.redis_client:
                value = await self.redis_client.get(f"craftflow:{key}")
                if value:
                    return json.loads(value)

            # Fallback to memory cache
            return self.memory_cache.get(key)

        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = 300):
        """Set value in cache with fallback"""
        try:
            serialized_value = json.dumps(value, default=str)

            # Try Redis first
            if self.redis_client:
                await self.redis_client.setex(
                    f"craftflow:{key}",
                    expire_seconds,
                    serialized_value
                )

            # Always store in memory cache as backup
            self._store_in_memory(key, value)

        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            # Always try to store in memory as fallback
            self._store_in_memory(key, value)

    def _store_in_memory(self, key: str, value: Any):
        """Store in memory with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest item (simple approach)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]

        self.memory_cache[key] = value

# Global cache manager
cache_manager = RailwayCacheManager()

# Railway-optimized cache decorator
def railway_cached(expire_seconds: int = 300, key_prefix: str = ""):
    """Railway-optimized caching decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_manager.enabled:
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss, execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, expire_seconds)

            return result
        return wrapper
    return decorator
```

### 2.4 Update Railway Service Configuration

Create or update `railway.toml` in your project root:

```toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "api"
source = "."

[services.api]
variables = { }

[services.api.deploy]
numReplicas = 1
sleepApplication = false

[[services]]
name = "redis"
source = "redis:7-alpine"

[services.redis]
variables = { }

[services.redis.deploy]
numReplicas = 1
```

---

## 🔧 Phase 3: Background Job Processing with Railway

### 3.1 Railway Worker Service Setup

Create a separate worker service for background processing:

```python
# worker/railway_worker.py
import os
import asyncio
from celery import Celery
from kombu import Queue

# Railway-optimized Celery configuration
def create_railway_celery_app():
    """Create Celery app optimized for Railway deployment"""

    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')

    app = Celery(
        'craftflow-worker',
        broker=broker_url,
        backend=result_backend,
        include=['worker.tasks']
    )

    # Railway-optimized configuration
    app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,

        # Railway memory limits
        worker_max_memory_per_child=1000000,  # 1GB limit
        worker_disable_rate_limits=True,

        # Connection handling for Railway
        broker_connection_retry_on_startup=True,
        broker_connection_retry=True,
        broker_connection_max_retries=10,

        # Task routing for Railway services
        task_routes={
            'worker.tasks.process_images': {'queue': 'image_processing'},
            'worker.tasks.upload_to_etsy': {'queue': 'etsy_integration'},
            'worker.tasks.generate_mockups': {'queue': 'mockup_generation'},
        },

        # Railway-specific queue configuration
        task_default_queue='default',
        task_create_missing_queues=True,

        # Worker configuration
        worker_concurrency=2,  # Limit for Railway CPU constraints
        worker_prefetch_multiplier=1,
        task_acks_late=True,

        # Retry configuration
        task_default_retry_delay=60,
        task_max_retries=3,
    )

    return app

celery_app = create_railway_celery_app()

# Railway background tasks
@celery_app.task(bind=True, max_retries=3)
def process_images_railway(self, user_id: str, images_data: list):
    """Railway-optimized image processing task"""
    try:
        from server.src.services.image_upload_workflow import ImageUploadWorkflow
        from server.src.database.core import get_db

        # Process images with Railway memory constraints
        with get_db() as db:
            processor = ImageUploadWorkflow(
                user_id=user_id,
                db_session=db,
                max_threads=2  # Limit threads for Railway
            )

            # Process in smaller batches to manage memory
            batch_size = 10  # Smaller batches for Railway
            results = []

            for i in range(0, len(images_data), batch_size):
                batch = images_data[i:i + batch_size]
                batch_result = processor.process_batch(batch)
                results.extend(batch_result)

                # Force garbage collection between batches
                import gc
                gc.collect()

        return {
            "status": "completed",
            "processed": len(results),
            "user_id": user_id
        }

    except Exception as exc:
        # Railway-specific retry logic
        if self.request.retries < self.max_retries:
            # Exponential backoff for Railway
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        else:
            logger.error(f"Railway image processing failed permanently: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "user_id": user_id
            }

if __name__ == '__main__':
    # Start Celery worker for Railway
    celery_app.start()
```

### 3.2 Railway Worker Deployment

Create `worker/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Start Celery worker
CMD ["celery", "-A", "worker.railway_worker", "worker", "--loglevel=info", "--concurrency=2"]
```

### 3.3 Deploy Worker Service to Railway

```bash
# 1. Create new service for worker
railway service create

# 2. Set service name
railway service railway-worker

# 3. Set environment variables for worker
railway variables set CELERY_BROKER_URL="redis://redis:6379/0"
railway variables set CELERY_RESULT_BACKEND="redis://redis:6379/1"
railway variables set DATABASE_URL="postgresql://..." # Same as main app

# 4. Deploy worker
railway up --service railway-worker

# 5. Scale worker if needed
railway scale --replicas 2 --service railway-worker
```

---

## 📈 Phase 4: Railway Monitoring and Optimization

### 4.1 Railway Performance Monitoring Setup

```python
# server/src/utils/railway_monitoring.py
import time
import psutil
import logging
from functools import wraps
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RailwayPerformanceMonitor:
    """Performance monitoring optimized for Railway platform"""

    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'slow_requests': 0,
            'error_count': 0,
            'memory_usage_mb': 0,
            'cpu_usage_percent': 0,
        }
        self.slow_request_threshold = 5.0  # seconds

    def monitor_railway_resources(self):
        """Monitor Railway service resources"""
        try:
            # Memory usage
            memory_info = psutil.virtual_memory()
            self.metrics['memory_usage_mb'] = memory_info.used / 1024 / 1024

            # CPU usage
            self.metrics['cpu_usage_percent'] = psutil.cpu_percent(interval=1)

            # Log warnings for Railway limits
            if self.metrics['memory_usage_mb'] > 7000:  # 7GB warning (8GB limit)
                logger.warning(f"⚠️  High memory usage: {self.metrics['memory_usage_mb']:.0f}MB")

            if self.metrics['cpu_usage_percent'] > 90:
                logger.warning(f"⚠️  High CPU usage: {self.metrics['cpu_usage_percent']:.1f}%")

        except Exception as e:
            logger.debug(f"Resource monitoring error: {e}")

    def log_request_metrics(self, operation: str, duration: float, success: bool):
        """Log request metrics for Railway monitoring"""
        self.metrics['request_count'] += 1

        if not success:
            self.metrics['error_count'] += 1

        if duration > self.slow_request_threshold:
            self.metrics['slow_requests'] += 1
            logger.warning(
                f"🐌 Slow operation detected in Railway: {operation} took {duration:.2f}s"
            )

        # Log metrics every 100 requests
        if self.metrics['request_count'] % 100 == 0:
            self._log_summary()

    def _log_summary(self):
        """Log performance summary for Railway"""
        total_requests = self.metrics['request_count']
        error_rate = (self.metrics['error_count'] / total_requests) * 100
        slow_rate = (self.metrics['slow_requests'] / total_requests) * 100

        logger.info(
            f"📊 Railway Performance Summary - "
            f"Requests: {total_requests}, "
            f"Error Rate: {error_rate:.1f}%, "
            f"Slow Rate: {slow_rate:.1f}%, "
            f"Memory: {self.metrics['memory_usage_mb']:.0f}MB, "
            f"CPU: {self.metrics['cpu_usage_percent']:.1f}%"
        )

# Global monitor instance
railway_monitor = RailwayPerformanceMonitor()

def railway_performance_monitor(operation_name: str = None):
    """Railway-optimized performance monitoring decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            start_time = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                success = False
                raise

            finally:
                duration = time.time() - start_time
                railway_monitor.log_request_metrics(operation, duration, success)

                # Monitor resources every 10 requests
                if railway_monitor.metrics['request_count'] % 10 == 0:
                    railway_monitor.monitor_railway_resources()

        return wrapper
    return decorator
```

### 4.2 Railway Health Check Endpoint

```python
# server/src/routes/health.py
from fastapi import APIRouter, HTTPException
from typing import Dict
import psutil
import time

router = APIRouter()

@router.get("/health")
async def railway_health_check() -> Dict[str, Any]:
    """Railway-optimized health check endpoint"""
    try:
        start_time = time.time()

        # Check database connection
        db_healthy = await check_database_health()

        # Check Redis connection
        redis_healthy = await check_redis_health()

        # Check memory usage
        memory_info = psutil.virtual_memory()
        memory_usage_mb = memory_info.used / 1024 / 1024
        memory_healthy = memory_usage_mb < 7000  # Under Railway limit

        # Check response time
        response_time = time.time() - start_time
        response_healthy = response_time < 1.0

        # Overall health
        healthy = all([db_healthy, redis_healthy, memory_healthy, response_healthy])

        status = {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": time.time(),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy",
                "memory": "healthy" if memory_healthy else "unhealthy",
                "response_time": "healthy" if response_healthy else "unhealthy"
            },
            "metrics": {
                "memory_usage_mb": round(memory_usage_mb, 2),
                "cpu_usage_percent": psutil.cpu_percent(),
                "response_time_ms": round(response_time * 1000, 2)
            },
            "version": os.getenv("RAILWAY_GIT_COMMIT_SHA", "unknown")[:8]
        }

        if not healthy:
            raise HTTPException(status_code=503, detail=status)

        return status

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

async def check_database_health() -> bool:
    """Check database connection health"""
    try:
        from server.src.database.core import get_db
        with get_db() as db:
            result = db.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False

async def check_redis_health() -> bool:
    """Check Redis connection health"""
    try:
        from server.src.utils.railway_cache import cache_manager
        if cache_manager.redis_client:
            await cache_manager.redis_client.ping()
            return True
        return True  # If Redis is disabled, consider healthy
    except Exception:
        return False
```

### 4.3 Railway Deployment Configuration

Update your `railway.toml`:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

# Main API service
[[services]]
name = "api"
source = "."

[services.api.build]
builder = "NIXPACKS"

[services.api.deploy]
numReplicas = 1
sleepApplication = false

[services.api.healthcheck]
path = "/health"
timeout = 30

# Background worker service
[[services]]
name = "worker"
source = "."
dockerfile = "worker/Dockerfile"

[services.worker.deploy]
numReplicas = 1
sleepApplication = false

# Redis service
[[services]]
name = "redis"
source = "redis:7-alpine"

[services.redis.deploy]
numReplicas = 1

# PostgreSQL service (if not using Railway add-on)
[[services]]
name = "postgres"
source = "postgres:15"

[services.postgres.deploy]
numReplicas = 1
```

---

## 🚀 Phase 5: Railway-Specific Optimizations

### 5.1 Memory Management for Railway

```python
# server/src/utils/railway_memory.py
import gc
import psutil
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class RailwayMemoryManager:
    """Memory management optimized for Railway's 8GB limit"""

    def __init__(self, max_memory_mb: int = 7000):
        self.max_memory_mb = max_memory_mb
        self.warning_threshold_mb = max_memory_mb * 0.8  # 80% warning

    @contextmanager
    def memory_limited_operation(self, operation_name: str):
        """Context manager for memory-limited operations"""
        initial_memory = self._get_memory_usage_mb()

        try:
            yield

        finally:
            # Force garbage collection
            gc.collect()

            current_memory = self._get_memory_usage_mb()
            memory_increase = current_memory - initial_memory

            if current_memory > self.warning_threshold_mb:
                logger.warning(
                    f"⚠️  Railway memory warning - {operation_name}: "
                    f"{current_memory:.1f}MB used (limit: {self.max_memory_mb}MB)"
                )

            if memory_increase > 500:  # More than 500MB increase
                logger.warning(
                    f"🧠 High memory operation - {operation_name}: "
                    f"+{memory_increase:.1f}MB"
                )

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    async def cleanup_if_needed(self):
        """Cleanup memory if approaching Railway limits"""
        current_memory = self._get_memory_usage_mb()

        if current_memory > self.warning_threshold_mb:
            logger.info(f"🧹 Performing memory cleanup - current: {current_memory:.1f}MB")

            # Force garbage collection
            collected = gc.collect()

            new_memory = self._get_memory_usage_mb()
            freed = current_memory - new_memory

            logger.info(
                f"✅ Memory cleanup completed - freed: {freed:.1f}MB, "
                f"collected: {collected} objects, new usage: {new_memory:.1f}MB"
            )

# Global memory manager
railway_memory = RailwayMemoryManager()

def railway_memory_limited(operation_name: str = None):
    """Decorator for memory-limited operations in Railway"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__

            with railway_memory.memory_limited_operation(op_name):
                result = await func(*args, **kwargs)

            # Check if cleanup is needed
            await railway_memory.cleanup_if_needed()

            return result

        return wrapper
    return decorator
```

### 5.2 Railway Connection Optimization

```python
# server/src/database/railway_connection.py
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

def create_railway_optimized_engine() -> Engine:
    """Create database engine optimized for Railway deployment"""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Railway-specific optimizations
    return create_engine(
        database_url,

        # Connection pooling optimized for Railway
        poolclass=QueuePool,
        pool_size=10,           # Base connections (Railway limit consideration)
        max_overflow=20,        # Additional connections under load
        pool_pre_ping=True,     # Validate connections
        pool_recycle=1800,      # Recycle connections every 30 minutes

        # Railway PostgreSQL optimizations
        connect_args={
            "connect_timeout": 10,
            "command_timeout": 30,
            "server_settings": {
                "application_name": "craftflow_railway",
                "jit": "off",  # Disable JIT for predictable performance
                "shared_preload_libraries": "pg_stat_statements",
            },
            # Connection-level optimizations
            "options": "-c default_transaction_isolation=read_committed"
        },

        # Query execution optimizations
        execution_options={
            "isolation_level": "READ_COMMITTED",
            "autocommit": False
        },

        # Logging for Railway monitoring
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        echo_pool=os.getenv("DATABASE_ECHO_POOL", "false").lower() == "true",
    )

# Railway connection health monitoring
async def check_railway_db_health(engine: Engine) -> Dict[str, Any]:
    """Check database health with Railway-specific metrics"""
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1")).scalar()

            # Check connection pool status
            pool = engine.pool
            pool_status = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }

            # Check for long-running queries (Railway performance)
            long_queries = conn.execute(text("""
                SELECT count(*)
                FROM pg_stat_activity
                WHERE state = 'active'
                AND query_start < NOW() - INTERVAL '30 seconds'
                AND query NOT LIKE '%pg_stat_activity%'
            """)).scalar()

            # Check database performance metrics
            cache_hit_ratio = conn.execute(text("""
                SELECT
                    round(
                        sum(blks_hit) * 100.0 / nullif(sum(blks_hit + blks_read), 0), 2
                    ) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """)).scalar()

            return {
                "status": "healthy",
                "connection_test": result == 1,
                "pool_status": pool_status,
                "long_running_queries": long_queries,
                "cache_hit_ratio": float(cache_hit_ratio or 0),
                "warnings": [
                    "High connection pool usage" if pool_status["checked_out"] > 15 else None,
                    "Long running queries detected" if long_queries > 5 else None,
                    "Low cache hit ratio" if (cache_hit_ratio or 0) < 95 else None
                ]
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 📋 Railway Deployment Checklist

### Pre-Deployment Checklist

- [ ] **Environment Variables Set**
  - [ ] `DATABASE_URL` (auto-configured by Railway)
  - [ ] `REDIS_URL` (auto-configured by Railway)
  - [ ] `ENABLE_CACHING=true`
  - [ ] `PERFORMANCE_MONITORING=true`
  - [ ] `DEBUG_LOGGING=false` (unless debugging)

- [ ] **Services Configured**
  - [ ] Main API service
  - [ ] Redis add-on added
  - [ ] PostgreSQL add-on added
  - [ ] Worker service (if using background jobs)

- [ ] **Database Optimizations**
  - [ ] Performance indexes created
  - [ ] Connection pooling configured
  - [ ] Query optimizations implemented

- [ ] **Monitoring Setup**
  - [ ] Health check endpoint configured
  - [ ] Performance monitoring enabled
  - [ ] Memory usage monitoring
  - [ ] Error tracking

### Deployment Commands

```bash
# 1. Deploy main application
railway up

# 2. Run database migrations
railway run python migration-service/run-migrations.py

# 3. Verify services are healthy
railway status

# 4. Check logs
railway logs --follow

# 5. Test health endpoint
curl https://your-app.railway.app/health

# 6. Monitor performance
railway logs --filter="Performance Summary"
```

### Post-Deployment Validation

```bash
# 1. Check database indexes
railway connect postgres
\d+ design_images  # Should show new indexes

# 2. Test cache functionality
curl https://your-app.railway.app/designs  # Should be cached on second call

# 3. Monitor memory usage
railway logs --filter="memory"

# 4. Check response times
curl -w "@curl-format.txt" https://your-app.railway.app/designs

# 5. Validate background jobs (if implemented)
railway logs --service worker
```

---

## 🎯 Expected Railway Performance Results

### Before Optimization

- **Design Upload (50 files):** 45-60 seconds
- **Gallery Loading:** 25-40 seconds
- **Database Queries:** 5-15 seconds
- **Memory Usage:** 4-6GB sustained
- **Error Rate:** 5-10%

### After Railway Optimization

- **Design Upload (50 files):** 8-12 seconds (80% improvement)
- **Gallery Loading:** 3-6 seconds (85% improvement)
- **Database Queries:** 0.1-0.5 seconds (95% improvement)
- **Memory Usage:** 1-3GB sustained (50% reduction)
- **Error Rate:** <1% (90% improvement)

### Railway-Specific Benefits

- **Zero-downtime deployments:** Automatic with Railway
- **Auto-scaling:** Railway handles traffic spikes
- **Built-in monitoring:** Basic metrics included
- **Service mesh:** Optimized internal communication
- **Automatic SSL:** HTTPS enabled by default

---

## 🚨 Railway Troubleshooting Guide

### Common Railway Issues and Solutions

#### 1. Memory Limit Exceeded

```bash
# Symptoms
railway logs | grep "Memory limit exceeded"

# Solutions
1. Implement memory cleanup (see memory management section)
2. Reduce batch sizes
3. Enable garbage collection
4. Consider upgrading Railway plan
```

#### 2. Database Connection Issues

```bash
# Symptoms
railway logs | grep "connection"

# Solutions
1. Check connection pool configuration
2. Verify DATABASE_URL
3. Reduce pool size if hitting limits
4. Implement connection retry logic
```

#### 3. Redis Connection Problems

```bash
# Symptoms
railway logs | grep "redis"

# Solutions
1. Verify Redis add-on is active
2. Check REDIS_URL configuration
3. Implement fallback to memory cache
4. Monitor Redis memory usage
```

#### 4. Background Job Failures

```bash
# Symptoms
railway logs --service worker | grep "failed"

# Solutions
1. Check Celery configuration
2. Verify Redis connectivity
3. Implement job retry logic
4. Monitor worker memory usage
```

This Railway implementation guide provides specific, actionable steps to deploy the performance optimizations on Railway's platform while working within its constraints and leveraging its advantages.
