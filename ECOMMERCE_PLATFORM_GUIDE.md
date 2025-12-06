# 🛒 Custom Ecommerce Platform - Complete Implementation Guide

**Project:** Direct-to-Consumer Ecommerce Service for Physical & Digital Goods
**Integration:** Connects to existing Etsy Seller Automation infrastructure
**Tech Stack:** FastAPI + React + PostgreSQL + Stripe + Railway
**Timeline:** 8-12 weeks (depending on scope)

---

## 📋 Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Phase 1: Planning & Design (Week 1-2)](#phase-1-planning--design)
3. [Phase 2: Database & Backend API (Week 3-4)](#phase-2-database--backend-api)
4. [Phase 3: Customer-Facing Storefront (Week 5-6)](#phase-3-customer-facing-storefront)
5. [Phase 4: Payment & Checkout (Week 7-8)](#phase-4-payment--checkout)
6. [Phase 5: Order Fulfillment Integration (Week 9-10)](#phase-5-order-fulfillment-integration)
7. [Phase 6: Testing & Launch (Week 11-12)](#phase-6-testing--launch)
8. [Post-Launch: Advanced Features](#post-launch-advanced-features)

---

## 🎯 Overview & Architecture

### **What You're Building**

A custom ecommerce platform that:

- ✅ Sells your physical products (UVDTF transfers, custom cups, etc.)
- ✅ Sells digital products (downloadable designs)
- ✅ Integrates with your existing gangsheet generation system
- ✅ Accepts payments via Stripe/PayPal
- ✅ Manages customer accounts and order history
- ✅ Automatically generates print files for orders
- ✅ Provides admin dashboard for order management
- ✅ Works alongside your Etsy/Shopify stores

### **Why Build This?**

1. **Lower Fees** - No Etsy/Shopify marketplace fees (3-6%)
2. **Full Control** - Own your customer data and branding
3. **Better Margins** - Direct sales = higher profit
4. **Custom Features** - Build exactly what you need
5. **Customer Relationships** - Direct communication with buyers

### **Integration with Existing System**

Your ecommerce platform will **reuse** existing infrastructure:

```
┌─────────────────────────────────────────────────────────┐
│                   YOUR ECOSYSTEM                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐     ┌──────────────┐                │
│  │ Etsy Store   │     │ Shopify Store│                │
│  └──────┬───────┘     └──────┬───────┘                │
│         │                    │                         │
│         └────────┬───────────┘                         │
│                  │                                     │
│         ┌────────▼────────────┐                       │
│         │  EXISTING BACKEND   │                       │
│         │  (FastAPI)          │                       │
│         │  - User Management  │                       │
│         │  - Design Storage   │                       │
│         │  - Gangsheet Gen    │                       │
│         │  - NAS Integration  │                       │
│         └────────┬────────────┘                       │
│                  │                                     │
│         ┌────────▼────────────┐                       │
│         │  NEW ECOMMERCE API  │  ← YOU BUILD THIS    │
│         │  - Products         │                       │
│         │  - Shopping Cart    │                       │
│         │  - Checkout         │                       │
│         │  - Customer Orders  │                       │
│         └────────┬────────────┘                       │
│                  │                                     │
│         ┌────────▼────────────┐                       │
│         │ STOREFRONT (React)  │  ← YOU BUILD THIS    │
│         │  - Product Catalog  │                       │
│         │  - Product Pages    │                       │
│         │  - Shopping Cart    │                       │
│         │  - Checkout         │                       │
│         │  - Customer Account │                       │
│         └─────────────────────┘                       │
│                                                         │
│         ┌─────────────────────┐                       │
│         │  SHARED RESOURCES   │                       │
│         │  - PostgreSQL DB    │                       │
│         │  - NAS Storage      │                       │
│         │  - Redis Cache      │                       │
│         │  - Gangsheet Engine │                       │
│         └─────────────────────┘                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### **Technology Stack**

**Backend (API):**

- FastAPI (same as existing)
- SQLAlchemy ORM
- Pydantic for validation
- Existing authentication system

**Frontend (Storefront):**

- React 18
- Tailwind CSS
- React Router for navigation
- Zustand for state management

**Payment Processing:**

- Stripe (recommended)
- PayPal (optional)

**Infrastructure:**

- PostgreSQL (existing database)
- Railway (existing deployment)
- NAS Storage (existing)
- Existing gangsheet generation

---

## 🗓️ Phase 1: Planning & Design (Week 1-2)

### **Goals**

- [ ] Define product catalog structure
- [ ] Design database schema
- [ ] Plan API endpoints
- [ ] Create wireframes for storefront
- [ ] Choose payment provider

### **Step 1.1: Define Your Product Types**

**Product Categorization Structure:**

Your products will use a **2-level hierarchical categorization**:

**Level 1: Print Method** (How the product is made)

- UVDTF (UV Direct to Film)
- DTF (Direct to Film)
- Sublimation
- Vinyl
- Other

**Level 2: Product Type** (What the product is)

- Cup Wraps
- Single Square
- Single Rectangle
- Other/Custom

**Physical Products:**

```yaml
Product Examples:

UVDTF Products:
  - UVDTF Cup Wraps:
      Print Method: UVDTF
      Product Type: Cup Wraps
      Sizes: 16oz, 12oz, 20oz
      Attributes:
        - Design name (UV001, UV002, etc.)
        - Cup size
        - Quantity
      Fulfillment: Print gangsheet → Ship physical product

  - UVDTF Single Square:
      Print Method: UVDTF
      Product Type: Single Square
      Sizes: 2x2", 3x3", 4x4"
      Attributes:
        - Design name
        - Size
        - Quantity
      Fulfillment: Print gangsheet → Ship

  - UVDTF Single Rectangle:
      Print Method: UVDTF
      Product Type: Single Rectangle
      Sizes: 3x5", 4x6", custom
      Attributes:
        - Design name
        - Size
        - Quantity
      Fulfillment: Print gangsheet → Ship

DTF Products:
  - DTF Cup Wraps:
      Print Method: DTF
      Product Type: Cup Wraps
      Similar to UVDTF but different printing process

Sublimation Products:
  - Sublimation Single Square:
      Print Method: Sublimation
      Product Type: Single Square
      For fabric, mugs, etc.

Vinyl Products:
  - Vinyl Decals:
      Print Method: Vinyl
      Product Type: Other/Custom
      Cut vinyl stickers

Custom/Other:
  - Custom Orders:
      Print Method: Other
      Product Type: Other/Custom
      Customer uploads design
      Choose print method and product type
      Fulfillment: Custom gangsheet → Ship
```

**Digital Products:**

```yaml
Digital Products:
  - Design Files:
      Print Method: N/A (Digital)
      Product Type: Other/Custom
      Attributes:
        - Design name
        - License type (personal/commercial)
        - File format (PNG, SVG, PDF)
      Fulfillment: Instant download link

  - Design Bundles:
      Print Method: N/A (Digital)
      Product Type: Other/Custom
      Multiple designs in themed collections
      Fulfillment: Instant download
```

### **Step 1.2: Database Schema Design**

Create file: `server/src/entities/ecommerce/`

**Core Tables:**

```python
# server/src/entities/ecommerce/product.py
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class ProductType(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"

class PrintMethod(str, Enum):
    """Print/production method - How the product is made"""
    UVDTF = "uvdtf"           # UV Direct to Film
    DTF = "dtf"               # Direct to Film
    SUBLIMATION = "sublimation"
    VINYL = "vinyl"
    OTHER = "other"
    DIGITAL = "digital"       # For digital products

class ProductCategory(str, Enum):
    """Product type - What the product is"""
    CUP_WRAPS = "cup_wraps"
    SINGLE_SQUARE = "single_square"
    SINGLE_RECTANGLE = "single_rectangle"
    OTHER_CUSTOM = "other_custom"

class Product(Base):
    __tablename__ = "ecommerce_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Info
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)  # URL-friendly name
    description = Column(Text)
    short_description = Column(String(500))

    # Product Classification (2-level hierarchy)
    product_type = Column(Enum(ProductType), nullable=False)  # physical or digital
    print_method = Column(Enum(PrintMethod), nullable=False)  # HOW it's made
    category = Column(Enum(ProductCategory), nullable=False)  # WHAT it is

    # Pricing
    price = Column(Float, nullable=False)  # Base price in USD
    compare_at_price = Column(Float)  # Original price (for sales)
    cost = Column(Float)  # Your cost (for profit tracking)

    # Inventory (for physical products)
    track_inventory = Column(Boolean, default=False)
    inventory_quantity = Column(Integer, default=0)
    allow_backorder = Column(Boolean, default=False)

    # Digital Product Info
    digital_file_url = Column(String(500))  # NAS path or download URL
    download_limit = Column(Integer, default=3)  # Max downloads per purchase

    # Images
    images = Column(JSON)  # Array of image URLs
    featured_image = Column(String(500))

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)

    # Variants (for sizes, colors, etc.)
    has_variants = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Integration with existing system
    design_id = Column(UUID(as_uuid=True), ForeignKey('design_images.id'))  # Link to your designs
    template_name = Column(String(100))  # UVDTF 16oz, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    variants = relationship("ProductVariant", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product")
    design = relationship("DesignImages")  # Link to existing design


class ProductVariant(Base):
    __tablename__ = "ecommerce_product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_products.id'))

    # Variant Info
    name = Column(String(255))  # "16oz", "12oz", "Red", etc.
    sku = Column(String(100), unique=True)

    # Pricing Override
    price = Column(Float)  # If different from base product

    # Inventory
    inventory_quantity = Column(Integer, default=0)

    # Options
    option1 = Column(String(100))  # Size
    option2 = Column(String(100))  # Color
    option3 = Column(String(100))  # Material

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="variants")


class Customer(Base):
    __tablename__ = "ecommerce_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Info
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255))  # Hashed password
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))

    # Marketing
    accepts_marketing = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # Stats
    total_spent = Column(Float, default=0)
    order_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relationships
    addresses = relationship("CustomerAddress", back_populates="customer")
    orders = relationship("Order", back_populates="customer")


class CustomerAddress(Base):
    __tablename__ = "ecommerce_customer_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'))

    # Address Info
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    address1 = Column(String(255))
    address2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    country = Column(String(100), default="United States")
    phone = Column(String(20))

    # Defaults
    is_default_shipping = Column(Boolean, default=False)
    is_default_billing = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="addresses")


class Order(Base):
    __tablename__ = "ecommerce_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True)  # ORD-2025-0001

    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'))

    # Guest Checkout Info (if customer_id is null)
    guest_email = Column(String(255))

    # Pricing
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0)
    shipping = Column(Float, default=0)
    discount = Column(Float, default=0)
    total = Column(Float, nullable=False)

    # Shipping Address
    shipping_address = Column(JSON)  # Store as JSON for flexibility

    # Billing Address
    billing_address = Column(JSON)

    # Payment
    payment_status = Column(String(50))  # pending, paid, failed, refunded
    payment_method = Column(String(50))  # stripe, paypal
    payment_id = Column(String(255))  # Stripe payment ID

    # Fulfillment
    fulfillment_status = Column(String(50))  # unfulfilled, fulfilled, shipped
    tracking_number = Column(String(255))
    tracking_url = Column(String(500))
    shipped_at = Column(DateTime)

    # Notes
    customer_note = Column(Text)
    internal_note = Column(Text)

    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, cancelled
    cancelled_at = Column(DateTime)
    cancel_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "ecommerce_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_orders.id'))
    product_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_products.id'))
    variant_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_product_variants.id'))

    # Item Details (snapshot at time of order)
    product_name = Column(String(255))
    variant_name = Column(String(255))
    sku = Column(String(100))

    # Pricing
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)

    # Digital Product
    download_url = Column(String(500))  # Generated download link
    download_count = Column(Integer, default=0)
    download_expires_at = Column(DateTime)

    # Custom Order Upload
    custom_design_url = Column(String(500))  # If customer uploaded design

    # Fulfillment
    is_fulfilled = Column(Boolean, default=False)
    gangsheet_generated = Column(Boolean, default=False)
    gangsheet_file_path = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")


class ShoppingCart(Base):
    __tablename__ = "ecommerce_shopping_carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'))
    session_id = Column(String(255))  # For guest carts

    # Cart Items (stored as JSON for simplicity)
    items = Column(JSON)  # [{product_id, variant_id, quantity, price}, ...]

    # Totals
    subtotal = Column(Float, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-delete after 30 days


class ProductReview(Base):
    __tablename__ = "ecommerce_product_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_products.id'))
    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'))

    # Review
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255))
    body = Column(Text)

    # Verification
    verified_purchase = Column(Boolean, default=False)

    # Moderation
    is_approved = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="reviews")
    customer = relationship("Customer")
```

### **Step 1.3: API Endpoint Planning**

**Public API (Storefront):**

```
GET    /api/storefront/products                    # List all products
       ?print_method=uvdtf                          # Filter by print method
       &category=cup_wraps                          # Filter by product type
       &featured=true                               # Filter featured only

GET    /api/storefront/products/:slug              # Get single product

GET    /api/storefront/products/print-method/:method  # Products by print method
       # Examples: /api/storefront/products/print-method/uvdtf
       #           /api/storefront/products/print-method/dtf

GET    /api/storefront/products/category/:category    # Products by category/type
       # Examples: /api/storefront/products/category/cup_wraps
       #           /api/storefront/products/category/single_square

GET    /api/storefront/products/search?q=          # Search products

POST   /api/storefront/cart/add                    # Add to cart
GET    /api/storefront/cart                        # Get cart
PUT    /api/storefront/cart/update                 # Update cart item
DELETE /api/storefront/cart/remove/:item_id        # Remove from cart

POST   /api/storefront/checkout/init               # Start checkout
POST   /api/storefront/checkout/payment            # Process payment
POST   /api/storefront/checkout/complete           # Complete order

POST   /api/storefront/auth/register               # Register customer
POST   /api/storefront/auth/login                  # Login
POST   /api/storefront/auth/logout                 # Logout

GET    /api/storefront/account/orders              # Customer orders
GET    /api/storefront/account/orders/:id          # Order details
GET    /api/storefront/account/profile             # Customer profile
PUT    /api/storefront/account/profile             # Update profile
```

**Admin API (Your Management):**

```
GET    /api/admin/products                         # List products (with filters)
POST   /api/admin/products                         # Create product
PUT    /api/admin/products/:id                     # Update product
DELETE /api/admin/products/:id                     # Delete product

GET    /api/admin/orders                           # List orders
GET    /api/admin/orders/:id                       # Order details
PUT    /api/admin/orders/:id/fulfill               # Mark fulfilled
POST   /api/admin/orders/:id/refund                # Process refund

GET    /api/admin/customers                        # List customers
GET    /api/admin/customers/:id                    # Customer details

GET    /api/admin/analytics/sales                  # Sales analytics
GET    /api/admin/analytics/products               # Product performance
```

### **Step 1.4: Frontend Wireframes**

**Storefront Pages:**

1. **Home Page** - Featured products, categories
2. **Product Catalog** - Grid view with filters
3. **Product Detail** - Images, description, add to cart
4. **Shopping Cart** - Cart items, totals, checkout button
5. **Checkout** - Shipping, payment, review
6. **Order Confirmation** - Thank you page with order details
7. **Customer Account** - Order history, profile, addresses
8. **Category Pages** - Products by category

**Admin Pages:**

1. **Products Dashboard** - List, add, edit products
2. **Orders Dashboard** - Order management
3. **Customers Dashboard** - Customer list
4. **Analytics** - Sales charts, top products

---

## 🔨 Phase 2: Database & Backend API (Week 3-4)

### **Goals**

- [ ] Create database migration
- [ ] Build backend API endpoints
- [ ] Implement authentication
- [ ] Set up Stripe integration
- [ ] Test API with Postman

### **Step 2.1: Database Migration**

Create migration file:

```bash
cd /Users/fserrano/Documents/Projects/etsy_seller_automater/server

# Create new migration
alembic revision -m "add_ecommerce_tables"
```

Edit migration file: `alembic/versions/xxx_add_ecommerce_tables.py`

```python
"""add_ecommerce_tables

Revision ID: xxx
Revises: yyy
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

def upgrade():
    # Create ecommerce_products table
    op.create_table(
        'ecommerce_products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('short_description', sa.String(500)),
        sa.Column('product_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('compare_at_price', sa.Float),
        sa.Column('cost', sa.Float),
        sa.Column('track_inventory', sa.Boolean, default=False),
        sa.Column('inventory_quantity', sa.Integer, default=0),
        sa.Column('allow_backorder', sa.Boolean, default=False),
        sa.Column('digital_file_url', sa.String(500)),
        sa.Column('download_limit', sa.Integer, default=3),
        sa.Column('images', JSON),
        sa.Column('featured_image', sa.String(500)),
        sa.Column('meta_title', sa.String(255)),
        sa.Column('meta_description', sa.Text),
        sa.Column('has_variants', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('design_id', UUID(as_uuid=True)),
        sa.Column('template_name', sa.String(100)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )

    # Add foreign key to existing design_images table
    op.create_foreign_key(
        'fk_products_design_id',
        'ecommerce_products', 'design_images',
        ['design_id'], ['id']
    )

    # Create indexes
    op.create_index('idx_products_slug', 'ecommerce_products', ['slug'])
    op.create_index('idx_products_category', 'ecommerce_products', ['category'])
    op.create_index('idx_products_active', 'ecommerce_products', ['is_active'])

    # Create other tables...
    # (Similar for ProductVariant, Customer, Order, etc.)

def downgrade():
    op.drop_table('ecommerce_products')
    # Drop other tables...
```

Run migration:

```bash
alembic upgrade head
```

### **Step 2.2: Create Backend Routes**

File structure:

```
server/src/routes/
├── ecommerce/
│   ├── __init__.py
│   ├── products.py        # Product endpoints
│   ├── cart.py           # Shopping cart
│   ├── checkout.py       # Checkout & payment
│   ├── customers.py      # Customer auth & account
│   ├── orders.py         # Order management
│   └── admin.py          # Admin dashboard
```

**Example: Products API**

`server/src/routes/ecommerce/products.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from server.src.database.core import get_db
from server.src.entities.ecommerce.product import Product, ProductCategory, PrintMethod
from pydantic import BaseModel

router = APIRouter(
    prefix='/api/storefront/products',
    tags=['Storefront - Products']
)

# Pydantic models
class ProductListResponse(BaseModel):
    id: str
    name: str
    slug: str
    short_description: str
    price: float
    compare_at_price: Optional[float]
    featured_image: str
    print_method: str      # NEW: UVDTF, DTF, Sublimation, etc.
    category: str          # NEW: Cup Wraps, Single Square, etc.
    is_featured: bool

    class Config:
        from_attributes = True

class ProductDetailResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    short_description: str
    price: float
    compare_at_price: Optional[float]
    images: List[str]
    featured_image: str
    print_method: str      # NEW: Print method
    category: str          # NEW: Product type
    product_type: str      # physical or digital
    has_variants: bool
    variants: List[dict]
    inventory_quantity: int
    track_inventory: bool
    meta_title: str
    meta_description: str

    class Config:
        from_attributes = True

@router.get('/', response_model=List[ProductListResponse])
async def list_products(
    print_method: Optional[str] = None,  # NEW: Filter by print method
    category: Optional[str] = None,      # Filter by product type
    featured: Optional[bool] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get list of products for storefront.
    Supports filtering by:
    - print_method: uvdtf, dtf, sublimation, vinyl, other
    - category: cup_wraps, single_square, single_rectangle, other_custom
    - featured: true/false
    """
    query = db.query(Product).filter(Product.is_active == True)

    # Filter by print method (HOW it's made)
    if print_method:
        query = query.filter(Product.print_method == print_method)

    # Filter by category/product type (WHAT it is)
    if category:
        query = query.filter(Product.category == category)

    if featured is not None:
        query = query.filter(Product.is_featured == featured)

    # Order by featured first, then by created date
    query = query.order_by(
        Product.is_featured.desc(),
        Product.created_at.desc()
    )

    products = query.offset(offset).limit(limit).all()

    return products

@router.get('/{slug}', response_model=ProductDetailResponse)
async def get_product(slug: str, db: Session = Depends(get_db)):
    """
    Get single product by slug.
    Returns full product details including variants.
    """
    product = db.query(Product).filter(
        Product.slug == slug,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

@router.get('/print-method/{method}')
async def get_products_by_print_method(
    method: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get products by print method (HOW they're made).

    Valid methods: uvdtf, dtf, sublimation, vinyl, other
    Example: /api/storefront/products/print-method/uvdtf
    """
    products = db.query(Product).filter(
        Product.print_method == method,
        Product.is_active == True
    ).offset(offset).limit(limit).all()

    return products

@router.get('/category/{category}')
async def get_products_by_category(
    category: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get products by category/product type (WHAT they are).

    Valid categories: cup_wraps, single_square, single_rectangle, other_custom
    Example: /api/storefront/products/category/cup_wraps
    """
    products = db.query(Product).filter(
        Product.category == category,
        Product.is_active == True
    ).offset(offset).limit(limit).all()

    return products

@router.get('/search')
async def search_products(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    Search products by name or description.
    """
    search_term = f"%{q}%"

    products = db.query(Product).filter(
        Product.is_active == True,
        (Product.name.ilike(search_term) |
         Product.description.ilike(search_term))
    ).limit(limit).all()

    return products
```

**📄 Continue to:** [ECOMMERCE_PLATFORM_GUIDE_PART2.md](./ECOMMERCE_PLATFORM_GUIDE_PART2.md) for Shopping Cart, Stripe Integration, and Customer Authentication implementation.

---
