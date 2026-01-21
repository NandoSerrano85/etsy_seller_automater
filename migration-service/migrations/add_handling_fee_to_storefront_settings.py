"""
Add handling_fee column to ecommerce_storefront_settings

This migration adds a handling_fee field that allows users to configure
an additional fee added to all shipping costs.
"""

from sqlalchemy import text


def upgrade(connection):
    """Add handling_fee column to ecommerce_storefront_settings"""

    # Check if ecommerce_storefront_settings table exists
    check_table_sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'ecommerce_storefront_settings'
        )
    """)

    result = connection.execute(check_table_sql)
    table_exists = result.fetchone()[0]

    if not table_exists:
        print("⚠️  ecommerce_storefront_settings table does not exist, skipping migration")
        return

    # Check if handling_fee column already exists
    check_column_sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'ecommerce_storefront_settings'
        AND column_name = 'handling_fee'
    """)

    result = connection.execute(check_column_sql)
    column_exists = result.fetchone()

    if column_exists:
        print("✅ handling_fee column already exists, skipping")
        return

    # Add handling_fee column
    add_column_sql = text("""
        ALTER TABLE ecommerce_storefront_settings
        ADD COLUMN handling_fee VARCHAR(10) DEFAULT '0.00'
    """)

    connection.execute(add_column_sql)
    print("✅ Added handling_fee column to ecommerce_storefront_settings")


def downgrade(connection):
    """Remove handling_fee column from ecommerce_storefront_settings"""

    # Check if column exists before dropping
    check_column_sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'ecommerce_storefront_settings'
        AND column_name = 'handling_fee'
    """)

    result = connection.execute(check_column_sql)
    column_exists = result.fetchone()

    if not column_exists:
        print("⚠️  handling_fee column does not exist, nothing to remove")
        return

    # Drop the column
    drop_column_sql = text("""
        ALTER TABLE ecommerce_storefront_settings
        DROP COLUMN handling_fee
    """)

    connection.execute(drop_column_sql)
    print("✅ Removed handling_fee column from ecommerce_storefront_settings")
