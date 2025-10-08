"""Shopify token refresh logic."""
import os
import logging
import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database import ShopifyStore, PlatformConnection, PlatformType

logger = logging.getLogger(__name__)


class ShopifyTokenRefresher:
    """Handles Shopify access token validation."""

    def __init__(self):
        self.api_key = os.getenv('SHOPIFY_API_KEY')
        self.api_secret = os.getenv('SHOPIFY_API_SECRET')

        if not self.api_key or not self.api_secret:
            raise ValueError("SHOPIFY_API_KEY and SHOPIFY_API_SECRET are required")

    def refresh_all_tokens(self, db: Session) -> dict:
        """
        Validate tokens for all active Shopify stores and connections.

        Note: Shopify access tokens don't expire by default. They only become
        invalid if the app is uninstalled or permissions are revoked.
        We'll validate tokens instead of refreshing them.

        Returns:
            dict: Summary of validation attempts
        """
        logger.info("🔄 Starting Shopify token validation...")

        results = {
            "total": 0,
            "validated": 0,
            "failed": 0,
            "errors": []
        }

        # Validate new platform connections
        connections = db.query(PlatformConnection).filter(
            PlatformConnection.platform == PlatformType.SHOPIFY,
            PlatformConnection.is_active == True
        ).all()

        # Validate legacy stores (those without connection_id or with access_token)
        legacy_stores = db.query(ShopifyStore).filter(
            ShopifyStore.is_active == True,
            ShopifyStore.access_token.isnot(None)
        ).all()

        total_items = len(connections) + len(legacy_stores)

        if total_items == 0:
            logger.info("No active Shopify connections found")
            return results

        logger.info(f"Found {len(connections)} Shopify connections and {len(legacy_stores)} legacy stores to validate")
        results["total"] = total_items

        # Validate platform connections
        for connection in connections:
            try:
                # Get the store associated with this connection
                store = db.query(ShopifyStore).filter(
                    ShopifyStore.connection_id == connection.id
                ).first()

                if not store:
                    logger.warning(f"⚠️ No store found for connection {connection.id}")
                    continue

                if self._validate_connection(connection, store):
                    results["validated"] += 1
                    connection.last_verified_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info(f"✅ Token valid for store: {store.shop_name}")
                else:
                    results["failed"] += 1
                    logger.warning(f"⚠️ Token invalid for store: {store.shop_name}")
                    connection.is_active = False
                    store.is_active = False
                    db.commit()

            except Exception as e:
                error_msg = f"Error validating connection {connection.id}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results["failed"] += 1
                results["errors"].append(error_msg)

        # Validate legacy stores
        for store in legacy_stores:
            try:
                if self._validate_legacy_store(store):
                    results["validated"] += 1
                    logger.info(f"✅ Token valid for legacy store: {store.shop_name}")
                else:
                    results["failed"] += 1
                    logger.warning(f"⚠️ Token invalid for legacy store: {store.shop_name}")
                    store.is_active = False
                    db.commit()

            except Exception as e:
                error_msg = f"Error validating legacy store {store.shop_name}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results["failed"] += 1
                results["errors"].append(error_msg)

        logger.info(f"✅ Shopify validation complete: {results['validated']} valid, {results['failed']} failed")
        return results

    def _validate_connection(self, connection: PlatformConnection, store: ShopifyStore) -> bool:
        """
        Validate a Shopify access token from a platform connection.

        Args:
            connection: PlatformConnection instance
            store: ShopifyStore instance

        Returns:
            bool: True if token is valid, False otherwise
        """
        url = f"https://{store.shop_domain}/admin/api/2024-01/shop.json"
        headers = {
            "X-Shopify-Access-Token": connection.access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                logger.warning(f"Token expired/invalid for {store.shop_name}")
                return False
            else:
                logger.warning(f"Unexpected status {response.status_code} for {store.shop_name}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error validating token for {store.shop_name}: {e}")
            # Don't mark as invalid on network errors
            return True

    def _validate_legacy_store(self, store: ShopifyStore) -> bool:
        """
        Validate a Shopify access token by making a simple API call.

        Args:
            store: ShopifyStore instance

        Returns:
            bool: True if token is valid, False otherwise
        """
        url = f"https://{store.shop_domain}/admin/api/2024-01/shop.json"
        headers = {
            "X-Shopify-Access-Token": store.access_token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                logger.warning(f"Token expired/invalid for {store.shop_name}")
                return False
            else:
                logger.warning(f"Unexpected status {response.status_code} for {store.shop_name}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error validating token for {store.shop_name}: {e}")
            # Don't mark as invalid on network errors
            return True
