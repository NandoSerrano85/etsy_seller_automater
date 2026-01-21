"""
Add user_id column to ecommerce_customers table for multi-tenant isolation

This migration adds a user_id column to ensure each user's customers are isolated.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add user_id column to ecommerce_customers table."""
    try:
        logging.info("Adding user_id column to ecommerce_customers table...")

        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_customers'
        """))

        if not result.fetchone():
            logging.info("ecommerce_customers table doesn't exist yet, skipping")
            return

        # Check if column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_customers'
            AND column_name = 'user_id'
        """))

        if result.fetchone():
            logging.info("user_id column already exists, skipping")
            return

        # Add user_id column (nullable initially for existing data)
        connection.execute(text("""
            ALTER TABLE ecommerce_customers
            ADD COLUMN user_id UUID
        """))

        # Get first user ID as default for existing customers
        result = connection.execute(text("""
            SELECT id FROM users LIMIT 1
        """))
        first_user = result.fetchone()

        if first_user:
            # Set existing customers to first user
            connection.execute(text("""
                UPDATE ecommerce_customers
                SET user_id = :user_id
                WHERE user_id IS NULL
            """), {"user_id": str(first_user[0])})
            logging.info(f"✅ Set user_id for existing customers to {first_user[0]}")

        # Make user_id NOT NULL and add index
        connection.execute(text("""
            ALTER TABLE ecommerce_customers
            ALTER COLUMN user_id SET NOT NULL
        """))

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ecommerce_customers_user_id
            ON ecommerce_customers(user_id)
        """))

        logging.info("✅ Successfully added user_id column to ecommerce_customers table")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error adding user_id column to ecommerce_customers: {e}")
        raise e


def downgrade(connection):
    """Remove user_id column from ecommerce_customers table."""
    try:
        logging.info("Removing user_id column from ecommerce_customers table...")

        # Drop index first
        connection.execute(text("""
            DROP INDEX IF EXISTS idx_ecommerce_customers_user_id
        """))

        # Drop column
        connection.execute(text("""
            ALTER TABLE ecommerce_customers
            DROP COLUMN IF EXISTS user_id
        """))

        logging.info("✅ Successfully removed user_id column from ecommerce_customers table")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error removing user_id column from ecommerce_customers: {e}")
        raise e
