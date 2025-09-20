"""
Automatic Token Refresh Service

This service runs in the background and monitors platform connections for tokens
that are about to expire, refreshing them proactively to prevent API failures.

Features:
- Monitors all active platform connections
- Refreshes tokens 30 seconds before expiration
- Handles multiple platforms (Etsy, Shopify, etc.)
- Runs as FastAPI background task
- Comprehensive error handling and logging
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.core import get_db
from ..entities.platform_connection import PlatformConnection, PlatformType
from ..utils.etsy_api_engine import EtsyAPI

logger = logging.getLogger(__name__)

class TokenRefreshService:
    """Service to automatically refresh platform tokens before they expire"""

    def __init__(self):
        self.is_running = False
        self.refresh_interval = 60  # Check every 60 seconds
        self.refresh_threshold = 30  # Refresh 30 seconds before expiry
        self.stats = {
            'total_checks': 0,
            'tokens_refreshed': 0,
            'refresh_failures': 0,
            'last_run': None
        }

    async def start(self):
        """Start the token refresh service"""
        if self.is_running:
            logger.warning("Token refresh service is already running")
            return

        self.is_running = True
        logger.info("🔄 Starting automatic token refresh service")
        logger.info(f"   ⏱️  Check interval: {self.refresh_interval} seconds")
        logger.info(f"   ⚠️  Refresh threshold: {self.refresh_threshold} seconds before expiry")

        try:
            while self.is_running:
                await self._refresh_cycle()
                await asyncio.sleep(self.refresh_interval)
        except Exception as e:
            logger.error(f"Token refresh service crashed: {e}")
            self.is_running = False
            raise

    def stop(self):
        """Stop the token refresh service"""
        self.is_running = False
        logger.info("🛑 Token refresh service stopped")

    async def _refresh_cycle(self):
        """Single refresh cycle - check and refresh tokens as needed"""
        try:
            self.stats['total_checks'] += 1
            self.stats['last_run'] = datetime.now(timezone.utc)

            # Get database session
            db: Session = next(get_db())

            try:
                # Find tokens that need refreshing
                tokens_to_refresh = await self._find_tokens_to_refresh(db)

                if not tokens_to_refresh:
                    logger.debug("No tokens need refreshing at this time")
                    return

                logger.info(f"🔄 Found {len(tokens_to_refresh)} tokens that need refreshing")

                # Refresh each token
                for connection in tokens_to_refresh:
                    await self._refresh_single_token(connection, db)

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in token refresh cycle: {e}")

    async def _find_tokens_to_refresh(self, db: Session) -> List[PlatformConnection]:
        """Find platform connections with tokens that need refreshing"""

        # Calculate the threshold time (now + refresh_threshold seconds)
        threshold_time = datetime.now(timezone.utc) + timedelta(seconds=self.refresh_threshold)

        # Query for active connections with tokens expiring soon
        connections = db.query(PlatformConnection).filter(
            and_(
                PlatformConnection.is_active == True,
                PlatformConnection.access_token.isnot(None),
                PlatformConnection.refresh_token.isnot(None),
                PlatformConnection.token_expires_at.isnot(None),
                PlatformConnection.token_expires_at <= threshold_time
            )
        ).all()

        return connections

    async def _refresh_single_token(self, connection: PlatformConnection, db: Session):
        """Refresh a single platform connection token"""

        platform = connection.platform.value
        user_id = connection.user_id

        logger.info(f"🔄 Refreshing {platform} token for user {user_id}")

        try:
            # Handle case-insensitive platform comparison
            platform_enum = connection.platform
            if hasattr(platform_enum, 'value'):
                platform_value = platform_enum.value.upper()
            else:
                platform_value = str(platform_enum).upper()

            if platform_value == 'ETSY' or platform_enum == PlatformType.ETSY:
                await self._refresh_etsy_token(connection, db)
            elif platform_value == 'SHOPIFY' or platform_enum == PlatformType.SHOPIFY:
                await self._refresh_shopify_token(connection, db)
            # Add other platforms as needed
            else:
                logger.warning(f"Token refresh not implemented for platform: {platform} (enum: {platform_enum})")
                return

            self.stats['tokens_refreshed'] += 1
            logger.info(f"✅ Successfully refreshed {platform} token for user {user_id}")

        except Exception as e:
            self.stats['refresh_failures'] += 1
            logger.error(f"❌ Failed to refresh {platform} token for user {user_id}: {e}")

            # Mark connection as inactive if refresh fails repeatedly
            await self._handle_refresh_failure(connection, db)

    async def _refresh_etsy_token(self, connection: PlatformConnection, db: Session):
        """Refresh Etsy token using the existing EtsyAPI class"""

        try:
            # Create EtsyAPI instance with database session
            etsy_api = EtsyAPI(user_id=connection.user_id, db=db)

            # Check if token needs refresh
            if etsy_api.is_token_expired():
                # Perform the refresh
                etsy_api.refresh_access_token()

                # Update the platform connection with new token data
                connection.access_token = etsy_api.oauth_token
                connection.refresh_token = etsy_api.refresh_token
                connection.token_expires_at = datetime.fromtimestamp(etsy_api.token_expiry, tz=timezone.utc)
                connection.last_verified_at = datetime.now(timezone.utc)

                # Commit the changes
                db.commit()

                logger.info(f"✅ Etsy token refreshed and saved for user {connection.user_id}")
            else:
                logger.debug(f"Etsy token for user {connection.user_id} doesn't need refresh yet")

        except Exception as e:
            db.rollback()
            raise Exception(f"Etsy token refresh failed: {e}")

    async def _refresh_shopify_token(self, connection: PlatformConnection, db: Session):
        """Refresh Shopify token - placeholder for future implementation"""
        # TODO: Implement Shopify token refresh when needed
        logger.warning("Shopify token refresh not yet implemented")
        pass

    async def _handle_refresh_failure(self, connection: PlatformConnection, db: Session):
        """Handle repeated refresh failures"""

        # For now, just log the failure
        # In the future, could implement retry logic or disable connection
        logger.warning(f"Token refresh failed for {connection.platform.value} user {connection.user_id}")

        # Could add logic here to:
        # - Count consecutive failures
        # - Disable connection after N failures
        # - Send notification to user
        # - etc.

    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'refresh_interval': self.refresh_interval,
            'refresh_threshold': self.refresh_threshold
        }

# Global service instance
token_refresh_service = TokenRefreshService()

async def start_token_refresh_service():
    """Start the token refresh service as a background task"""
    await token_refresh_service.start()

def stop_token_refresh_service():
    """Stop the token refresh service"""
    token_refresh_service.stop()

def get_token_refresh_stats() -> Dict:
    """Get token refresh service statistics"""
    return token_refresh_service.get_stats()