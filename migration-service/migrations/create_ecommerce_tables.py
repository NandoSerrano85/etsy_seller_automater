"""
Create ecommerce tables for custom storefront

This migration creates all necessary tables for the ecommerce platform:
- ecommerce_products: Product catalog
- ecommerce_product_variants: Product size/color variants
- ecommerce_customers: Customer accounts
- ecommerce_customer_addresses: Shipping/billing addresses
- ecommerce_orders: Customer orders
- ecommerce_order_items: Order line items
- ecommerce_shopping_carts: Shopping cart sessions
- ecommerce_product_reviews: Product reviews and ratings
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Create all ecommerce tables."""
    try:
        logging.info("Starting ecommerce tables migration...")

        # ====================================================================
        # 1. Create ecommerce_products table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_products'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_products table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_products (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Basic Info
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    description TEXT,
                    short_description VARCHAR(500),

                    -- Product Classification (2-level hierarchy)
                    product_type VARCHAR(50) NOT NULL,  -- physical or digital
                    print_method VARCHAR(50) NOT NULL,  -- uvdtf, dtf, sublimation, vinyl, other, digital
                    category VARCHAR(50) NOT NULL,      -- cup_wraps, single_square, single_rectangle, other_custom

                    -- Pricing
                    price FLOAT NOT NULL,
                    compare_at_price FLOAT,
                    cost FLOAT,

                    -- Inventory (for physical products)
                    track_inventory BOOLEAN DEFAULT FALSE,
                    inventory_quantity INTEGER DEFAULT 0,
                    allow_backorder BOOLEAN DEFAULT FALSE,

                    -- Digital Product Info
                    digital_file_url VARCHAR(500),
                    download_limit INTEGER DEFAULT 3,

                    -- Images
                    images JSONB,  -- Array of image URLs
                    featured_image VARCHAR(500),

                    -- SEO
                    meta_title VARCHAR(255),
                    meta_description TEXT,

                    -- Variants
                    has_variants BOOLEAN DEFAULT FALSE,

                    -- Status
                    is_active BOOLEAN DEFAULT TRUE,
                    is_featured BOOLEAN DEFAULT FALSE,

                    -- Integration with existing system
                    design_id UUID,  -- Link to design_images table
                    template_name VARCHAR(100),

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Add foreign key to design_images if table exists
            design_table_check = connection.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'design_images'
            """))

            if design_table_check.fetchone():
                connection.execute(text("""
                    ALTER TABLE ecommerce_products
                    ADD CONSTRAINT fk_products_design_id
                    FOREIGN KEY (design_id)
                    REFERENCES design_images(id)
                    ON DELETE SET NULL
                """))
                logging.info("Added foreign key constraint for design_id")

            # Create indexes
            connection.execute(text("""
                CREATE INDEX idx_products_slug ON ecommerce_products(slug)
            """))
            connection.execute(text("""
                CREATE INDEX idx_products_print_method ON ecommerce_products(print_method)
            """))
            connection.execute(text("""
                CREATE INDEX idx_products_category ON ecommerce_products(category)
            """))
            connection.execute(text("""
                CREATE INDEX idx_products_active ON ecommerce_products(is_active)
            """))
            connection.execute(text("""
                CREATE INDEX idx_products_featured ON ecommerce_products(is_featured)
            """))

            logging.info("✅ Created ecommerce_products table")
        else:
            logging.info("ecommerce_products table already exists")

        # ====================================================================
        # 2. Create ecommerce_product_variants table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_product_variants'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_product_variants table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_product_variants (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    product_id UUID NOT NULL REFERENCES ecommerce_products(id) ON DELETE CASCADE,

                    -- Variant Info
                    name VARCHAR(255) NOT NULL,  -- "16oz", "12oz", "Red", etc.
                    sku VARCHAR(100) UNIQUE,

                    -- Pricing Override
                    price FLOAT,  -- If different from base product

                    -- Inventory
                    inventory_quantity INTEGER DEFAULT 0,

                    -- Options
                    option1 VARCHAR(100),  -- Size
                    option2 VARCHAR(100),  -- Color
                    option3 VARCHAR(100),  -- Material

                    -- Status
                    is_active BOOLEAN DEFAULT TRUE,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_variants_product_id ON ecommerce_product_variants(product_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_variants_sku ON ecommerce_product_variants(sku)
            """))

            logging.info("✅ Created ecommerce_product_variants table")
        else:
            logging.info("ecommerce_product_variants table already exists")

        # ====================================================================
        # 3. Create ecommerce_customers table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_customers'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_customers table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_customers (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Basic Info
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone VARCHAR(20),

                    -- Marketing
                    accepts_marketing BOOLEAN DEFAULT FALSE,

                    -- Status
                    is_active BOOLEAN DEFAULT TRUE,
                    email_verified BOOLEAN DEFAULT FALSE,

                    -- Stats
                    total_spent FLOAT DEFAULT 0,
                    order_count INTEGER DEFAULT 0,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP WITH TIME ZONE
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_customers_email ON ecommerce_customers(email)
            """))
            connection.execute(text("""
                CREATE INDEX idx_customers_active ON ecommerce_customers(is_active)
            """))

            logging.info("✅ Created ecommerce_customers table")
        else:
            logging.info("ecommerce_customers table already exists")

        # ====================================================================
        # 4. Create ecommerce_customer_addresses table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_customer_addresses'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_customer_addresses table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_customer_addresses (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    customer_id UUID NOT NULL REFERENCES ecommerce_customers(id) ON DELETE CASCADE,

                    -- Address Info
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    company VARCHAR(255),
                    address1 VARCHAR(255),
                    address2 VARCHAR(255),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    zip_code VARCHAR(20),
                    country VARCHAR(100) DEFAULT 'United States',
                    phone VARCHAR(20),

                    -- Defaults
                    is_default_shipping BOOLEAN DEFAULT FALSE,
                    is_default_billing BOOLEAN DEFAULT FALSE,

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_addresses_customer_id ON ecommerce_customer_addresses(customer_id)
            """))

            logging.info("✅ Created ecommerce_customer_addresses table")
        else:
            logging.info("ecommerce_customer_addresses table already exists")

        # ====================================================================
        # 5. Create ecommerce_orders table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_orders'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_orders table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_orders (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    order_number VARCHAR(50) UNIQUE NOT NULL,

                    customer_id UUID REFERENCES ecommerce_customers(id) ON DELETE SET NULL,

                    -- Guest Checkout Info (if customer_id is null)
                    guest_email VARCHAR(255),

                    -- Pricing
                    subtotal FLOAT NOT NULL,
                    tax FLOAT DEFAULT 0,
                    shipping FLOAT DEFAULT 0,
                    discount FLOAT DEFAULT 0,
                    total FLOAT NOT NULL,

                    -- Shipping Address (stored as JSON)
                    shipping_address JSONB,

                    -- Billing Address (stored as JSON)
                    billing_address JSONB,

                    -- Payment
                    payment_status VARCHAR(50),  -- pending, paid, failed, refunded
                    payment_method VARCHAR(50),  -- stripe, paypal
                    payment_id VARCHAR(255),     -- Stripe payment ID

                    -- Fulfillment
                    fulfillment_status VARCHAR(50),  -- unfulfilled, fulfilled, shipped
                    tracking_number VARCHAR(255),
                    tracking_url VARCHAR(500),
                    shipped_at TIMESTAMP WITH TIME ZONE,

                    -- Notes
                    customer_note TEXT,
                    internal_note TEXT,

                    -- Status
                    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, cancelled
                    cancelled_at TIMESTAMP WITH TIME ZONE,
                    cancel_reason TEXT,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_orders_order_number ON ecommerce_orders(order_number)
            """))
            connection.execute(text("""
                CREATE INDEX idx_orders_customer_id ON ecommerce_orders(customer_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_orders_status ON ecommerce_orders(status)
            """))
            connection.execute(text("""
                CREATE INDEX idx_orders_payment_status ON ecommerce_orders(payment_status)
            """))
            connection.execute(text("""
                CREATE INDEX idx_orders_created_at ON ecommerce_orders(created_at DESC)
            """))

            logging.info("✅ Created ecommerce_orders table")
        else:
            logging.info("ecommerce_orders table already exists")

        # ====================================================================
        # 6. Create ecommerce_order_items table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_order_items'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_order_items table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_order_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    order_id UUID NOT NULL REFERENCES ecommerce_orders(id) ON DELETE CASCADE,
                    product_id UUID REFERENCES ecommerce_products(id) ON DELETE SET NULL,
                    variant_id UUID REFERENCES ecommerce_product_variants(id) ON DELETE SET NULL,

                    -- Item Details (snapshot at time of order)
                    product_name VARCHAR(255),
                    variant_name VARCHAR(255),
                    sku VARCHAR(100),

                    -- Pricing
                    price FLOAT NOT NULL,
                    quantity INTEGER NOT NULL,
                    total FLOAT NOT NULL,

                    -- Digital Product
                    download_url VARCHAR(500),  -- Generated download link
                    download_count INTEGER DEFAULT 0,
                    download_expires_at TIMESTAMP WITH TIME ZONE,

                    -- Custom Order Upload
                    custom_design_url VARCHAR(500),  -- If customer uploaded design

                    -- Fulfillment
                    is_fulfilled BOOLEAN DEFAULT FALSE,
                    gangsheet_generated BOOLEAN DEFAULT FALSE,
                    gangsheet_file_path VARCHAR(500),

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_order_items_order_id ON ecommerce_order_items(order_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_order_items_product_id ON ecommerce_order_items(product_id)
            """))

            logging.info("✅ Created ecommerce_order_items table")
        else:
            logging.info("ecommerce_order_items table already exists")

        # ====================================================================
        # 7. Create ecommerce_shopping_carts table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_shopping_carts'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_shopping_carts table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_shopping_carts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    customer_id UUID REFERENCES ecommerce_customers(id) ON DELETE CASCADE,
                    session_id VARCHAR(255),  -- For guest carts

                    -- Cart Items (stored as JSON for simplicity)
                    items JSONB,  -- [{product_id, variant_id, quantity, price}, ...]

                    -- Totals
                    subtotal FLOAT DEFAULT 0,

                    -- Status
                    is_active BOOLEAN DEFAULT TRUE,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE  -- Auto-delete after 30 days
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_carts_customer_id ON ecommerce_shopping_carts(customer_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_carts_session_id ON ecommerce_shopping_carts(session_id)
            """))

            logging.info("✅ Created ecommerce_shopping_carts table")
        else:
            logging.info("ecommerce_shopping_carts table already exists")

        # ====================================================================
        # 8. Create ecommerce_product_reviews table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_product_reviews'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_product_reviews table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_product_reviews (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    product_id UUID NOT NULL REFERENCES ecommerce_products(id) ON DELETE CASCADE,
                    customer_id UUID REFERENCES ecommerce_customers(id) ON DELETE SET NULL,

                    -- Review
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    title VARCHAR(255),
                    body TEXT,

                    -- Verification
                    verified_purchase BOOLEAN DEFAULT FALSE,

                    -- Moderation
                    is_approved BOOLEAN DEFAULT FALSE,

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_reviews_product_id ON ecommerce_product_reviews(product_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_reviews_customer_id ON ecommerce_product_reviews(customer_id)
            """))
            connection.execute(text("""
                CREATE INDEX idx_reviews_approved ON ecommerce_product_reviews(is_approved)
            """))

            logging.info("✅ Created ecommerce_product_reviews table")
        else:
            logging.info("ecommerce_product_reviews table already exists")

        # ====================================================================
        # 9. Create ecommerce_storefront_settings table
        # ====================================================================
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_storefront_settings'
        """))

        if not result.fetchone():
            logging.info("Creating ecommerce_storefront_settings table...")
            connection.execute(text("""
                CREATE TABLE ecommerce_storefront_settings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,

                    -- Store Information
                    store_name VARCHAR(255),
                    store_description TEXT,

                    -- Branding Assets
                    logo_url VARCHAR(512),

                    -- Color Scheme (hex color codes)
                    primary_color VARCHAR(7) DEFAULT '#10b981',
                    secondary_color VARCHAR(7) DEFAULT '#059669',
                    accent_color VARCHAR(7) DEFAULT '#34d399',
                    text_color VARCHAR(7) DEFAULT '#111827',
                    background_color VARCHAR(7) DEFAULT '#ffffff',

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))

            connection.execute(text("""
                CREATE INDEX idx_storefront_settings_user_id ON ecommerce_storefront_settings(user_id)
            """))

            logging.info("✅ Created ecommerce_storefront_settings table")
        else:
            logging.info("ecommerce_storefront_settings table already exists")

        # Analyze all tables for better query performance
        connection.execute(text("""
            ANALYZE ecommerce_products,
                    ecommerce_product_variants,
                    ecommerce_customers,
                    ecommerce_customer_addresses,
                    ecommerce_orders,
                    ecommerce_order_items,
                    ecommerce_shopping_carts,
                    ecommerce_product_reviews,
                    ecommerce_storefront_settings
        """))

        logging.info("✅ Successfully completed ecommerce tables migration")
        connection.commit()

    except Exception as e:
        logging.error(f"Error in ecommerce tables migration: {e}")
        raise e


def downgrade(connection):
    """Drop all ecommerce tables in reverse order (respecting foreign keys)."""
    try:
        logging.info("Dropping ecommerce tables...")

        # Drop in reverse order to respect foreign key constraints
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_storefront_settings CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_product_reviews CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_shopping_carts CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_order_items CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_orders CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_customer_addresses CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_customers CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_product_variants CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS ecommerce_products CASCADE"))

        logging.info("✅ Successfully dropped all ecommerce tables")
        connection.commit()

    except Exception as e:
        logging.error(f"Error dropping ecommerce tables: {e}")
        raise e
