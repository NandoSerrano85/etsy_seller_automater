#!/usr/bin/env python3
"""
Script to delete all design_images records from Railway database.

This script will:
1. Connect to the Railway database
2. Delete all records from design_images table
3. Reset the sequence/auto-increment if needed

Usage:
    python clear_design_images.py

Environment Variables Required:
    DATABASE_URL - Railway database connection string
"""

import os
import sys
import logging
from pathlib import Path

# Add server src to path
server_root = Path(__file__).parent / "server" / "src"
sys.path.insert(0, str(server_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required but not set")
    return database_url

def clear_design_images():
    """Delete all records from design_images table."""
    logger.info("🗄️  Connecting to Railway database...")

    try:
        engine = create_engine(get_database_url(), connect_args={'connect_timeout': 30})
        Session = sessionmaker(bind=engine)

        with Session() as session:
            # First, get count of existing records
            result = session.execute(text("SELECT COUNT(*) FROM design_images"))
            count = result.scalar()

            if count == 0:
                logger.info("✅ No design_images records found - table is already empty")
                return True

            logger.info(f"📊 Found {count} design_images records")
            logger.info("🗑️  Deleting all design_images records...")

            # Delete all records
            result = session.execute(text("DELETE FROM design_images"))
            deleted_count = result.rowcount

            # Commit the transaction
            session.commit()

            logger.info(f"✅ Successfully deleted {deleted_count} design_images records")

            # Verify deletion
            result = session.execute(text("SELECT COUNT(*) FROM design_images"))
            remaining_count = result.scalar()

            if remaining_count == 0:
                logger.info("✅ Verification: design_images table is now empty")
            else:
                logger.warning(f"⚠️  Warning: {remaining_count} records still remain")

            return True

    except Exception as e:
        logger.error(f"❌ Error clearing design_images: {e}")
        return False

def main():
    """Main function."""
    logger.info("🚀 Starting design_images cleanup for Railway...")
    logger.info("=" * 50)

    # Check environment
    try:
        get_database_url()
        logger.info("✅ Database connection configured")
    except ValueError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)

    # Clear design_images
    if not clear_design_images():
        logger.error("❌ Failed to clear design_images")
        sys.exit(1)

    logger.info("")
    logger.info("🎉 Design images cleanup completed successfully!")
    logger.info("=" * 50)
    logger.info("📊 Summary:")
    logger.info("   - All design_images records: ✅ Deleted")
    logger.info("   - Database cleanup: ✅ Complete")
    logger.info("")

if __name__ == "__main__":
    main()