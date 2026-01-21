"""
Fix platform_connections check constraint to accept both cases

This migration updates the check constraint to accept both lowercase and uppercase
platform values to prevent insert failures during migration.
"""

from sqlalchemy import text
import logging


def upgrade(connection):
    """Fix the check constraint to accept both cases."""
    try:
        logging.info("Fixing platform_connections check constraint to accept both cases...")

        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'platform_connections'
        """))

        if not result.fetchone():
            logging.info("platform_connections table doesn't exist yet, skipping")
            return

        # Drop the existing constraint
        logging.info("Dropping existing check constraint...")
        connection.execute(text("""
            ALTER TABLE platform_connections
            DROP CONSTRAINT IF EXISTS platform_connections_platform_check
        """))

        # Recreate constraint accepting both cases
        logging.info("Creating new check constraint accepting both cases...")
        connection.execute(text("""
            ALTER TABLE platform_connections
            ADD CONSTRAINT platform_connections_platform_check
            CHECK (platform IN ('etsy', 'shopify', 'amazon', 'ebay', 'ETSY', 'SHOPIFY', 'AMAZON', 'EBAY'))
        """))

        logging.info("✅ Successfully updated platform_connections check constraint")

    except Exception as e:
        logging.error(f"Error fixing platform constraint: {e}")
        raise e


def downgrade(connection):
    """Revert to uppercase-only constraint."""
    try:
        logging.info("Reverting to uppercase-only constraint...")

        connection.execute(text("""
            ALTER TABLE platform_connections
            DROP CONSTRAINT IF EXISTS platform_connections_platform_check
        """))

        connection.execute(text("""
            ALTER TABLE platform_connections
            ADD CONSTRAINT platform_connections_platform_check
            CHECK (platform IN ('ETSY', 'SHOPIFY', 'AMAZON', 'EBAY'))
        """))

        logging.info("✅ Reverted to uppercase-only constraint")

    except Exception as e:
        logging.error(f"Error reverting constraint: {e}")
        raise e
