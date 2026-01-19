"""
Link guest orders to registered customers by email

When customers place orders as guests and later register an account,
this migration links those orders to their customer account by matching
the guest_email with the customer's email address.
"""

from sqlalchemy import text
import logging


def upgrade(connection):
    """Link guest orders to matching customer accounts."""
    try:
        logging.info("Checking for guest orders that can be linked to customers...")

        # First, count how many orders need linking
        result = connection.execute(text("""
            SELECT COUNT(*) as count
            FROM ecommerce_orders o
            JOIN ecommerce_customers c ON LOWER(o.guest_email) = LOWER(c.email)
            WHERE o.customer_id IS NULL
              AND o.guest_email IS NOT NULL
        """))
        row = result.fetchone()
        count = row[0] if row else 0

        if count == 0:
            logging.info("No guest orders found that need linking to customers")
            return

        logging.info(f"Found {count} guest orders to link to customer accounts")

        # Update orders to link them to customers
        connection.execute(text("""
            UPDATE ecommerce_orders o
            SET customer_id = c.id
            FROM ecommerce_customers c
            WHERE LOWER(o.guest_email) = LOWER(c.email)
              AND o.customer_id IS NULL
              AND o.guest_email IS NOT NULL
        """))

        logging.info(f"Successfully linked {count} guest orders to customer accounts")

    except Exception as e:
        logging.error(f"Error linking guest orders to customers: {e}")
        raise e


def downgrade(connection):
    """
    Cannot safely downgrade this migration as we don't track
    which orders were originally guest orders vs customer orders.
    """
    logging.warning("Downgrade not supported for this migration - order links will remain")
