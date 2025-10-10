"""Etsy token refresh logic."""
import os
import logging
import requests
import base64
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database import PlatformConnection, PlatformType

logger = logging.getLogger(__name__)


class EtsyTokenRefresher:
    """Handles Etsy OAuth token refresh."""

    def __init__(self):
        self.client_id = os.getenv('ETSY_CLIENT_ID')
        self.client_secret = os.getenv('ETSY_CLIENT_SECRET')
        self.token_url = "https://api.etsy.com/v3/public/oauth/token"

        if not self.client_id or not self.client_secret:
            raise ValueError("ETSY_CLIENT_ID and ETSY_CLIENT_SECRET are required")

    def refresh_all_tokens(self, db: Session) -> dict:
        """
        Refresh tokens for all Etsy platform connections that are expiring soon or expired.

        Returns:
            dict: Summary of refresh attempts
        """
        logger.info("🔄 Starting Etsy token refresh...")

        # Get connections whose tokens expire within the next 10 minutes or are already expired
        expiry_threshold = datetime.now(timezone.utc) + timedelta(minutes=10)

        # First, check all Etsy connections for debugging
        all_etsy_connections = db.query(PlatformConnection).filter(
            PlatformConnection.platform == PlatformType.ETSY,
            PlatformConnection.is_active == True
        ).all()

        logger.info(f"Found {len(all_etsy_connections)} total active Etsy connections")

        for conn in all_etsy_connections:
            if conn.token_expires_at:
                time_until_expiry = conn.token_expires_at - datetime.now(timezone.utc)
                logger.info(f"  Connection {conn.id}: expires in {time_until_expiry}")
            else:
                logger.info(f"  Connection {conn.id}: no expiration set")

        connections = db.query(PlatformConnection).filter(
            PlatformConnection.platform == PlatformType.ETSY,
            PlatformConnection.is_active == True,
            PlatformConnection.token_expires_at <= expiry_threshold
        ).all()

        if not connections:
            logger.info("No Etsy tokens need refreshing (all tokens valid for >10 minutes)")
            return {"total": 0, "refreshed": 0, "failed": 0, "errors": []}

        logger.info(f"Found {len(connections)} Etsy connections with expiring/expired tokens")

        results = {
            "total": len(connections),
            "refreshed": 0,
            "failed": 0,
            "errors": []
        }

        for connection in connections:
            try:
                new_tokens = self._refresh_token(connection.refresh_token)

                if new_tokens:
                    # Update connection with new tokens
                    connection.access_token = new_tokens['access_token']
                    connection.refresh_token = new_tokens['refresh_token']
                    connection.token_expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=new_tokens['expires_in']
                    )
                    connection.last_verified_at = datetime.now(timezone.utc)

                    db.commit()
                    results["refreshed"] += 1
                    logger.info(f"✅ Refreshed token for Etsy connection: {connection.id}")
                else:
                    results["failed"] += 1
                    logger.error(f"❌ Failed to refresh token for Etsy connection: {connection.id}")

            except Exception as e:
                error_msg = f"Error refreshing token for Etsy connection {connection.id}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results["failed"] += 1
                results["errors"].append(error_msg)
                db.rollback()

        logger.info(f"✅ Etsy refresh complete: {results['refreshed']} refreshed, {results['failed']} failed")
        return results

    def _refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh an Etsy access token using the refresh token.

        Args:
            refresh_token: Current refresh token

        Returns:
            dict: New token data with access_token, refresh_token, and expires_in
        """
        # Create Basic Auth header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        try:
            logger.info(f"🔄 Requesting new Etsy token...")
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                logger.info("✅ Successfully obtained new Etsy token")
                return token_data
            else:
                logger.error(f"❌ Etsy token refresh failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error during Etsy token refresh: {e}")
            return None
