"""Token Refresh Service - Main Entry Point.

This service runs continuously and refreshes authentication tokens
for all integrated services (Etsy, Shopify) at regular intervals.
"""
import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from database import get_db
from etsy_refresher import EtsyTokenRefresher
from shopify_refresher import ShopifyTokenRefresher

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/token-refresh.log') if os.path.exists('/var/log') else logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class TokenRefreshService:
    """Main service orchestrator for token refresh."""

    def __init__(self):
        self.refresh_interval = int(os.getenv('REFRESH_INTERVAL_MINUTES', '3')) * 60  # Convert to seconds
        self.etsy_refresher = None
        self.shopify_refresher = None

        logger.info("🚀 Token Refresh Service starting...")
        logger.info(f"⏱️  Refresh interval: {self.refresh_interval // 60} minutes")

        # Initialize refreshers
        try:
            self.etsy_refresher = EtsyTokenRefresher()
            logger.info("✅ Etsy refresher initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Etsy refresher: {e}")

        try:
            self.shopify_refresher = ShopifyTokenRefresher()
            logger.info("✅ Shopify refresher initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Shopify refresher: {e}")

        if not self.etsy_refresher and not self.shopify_refresher:
            logger.error("❌ No refreshers initialized. Exiting...")
            sys.exit(1)

    def run_refresh_cycle(self):
        """Run one complete refresh cycle for all services."""
        logger.info("=" * 80)
        logger.info(f"🔄 Starting refresh cycle at {datetime.now().isoformat()}")
        logger.info("=" * 80)

        db = None
        try:
            db = get_db()

            total_results = {
                "etsy": {"total": 0, "refreshed": 0, "validated": 0, "failed": 0, "errors": []},
                "shopify": {"total": 0, "refreshed": 0, "validated": 0, "failed": 0, "errors": []}
            }

            # Refresh Etsy tokens
            if self.etsy_refresher:
                logger.info("\n🔵 Processing Etsy tokens...")
                etsy_results = self.etsy_refresher.refresh_all_tokens(db)
                total_results["etsy"] = etsy_results

            # Validate Shopify tokens
            if self.shopify_refresher:
                logger.info("\n🟢 Processing Shopify tokens...")
                shopify_results = self.shopify_refresher.refresh_all_tokens(db)
                total_results["shopify"] = shopify_results

            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("📊 REFRESH CYCLE SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Etsy:    {total_results['etsy']['refreshed']}/{total_results['etsy']['total']} refreshed, "
                       f"{total_results['etsy']['failed']} failed")
            logger.info(f"Shopify: {total_results['shopify']['validated']}/{total_results['shopify']['total']} validated, "
                       f"{total_results['shopify']['failed']} failed")

            if total_results['etsy']['errors']:
                logger.warning(f"⚠️  Etsy errors: {len(total_results['etsy']['errors'])}")
            if total_results['shopify']['errors']:
                logger.warning(f"⚠️  Shopify errors: {len(total_results['shopify']['errors'])}")

            logger.info("=" * 80)
            logger.info(f"✅ Refresh cycle completed at {datetime.now().isoformat()}")
            logger.info("=" * 80 + "\n")

        except Exception as e:
            logger.error(f"❌ Error during refresh cycle: {e}", exc_info=True)
        finally:
            if db:
                db.close()

    def run(self):
        """Run the service continuously."""
        logger.info("🎯 Token Refresh Service is running...")
        logger.info(f"⏰ Next refresh at: {datetime.now()}")

        # Run initial refresh immediately
        self.run_refresh_cycle()

        # Continue running on schedule
        while True:
            try:
                logger.info(f"💤 Sleeping for {self.refresh_interval // 60} minutes...")
                time.sleep(self.refresh_interval)
                self.run_refresh_cycle()

            except KeyboardInterrupt:
                logger.info("\n🛑 Received shutdown signal. Stopping service...")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in main loop: {e}", exc_info=True)
                logger.info("⏱️  Waiting 60 seconds before retrying...")
                time.sleep(60)

        logger.info("👋 Token Refresh Service stopped")


def main():
    """Main entry point."""
    service = TokenRefreshService()
    service.run()


if __name__ == "__main__":
    main()
