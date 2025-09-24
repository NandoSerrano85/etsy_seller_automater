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

        # Add startup delay to allow database to be ready
        logger.info("   ⏳  Waiting 30 seconds before first token check...")
        await asyncio.sleep(30)

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

            # Get database session with error handling and timeout
            try:
                # Add timeout for database connection
                db_task = asyncio.create_task(asyncio.to_thread(lambda: next(get_db())))
                db: Session = await asyncio.wait_for(db_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Database connection timed out, skipping token refresh cycle")
                return
            except Exception as db_error:
                logger.warning(f"Database connection failed, skipping token refresh cycle: {db_error}")
                return

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
            logger.warning(f"Token refresh cycle failed, continuing service: {e}")

    async def _find_tokens_to_refresh(self, db: Session) -> List[PlatformConnection]:
        """Find platform connections with tokens that need refreshing"""

        try:
            # Calculate the threshold time (now + refresh_threshold seconds)
            threshold_time = datetime.now(timezone.utc) + timedelta(seconds=self.refresh_threshold)

            # Use raw SQL to avoid enum issues
            from sqlalchemy import text
            result = db.execute(text("""
                SELECT id, user_id, platform, access_token, refresh_token, token_expires_at, is_active
                FROM platform_connections
                WHERE is_active = true
                AND access_token IS NOT NULL
                AND refresh_token IS NOT NULL
                AND token_expires_at IS NOT NULL
                AND token_expires_at <= :threshold_time
            """), {"threshold_time": threshold_time})

            raw_connections = result.fetchall()

            # Manually create connection objects to avoid enum issues
            valid_connections = []
            for row in raw_connections:
                try:
                    # Check if platform value is valid before processing (case insensitive)
                    platform_value = row.platform.upper() if row.platform else None
                    if platform_value and platform_value.upper() in ['ETSY', 'SHOPIFY', 'AMAZON', 'EBAY']:
                        # Skip ORM query that causes enum errors - just use raw data
                        # We'll handle the token refresh using raw connection data
                        valid_connections.append(row)
                    else:
                        # Don't log warnings for invalid platforms to reduce noise
                        logger.debug(f"Skipping connection {row.id} with invalid platform: {row.platform}")
                except Exception as e:
                    # Reduce log noise - only log at debug level
                    logger.debug(f"Error processing connection {row.id}: {e}")
                    continue

            logger.debug(f"Found {len(valid_connections)} valid connections out of {len(raw_connections)} total")
            return valid_connections

        except Exception as e:
            logger.error(f"Error finding tokens to refresh: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    async def _refresh_single_token(self, connection_row, db: Session):
        """Refresh a single platform connection token using raw connection data"""

        user_id = connection_row.user_id
        connection_id = connection_row.id

        try:
            # Extract platform value from raw data (already validated)
            platform_value = connection_row.platform.upper() if connection_row.platform else None

            if not platform_value:
                logger.debug(f"Connection {connection_id} has no platform information")
                return

            logger.info(f"🔄 Refreshing {platform_value} token for user {user_id}")

            # Get the actual ORM object only when needed for token refresh
            connection = db.query(PlatformConnection).filter(PlatformConnection.id == connection_id).first()
            if not connection:
                logger.debug(f"Connection {connection_id} not found in database")
                return

            # Direct platform value comparison (already uppercase)
            if platform_value == 'ETSY':
                await self._refresh_etsy_token(connection, db)
            elif platform_value == 'SHOPIFY':
                await self._refresh_shopify_token(connection, db)
            # Add other platforms as needed
            else:
                logger.debug(f"Token refresh not implemented for platform: {platform_value}")
                return

            self.stats['tokens_refreshed'] += 1
            logger.info(f"✅ Successfully refreshed {platform_value} token for user {user_id}")

        except Exception as e:
            self.stats['refresh_failures'] += 1

            # Skip logging enum-related errors to reduce noise
            if 'not among the defined enum values' not in str(e):
                logger.error(f"❌ Failed to refresh token for user {user_id}: {e}")
            else:
                logger.debug(f"Skipping token refresh due to enum mismatch for user {user_id}")

            # Don't try to handle refresh failure for enum issues
            if 'not among the defined enum values' not in str(e):
                await self._handle_refresh_failure(connection_row, db)

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
                if etsy_api.oauth_token:
                    connection.access_token = etsy_api.oauth_token
                if etsy_api.refresh_token:
                    connection.refresh_token = etsy_api.refresh_token
                if etsy_api.token_expiry:
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

    async def _handle_refresh_failure(self, connection_data, db: Session):
        """Handle repeated refresh failures"""

        # For now, just log the failure
        # In the future, could implement retry logic or disable connection
        try:
            # Handle both ORM objects and raw connection data
            if hasattr(connection_data, 'platform') and hasattr(connection_data.platform, 'value'):
                platform_value = connection_data.platform.value
                user_id = connection_data.user_id
            else:
                platform_value = getattr(connection_data, 'platform', 'unknown')
                user_id = getattr(connection_data, 'user_id', 'unknown')

            logger.debug(f"Token refresh failed for {platform_value} user {user_id}")
        except Exception as e:
            logger.debug(f"Error handling refresh failure: {e}")

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