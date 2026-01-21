"""
Migration: Create ecommerce tables

This migration creates all the necessary tables for the ecommerce platform:
- ecommerce_products
- ecommerce_product_variants
- ecommerce_customers
- ecommerce_customer_addresses
- ecommerce_orders
- ecommerce_order_items
- ecommerce_shopping_carts
- ecommerce_product_reviews
"""

from sqlalchemy import text
from server.src.database.core import engine


def upgrade():
    """Create ecommerce tables."""

    with engine.connect() as conn:
        # Create ecommerce_products table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_products (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                short_description VARCHAR(500),
                product_type VARCHAR(50) NOT NULL,
                print_method VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price FLOAT NOT NULL,
                compare_at_price FLOAT,
                cost FLOAT,
                track_inventory BOOLEAN DEFAULT FALSE,
                inventory_quantity INTEGER DEFAULT 0,
                allow_backorder BOOLEAN DEFAULT FALSE,
                digital_file_url VARCHAR(500),
                download_limit INTEGER DEFAULT 3,
                images JSON,
                featured_image VARCHAR(500),
                meta_title VARCHAR(255),
                meta_description TEXT,
                has_variants BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                is_featured BOOLEAN DEFAULT FALSE,
                design_id UUID,
                template_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create indexes for products
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_products_slug ON ecommerce_products(slug)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_products_print_method ON ecommerce_products(print_method)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_products_category ON ecommerce_products(category)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_products_is_active ON ecommerce_products(is_active)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_products_print_category ON ecommerce_products(print_method, category)
        """))

        # Create ecommerce_product_variants table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_product_variants (
                id UUID PRIMARY KEY,
                product_id UUID NOT NULL REFERENCES ecommerce_products(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                sku VARCHAR(100) UNIQUE,
                price FLOAT,
                inventory_quantity INTEGER DEFAULT 0,
                option1 VARCHAR(100),
                option2 VARCHAR(100),
                option3 VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create ecommerce_customers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_customers (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                accepts_marketing BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                total_spent FLOAT DEFAULT 0,
                order_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create index for customer email
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_customers_email ON ecommerce_customers(email)
        """))

        # Create ecommerce_customer_addresses table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_customer_addresses (
                id UUID PRIMARY KEY,
                customer_id UUID NOT NULL REFERENCES ecommerce_customers(id) ON DELETE CASCADE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                company VARCHAR(255),
                address1 VARCHAR(255) NOT NULL,
                address2 VARCHAR(255),
                city VARCHAR(100) NOT NULL,
                state VARCHAR(100) NOT NULL,
                zip_code VARCHAR(20) NOT NULL,
                country VARCHAR(100) DEFAULT 'United States',
                phone VARCHAR(20),
                is_default_shipping BOOLEAN DEFAULT FALSE,
                is_default_billing BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create ecommerce_orders table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_orders (
                id UUID PRIMARY KEY,
                order_number VARCHAR(50) UNIQUE NOT NULL,
                customer_id UUID REFERENCES ecommerce_customers(id),
                guest_email VARCHAR(255),
                subtotal FLOAT NOT NULL,
                tax FLOAT DEFAULT 0,
                shipping FLOAT DEFAULT 0,
                discount FLOAT DEFAULT 0,
                total FLOAT NOT NULL,
                shipping_address JSON,
                billing_address JSON,
                payment_status VARCHAR(50) DEFAULT 'pending',
                payment_method VARCHAR(50),
                payment_id VARCHAR(255),
                fulfillment_status VARCHAR(50) DEFAULT 'unfulfilled',
                tracking_number VARCHAR(255),
                tracking_url VARCHAR(500),
                shipped_at TIMESTAMP,
                customer_note TEXT,
                internal_note TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                cancelled_at TIMESTAMP,
                cancel_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create indexes for orders
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_number ON ecommerce_orders(order_number)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_status ON ecommerce_orders(status)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_created ON ecommerce_orders(created_at)
        """))

        # Create ecommerce_order_items table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_order_items (
                id UUID PRIMARY KEY,
                order_id UUID NOT NULL REFERENCES ecommerce_orders(id) ON DELETE CASCADE,
                product_id UUID REFERENCES ecommerce_products(id),
                variant_id UUID REFERENCES ecommerce_product_variants(id),
                product_name VARCHAR(255) NOT NULL,
                variant_name VARCHAR(255),
                sku VARCHAR(100),
                price FLOAT NOT NULL,
                quantity INTEGER NOT NULL,
                total FLOAT NOT NULL,
                download_url VARCHAR(500),
                download_count INTEGER DEFAULT 0,
                download_expires_at TIMESTAMP,
                custom_design_url VARCHAR(500),
                is_fulfilled BOOLEAN DEFAULT FALSE,
                gangsheet_generated BOOLEAN DEFAULT FALSE,
                gangsheet_file_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create ecommerce_shopping_carts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_shopping_carts (
                id UUID PRIMARY KEY,
                customer_id UUID REFERENCES ecommerce_customers(id),
                session_id VARCHAR(255),
                items JSON,
                subtotal FLOAT DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """))

        # Create index for cart session
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_carts_session ON ecommerce_shopping_carts(session_id)
        """))

        # Create ecommerce_product_reviews table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ecommerce_product_reviews (
                id UUID PRIMARY KEY,
                product_id UUID NOT NULL REFERENCES ecommerce_products(id) ON DELETE CASCADE,
                customer_id UUID NOT NULL REFERENCES ecommerce_customers(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL,
                title VARCHAR(255),
                body TEXT,
                verified_purchase BOOLEAN DEFAULT FALSE,
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create index for reviews
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reviews_created ON ecommerce_product_reviews(created_at)
        """))

        conn.commit()
        print("✅ Ecommerce tables created successfully!")


def downgrade():
    """Drop ecommerce tables."""

    with engine.connect() as conn:
        # Drop tables in reverse order (to respect foreign key constraints)
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_product_reviews CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_shopping_carts CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_order_items CASCADE"))
        conn.execute(text("DROP TABLE IF NOT EXISTS ecommerce_orders CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_customer_addresses CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_customers CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_product_variants CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS ecommerce_products CASCADE"))

        conn.commit()
        print("✅ Ecommerce tables dropped successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python 001_create_ecommerce_tables.py [upgrade|downgrade]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "upgrade":
        upgrade()
    elif command == "downgrade":
        downgrade()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python 001_create_ecommerce_tables.py [upgrade|downgrade]")
        sys.exit(1)
