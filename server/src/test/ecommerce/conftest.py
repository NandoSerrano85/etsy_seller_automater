"""Test fixtures for ecommerce tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from server.src.database.core import Base, get_db
from server.main import app
from server.src.entities.ecommerce.product import Product, ProductVariant
from server.src.entities.ecommerce.customer import Customer, CustomerAddress
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.entities.ecommerce.cart import ShoppingCart
from server.src.entities.ecommerce.review import ProductReview


# ============================================================================
# Database Setup
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create only ecommerce tables (not all tables in Base.metadata)
    # This avoids issues with PostgreSQL-specific types like JSONB
    Product.__table__.create(bind=engine, checkfirst=True)
    ProductVariant.__table__.create(bind=engine, checkfirst=True)
    Customer.__table__.create(bind=engine, checkfirst=True)
    CustomerAddress.__table__.create(bind=engine, checkfirst=True)
    Order.__table__.create(bind=engine, checkfirst=True)
    OrderItem.__table__.create(bind=engine, checkfirst=True)
    ShoppingCart.__table__.create(bind=engine, checkfirst=True)
    ProductReview.__table__.create(bind=engine, checkfirst=True)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop only ecommerce tables
        ProductReview.__table__.drop(bind=engine, checkfirst=True)
        ShoppingCart.__table__.drop(bind=engine, checkfirst=True)
        OrderItem.__table__.drop(bind=engine, checkfirst=True)
        Order.__table__.drop(bind=engine, checkfirst=True)
        CustomerAddress.__table__.drop(bind=engine, checkfirst=True)
        Customer.__table__.drop(bind=engine, checkfirst=True)
        ProductVariant.__table__.drop(bind=engine, checkfirst=True)
        Product.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Product Fixtures
# ============================================================================

@pytest.fixture
def sample_uvdtf_cup_wrap(test_db):
    """Create a sample UVDTF cup wrap product."""
    product = Product(
        id=uuid.uuid4(),
        name="UVDTF Cup Wrap - Floral Design - 16oz",
        slug="uvdtf-cup-wrap-floral-16oz",
        description="Beautiful floral design UVDTF cup wrap for 16oz cups",
        short_description="Floral UVDTF wrap for 16oz cups",
        product_type="physical",
        print_method="uvdtf",
        category="cup_wraps",
        price=12.99,
        compare_at_price=15.99,
        cost=5.00,
        track_inventory=True,
        inventory_quantity=50,
        allow_backorder=False,
        images=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        featured_image="https://example.com/featured.jpg",
        meta_title="UVDTF Floral Cup Wrap 16oz",
        meta_description="High-quality UVDTF cup wrap with floral design",
        has_variants=True,
        is_active=True,
        is_featured=True,
        template_name="UVDTF 16oz"
    )

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    return product


@pytest.fixture
def sample_dtf_square(test_db):
    """Create a sample DTF single square product."""
    product = Product(
        id=uuid.uuid4(),
        name="DTF Transfer - Square - 3x3 inch",
        slug="dtf-square-3x3",
        description="High-quality DTF transfer in 3x3 inch square format",
        short_description="DTF square transfer 3x3\"",
        product_type="physical",
        print_method="dtf",
        category="single_square",
        price=8.99,
        compare_at_price=None,
        cost=3.50,
        track_inventory=True,
        inventory_quantity=100,
        featured_image="https://example.com/dtf-square.jpg",
        is_active=True,
        is_featured=False
    )

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    return product


@pytest.fixture
def sample_digital_product(test_db):
    """Create a sample digital product."""
    product = Product(
        id=uuid.uuid4(),
        name="Digital Design Pack - Summer Vibes",
        slug="digital-summer-vibes",
        description="Collection of 10 summer-themed designs for personal use",
        short_description="Summer-themed digital designs",
        product_type="digital",
        print_method="digital",
        category="other_custom",
        price=24.99,
        digital_file_url="https://example.com/downloads/summer-pack.zip",
        download_limit=3,
        images=["https://example.com/preview1.jpg"],
        featured_image="https://example.com/summer-preview.jpg",
        is_active=True,
        is_featured=True
    )

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    return product


@pytest.fixture
def sample_product_variants(test_db, sample_uvdtf_cup_wrap):
    """Create sample product variants for the UVDTF cup wrap."""
    variants = []

    # 16oz variant
    variant_16oz = ProductVariant(
        id=uuid.uuid4(),
        product_id=sample_uvdtf_cup_wrap.id,
        name="16oz",
        sku="UVDTF-FLORAL-16OZ",
        price=12.99,
        inventory_quantity=30,
        option1="16oz",
        is_active=True
    )

    # 12oz variant
    variant_12oz = ProductVariant(
        id=uuid.uuid4(),
        product_id=sample_uvdtf_cup_wrap.id,
        name="12oz",
        sku="UVDTF-FLORAL-12OZ",
        price=10.99,
        inventory_quantity=20,
        option1="12oz",
        is_active=True
    )

    variants.extend([variant_16oz, variant_12oz])
    test_db.add_all(variants)
    test_db.commit()

    return variants


@pytest.fixture
def inactive_product(test_db):
    """Create an inactive product (should not appear in queries)."""
    product = Product(
        id=uuid.uuid4(),
        name="Inactive Product",
        slug="inactive-product",
        description="This product is inactive",
        product_type="physical",
        print_method="vinyl",
        category="other_custom",
        price=5.99,
        is_active=False
    )

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    return product


@pytest.fixture
def multiple_products(test_db):
    """Create multiple products for testing filtering and pagination."""
    products = []

    # UVDTF products
    for i in range(5):
        product = Product(
            id=uuid.uuid4(),
            name=f"UVDTF Product {i+1}",
            slug=f"uvdtf-product-{i+1}",
            description=f"UVDTF product number {i+1}",
            product_type="physical",
            print_method="uvdtf",
            category="cup_wraps" if i % 2 == 0 else "single_rectangle",
            price=10.00 + i,
            is_active=True,
            is_featured=(i == 0)
        )
        products.append(product)

    # DTF products
    for i in range(3):
        product = Product(
            id=uuid.uuid4(),
            name=f"DTF Product {i+1}",
            slug=f"dtf-product-{i+1}",
            description=f"DTF product number {i+1}",
            product_type="physical",
            print_method="dtf",
            category="single_square",
            price=15.00 + i,
            is_active=True,
            is_featured=False
        )
        products.append(product)

    # Sublimation products
    for i in range(2):
        product = Product(
            id=uuid.uuid4(),
            name=f"Sublimation Product {i+1}",
            slug=f"sublimation-product-{i+1}",
            description=f"Sublimation product number {i+1}",
            product_type="physical",
            print_method="sublimation",
            category="cup_wraps",
            price=20.00 + i,
            is_active=True,
            is_featured=False
        )
        products.append(product)

    test_db.add_all(products)
    test_db.commit()

    return products


# ============================================================================
# Customer Fixtures
# ============================================================================

@pytest.fixture
def sample_customer(test_db):
    """Create a sample customer."""
    customer = Customer(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        first_name="John",
        last_name="Doe",
        phone="555-1234",
        accepts_marketing=True,
        is_active=True,
        email_verified=True
    )

    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)

    return customer


@pytest.fixture
def sample_customer_addresses(test_db, sample_customer):
    """Create sample addresses for customer."""
    addresses = []

    # Default shipping address
    shipping_address = CustomerAddress(
        id=uuid.uuid4(),
        customer_id=sample_customer.id,
        first_name="John",
        last_name="Doe",
        address1="123 Main St",
        address2="Apt 4B",
        city="New York",
        state="NY",
        zip_code="10001",
        country="United States",
        phone="555-1234",
        is_default_shipping=True,
        is_default_billing=False
    )

    # Billing address
    billing_address = CustomerAddress(
        id=uuid.uuid4(),
        customer_id=sample_customer.id,
        first_name="John",
        last_name="Doe",
        address1="456 Oak Ave",
        city="Brooklyn",
        state="NY",
        zip_code="11201",
        country="United States",
        phone="555-5678",
        is_default_shipping=False,
        is_default_billing=True
    )

    addresses.extend([shipping_address, billing_address])
    test_db.add_all(addresses)
    test_db.commit()

    return addresses


# ============================================================================
# Shopping Cart Fixtures
# ============================================================================

@pytest.fixture
def sample_cart(test_db, sample_customer, sample_uvdtf_cup_wrap):
    """Create a sample shopping cart with items."""
    cart = ShoppingCart(
        id=uuid.uuid4(),
        customer_id=sample_customer.id,
        session_id=None,
        items=[
            {
                "id": str(uuid.uuid4()),
                "product_id": str(sample_uvdtf_cup_wrap.id),
                "product_name": sample_uvdtf_cup_wrap.name,
                "product_slug": sample_uvdtf_cup_wrap.slug,
                "variant_id": None,
                "variant_name": None,
                "price": sample_uvdtf_cup_wrap.price,
                "quantity": 2,
                "subtotal": sample_uvdtf_cup_wrap.price * 2,
                "image": sample_uvdtf_cup_wrap.featured_image
            }
        ],
        subtotal=sample_uvdtf_cup_wrap.price * 2,
        is_active=True
    )

    test_db.add(cart)
    test_db.commit()
    test_db.refresh(cart)

    return cart


@pytest.fixture
def guest_cart(test_db, sample_dtf_square):
    """Create a guest shopping cart (no customer)."""
    session_id = f"guest-{uuid.uuid4()}"

    cart = ShoppingCart(
        id=uuid.uuid4(),
        customer_id=None,
        session_id=session_id,
        items=[
            {
                "id": str(uuid.uuid4()),
                "product_id": str(sample_dtf_square.id),
                "product_name": sample_dtf_square.name,
                "product_slug": sample_dtf_square.slug,
                "variant_id": None,
                "variant_name": None,
                "price": sample_dtf_square.price,
                "quantity": 1,
                "subtotal": sample_dtf_square.price,
                "image": sample_dtf_square.featured_image
            }
        ],
        subtotal=sample_dtf_square.price,
        is_active=True
    )

    test_db.add(cart)
    test_db.commit()
    test_db.refresh(cart)

    return cart


# ============================================================================
# Order Fixtures
# ============================================================================

@pytest.fixture
def sample_order(test_db, sample_customer, sample_uvdtf_cup_wrap):
    """Create a sample order."""
    order = Order(
        id=uuid.uuid4(),
        order_number=f"ORD-TEST-{uuid.uuid4().hex[:8].upper()}",
        customer_id=sample_customer.id,
        guest_email=None,
        subtotal=25.98,
        tax=2.08,
        shipping=5.99,
        discount=0,
        total=34.05,
        shipping_address={
            "first_name": "John",
            "last_name": "Doe",
            "address1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "United States"
        },
        billing_address={
            "first_name": "John",
            "last_name": "Doe",
            "address1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "United States"
        },
        payment_status="paid",
        payment_method="stripe",
        payment_id="pi_test_123456",
        fulfillment_status="unfulfilled",
        status="processing"
    )

    test_db.add(order)
    test_db.flush()

    # Add order item
    order_item = OrderItem(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=sample_uvdtf_cup_wrap.id,
        variant_id=None,
        product_name=sample_uvdtf_cup_wrap.name,
        variant_name=None,
        sku="UVDTF-001",
        price=12.99,
        quantity=2,
        total=25.98,
        is_fulfilled=False
    )

    test_db.add(order_item)
    test_db.commit()
    test_db.refresh(order)

    return order


@pytest.fixture
def guest_order(test_db, sample_dtf_square):
    """Create a guest order (no customer account)."""
    order = Order(
        id=uuid.uuid4(),
        order_number=f"ORD-GUEST-{uuid.uuid4().hex[:8].upper()}",
        customer_id=None,
        guest_email="guest@example.com",
        subtotal=8.99,
        tax=0.72,
        shipping=5.99,
        discount=0,
        total=15.70,
        shipping_address={
            "first_name": "Guest",
            "last_name": "User",
            "address1": "789 Guest St",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90001",
            "country": "United States"
        },
        billing_address={
            "first_name": "Guest",
            "last_name": "User",
            "address1": "789 Guest St",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90001",
            "country": "United States"
        },
        payment_status="paid",
        payment_method="stripe",
        payment_id="pi_guest_123456",
        fulfillment_status="unfulfilled",
        status="processing"
    )

    test_db.add(order)
    test_db.flush()

    # Add order item
    order_item = OrderItem(
        id=uuid.uuid4(),
        order_id=order.id,
        product_id=sample_dtf_square.id,
        variant_id=None,
        product_name=sample_dtf_square.name,
        variant_name=None,
        sku="DTF-001",
        price=8.99,
        quantity=1,
        total=8.99,
        is_fulfilled=False
    )

    test_db.add(order_item)
    test_db.commit()
    test_db.refresh(order)

    return order


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_token(sample_customer):
    """Generate a JWT token for authenticated requests."""
    import jwt
    from datetime import datetime, timedelta
    import os

    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'test-secret-key')

    expires_delta = timedelta(minutes=60)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(sample_customer.id),
        "email": sample_customer.email,
        "exp": expire,
        "type": "ecommerce_customer"
    }

    token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Generate authorization headers for authenticated requests."""
    return {
        "Authorization": f"Bearer {auth_token}"
    }


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_product(test_db, **kwargs):
    """Helper function to create a test product with custom fields."""
    defaults = {
        "id": uuid.uuid4(),
        "name": "Test Product",
        "slug": f"test-product-{uuid.uuid4().hex[:8]}",
        "product_type": "physical",
        "print_method": "uvdtf",
        "category": "cup_wraps",
        "price": 9.99,
        "is_active": True
    }

    defaults.update(kwargs)
    product = Product(**defaults)

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    return product


def create_test_customer(test_db, **kwargs):
    """Helper function to create a test customer with custom fields."""
    import bcrypt

    defaults = {
        "id": uuid.uuid4(),
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "email_verified": True
    }

    defaults.update(kwargs)
    customer = Customer(**defaults)

    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)

    return customer
