"""
Create subscription system tables

This migration creates all necessary tables for the subscription system:
- subscriptions: User subscription records managed by Stripe
- subscription_usage: Track monthly usage limits for subscriptions
- billing_history: Track billing and invoice history
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Create all subscription tables."""
    try:
        logging.info("Starting subscription tables migration...")

        # ====================================================================
        # 1. Create subscriptions table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'subscriptions'
        """))

        if not result.fetchone():
            logging.info("Creating subscriptions table...")
            connection.execute(text("""
                CREATE TABLE subscriptions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

                    -- Stripe IDs
                    stripe_customer_id VARCHAR(255),
                    stripe_subscription_id VARCHAR(255) UNIQUE,
                    stripe_price_id VARCHAR(255),

                    -- Subscription details
                    tier VARCHAR(50) NOT NULL DEFAULT 'free',
                    status VARCHAR(50) NOT NULL DEFAULT 'active',

                    -- Billing
                    current_period_start TIMESTAMP,
                    current_period_end TIMESTAMP,
                    cancel_at_period_end BOOLEAN DEFAULT false,
                    canceled_at TIMESTAMP,

                    -- Payment
                    default_payment_method VARCHAR(255),

                    -- Additional data
                    extra_metadata JSONB DEFAULT '{}'::jsonb,

                    -- Audit fields
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))

            logging.info("Creating indexes on subscriptions...")
            connection.execute(text("""
                CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id)
            """))

            logging.info("✓ subscriptions table created successfully")
        else:
            logging.info("subscriptions table already exists, skipping...")

        # ====================================================================
        # 2. Create subscription_usage table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'subscription_usage'
        """))

        if not result.fetchone():
            logging.info("Creating subscription_usage table...")
            connection.execute(text("""
                CREATE TABLE subscription_usage (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Usage tracking
                    mockups_this_month INTEGER DEFAULT 0,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),

                    UNIQUE(user_id, month, year)
                )
            """))

            logging.info("Creating indexes on subscription_usage...")
            connection.execute(text("""
                CREATE INDEX idx_subscription_usage_user_id ON subscription_usage(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_subscription_usage_period ON subscription_usage(year, month)
            """))

            logging.info("✓ subscription_usage table created successfully")
        else:
            logging.info("subscription_usage table already exists, skipping...")

        # ====================================================================
        # 3. Create billing_history table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'billing_history'
        """))

        if not result.fetchone():
            logging.info("Creating billing_history table...")
            connection.execute(text("""
                CREATE TABLE billing_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,

                    -- Stripe info
                    stripe_invoice_id VARCHAR(255) UNIQUE,
                    stripe_charge_id VARCHAR(255),

                    -- Invoice details
                    amount NUMERIC(10, 2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'usd',
                    status VARCHAR(50) NOT NULL,

                    -- Dates
                    invoice_date TIMESTAMP NOT NULL,
                    paid_at TIMESTAMP,

                    -- Invoice data
                    invoice_pdf_url VARCHAR(500),
                    hosted_invoice_url VARCHAR(500),

                    -- Description
                    description VARCHAR(500),

                    -- Additional data
                    extra_metadata JSONB DEFAULT '{}'::jsonb,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))

            logging.info("Creating indexes on billing_history...")
            connection.execute(text("""
                CREATE INDEX idx_billing_history_user_id ON billing_history(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_billing_history_subscription_id ON billing_history(subscription_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_billing_history_stripe_invoice_id ON billing_history(stripe_invoice_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_billing_history_invoice_date ON billing_history(invoice_date)
            """))

            logging.info("✓ billing_history table created successfully")
        else:
            logging.info("billing_history table already exists, skipping...")

        logging.info("✅ Subscription tables migration completed successfully!")

    except Exception as e:
        logging.error(f"❌ Error in subscription tables migration: {e}")
        raise


def downgrade(connection):
    """Drop all subscription tables."""
    try:
        logging.info("Dropping subscription tables...")

        connection.execute(text("""
            DROP TABLE IF EXISTS billing_history CASCADE
        """))
        logging.info("✓ Dropped billing_history")

        connection.execute(text("""
            DROP TABLE IF EXISTS subscription_usage CASCADE
        """))
        logging.info("✓ Dropped subscription_usage")

        connection.execute(text("""
            DROP TABLE IF EXISTS subscriptions CASCADE
        """))
        logging.info("✓ Dropped subscriptions")

        logging.info("✅ Subscription tables dropped successfully!")

    except Exception as e:
        logging.error(f"❌ Error dropping subscription tables: {e}")
        raise
