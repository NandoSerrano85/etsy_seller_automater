"""
Add user_id column to ecommerce_products table for multi-tenant isolation

This migration adds a user_id column to ensure each user's products are isolated.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add user_id column to ecommerce_products table."""
    try:
        logging.info("Adding user_id column to ecommerce_products table...")

        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_products'
        """))

        if not result.fetchone():
            logging.info("ecommerce_products table doesn't exist yet, skipping")
            return

        # Check if column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_products'
            AND column_name = 'user_id'
        """))

        if result.fetchone():
            logging.info("user_id column already exists, skipping")
            return

        # Add user_id column (nullable initially for existing data)
        connection.execute(text("""
            ALTER TABLE ecommerce_products
            ADD COLUMN user_id UUID
        """))

        # Get first user ID as default for existing products
        result = connection.execute(text("""
            SELECT id FROM users LIMIT 1
        """))
        first_user = result.fetchone()

        if first_user:
            # Set existing products to first user
            connection.execute(text("""
                UPDATE ecommerce_products
                SET user_id = :user_id
                WHERE user_id IS NULL
            """), {"user_id": str(first_user[0])})
            logging.info(f"✅ Set user_id for existing products to {first_user[0]}")

        # Make user_id NOT NULL and add index
        connection.execute(text("""
            ALTER TABLE ecommerce_products
            ALTER COLUMN user_id SET NOT NULL
        """))

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ecommerce_products_user_id
            ON ecommerce_products(user_id)
        """))

        logging.info("✅ Successfully added user_id column to ecommerce_products table")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error adding user_id column to ecommerce_products: {e}")
        raise e


def downgrade(connection):
    """Remove user_id column from ecommerce_products table."""
    try:
        logging.info("Removing user_id column from ecommerce_products table...")

        # Drop index first
        connection.execute(text("""
            DROP INDEX IF EXISTS idx_ecommerce_products_user_id
        """))

        # Drop column
        connection.execute(text("""
            ALTER TABLE ecommerce_products
            DROP COLUMN IF EXISTS user_id
        """))

        logging.info("✅ Successfully removed user_id column from ecommerce_products table")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error removing user_id column from ecommerce_products: {e}")
        raise e
