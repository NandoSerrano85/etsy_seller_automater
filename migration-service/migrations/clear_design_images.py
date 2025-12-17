#!/usr/bin/env python3
"""
Clear all design images from the database.
Use this to reset before re-importing designs.
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Handle Railway's postgres:// vs postgresql:// URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return database_url


def clear_design_images():
    """Clear all design images and related associations."""
    database_url = get_database_url()
    engine = create_engine(database_url)

    with engine.connect() as connection:
        try:
            logger.info("🗑️  Starting to clear design_images table...")

            # Start transaction
            trans = connection.begin()

            # Get count before deletion
            result = connection.execute(text("SELECT COUNT(*) FROM design_images"))
            design_count = result.fetchone()[0]

            result = connection.execute(text("SELECT COUNT(*) FROM design_template_association"))
            association_count = result.fetchone()[0]

            logger.info(f"📊 Found {design_count} designs and {association_count} template associations")

            if design_count == 0:
                logger.info("✅ Tables are already empty")
                trans.rollback()
                return

            # Confirm deletion
            print(f"\n⚠️  WARNING: This will delete {design_count} design(s)")
            response = input("Are you sure you want to continue? (yes/no): ")

            if response.lower() != 'yes':
                logger.info("❌ Operation cancelled by user")
                trans.rollback()
                return

            # Delete from junction table first (foreign key constraint)
            logger.info("🗑️  Deleting design-template associations...")
            connection.execute(text("DELETE FROM design_template_association"))

            # Delete from design_images
            logger.info("🗑️  Deleting design images...")
            connection.execute(text("DELETE FROM design_images"))

            # Commit transaction
            trans.commit()

            # Verify deletion
            result = connection.execute(text("SELECT COUNT(*) FROM design_images"))
            remaining = result.fetchone()[0]

            if remaining == 0:
                logger.info(f"✅ Successfully deleted {design_count} design(s)")
            else:
                logger.error(f"⚠️  Warning: {remaining} design(s) still remain")

        except Exception as e:
            logger.error(f"❌ Error clearing design_images: {e}")
            trans.rollback()
            raise


def upgrade(connection):
    """Main upgrade function."""
    clear_design_images()

def downgrade(connection):
    """This migration cannot be downgraded."""
    pass


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'upgrade':
        upgrade()
    else:
        print("Usage: python clear_design_images.py upgrade")
        sys.exit(1)
