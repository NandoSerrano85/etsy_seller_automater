"""Product entity models for ecommerce platform."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from server.src.database.core import Base


class ProductType(str, enum.Enum):
    """Product type - Physical or Digital."""
    PHYSICAL = "physical"
    DIGITAL = "digital"


class PrintMethod(str, enum.Enum):
    """Print/production method - HOW the product is made."""
    UVDTF = "uvdtf"           # UV Direct to Film
    DTF = "dtf"               # Direct to Film
    SUBLIMATION = "sublimation"
    VINYL = "vinyl"
    OTHER = "other"
    DIGITAL = "digital"       # For digital products


class ProductCategory(str, enum.Enum):
    """Product category - WHAT the product is."""
    CUP_WRAPS = "cup_wraps"
    SINGLE_SQUARE = "single_square"
    SINGLE_RECTANGLE = "single_rectangle"
    OTHER_CUSTOM = "other_custom"


class Product(Base):
    """Product model for ecommerce platform."""

    __tablename__ = "ecommerce_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Info
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    short_description = Column(String(500))

    # Product Classification (2-level hierarchy)
    product_type = Column(String(50), nullable=False)  # physical or digital
    print_method = Column(String(50), nullable=False, index=True)  # HOW it's made
    category = Column(String(50), nullable=False, index=True)  # WHAT it is

    # Pricing
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float)
    cost = Column(Float)

    # Inventory (for physical products)
    track_inventory = Column(Boolean, default=False)
    inventory_quantity = Column(Integer, default=0)
    allow_backorder = Column(Boolean, default=False)

    # Digital Product Info
    digital_file_url = Column(String(500))
    download_limit = Column(Integer, default=3)

    # Images
    images = Column(JSON)  # Array of image URLs
    featured_image = Column(String(500))

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)

    # Variants
    has_variants = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)

    # Integration with existing system
    design_id = Column(UUID(as_uuid=True))
    template_name = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name} ({self.slug})>"


class ProductVariant(Base):
    """Product variant model for different sizes, colors, etc."""

    __tablename__ = "ecommerce_product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_products.id'), nullable=False)

    # Variant Info
    name = Column(String(255), nullable=False)  # "16oz", "12oz", "Red", etc.
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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="variants")

    def __repr__(self):
        return f"<ProductVariant {self.name} for {self.product_id}>"
