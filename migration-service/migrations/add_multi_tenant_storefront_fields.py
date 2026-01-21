"""
Add multi-tenant storefront fields to ecommerce_storefront_settings table.

This migration adds domain management, SSL configuration, SEO, social links,
and status fields to support multi-tenant storefronts with custom domains.

Columns added:
- Domain: subdomain, custom_domain, domain_verified, verification_token/method
- SSL: ssl_status, ssl_certificate_path, ssl_private_key_path, ssl_expires_at, ssl_auto_renew
- Branding: favicon_url, font_family
- Settings: currency, timezone, contact_email, support_phone
- Social: social_links (JSONB)
- SEO: meta_title, meta_description, google_analytics_id, facebook_pixel_id
- Status: is_active, is_published, maintenance_mode, published_at

Also creates domain_verifications table for tracking verification attempts.
"""

from sqlalchemy import text


def upgrade(connection):
    """Add multi-tenant storefront fields to ecommerce_storefront_settings"""

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
        print("Table ecommerce_storefront_settings does not exist, skipping migration")
        return

    # List of columns to add to ecommerce_storefront_settings
    columns_to_add = [
        # Domain Configuration
        ("subdomain", "VARCHAR(63) UNIQUE"),
        ("custom_domain", "VARCHAR(255) UNIQUE"),
        ("domain_verified", "BOOLEAN DEFAULT FALSE"),
        ("domain_verification_token", "VARCHAR(64)"),
        ("domain_verification_method", "VARCHAR(20)"),

        # SSL Configuration
        ("ssl_status", "VARCHAR(20) DEFAULT 'none'"),
        ("ssl_certificate_path", "VARCHAR(500)"),
        ("ssl_private_key_path", "VARCHAR(500)"),
        ("ssl_expires_at", "TIMESTAMP WITH TIME ZONE"),
        ("ssl_auto_renew", "BOOLEAN DEFAULT TRUE"),

        # Additional Branding
        ("favicon_url", "VARCHAR(512)"),
        ("font_family", "VARCHAR(100) DEFAULT 'Inter'"),

        # Store Settings
        ("currency", "VARCHAR(3) DEFAULT 'USD'"),
        ("timezone", "VARCHAR(50) DEFAULT 'America/New_York'"),
        ("contact_email", "VARCHAR(255)"),
        ("support_phone", "VARCHAR(20)"),

        # Social Links (JSONB for flexibility)
        ("social_links", "JSONB DEFAULT '{}'::jsonb"),

        # SEO Configuration
        ("meta_title", "VARCHAR(70)"),
        ("meta_description", "VARCHAR(160)"),
        ("google_analytics_id", "VARCHAR(20)"),
        ("facebook_pixel_id", "VARCHAR(20)"),

        # Status
        ("is_active", "BOOLEAN DEFAULT TRUE"),
        ("is_published", "BOOLEAN DEFAULT FALSE"),
        ("maintenance_mode", "BOOLEAN DEFAULT FALSE"),
        ("published_at", "TIMESTAMP WITH TIME ZONE"),
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
            print(f"Added column: {column_name}")
        else:
            print(f"Column {column_name} already exists, skipping")

    # Create indexes for domain lookups
    indexes_to_create = [
        ("idx_storefront_subdomain", "subdomain"),
        ("idx_storefront_custom_domain", "custom_domain"),
        ("idx_storefront_is_active", "is_active"),
        ("idx_storefront_is_published", "is_published"),
    ]

    for index_name, column_name in indexes_to_create:
        check_index_sql = text(f"""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE tablename = 'ecommerce_storefront_settings'
                AND indexname = '{index_name}'
            )
        """)
        result = connection.execute(check_index_sql)
        index_exists = result.fetchone()[0]

        if not index_exists:
            create_index_sql = text(f"""
                CREATE INDEX {index_name}
                ON ecommerce_storefront_settings({column_name})
            """)
            try:
                connection.execute(create_index_sql)
                print(f"Created index: {index_name}")
            except Exception as e:
                print(f"Could not create index {index_name}: {e}")
        else:
            print(f"Index {index_name} already exists, skipping")

    # Create domain_verifications table
    create_domain_verifications_sql = text("""
        CREATE TABLE IF NOT EXISTS domain_verifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            storefront_id INTEGER NOT NULL REFERENCES ecommerce_storefront_settings(id) ON DELETE CASCADE,
            domain VARCHAR(255) NOT NULL,
            verification_token VARCHAR(64) NOT NULL,
            verification_method VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            last_checked_at TIMESTAMP WITH TIME ZONE,
            verified_at TIMESTAMP WITH TIME ZONE,
            expires_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    try:
        connection.execute(create_domain_verifications_sql)
        print("Created table: domain_verifications")
    except Exception as e:
        print(f"Table domain_verifications may already exist: {e}")

    # Create index on domain_verifications
    create_domain_verify_index_sql = text("""
        CREATE INDEX IF NOT EXISTS idx_domain_verifications_storefront_id
        ON domain_verifications(storefront_id)
    """)
    try:
        connection.execute(create_domain_verify_index_sql)
        print("Created index on domain_verifications")
    except Exception as e:
        print(f"Could not create index on domain_verifications: {e}")

    print("Multi-tenant storefront migration completed")


def downgrade(connection):
    """Remove multi-tenant storefront fields"""

    columns_to_remove = [
        "subdomain",
        "custom_domain",
        "domain_verified",
        "domain_verification_token",
        "domain_verification_method",
        "ssl_status",
        "ssl_certificate_path",
        "ssl_private_key_path",
        "ssl_expires_at",
        "ssl_auto_renew",
        "favicon_url",
        "font_family",
        "currency",
        "timezone",
        "contact_email",
        "support_phone",
        "social_links",
        "meta_title",
        "meta_description",
        "google_analytics_id",
        "facebook_pixel_id",
        "is_active",
        "is_published",
        "maintenance_mode",
        "published_at",
    ]

    for column_name in columns_to_remove:
        drop_column_sql = text(f"""
            ALTER TABLE ecommerce_storefront_settings
            DROP COLUMN IF EXISTS {column_name}
        """)
        connection.execute(drop_column_sql)
        print(f"Removed column: {column_name}")

    # Drop domain_verifications table
    drop_table_sql = text("DROP TABLE IF EXISTS domain_verifications CASCADE")
    connection.execute(drop_table_sql)
    print("Dropped table: domain_verifications")

    # Drop indexes
    indexes_to_drop = [
        "idx_storefront_subdomain",
        "idx_storefront_custom_domain",
        "idx_storefront_is_active",
        "idx_storefront_is_published",
    ]

    for index_name in indexes_to_drop:
        drop_index_sql = text(f"DROP INDEX IF EXISTS {index_name}")
        connection.execute(drop_index_sql)
        print(f"Dropped index: {index_name}")

    print("Multi-tenant storefront downgrade completed")
