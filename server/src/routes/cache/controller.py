#!/usr/bin/env python3
"""
Cache Controller for Railway Deployment

Provides cache monitoring and management endpoints for Railway deployment.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from server.src.services.cache_service import cache_service, get_cache_health
from server.src.routes.auth.service import get_current_user, TokenData

router = APIRouter(
    prefix="/cache",
    tags=["cache"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

logger = logging.getLogger(__name__)

@router.get("/health", response_model=Dict[str, Any])
async def get_cache_health_status():
    """
    Get cache system health status

    Returns comprehensive health information about the caching system
    including Redis connectivity, memory usage, and performance metrics.
    """
    try:
        health_status = await get_cache_health()
        return health_status
    except Exception as e:
        logger.error(f"Error getting cache health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache health status"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_statistics():
    """
    Get cache performance statistics

    Returns detailed performance metrics including hit rates,
    cache sizes, and error counts.
    """
    try:
        stats = cache_service.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )

@router.post("/clear/user/{user_id}")
async def clear_user_cache_endpoint(
    user_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Clear all cache entries for a specific user

    Requires authentication. Users can only clear their own cache,
    or admin users can clear any user's cache.
    """
    try:
        # Check if user is clearing their own cache or is admin
        if str(current_user.get_uuid()) != user_id:
            # Add admin check here if needed
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only clear your own cache"
            )

        await cache_service.clear_user_cache(user_id)

        return {
            "message": f"Cache cleared for user {user_id}",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing user cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear user cache"
        )

@router.post("/clear/template/{template_id}")
async def clear_template_cache_endpoint(
    template_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Clear cache for a specific template

    Requires authentication. This will clear all cached data
    related to the specified template.
    """
    try:
        await cache_service.clear_template_cache(template_id)

        return {
            "message": f"Cache cleared for template {template_id}",
            "template_id": template_id
        }

    except Exception as e:
        logger.error(f"Error clearing template cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear template cache"
        )