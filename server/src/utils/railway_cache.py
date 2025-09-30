#!/usr/bin/env python3
"""
Railway-Optimized Caching System

This module provides a comprehensive caching solution optimized for Railway deployment
with Redis backend and memory fallback for maximum reliability and performance.

Features:
- Railway Redis integration with automatic fallback
- Memory-based caching for development/fallback scenarios
- JSON serialization with custom datetime handling
- LRU eviction for memory cache
- Comprehensive error handling and logging
- Performance monitoring and metrics
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict, Callable
from functools import wraps
import asyncio

# Handle optional Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class RailwayCacheManager:
    """Railway-optimized caching with Redis backend and memory fallback"""

    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self.max_memory_items = int(os.getenv('CACHE_MAX_MEMORY_ITEMS', '1000'))
        self.enabled = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        self.default_ttl = int(os.getenv('CACHE_TTL_SECONDS', '300'))

        # Performance tracking
        self.stats = {
            'hits': 0,
            'misses': 0,
            'redis_hits': 0,
            'memory_hits': 0,
            'redis_errors': 0,
            'memory_errors': 0
        }

        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection with Railway configuration"""
        if self._initialized:
            return

        if not self.enabled:
            logger.info("🚫 Caching disabled via ENABLE_CACHING environment variable")
            self._initialized = True
            return

        # Initialize Redis connection
        if REDIS_AVAILABLE:
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
                        max_connections=20,
                        health_check_interval=30
                    )

                    # Test connection
                    await self.redis_client.ping()
                    logger.info("✅ Railway Redis connection established")
                else:
                    logger.warning("⚠️  REDIS_URL not found, using memory cache only")

            except Exception as e:
                logger.warning(f"⚠️  Redis connection failed, using memory cache: {e}")
                self.redis_client = None
        else:
            logger.warning("⚠️  Redis not available, using memory cache only")

        self._initialized = True
        logger.info(f"🎯 Cache manager initialized - Memory limit: {self.max_memory_items} items, TTL: {self.default_ttl}s")

    def _generate_cache_key(self, key: str) -> str:
        """Generate namespaced cache key"""
        return f"craftflow:v1:{key}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON with custom datetime handling"""
        try:
            return json.dumps(value, cls=DateTimeJSONEncoder, default=str)
        except Exception as e:
            logger.error(f"❌ Serialization error: {e}")
            raise

    def _deserialize_value(self, serialized_value: str) -> Any:
        """Deserialize JSON value"""
        try:
            return json.loads(serialized_value)
        except Exception as e:
            logger.error(f"❌ Deserialization error: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with Redis primary, memory fallback"""
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(key)

        try:
            # Try Redis first
            if self.redis_client:
                try:
                    value = await self.redis_client.get(cache_key)
                    if value:
                        self.stats['hits'] += 1
                        self.stats['redis_hits'] += 1
                        return self._deserialize_value(value)
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    logger.debug(f"Redis get error for {key}: {e}")

            # Fallback to memory cache
            if cache_key in self.memory_cache:
                value, expiry_time = self.memory_cache[cache_key]
                if expiry_time > time.time():
                    self.stats['hits'] += 1
                    self.stats['memory_hits'] += 1
                    return value
                else:
                    # Expired, remove from memory
                    del self.memory_cache[cache_key]

            # Cache miss
            self.stats['misses'] += 1
            return None

        except Exception as e:
            self.stats['memory_errors'] += 1
            logger.debug(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        """Set value in cache with Redis primary, memory backup"""
        if not self.enabled:
            return

        expire_seconds = expire_seconds or self.default_ttl
        cache_key = self._generate_cache_key(key)

        try:
            serialized_value = self._serialize_value(value)

            # Try Redis first
            if self.redis_client:
                try:
                    await self.redis_client.setex(cache_key, expire_seconds, serialized_value)
                except Exception as e:
                    self.stats['redis_errors'] += 1
                    logger.debug(f"Redis set error for {key}: {e}")

            # Always store in memory cache as backup
            self._store_in_memory(cache_key, value, expire_seconds)

        except Exception as e:
            self.stats['memory_errors'] += 1
            logger.debug(f"Cache set error for {key}: {e}")
            # Try to store in memory as fallback
            try:
                self._store_in_memory(cache_key, value, expire_seconds)
            except:
                pass  # Fail silently to not break application

    async def delete(self, key: str):
        """Delete value from cache"""
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(key)

        # Delete from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.debug(f"Redis delete error for {key}: {e}")

        # Delete from memory cache
        self.memory_cache.pop(cache_key, None)

    async def clear_pattern(self, pattern: str):
        """Clear cache keys matching pattern"""
        if not self.enabled:
            return

        cache_pattern = self._generate_cache_key(pattern)

        # Clear from Redis
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(cache_pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.debug(f"Redis pattern clear error for {pattern}: {e}")

        # Clear from memory cache
        keys_to_delete = [k for k in self.memory_cache.keys() if cache_pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.memory_cache[key]

    def _store_in_memory(self, cache_key: str, value: Any, expire_seconds: int):
        """Store in memory with LRU eviction"""
        # Calculate expiry time
        expiry_time = time.time() + expire_seconds

        # LRU eviction if at capacity
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove expired items first
            current_time = time.time()
            expired_keys = [k for k, (_, exp) in self.memory_cache.items() if exp <= current_time]
            for key in expired_keys:
                del self.memory_cache[key]

            # If still at capacity, remove oldest
            if len(self.memory_cache) >= self.max_memory_items:
                oldest_key = min(self.memory_cache.keys(),
                               key=lambda k: self.memory_cache[k][1])
                del self.memory_cache[oldest_key]

        self.memory_cache[cache_key] = (value, expiry_time)

    def get_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None,
            'enabled': self.enabled
        }

    async def health_check(self) -> dict:
        """Perform health check on cache systems"""
        status = {
            'redis': 'unavailable',
            'memory': 'available',
            'overall': 'degraded'
        }

        # Test Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                status['redis'] = 'healthy'
                status['overall'] = 'healthy'
            except Exception as e:
                status['redis'] = f'error: {str(e)}'

        # Test memory cache
        try:
            test_key = 'health_check_test'
            test_value = {'timestamp': datetime.now().isoformat()}
            self._store_in_memory(self._generate_cache_key(test_key), test_value, 10)
            status['memory'] = 'healthy'
        except Exception as e:
            status['memory'] = f'error: {str(e)}'

        return status

# Global cache manager instance
cache_manager = RailwayCacheManager()

def railway_cached(expire_seconds: Optional[int] = None, key_prefix: str = "",
                  skip_cache_if: Optional[Callable] = None):
    """
    Railway-optimized caching decorator

    Args:
        expire_seconds: Cache expiration time in seconds
        key_prefix: Prefix for cache key
        skip_cache_if: Function that returns True to skip caching
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not cache_manager.enabled:
                return await func(*args, **kwargs)

            # Check if we should skip cache
            if skip_cache_if and skip_cache_if(*args, **kwargs):
                return await func(*args, **kwargs)

            # Generate cache key
            key_parts = [key_prefix, func.__name__]

            # Add positional args (excluding 'self' and complex objects)
            for arg in args:
                if not hasattr(arg, '__dict__'):  # Skip complex objects
                    key_parts.append(str(arg))

            # Add keyword args
            for k, v in sorted(kwargs.items()):
                if not hasattr(v, '__dict__'):  # Skip complex objects
                    key_parts.append(f"{k}={v}")

            cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss, execute function
            result = await func(*args, **kwargs)

            # Store in cache (handle None results)
            if result is not None:
                await cache_manager.set(cache_key, result, expire_seconds)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not cache_manager.enabled:
                return func(*args, **kwargs)

            # For sync functions, we'll skip caching for now
            # Could be enhanced to use sync Redis client
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Convenience functions for common cache patterns
async def cache_user_data(user_id: str, data: dict, expire_seconds: int = 900):
    """Cache user-related data"""
    await cache_manager.set(f"user:{user_id}", data, expire_seconds)

async def get_cached_user_data(user_id: str) -> Optional[dict]:
    """Get cached user data"""
    return await cache_manager.get(f"user:{user_id}")

async def cache_template_data(template_id: str, data: dict, expire_seconds: int = 1800):
    """Cache template-related data"""
    await cache_manager.set(f"template:{template_id}", data, expire_seconds)

async def get_cached_template_data(template_id: str) -> Optional[dict]:
    """Get cached template data"""
    return await cache_manager.get(f"template:{template_id}")

async def cache_design_list(user_id: str, filters: dict, designs: list, expire_seconds: int = 300):
    """Cache design list with filters"""
    filter_key = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
    cache_key = f"designs:{user_id}:{filter_key}"
    await cache_manager.set(cache_key, designs, expire_seconds)

async def get_cached_design_list(user_id: str, filters: dict) -> Optional[list]:
    """Get cached design list"""
    filter_key = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
    cache_key = f"designs:{user_id}:{filter_key}"
    return await cache_manager.get(cache_key)

async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user"""
    await cache_manager.clear_pattern(f"user:{user_id}*")
    await cache_manager.clear_pattern(f"designs:{user_id}*")

async def invalidate_template_cache(template_id: str):
    """Invalidate template cache"""
    await cache_manager.clear_pattern(f"template:{template_id}*")