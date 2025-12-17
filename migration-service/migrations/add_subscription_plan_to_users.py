"""
Add subscription_plan column to users table

This migration adds a subscription_plan column to track user subscription tiers.
Plans: 'free', 'basic', 'pro', 'enterprise'
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add subscription_plan column to users table."""
    try:
        logging.info("Adding subscription_plan column to users table...")

        # Check if column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name = 'subscription_plan'
        """))

        if result.fetchone():
            logging.info("subscription_plan column already exists, skipping")
            return

        # Add subscription_plan column with default 'free'
        connection.execute(text("""
            ALTER TABLE users
            ADD COLUMN subscription_plan VARCHAR(50) NOT NULL DEFAULT 'free'
        """))

        logging.info("✅ Successfully added subscription_plan column to users table")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error adding subscription_plan column: {e}")
        raise e


def downgrade(connection):
    """Remove subscription_plan column from users table."""
    try:
        logging.info("Removing subscription_plan column from users table...")

        connection.execute(text("""
            ALTER TABLE users
            DROP COLUMN IF EXISTS subscription_plan
        """))

        logging.info("✅ Successfully removed subscription_plan column from users table")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error removing subscription_plan column: {e}")
        raise e
