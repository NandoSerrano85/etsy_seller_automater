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
