"""
Add updated_at column to ecommerce_customer_addresses table

This migration adds the missing updated_at column to match the CustomerAddress entity.
"""

from sqlalchemy import text
import logging


def upgrade(connection):
    """Add updated_at column to ecommerce_customer_addresses."""
    try:
        logging.info("Checking ecommerce_customer_addresses table for updated_at column...")

        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_customer_addresses'
        """))

        if not result.fetchone():
            logging.info("Table doesn't exist yet, skipping migration")
            return

        # Check if updated_at column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_customer_addresses'
            AND column_name = 'updated_at'
        """))

        if result.fetchone():
            logging.info("updated_at column already exists, skipping")
            return

        # Add updated_at column
        logging.info("Adding updated_at column to ecommerce_customer_addresses...")
        connection.execute(text("""
            ALTER TABLE ecommerce_customer_addresses
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        """))

        logging.info("✅ Successfully added updated_at column to ecommerce_customer_addresses")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error adding updated_at column to customer addresses: {e}")
        raise e


def downgrade(connection):
    """Remove updated_at column from ecommerce_customer_addresses."""
    try:
        logging.info("Removing updated_at column from ecommerce_customer_addresses...")

        connection.execute(text("""
            ALTER TABLE ecommerce_customer_addresses
            DROP COLUMN IF EXISTS updated_at
        """))

        logging.info("✅ Successfully removed updated_at column from ecommerce_customer_addresses")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error removing updated_at column: {e}")
        raise e
