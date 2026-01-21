"""
Remove updated_at column from ecommerce_order_items table

This migration removes the updated_at column from order items if it exists.
The database schema doesn't include this column, but the SQLAlchemy model
previously had it, which could cause issues during order creation.

Date: 2026-01-07
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade(connection):
    """
    Remove updated_at column from ecommerce_order_items if it exists
    """
    try:
        # Check if the column exists
        check_column_sql = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_order_items'
            AND column_name = 'updated_at'
        """)

        result = connection.execute(check_column_sql)
        column_exists = result.fetchone() is not None

        if column_exists:
            logger.info("🔄 Removing updated_at column from ecommerce_order_items table")

            # Drop the column
            drop_column_sql = text("""
                ALTER TABLE ecommerce_order_items
                DROP COLUMN IF EXISTS updated_at
            """)

            connection.execute(drop_column_sql)
            logger.info("✅ Successfully removed updated_at column from ecommerce_order_items")
        else:
            logger.info("ℹ️  Column updated_at does not exist in ecommerce_order_items, skipping")

    except Exception as e:
        logger.error(f"❌ Error in remove_updated_at_from_order_items migration: {e}")
        raise


def downgrade(connection):
    """
    Add back the updated_at column (if needed for rollback)
    """
    try:
        # Check if the column exists
        check_column_sql = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_order_items'
            AND column_name = 'updated_at'
        """)

        result = connection.execute(check_column_sql)
        column_exists = result.fetchone() is not None

        if not column_exists:
            logger.info("🔄 Adding back updated_at column to ecommerce_order_items table")

            # Add the column back
            add_column_sql = text("""
                ALTER TABLE ecommerce_order_items
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)

            connection.execute(add_column_sql)
            logger.info("✅ Successfully added back updated_at column to ecommerce_order_items")
        else:
            logger.info("ℹ️  Column updated_at already exists in ecommerce_order_items, skipping")

    except Exception as e:
        logger.error(f"❌ Error in remove_updated_at_from_order_items downgrade: {e}")
        raise
