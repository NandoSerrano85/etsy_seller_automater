"""
Add etsy_shop_id column to users table

This migration adds a nullable etsy_shop_id column to the users table
to store the Etsy shop ID when users connect their Etsy account.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add etsy_shop_id column to users table."""
    try:
        # Check if column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'etsy_shop_id'
        """))

        if result.fetchone():
            logging.info("etsy_shop_id column already exists in users table")
            return

        # Add the new column
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN etsy_shop_id VARCHAR;
        """))

        logging.info("Successfully added etsy_shop_id column to users table")

    except Exception as e:
        logging.error(f"Error adding etsy_shop_id column: {e}")
        raise

def downgrade(connection):
    """Remove etsy_shop_id column from users table."""
    try:
        # Remove the column
        connection.execute(text("""
            ALTER TABLE users DROP COLUMN IF EXISTS etsy_shop_id;
        """))
        
        logging.info("Successfully removed etsy_shop_id column from users table")
        
    except Exception as e:
        logging.error(f"Error removing etsy_shop_id column: {e}")
        raise

if __name__ == "__main__":
    # This can be run directly for testing
    from server.src.database.core import engine
    with engine.connect() as conn:
        with conn.begin():
            upgrade(conn)