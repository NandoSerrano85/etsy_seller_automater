#!/usr/bin/env python3
"""
Quick script to run just the additional hash columns migration

This script adds the missing ahash, dhash, and whash columns to the design_images table.

Usage:
    DATABASE_URL="postgresql://..." python run_hash_columns_migration.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the additional hash columns migration"""

    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        # Create database engine
        engine = create_engine(database_url)
        logger.info("✅ Connected to database")

        # Import and run the migration
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'migrations'))
        import add_additional_hash_columns

        with engine.connect() as conn:
            trans = conn.begin()
            try:
                logger.info("🔄 Running additional hash columns migration...")
                add_additional_hash_columns.upgrade(conn)
                trans.commit()
                logger.info("✅ Migration completed successfully!")

                # Verify the columns were added
                result = conn.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'design_images'
                    AND column_name IN ('phash', 'ahash', 'dhash', 'whash')
                    ORDER BY column_name;
                """)

                columns = [row[0] for row in result.fetchall()]
                logger.info(f"Hash columns now in design_images table: {', '.join(columns)}")

                if len(columns) == 4:
                    logger.info("🎉 All hash columns are now available!")
                else:
                    logger.warning(f"⚠️  Expected 4 hash columns, found {len(columns)}")

            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Migration failed: {e}")
                raise

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()