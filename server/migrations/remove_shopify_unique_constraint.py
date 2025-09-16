"""
Remove unique constraint from shopify_stores.user_id to allow 1:many relationship

This migration removes the unique constraint on user_id in shopify_stores table
to allow one user to have multiple Shopify stores connected.
"""

import logging
from sqlalchemy import text

def upgrade(connection):
    """Remove unique constraint from shopify_stores.user_id."""
    try:
        # Check if the unique constraint exists
        result = connection.execute(text("""
            SELECT conname
            FROM pg_constraint
            WHERE conname LIKE '%user_id%'
            AND conrelid = (SELECT oid FROM pg_class WHERE relname = 'shopify_stores')
            AND contype = 'u'
        """))

        constraints = result.fetchall()

        if constraints:
            # Drop the unique constraint
            for constraint in constraints:
                constraint_name = constraint[0]
                logging.info(f"Dropping unique constraint: {constraint_name}")
                connection.execute(text(f"""
                    ALTER TABLE shopify_stores DROP CONSTRAINT IF EXISTS {constraint_name}
                """))
                logging.info(f"Successfully dropped constraint: {constraint_name}")
        else:
            logging.info("No unique constraint found on shopify_stores.user_id")

        # Also check for unique index and drop it if it exists
        result = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'shopify_stores'
            AND indexdef LIKE '%UNIQUE%'
            AND indexdef LIKE '%user_id%'
        """))

        indexes = result.fetchall()

        if indexes:
            for index in indexes:
                index_name = index[0]
                logging.info(f"Dropping unique index: {index_name}")
                connection.execute(text(f"""
                    DROP INDEX IF EXISTS {index_name}
                """))
                logging.info(f"Successfully dropped index: {index_name}")
        else:
            logging.info("No unique index found on shopify_stores.user_id")

        logging.info("Successfully completed shopify_stores unique constraint removal")

    except Exception as e:
        logging.error(f"Error removing unique constraint from shopify_stores: {e}")
        raise e

def downgrade(connection):
    """Add back unique constraint to shopify_stores.user_id (optional)."""
    try:
        # Add back the unique constraint (this might fail if there are duplicates)
        connection.execute(text("""
            ALTER TABLE shopify_stores
            ADD CONSTRAINT shopify_stores_user_id_key UNIQUE (user_id)
        """))

        logging.info("Successfully added back unique constraint to shopify_stores.user_id")

    except Exception as e:
        logging.warning(f"Could not add back unique constraint (likely due to existing duplicates): {e}")
        # Don't raise - this is expected if there are multiple stores per user