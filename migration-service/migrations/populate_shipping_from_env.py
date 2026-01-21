"""
Populate shipping configuration from environment variables (optional migration).

This migration reads Shippo environment variables and populates the first user's
storefront settings. This helps transition from environment-only to hybrid approach.

This migration is OPTIONAL and can be disabled by setting:
POPULATE_SHIPPING_FROM_ENV=false

Run this migration AFTER add_shipping_config_to_storefront_settings.
"""

import os
from sqlalchemy import text


def upgrade(connection):
    """Populate shipping settings from environment variables"""

    # Check if this migration should run
    should_populate = os.getenv('POPULATE_SHIPPING_FROM_ENV', 'true').lower() == 'true'

    if not should_populate:
        print("⏭️  POPULATE_SHIPPING_FROM_ENV=false, skipping shipping population")
        return

    # Check if storefront settings table exists
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

    # Get the first user's storefront settings (or any settings)
    check_settings_sql = text("""
        SELECT id, shipping_from_street1, shippo_api_key
        FROM ecommerce_storefront_settings
        ORDER BY id ASC
        LIMIT 1
    """)

    result = connection.execute(check_settings_sql)
    settings_row = result.fetchone()

    if not settings_row:
        print("ℹ️  No storefront settings found. Please create storefront settings first.")
        print("   This migration will populate settings once they exist.")
        return

    settings_id = settings_row[0]
    existing_address = settings_row[1]
    existing_api_key = settings_row[2]

    # Check if settings are already populated
    if existing_address or existing_api_key:
        print("⏭️  Shipping settings already configured in database, skipping population")
        print(f"   Settings ID: {settings_id}")
        return

    # Read environment variables
    env_values = {
        'shipping_from_name': os.getenv('SHIPPO_FROM_NAME', ''),
        'shipping_from_company': os.getenv('SHIPPO_FROM_COMPANY', ''),
        'shipping_from_street1': os.getenv('SHIPPO_FROM_STREET1', ''),
        'shipping_from_street2': os.getenv('SHIPPO_FROM_STREET2', ''),
        'shipping_from_city': os.getenv('SHIPPO_FROM_CITY', ''),
        'shipping_from_state': os.getenv('SHIPPO_FROM_STATE', ''),
        'shipping_from_zip': os.getenv('SHIPPO_FROM_ZIP', ''),
        'shipping_from_country': os.getenv('SHIPPO_FROM_COUNTRY', 'US'),
        'shipping_from_phone': os.getenv('SHIPPO_FROM_PHONE', ''),
        'shipping_from_email': os.getenv('SHIPPO_FROM_EMAIL', ''),
        'shipping_default_length': os.getenv('SHIPPO_DEFAULT_LENGTH', '10'),
        'shipping_default_width': os.getenv('SHIPPO_DEFAULT_WIDTH', '8'),
        'shipping_default_height': os.getenv('SHIPPO_DEFAULT_HEIGHT', '4'),
        'shipping_default_weight': os.getenv('SHIPPO_DEFAULT_WEIGHT', '1'),
        'shippo_api_key': os.getenv('SHIPPO_API_KEY', ''),
        'shippo_test_mode': os.getenv('SHIPPO_TEST_MODE', 'true'),
    }

    # Count how many non-empty values we have
    non_empty_count = sum(1 for v in env_values.values() if v)

    if non_empty_count == 0:
        print("ℹ️  No Shippo environment variables found, skipping population")
        print("   Settings will use fallback defaults until configured")
        return

    # Build UPDATE SQL with only non-empty values
    update_fields = []
    for key, value in env_values.items():
        if value:  # Only update non-empty values
            # Escape single quotes in values
            safe_value = value.replace("'", "''")
            update_fields.append(f"{key} = '{safe_value}'")

    if not update_fields:
        print("ℹ️  No values to populate, skipping")
        return

    update_sql = text(f"""
        UPDATE ecommerce_storefront_settings
        SET {', '.join(update_fields)}
        WHERE id = {settings_id}
    """)

    connection.execute(update_sql)

    print(f"✅ Populated {non_empty_count} shipping configuration values from environment variables")
    print(f"   Settings ID: {settings_id}")
    print(f"   Fields updated: {', '.join([k for k, v in env_values.items() if v])}")
    print("   💡 These values can now be updated through the admin UI")


def downgrade(connection):
    """Clear shipping settings populated from environment variables"""

    # This downgrade is optional - it clears the shipping settings
    # but doesn't delete the columns (that's handled by add_shipping_config_to_storefront_settings)

    check_table_sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'ecommerce_storefront_settings'
        )
    """)

    result = connection.execute(check_table_sql)
    table_exists = result.fetchone()[0]

    if not table_exists:
        print("⚠️  Table ecommerce_storefront_settings does not exist, skipping downgrade")
        return

    # Clear shipping configuration values
    clear_sql = text("""
        UPDATE ecommerce_storefront_settings
        SET
            shipping_from_name = NULL,
            shipping_from_company = NULL,
            shipping_from_street1 = NULL,
            shipping_from_street2 = NULL,
            shipping_from_city = NULL,
            shipping_from_state = NULL,
            shipping_from_zip = NULL,
            shipping_from_country = 'US',
            shipping_from_phone = NULL,
            shipping_from_email = NULL,
            shipping_default_length = '10',
            shipping_default_width = '8',
            shipping_default_height = '4',
            shipping_default_weight = '1',
            shippo_api_key = NULL,
            shippo_test_mode = 'true'
    """)

    connection.execute(clear_sql)
    print("✅ Cleared shipping configuration values (reset to defaults)")
