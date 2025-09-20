"""
Separate platform connections and store information

This migration creates the new platform connection architecture:
1. Creates platform_connections table for OAuth/API credentials
2. Creates etsy_stores table for Etsy business information
3. Updates shopify_stores table structure (adds connection_id, keeps legacy fields for migration)
4. Migrates existing data from old structure to new structure

Revision ID: separate_platform_connections
"""

import logging
from sqlalchemy import text, MetaData, Table, Column, String, Boolean, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timezone

def upgrade(connection):
    """Create new platform connection architecture and migrate existing data."""
    try:
        logging.info("Starting platform connections separation migration...")

        # Create platform_connections table
        logging.info("Creating platform_connections table...")
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_connections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                platform VARCHAR(20) NOT NULL CHECK (platform IN ('etsy', 'shopify', 'amazon', 'ebay')),
                connection_type VARCHAR(20) NOT NULL DEFAULT 'oauth2' CHECK (connection_type IN ('oauth2', 'api_key', 'basic_auth')),
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TIMESTAMPTZ,
                auth_data TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                last_verified_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        # Create etsy_stores table
        logging.info("Creating etsy_stores table...")
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS etsy_stores (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                connection_id UUID NOT NULL REFERENCES platform_connections(id) ON DELETE CASCADE,
                etsy_shop_id VARCHAR(50) NOT NULL UNIQUE,
                shop_name VARCHAR(255) NOT NULL,
                shop_url VARCHAR(255),
                currency_code VARCHAR(3),
                country_code VARCHAR(2),
                language VARCHAR(10),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_vacation_mode BOOLEAN NOT NULL DEFAULT FALSE,
                total_listings INTEGER,
                total_sales INTEGER,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        # Add new columns to shopify_stores table (keeping existing for migration)
        logging.info("Updating shopify_stores table structure...")
        try:
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS connection_id UUID REFERENCES platform_connections(id)"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS shopify_shop_id VARCHAR(50)"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS shop_url VARCHAR(255)"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS currency_code VARCHAR(3)"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS country_code VARCHAR(2)"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS timezone VARCHAR(50)"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS total_products INTEGER"))
            connection.execute(text("ALTER TABLE shopify_stores ADD COLUMN IF NOT EXISTS total_orders INTEGER"))

            # Make access_token nullable for migration
            connection.execute(text("ALTER TABLE shopify_stores ALTER COLUMN access_token DROP NOT NULL"))
        except Exception as e:
            logging.warning(f"Some shopify_stores columns may already exist: {e}")

        # Migrate existing Etsy data from users table to new structure
        logging.info("Migrating existing Etsy data...")

        # First, get users with Etsy data (either etsy_shop_id or third_party_oauth_tokens)
        etsy_users_result = connection.execute(text("""
            SELECT DISTINCT u.id, u.etsy_shop_id, u.shop_name, t.access_token, t.refresh_token, t.expires_at
            FROM users u
            LEFT JOIN third_party_oauth_tokens t ON u.id = t.user_id
            WHERE u.etsy_shop_id IS NOT NULL OR t.access_token IS NOT NULL
        """))

        etsy_users = etsy_users_result.fetchall()
        migrated_etsy_count = 0

        for user in etsy_users:
            user_id, etsy_shop_id, shop_name, access_token, refresh_token, expires_at = user

            if not access_token:
                logging.warning(f"User {user_id} has etsy_shop_id but no access_token, skipping")
                continue

            try:
                # Create platform connection
                connection_result = connection.execute(text("""
                    INSERT INTO platform_connections
                    (user_id, platform, connection_type, access_token, refresh_token, token_expires_at, is_active)
                    VALUES (:user_id, 'etsy', 'oauth2', :access_token, :refresh_token, :expires_at, true)
                    RETURNING id
                """), {
                    "user_id": user_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at
                })

                connection_id = connection_result.fetchone()[0]

                # Create Etsy store if we have shop info (avoid duplicates)
                if etsy_shop_id and shop_name:
                    connection.execute(text("""
                        INSERT INTO etsy_stores
                        (user_id, connection_id, etsy_shop_id, shop_name, is_active)
                        VALUES (:user_id, :connection_id, :etsy_shop_id, :shop_name, true)
                        ON CONFLICT (etsy_shop_id) DO UPDATE SET
                            connection_id = EXCLUDED.connection_id,
                            shop_name = EXCLUDED.shop_name,
                            is_active = true
                    """), {
                        "user_id": user_id,
                        "connection_id": connection_id,
                        "etsy_shop_id": etsy_shop_id,
                        "shop_name": shop_name
                    })

                migrated_etsy_count += 1
                logging.info(f"Migrated Etsy data for user {user_id}")

            except Exception as e:
                logging.error(f"Error migrating Etsy data for user {user_id}: {e}")
                continue

        # Migrate existing Shopify data (use separate connection to avoid transaction issues)
        logging.info("Migrating existing Shopify data...")

        try:
            shopify_stores_result = connection.execute(text("""
                SELECT id, user_id, access_token, shop_domain, shop_name
                FROM shopify_stores
                WHERE access_token IS NOT NULL
            """))
        except Exception as e:
            logging.error(f"Failed to query Shopify stores, likely due to transaction rollback: {e}")
            logging.info("Attempting to start fresh transaction for Shopify migration...")
            # Create new connection for Shopify migration
            from sqlalchemy import create_engine
            import os
            engine = create_engine(os.getenv('DATABASE_URL'))
            connection = engine.connect()
            shopify_stores_result = connection.execute(text("""
                SELECT id, user_id, access_token, shop_domain, shop_name
                FROM shopify_stores
                WHERE access_token IS NOT NULL
            """))

        shopify_stores = shopify_stores_result.fetchall()
        migrated_shopify_count = 0

        for store in shopify_stores:
            store_id, user_id, access_token, shop_domain, shop_name = store

            try:
                # Create platform connection for Shopify
                connection_result = connection.execute(text("""
                    INSERT INTO platform_connections
                    (user_id, platform, connection_type, access_token, is_active)
                    VALUES (:user_id, 'shopify', 'oauth2', :access_token, true)
                    RETURNING id
                """), {
                    "user_id": user_id,
                    "access_token": access_token
                })

                connection_id = connection_result.fetchone()[0]

                # Update shopify_stores with connection_id
                connection.execute(text("""
                    UPDATE shopify_stores
                    SET connection_id = :connection_id
                    WHERE id = :store_id
                """), {
                    "connection_id": connection_id,
                    "store_id": store_id
                })

                migrated_shopify_count += 1
                logging.info(f"Migrated Shopify store {store_id}")

            except Exception as e:
                logging.error(f"Error migrating Shopify store {store_id}: {e}")
                continue

        # Create indexes for better performance
        logging.info("Creating indexes...")
        try:
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_platform_connections_user_platform ON platform_connections(user_id, platform)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_etsy_stores_user_id ON etsy_stores(user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_etsy_stores_connection_id ON etsy_stores(connection_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS idx_shopify_stores_connection_id ON shopify_stores(connection_id)"))
        except Exception as e:
            logging.warning(f"Some indexes may already exist: {e}")

        logging.info(f"Platform connections separation migration completed!")
        logging.info(f"Migrated {migrated_etsy_count} Etsy connections and {migrated_shopify_count} Shopify connections")

    except Exception as e:
        logging.error(f"Error during platform connections separation migration: {e}")
        raise e

def downgrade(connection):
    """Downgrade the platform connections separation."""
    try:
        logging.info("Starting platform connections separation downgrade...")

        # Note: This is a destructive operation and should be used with caution
        logging.warning("This downgrade will remove the separated platform connection structure")

        # Remove new columns from shopify_stores
        try:
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS connection_id"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS shopify_shop_id"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS shop_url"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS currency_code"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS country_code"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS timezone"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS total_products"))
            connection.execute(text("ALTER TABLE shopify_stores DROP COLUMN IF EXISTS total_orders"))

            # Make access_token required again
            connection.execute(text("ALTER TABLE shopify_stores ALTER COLUMN access_token SET NOT NULL"))
        except Exception as e:
            logging.warning(f"Error removing shopify_stores columns: {e}")

        # Drop new tables
        connection.execute(text("DROP TABLE IF EXISTS etsy_stores"))
        connection.execute(text("DROP TABLE IF EXISTS platform_connections"))

        logging.info("Platform connections separation downgrade completed")

    except Exception as e:
        logging.error(f"Error during platform connections separation downgrade: {e}")
        raise e