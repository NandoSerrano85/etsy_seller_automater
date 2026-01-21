"""
OAuth Token Refresh Service

Handles automatic token refresh for all OAuth 2.0 platform connections.
Monitors token expiry and refreshes tokens before they expire.
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from server.src.database.core import SessionLocal
from server.src.entities.platform_connection import PlatformConnection, PlatformType, ConnectionType
from server.src.entities.shopify_store import ShopifyStore
from server.src.entities.etsy_store import EtsyStore

logger = logging.getLogger(__name__)


class OAuthTokenRefreshService:
    """Service to manage OAuth token refresh across all platforms"""

    def __init__(self):
        self.refresh_interval = 60  # Check every 60 seconds
        self.refresh_threshold = 300  # Refresh tokens expiring within 5 minutes
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the token refresh service"""
        if self.is_running:
            logger.warning("Token refresh service is already running")
            return

        self.is_running = True
        logger.info("🔄 Starting OAuth token refresh service...")
        logger.info(f"   ⏰ Check interval: {self.refresh_interval} seconds")
        logger.info(f"   ⏳ Refresh threshold: {self.refresh_threshold} seconds")

        self._task = asyncio.create_task(self._run_refresh_loop())
        logger.info("✅ OAuth token refresh service started")

    async def stop(self):
        """Stop the token refresh service"""
        if not self.is_running:
            return

        logger.info("⏹️  Stopping OAuth token refresh service...")
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("✅ OAuth token refresh service stopped")

    async def _run_refresh_loop(self):
        """Main loop that checks and refreshes tokens"""
        logger.info("🔁 Token refresh loop started")

        while self.is_running:
            try:
                await self._check_and_refresh_tokens()
            except Exception as e:
                logger.error(f"❌ Error in token refresh loop: {e}", exc_info=True)

            # Wait for next interval
            await asyncio.sleep(self.refresh_interval)

    async def _check_and_refresh_tokens(self):
        """Check all OAuth connections and refresh tokens that are expiring soon"""
        db = SessionLocal()
        try:
            # Get all active OAuth2 connections
            connections = db.query(PlatformConnection).filter(
                and_(
                    PlatformConnection.is_active == True,
                    PlatformConnection.connection_type == ConnectionType.OAUTH2,
                    PlatformConnection.token_expires_at.isnot(None)
                )
            ).all()

            if not connections:
                logger.debug("No OAuth connections found to check")
                return

            logger.debug(f"🔍 Checking {len(connections)} OAuth connections for token refresh")

            refresh_count = 0
            for connection in connections:
                if connection.needs_token_refresh(self.refresh_threshold):
                    logger.info(
                        f"🔄 Token needs refresh for {connection.platform.value} "
                        f"(user_id: {connection.user_id}, expires at: {connection.token_expires_at})"
                    )

                    try:
                        await self._refresh_connection_token(connection, db)
                        refresh_count += 1
                    except Exception as e:
                        logger.error(
                            f"❌ Failed to refresh token for {connection.platform.value} "
                            f"(user_id: {connection.user_id}): {e}",
                            exc_info=True
                        )

            if refresh_count > 0:
                logger.info(f"✅ Successfully refreshed {refresh_count} token(s)")

        except Exception as e:
            logger.error(f"❌ Error checking tokens: {e}", exc_info=True)
        finally:
            db.close()

    async def _refresh_connection_token(self, connection: PlatformConnection, db: Session):
        """Refresh token for a specific platform connection"""
        if connection.platform == PlatformType.ETSY:
            await self._refresh_etsy_token(connection, db)
        elif connection.platform == PlatformType.SHOPIFY:
            await self._refresh_shopify_token(connection, db)
        else:
            logger.warning(f"Token refresh not implemented for platform: {connection.platform.value}")

    async def _refresh_etsy_token(self, connection: PlatformConnection, db: Session):
        """Refresh Etsy OAuth token"""
        import os
        import requests
        import base64

        if not connection.refresh_token:
            logger.error(f"No refresh token available for Etsy connection {connection.id}")
            connection.is_active = False
            db.commit()
            return

        try:
            # Etsy OAuth2 token refresh
            client_id = os.getenv('ETSY_API_KEY')
            client_secret = os.getenv('ETSY_API_SECRET')

            if not client_id or not client_secret:
                logger.error("Etsy API credentials not configured")
                return

            # Create Basic Auth header
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            token_url = "https://api.etsy.com/v3/public/oauth/token"
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = {
                "grant_type": "refresh_token",
                "refresh_token": connection.refresh_token,
            }

            logger.info(f"🔄 Refreshing Etsy token for user {connection.user_id}")
            response = requests.post(token_url, headers=headers, data=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()

                # Update connection with new tokens
                connection.access_token = token_data['access_token']
                connection.refresh_token = token_data.get('refresh_token', connection.refresh_token)
                connection.token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=token_data['expires_in']
                )
                connection.last_verified_at = datetime.now(timezone.utc)

                db.commit()

                logger.info(
                    f"✅ Successfully refreshed Etsy token for user {connection.user_id}, "
                    f"expires at {connection.token_expires_at}"
                )
            else:
                logger.error(
                    f"❌ Failed to refresh Etsy token: {response.status_code} - {response.text}"
                )
                if response.status_code in [400, 401]:
                    # Invalid refresh token - mark connection as inactive
                    connection.is_active = False
                    db.commit()
                    logger.warning(f"⚠️  Marked Etsy connection {connection.id} as inactive due to invalid token")

        except Exception as e:
            logger.error(f"❌ Error refreshing Etsy token: {e}", exc_info=True)
            raise

    async def _refresh_shopify_token(self, connection: PlatformConnection, db: Session):
        """
        Shopify OAuth tokens don't expire by default, but can be revoked.
        This checks if the token is still valid.
        """
        try:
            # Get the associated Shopify store
            store = db.query(ShopifyStore).filter(
                ShopifyStore.connection_id == connection.id
            ).first()

            if not store:
                logger.warning(f"No Shopify store found for connection {connection.id}")
                return

            # Shopify tokens are long-lived and don't typically need refresh
            # Just verify the token is still valid
            import requests

            shop_url = f"https://{store.shop_domain}/admin/api/2024-01/shop.json"
            headers = {
                "X-Shopify-Access-Token": connection.access_token,
            }

            logger.info(f"🔍 Verifying Shopify token for store {store.shop_name}")
            response = requests.get(shop_url, headers=headers, timeout=10)

            if response.status_code == 200:
                # Token is still valid
                connection.last_verified_at = datetime.now(timezone.utc)
                # Shopify tokens don't expire, set expiry far in the future
                connection.token_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
                db.commit()
                logger.info(f"✅ Shopify token verified for store {store.shop_name}")
            elif response.status_code in [401, 403]:
                # Token is invalid
                logger.error(f"❌ Shopify token is invalid for store {store.shop_name}")
                connection.is_active = False
                store.is_active = False
                db.commit()
                logger.warning(f"⚠️  Marked Shopify connection {connection.id} as inactive")
            else:
                logger.warning(f"⚠️  Unexpected response verifying Shopify token: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Error verifying Shopify token: {e}", exc_info=True)
            raise

    async def refresh_token_for_user(
        self,
        user_id: str,
        platform: PlatformType,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Manually refresh token for a specific user and platform.
        Returns the new token data if successful.
        """
        try:
            connection = db.query(PlatformConnection).filter(
                and_(
                    PlatformConnection.user_id == user_id,
                    PlatformConnection.platform == platform,
                    PlatformConnection.is_active == True
                )
            ).first()

            if not connection:
                logger.warning(f"No active connection found for user {user_id} on {platform.value}")
                return None

            await self._refresh_connection_token(connection, db)

            return {
                "access_token": connection.access_token,
                "refresh_token": connection.refresh_token,
                "expires_at": connection.token_expires_at.isoformat() if connection.token_expires_at else None,
                "platform": connection.platform.value,
            }

        except Exception as e:
            logger.error(f"❌ Error manually refreshing token: {e}", exc_info=True)
            return None

    def get_token_info(self, user_id: str, platform: PlatformType, db: Session) -> Optional[Dict[str, Any]]:
        """Get token information for a user and platform"""
        try:
            connection = db.query(PlatformConnection).filter(
                and_(
                    PlatformConnection.user_id == user_id,
                    PlatformConnection.platform == platform,
                    PlatformConnection.is_active == True
                )
            ).first()

            if not connection:
                return None

            return {
                "access_token": connection.access_token,
                "refresh_token": connection.refresh_token,
                "expires_at": connection.token_expires_at.isoformat() if connection.token_expires_at else None,
                "is_expired": connection.is_token_expired(),
                "needs_refresh": connection.needs_token_refresh(self.refresh_threshold),
                "time_until_expiry": str(connection.time_until_expiry()),
                "platform": connection.platform.value,
                "last_verified_at": connection.last_verified_at.isoformat() if connection.last_verified_at else None,
            }

        except Exception as e:
            logger.error(f"❌ Error getting token info: {e}", exc_info=True)
            return None


# Global service instance
oauth_refresh_service = OAuthTokenRefreshService()


async def start_oauth_refresh_service():
    """Start the global OAuth refresh service"""
    await oauth_refresh_service.start()


async def stop_oauth_refresh_service():
    """Stop the global OAuth refresh service"""
    await oauth_refresh_service.stop()


def get_oauth_refresh_service() -> OAuthTokenRefreshService:
    """Get the global OAuth refresh service instance"""
    return oauth_refresh_service
