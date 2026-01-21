"""
Create email messaging system tables

This migration creates all necessary tables for the email messaging system:
- ecommerce_email_templates: Customizable email templates for transactional and marketing emails
- ecommerce_email_logs: Audit log of all sent emails with delivery tracking
- ecommerce_email_subscribers: Marketing email subscribers with segmentation
- ecommerce_scheduled_emails: Scheduled marketing email campaigns
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Create all email messaging tables."""
    try:
        logging.info("Starting email messaging tables migration...")

        # ====================================================================
        # 1. Create ecommerce_email_templates table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_email_templates'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_email_templates table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_email_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Template metadata
                    name VARCHAR(255) NOT NULL,
                    template_type VARCHAR(50) NOT NULL,  -- transactional, marketing
                    email_type VARCHAR(50) NOT NULL,     -- order_confirmation, shipping_notification, marketing
                    subject VARCHAR(500) NOT NULL,

                    -- Template content (JSON blocks for visual editor)
                    blocks JSONB DEFAULT '[]'::jsonb,

                    -- Branding settings
                    primary_color VARCHAR(7) DEFAULT '#10b981',
                    secondary_color VARCHAR(7) DEFAULT '#059669',
                    logo_url VARCHAR(512),

                    -- SendGrid integration
                    sendgrid_template_id VARCHAR(255),

                    -- Status
                    is_active BOOLEAN DEFAULT true,
                    is_default BOOLEAN DEFAULT false,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))

            logging.info("Creating indexes on ecommerce_email_templates...")
            connection.execute(text("""
                CREATE INDEX idx_email_templates_user_id ON ecommerce_email_templates(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_email_templates_email_type ON ecommerce_email_templates(email_type)
            """))

            logging.info("✓ ecommerce_email_templates table created successfully")
        else:
            logging.info("ecommerce_email_templates table already exists, skipping...")

        # ====================================================================
        # 2. Create ecommerce_email_logs table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_email_logs'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_email_logs table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_email_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Email details
                    template_id UUID REFERENCES ecommerce_email_templates(id) ON DELETE SET NULL,
                    email_type VARCHAR(50) NOT NULL,
                    recipient_email VARCHAR(255) NOT NULL,
                    subject VARCHAR(500) NOT NULL,

                    -- Related entities
                    order_id UUID REFERENCES ecommerce_orders(id) ON DELETE SET NULL,
                    customer_id UUID REFERENCES ecommerce_customers(id) ON DELETE SET NULL,

                    -- SendGrid tracking
                    sendgrid_message_id VARCHAR(255),
                    sendgrid_status VARCHAR(50),  -- sent, delivered, opened, clicked, bounced

                    -- Delivery tracking
                    sent_at TIMESTAMP DEFAULT NOW(),
                    delivered_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP,

                    -- Error tracking
                    error_message TEXT,

                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))

            logging.info("Creating indexes on ecommerce_email_logs...")
            connection.execute(text("""
                CREATE INDEX idx_email_logs_user_id ON ecommerce_email_logs(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_email_logs_order_id ON ecommerce_email_logs(order_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_email_logs_sent_at ON ecommerce_email_logs(sent_at)
            """))
            connection.execute(text("""
                CREATE INDEX idx_email_logs_sendgrid_message_id ON ecommerce_email_logs(sendgrid_message_id)
            """))

            logging.info("✓ ecommerce_email_logs table created successfully")
        else:
            logging.info("ecommerce_email_logs table already exists, skipping...")

        # ====================================================================
        # 3. Create ecommerce_email_subscribers table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_email_subscribers'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_email_subscribers table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_email_subscribers (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    -- Subscriber info
                    email VARCHAR(255) NOT NULL,
                    customer_id UUID REFERENCES ecommerce_customers(id) ON DELETE SET NULL,

                    -- Subscription status
                    is_subscribed BOOLEAN DEFAULT true,
                    unsubscribed_at TIMESTAMP,

                    -- Segmentation tags
                    tags JSONB DEFAULT '[]'::jsonb,

                    -- Analytics
                    total_sent INTEGER DEFAULT 0,
                    total_opened INTEGER DEFAULT 0,
                    total_clicked INTEGER DEFAULT 0,
                    last_sent_at TIMESTAMP,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),

                    UNIQUE(user_id, email)
                )
            """))

            logging.info("Creating indexes on ecommerce_email_subscribers...")
            connection.execute(text("""
                CREATE INDEX idx_email_subscribers_user_id ON ecommerce_email_subscribers(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_email_subscribers_tags ON ecommerce_email_subscribers USING gin(tags)
            """))
            connection.execute(text("""
                CREATE INDEX idx_email_subscribers_email ON ecommerce_email_subscribers(email)
            """))

            logging.info("✓ ecommerce_email_subscribers table created successfully")
        else:
            logging.info("ecommerce_email_subscribers table already exists, skipping...")

        # ====================================================================
        # 4. Create ecommerce_scheduled_emails table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_scheduled_emails'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_scheduled_emails table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_scheduled_emails (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    template_id UUID NOT NULL REFERENCES ecommerce_email_templates(id) ON DELETE CASCADE,

                    -- Recipient segmentation
                    recipient_filter JSONB,
                    recipient_count INTEGER,

                    -- Scheduling
                    scheduled_for TIMESTAMP NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',  -- pending, sending, sent, failed, cancelled

                    -- Execution tracking
                    sent_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))

            logging.info("Creating indexes on ecommerce_scheduled_emails...")
            connection.execute(text("""
                CREATE INDEX idx_scheduled_emails_user_id ON ecommerce_scheduled_emails(user_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_scheduled_emails_scheduled_for ON ecommerce_scheduled_emails(scheduled_for)
            """))
            connection.execute(text("""
                CREATE INDEX idx_scheduled_emails_status ON ecommerce_scheduled_emails(status)
            """))

            logging.info("✓ ecommerce_scheduled_emails table created successfully")
        else:
            logging.info("ecommerce_scheduled_emails table already exists, skipping...")

        logging.info("✅ Email messaging tables migration completed successfully!")

    except Exception as e:
        logging.error(f"❌ Error in email messaging tables migration: {e}")
        raise


def downgrade(connection):
    """Drop all email messaging tables."""
    try:
        logging.info("Dropping email messaging tables...")

        connection.execute(text("""
            DROP TABLE IF EXISTS ecommerce_scheduled_emails CASCADE
        """))
        logging.info("✓ Dropped ecommerce_scheduled_emails")

        connection.execute(text("""
            DROP TABLE IF EXISTS ecommerce_email_subscribers CASCADE
        """))
        logging.info("✓ Dropped ecommerce_email_subscribers")

        connection.execute(text("""
            DROP TABLE IF EXISTS ecommerce_email_logs CASCADE
        """))
        logging.info("✓ Dropped ecommerce_email_logs")

        connection.execute(text("""
            DROP TABLE IF EXISTS ecommerce_email_templates CASCADE
        """))
        logging.info("✓ Dropped ecommerce_email_templates")

        logging.info("✅ Email messaging tables dropped successfully!")

    except Exception as e:
        logging.error(f"❌ Error dropping email messaging tables: {e}")
        raise
