"""
Redis Caching Service

Provides centralized caching functionality for improving API performance.
Handles connection management, cache operations, and TTL management.

Key Features:
- Automatic connection handling
- JSON serialization/deserialization
- TTL (Time To Live) management
- Error handling and fallback
- Cache invalidation patterns
"""

import redis
import json
import logging
import os
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service"""

    def __init__(self):
        self.redis_client = None
        self.is_enabled = False
        self._connect()

    def _connect(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                logger.warning("REDIS_URL not found, caching will be disabled")
                return

            # Parse Redis URL for Railway
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            self.redis_client.ping()
            self.is_enabled = True
            logger.info("✅ Redis cache service connected successfully")

        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed, caching disabled: {e}")
            self.is_enabled = False
            self.redis_client = None

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        # Create a hash of the arguments for consistent key generation
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        if kwargs:
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

        # Hash long keys to keep them manageable
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:{key_hash}"

        return key_data

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_enabled:
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (seconds)"""
        if not self.is_enabled:
            return False

        try:
            # Serialize value
            if hasattr(value, 'model_dump'):
                # Pydantic model - convert to dict first
                serialized_value = json.dumps(value.model_dump(), default=str)
            elif isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)

            # Set with TTL
            result = self.redis_client.setex(key, ttl, serialized_value)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_enabled:
            return False

        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_enabled:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_enabled:
            return {"enabled": False, "message": "Redis not available"}

        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

# Global cache service instance
cache_service = CacheService()

# Cache decorator for easy use
def cached(ttl: int = 300, key_prefix: str = "api"):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_key(key_prefix, func.__name__, *args, **kwargs)

            # Try to get from cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            if result is not None:
                await cache_service.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")

            return result
        return wrapper
    return decorator

# Specific cache functions for common use cases
class ApiCache:
    """High-level cache functions for API endpoints"""

    @staticmethod
    async def get_user_cache(user_id: str, cache_type: str) -> Optional[Any]:
        """Get cached data for a specific user"""
        key = cache_service._generate_key("user", user_id, cache_type)
        return await cache_service.get(key)

    @staticmethod
    async def set_user_cache(user_id: str, cache_type: str, data: Any, ttl: int = 300) -> bool:
        """Set cached data for a specific user"""
        key = cache_service._generate_key("user", user_id, cache_type)
        return await cache_service.set(key, data, ttl)

    @staticmethod
    async def invalidate_user_cache(user_id: str, cache_type: str = None) -> int:
        """Invalidate cache for a user (optionally specific type)"""
        if cache_type:
            key = cache_service._generate_key("user", user_id, cache_type)
            return 1 if await cache_service.delete(key) else 0
        else:
            pattern = f"user:{user_id}:*"
            return await cache_service.delete_pattern(pattern)

    @staticmethod
    async def get_connection_cache(user_id: str) -> Optional[Any]:
        """Get cached connection verification data"""
        return await ApiCache.get_user_cache(user_id, "connection_status")

    @staticmethod
    async def set_connection_cache(user_id: str, data: Any, ttl: int = 300) -> bool:
        """Cache connection verification data (5 min default)"""
        return await ApiCache.set_user_cache(user_id, "connection_status", data, ttl)

    @staticmethod
    async def get_analytics_cache(user_id: str, year: int) -> Optional[Any]:
        """Get cached analytics data"""
        return await ApiCache.get_user_cache(user_id, f"analytics_{year}")

    @staticmethod
    async def set_analytics_cache(user_id: str, year: int, data: Any, ttl: int = 3600) -> bool:
        """Cache analytics data (1 hour default)"""
        return await ApiCache.set_user_cache(user_id, f"analytics_{year}", data, ttl)

    @staticmethod
    async def get_gallery_cache(user_id: str, page: int = 1) -> Optional[Any]:
        """Get cached gallery data"""
        return await ApiCache.get_user_cache(user_id, f"gallery_page_{page}")

    @staticmethod
    async def set_gallery_cache(user_id: str, page: int, data: Any, ttl: int = 1800) -> bool:
        """Cache gallery data (30 min default)"""
        return await ApiCache.set_user_cache(user_id, f"gallery_page_{page}", data, ttl)

# Export the global instance
__all__ = ['cache_service', 'cached', 'ApiCache']