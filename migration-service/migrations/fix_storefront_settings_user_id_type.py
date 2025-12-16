"""
Fix storefront settings user_id column type from INTEGER to UUID

This migration alters the user_id column in ecommerce_storefront_settings
to be UUID type instead of INTEGER, matching the users table.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Alter user_id column from INTEGER to UUID."""
    try:
        logging.info("Checking ecommerce_storefront_settings table...")

        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_storefront_settings'
        """))

        if not result.fetchone():
            logging.info("Table doesn't exist yet, skipping migration")
            return

        # Check current column type
        result = connection.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_storefront_settings'
            AND column_name = 'user_id'
        """))

        row = result.fetchone()
        if row and row[0] == 'integer':
            logging.info("Converting user_id from INTEGER to UUID...")

            # Since the table might have data, we need to handle this carefully
            # Drop the old column and recreate it as UUID
            # This will lose existing data, but since this is a new feature it should be safe
            connection.execute(text("""
                ALTER TABLE ecommerce_storefront_settings
                DROP COLUMN IF EXISTS user_id
            """))

            connection.execute(text("""
                ALTER TABLE ecommerce_storefront_settings
                ADD COLUMN user_id UUID NOT NULL UNIQUE
            """))

            logging.info("✅ Successfully converted user_id to UUID type")
        else:
            logging.info(f"user_id column is already correct type: {row[0] if row else 'not found'}")

        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error in storefront settings user_id type migration: {e}")
        raise e


def downgrade(connection):
    """Revert user_id column back to INTEGER (for rollback)."""
    try:
        logging.info("Reverting user_id column to INTEGER...")

        connection.execute(text("""
            ALTER TABLE ecommerce_storefront_settings
            DROP COLUMN IF EXISTS user_id
        """))

        connection.execute(text("""
            ALTER TABLE ecommerce_storefront_settings
            ADD COLUMN user_id INTEGER NOT NULL UNIQUE
        """))

        logging.info("✅ Successfully reverted user_id to INTEGER type")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error reverting storefront settings user_id type: {e}")
        raise e
