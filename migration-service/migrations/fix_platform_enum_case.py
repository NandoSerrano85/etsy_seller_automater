"""
Migration: Fix platform enum case mismatch
Author: System Migration
Date: 2024-09-24
Purpose: Fix platformtype enum case mismatch where database contains lowercase values but enum expects uppercase

Issue: Railway production logs show repeated warnings:
'etsy' is not among the defined enum values. Enum name: platformtype. Possible values: ETSY, SHOPIFY, AMAZON, EBAY

This migration updates all platform values to uppercase to match the enum definition.
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return database_url

def run_migration(conn):
    """Run the platform enum case fix migration"""
    logger.info("Starting platform enum case fix migration")

    try:
        # Check current platform values
        logger.info("Checking current platform values...")
        result = conn.execute(text("SELECT DISTINCT platform FROM platform_connections"))
        current_values = [row[0] for row in result.fetchall()]
        logger.info(f"Current platform values: {current_values}")

        # Drop the check constraint if it exists
        logger.info("Dropping check constraint if it exists...")
        conn.execute(text("""
            ALTER TABLE platform_connections
            DROP CONSTRAINT IF EXISTS platform_connections_platform_check
        """))
        logger.info("✅ Check constraint dropped")

        # Update platform values to uppercase
        platform_mapping = {
            'etsy': 'ETSY',
            'shopify': 'SHOPIFY',
            'amazon': 'AMAZON',
            'ebay': 'EBAY'
        }

        total_updated = 0
        for lowercase_value, uppercase_value in platform_mapping.items():
            # Update records with lowercase values to uppercase
            result = conn.execute(
                text("UPDATE platform_connections SET platform = :uppercase WHERE platform = :lowercase"),
                {"uppercase": uppercase_value, "lowercase": lowercase_value}
            )
            updated_count = result.rowcount
            total_updated += updated_count

            if updated_count > 0:
                logger.info(f"Updated {updated_count} records: '{lowercase_value}' -> '{uppercase_value}'")

        # Recreate the check constraint with uppercase values
        logger.info("Recreating check constraint with uppercase values...")
        conn.execute(text("""
            ALTER TABLE platform_connections
            ADD CONSTRAINT platform_connections_platform_check
            CHECK (platform IN ('ETSY', 'SHOPIFY', 'AMAZON', 'EBAY'))
        """))
        logger.info("✅ Check constraint recreated")

        # Verify the changes
        logger.info("Verifying platform values after update...")
        result = conn.execute(text("SELECT DISTINCT platform FROM platform_connections"))
        new_values = [row[0] for row in result.fetchall()]
        logger.info(f"New platform values: {new_values}")

        logger.info(f"Migration completed successfully. Total records updated: {total_updated}")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise

def upgrade(connection):
    """Alembic upgrade function"""
    run_migration(connection)

def downgrade(connection):
    """Alembic downgrade function - convert back to lowercase"""
    logger.info("Starting platform enum case downgrade migration")

    try:
        # Drop the check constraint if it exists
        logger.info("Dropping check constraint if it exists...")
        connection.execute(text("""
            ALTER TABLE platform_connections
            DROP CONSTRAINT IF EXISTS platform_connections_platform_check
        """))
        logger.info("✅ Check constraint dropped")

        # Update platform values back to lowercase
        platform_mapping = {
            'ETSY': 'etsy',
            'SHOPIFY': 'shopify',
            'AMAZON': 'amazon',
            'EBAY': 'ebay'
        }

        total_updated = 0
        for uppercase_value, lowercase_value in platform_mapping.items():
            result = connection.execute(
                text("UPDATE platform_connections SET platform = :lowercase WHERE platform = :uppercase"),
                {"lowercase": lowercase_value, "uppercase": uppercase_value}
            )
            updated_count = result.rowcount
            total_updated += updated_count

            if updated_count > 0:
                logger.info(f"Downgraded {updated_count} records: '{uppercase_value}' -> '{lowercase_value}'")

        # Recreate the check constraint with lowercase values
        logger.info("Recreating check constraint with lowercase values...")
        connection.execute(text("""
            ALTER TABLE platform_connections
            ADD CONSTRAINT platform_connections_platform_check
            CHECK (platform IN ('etsy', 'shopify', 'amazon', 'ebay'))
        """))
        logger.info("✅ Check constraint recreated")

        logger.info(f"Downgrade completed successfully. Total records updated: {total_updated}")

    except Exception as e:
        logger.error(f"Downgrade failed: {e}")
        raise

if __name__ == "__main__":
    # Allow running this migration directly
    from sqlalchemy import create_engine
    database_url = get_database_url()
    engine = create_engine(database_url)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            run_migration(conn)
            trans.commit()
        except Exception:
            trans.rollback()
            raise