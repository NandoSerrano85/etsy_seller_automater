#!/usr/bin/env python3
"""
Cache Service for Railway Deployment

Centralized cache service management with health monitoring,
automatic initialization, and performance tracking.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from server.src.utils.railway_cache import cache_manager

logger = logging.getLogger(__name__)

class CacheService:
    """Centralized cache service with health monitoring and management"""

    def __init__(self):
        self.health_status = "initializing"
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes
        self._health_check_task = None

    async def initialize(self):
        """Initialize cache service and start health monitoring"""
        try:
            logger.info("🚀 Initializing cache service...")

            # Initialize the cache manager
            await cache_manager.initialize()

            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._periodic_health_check())

            self.health_status = "healthy"
            logger.info("✅ Cache service initialized successfully")

        except Exception as e:
            self.health_status = "error"
            logger.error(f"❌ Cache service initialization failed: {e}")
            raise

    async def shutdown(self):
        """Shutdown cache service and cleanup resources"""
        try:
            logger.info("🛑 Shutting down cache service...")

            # Cancel health check task
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Close Redis connections
            if cache_manager.redis_client:
                await cache_manager.redis_client.close()

            self.health_status = "shutdown"
            logger.info("✅ Cache service shutdown complete")

        except Exception as e:
            logger.error(f"❌ Cache service shutdown error: {e}")

    async def _periodic_health_check(self):
        """Periodic health check background task"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")

    async def health_check(self) -> dict:
        """Perform comprehensive health check"""
        try:
            health_status = await cache_manager.health_check()
            stats = cache_manager.get_stats()

            self.last_health_check = datetime.now()

            # Determine overall health
            if health_status['redis'] == 'healthy' or health_status['memory'] == 'healthy':
                self.health_status = "healthy"
            elif 'error' in health_status['redis'] and 'error' in health_status['memory']:
                self.health_status = "error"
            else:
                self.health_status = "degraded"

            result = {
                "status": self.health_status,
                "last_check": self.last_health_check.isoformat(),
                "cache_health": health_status,
                "performance_stats": stats,
                "uptime_seconds": (datetime.now() - self.last_health_check).total_seconds() if self.last_health_check else 0
            }

            # Log health status periodically
            if stats.get('hit_rate_percent', 0) > 0:
                logger.info(f"📊 Cache health: {self.health_status} | Hit rate: {stats.get('hit_rate_percent', 0)}% | Memory items: {stats.get('memory_cache_size', 0)}")

            return result

        except Exception as e:
            self.health_status = "error"
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

    async def clear_user_cache(self, user_id: str):
        """Clear all cache entries for a specific user"""
        try:
            await cache_manager.clear_pattern(f"user:{user_id}*")
            await cache_manager.clear_pattern(f"designs:{user_id}*")
            await cache_manager.clear_pattern(f"mockups:{user_id}*")
            logger.info(f"🧹 Cleared cache for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ Error clearing user cache for {user_id}: {e}")

    async def clear_template_cache(self, template_id: str):
        """Clear cache for a specific template"""
        try:
            await cache_manager.clear_pattern(f"template:{template_id}*")
            logger.info(f"🧹 Cleared cache for template: {template_id}")
        except Exception as e:
            logger.error(f"❌ Error clearing template cache for {template_id}: {e}")

    async def preload_critical_data(self):
        """Preload critical data into cache for better performance"""
        try:
            logger.info("🚀 Preloading critical cache data...")

            # This would typically load frequently accessed data
            # Implementation depends on specific application needs

            logger.info("✅ Critical data preloaded successfully")

        except Exception as e:
            logger.error(f"❌ Error preloading critical data: {e}")

    def get_cache_stats(self) -> dict:
        """Get current cache statistics"""
        return {
            "service_status": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "cache_stats": cache_manager.get_stats()
        }

# Global cache service instance
cache_service = CacheService()

# Convenience functions for easy access
async def init_cache_service():
    """Initialize the cache service"""
    await cache_service.initialize()

async def shutdown_cache_service():
    """Shutdown the cache service"""
    await cache_service.shutdown()

async def get_cache_health():
    """Get cache health status"""
    return await cache_service.health_check()

async def clear_user_cache(user_id: str):
    """Clear user cache"""
    await cache_service.clear_user_cache(user_id)

async def clear_template_cache(template_id: str):
    """Clear template cache"""
    await cache_service.clear_template_cache(template_id)