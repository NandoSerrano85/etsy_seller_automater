"""
OAuth Token Management API Endpoints

Provides endpoints for managing and refreshing OAuth tokens.
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.entities.platform_connection import PlatformType
from server.src.services.oauth_token_refresh_service import get_oauth_refresh_service

router = APIRouter(prefix="/api/oauth", tags=["OAuth Tokens"])
logger = logging.getLogger(__name__)


@router.get("/tokens")
async def get_user_tokens(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get all OAuth token information for the current user"""
    try:
        service = get_oauth_refresh_service()
        tokens = {}

        # Check each platform
        for platform in PlatformType:
            token_info = service.get_token_info(
                user_id=str(current_user.get_uuid()),
                platform=platform,
                db=db
            )
            if token_info:
                # Don't send actual tokens to frontend, just status info
                tokens[platform.value] = {
                    "platform": token_info["platform"],
                    "expires_at": token_info["expires_at"],
                    "is_expired": token_info["is_expired"],
                    "needs_refresh": token_info["needs_refresh"],
                    "time_until_expiry": token_info["time_until_expiry"],
                    "last_verified_at": token_info["last_verified_at"],
                }

        logger.info(f"📋 Retrieved token info for user {current_user.get_uuid()}: {len(tokens)} platforms")
        return {
            "success": True,
            "tokens": tokens
        }

    except Exception as e:
        logger.error(f"❌ Error getting user tokens: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token information"
        )


@router.get("/tokens/{platform}")
async def get_platform_token(
    platform: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get OAuth token information for a specific platform"""
    try:
        # Validate platform
        try:
            platform_type = PlatformType[platform.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}. Valid platforms: {[p.value for p in PlatformType]}"
            )

        service = get_oauth_refresh_service()
        token_info = service.get_token_info(
            user_id=str(current_user.get_uuid()),
            platform=platform_type,
            db=db
        )

        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active token found for platform: {platform}"
            )

        # Don't send actual tokens to frontend, just status info
        return {
            "success": True,
            "token": {
                "platform": token_info["platform"],
                "expires_at": token_info["expires_at"],
                "is_expired": token_info["is_expired"],
                "needs_refresh": token_info["needs_refresh"],
                "time_until_expiry": token_info["time_until_expiry"],
                "last_verified_at": token_info["last_verified_at"],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting platform token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token information"
        )


@router.post("/tokens/{platform}/refresh")
async def refresh_platform_token(
    platform: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Manually refresh OAuth token for a specific platform"""
    try:
        # Validate platform
        try:
            platform_type = PlatformType[platform.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}. Valid platforms: {[p.value for p in PlatformType]}"
            )

        logger.info(f"🔄 Manual token refresh requested for {platform} by user {current_user.get_uuid()}")

        service = get_oauth_refresh_service()
        token_data = await service.refresh_token_for_user(
            user_id=str(current_user.get_uuid()),
            platform=platform_type,
            db=db
        )

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active connection found for platform: {platform}"
            )

        logger.info(f"✅ Successfully refreshed token for {platform} for user {current_user.get_uuid()}")

        # Return status info (not actual tokens)
        return {
            "success": True,
            "message": f"Token refreshed successfully for {platform}",
            "token": {
                "platform": token_data["platform"],
                "expires_at": token_data["expires_at"],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error refreshing platform token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.get("/service/status")
async def get_service_status(
    current_user: CurrentUser,
):
    """Get the status of the OAuth token refresh service"""
    try:
        service = get_oauth_refresh_service()

        return {
            "success": True,
            "service": {
                "is_running": service.is_running,
                "refresh_interval": service.refresh_interval,
                "refresh_threshold": service.refresh_threshold,
            }
        }

    except Exception as e:
        logger.error(f"❌ Error getting service status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service status"
        )


@router.post("/service/refresh-all")
async def refresh_all_user_tokens(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Manually refresh all OAuth tokens for the current user"""
    try:
        logger.info(f"🔄 Refreshing all tokens for user {current_user.get_uuid()}")

        service = get_oauth_refresh_service()
        results = {}

        # Try to refresh each platform
        for platform in PlatformType:
            try:
                token_data = await service.refresh_token_for_user(
                    user_id=str(current_user.get_uuid()),
                    platform=platform,
                    db=db
                )

                if token_data:
                    results[platform.value] = {
                        "success": True,
                        "expires_at": token_data["expires_at"],
                    }
                else:
                    results[platform.value] = {
                        "success": False,
                        "message": "No active connection found"
                    }

            except Exception as e:
                logger.error(f"❌ Error refreshing {platform.value} token: {e}")
                results[platform.value] = {
                    "success": False,
                    "message": str(e)
                }

        successful_refreshes = sum(1 for r in results.values() if r.get("success"))
        logger.info(
            f"✅ Refreshed {successful_refreshes}/{len(results)} tokens for user {current_user.get_uuid()}"
        )

        return {
            "success": True,
            "message": f"Refreshed {successful_refreshes} token(s)",
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Error refreshing all tokens: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh tokens"
        )
