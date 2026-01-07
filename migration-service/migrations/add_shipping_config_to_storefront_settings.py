"""
Add shipping configuration columns to ecommerce_storefront_settings table.

This migration adds origin/warehouse address fields, package dimensions,
and Shippo API configuration to the storefront settings.

Columns added:
- shipping_from_* (origin address fields)
- shipping_default_* (package dimension defaults)
- shippo_api_key and shippo_test_mode
"""

from sqlalchemy import text


def upgrade(connection):
    """Add shipping configuration columns to ecommerce_storefront_settings"""

    # Check if table exists
    check_table_sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'ecommerce_storefront_settings'
        )
    """)

    result = connection.execute(check_table_sql)
    table_exists = result.fetchone()[0]

    if not table_exists:
        print("⚠️  Table ecommerce_storefront_settings does not exist, skipping migration")
        return

    # List of columns to add
    columns_to_add = [
        # Origin/Warehouse Address
        ("shipping_from_name", "VARCHAR(255)"),
        ("shipping_from_company", "VARCHAR(255)"),
        ("shipping_from_street1", "VARCHAR(255)"),
        ("shipping_from_street2", "VARCHAR(255)"),
        ("shipping_from_city", "VARCHAR(100)"),
        ("shipping_from_state", "VARCHAR(50)"),
        ("shipping_from_zip", "VARCHAR(20)"),
        ("shipping_from_country", "VARCHAR(50) DEFAULT 'US'"),
        ("shipping_from_phone", "VARCHAR(50)"),
        ("shipping_from_email", "VARCHAR(255)"),

        # Default Package Dimensions
        ("shipping_default_length", "VARCHAR(10) DEFAULT '10'"),
        ("shipping_default_width", "VARCHAR(10) DEFAULT '8'"),
        ("shipping_default_height", "VARCHAR(10) DEFAULT '4'"),
        ("shipping_default_weight", "VARCHAR(10) DEFAULT '1'"),

        # Shippo API Configuration
        ("shippo_api_key", "VARCHAR(255)"),
        ("shippo_test_mode", "VARCHAR(10) DEFAULT 'true'"),
    ]

    for column_name, column_type in columns_to_add:
        # Check if column exists
        check_column_sql = text(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_storefront_settings'
            AND column_name = '{column_name}'
        """)

        result = connection.execute(check_column_sql)
        column_exists = result.fetchone()

        if not column_exists:
            # Add column
            add_column_sql = text(f"""
                ALTER TABLE ecommerce_storefront_settings
                ADD COLUMN {column_name} {column_type}
            """)
            connection.execute(add_column_sql)
            print(f"✅ Added column: {column_name}")
        else:
            print(f"⏭️  Column {column_name} already exists, skipping")

    print("✅ Shipping configuration migration completed")


def downgrade(connection):
    """Remove shipping configuration columns from ecommerce_storefront_settings"""

    columns_to_remove = [
        "shipping_from_name",
        "shipping_from_company",
        "shipping_from_street1",
        "shipping_from_street2",
        "shipping_from_city",
        "shipping_from_state",
        "shipping_from_zip",
        "shipping_from_country",
        "shipping_from_phone",
        "shipping_from_email",
        "shipping_default_length",
        "shipping_default_width",
        "shipping_default_height",
        "shipping_default_weight",
        "shippo_api_key",
        "shippo_test_mode",
    ]

    for column_name in columns_to_remove:
        drop_column_sql = text(f"""
            ALTER TABLE ecommerce_storefront_settings
            DROP COLUMN IF EXISTS {column_name}
        """)
        connection.execute(drop_column_sql)
        print(f"✅ Removed column: {column_name}")

    print("✅ Shipping configuration downgrade completed")
