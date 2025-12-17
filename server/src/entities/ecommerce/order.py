"""Order entity models for ecommerce platform."""

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from server.src.database.core import Base


class Order(Base):
    """Order model for ecommerce platform."""

    __tablename__ = "ecommerce_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)

    # Owner/Isolation
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For multi-tenant isolation

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
    shipping_address = Column(JSON)

    # Billing Address
    billing_address = Column(JSON)

    # Payment
    payment_status = Column(String(50), default="pending")  # pending, paid, failed, refunded
    payment_method = Column(String(50))  # stripe, paypal
    payment_id = Column(String(255))  # Stripe payment ID

    # Fulfillment
    fulfillment_status = Column(String(50), default="unfulfilled")  # unfulfilled, fulfilled, shipped
    tracking_number = Column(String(255))
    tracking_url = Column(String(500))
    shipped_at = Column(DateTime)

    # Notes
    customer_note = Column(Text)
    internal_note = Column(Text)

    # Status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, cancelled
    cancelled_at = Column(DateTime)
    cancel_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(Base):
    """Order item model."""

    __tablename__ = "ecommerce_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_orders.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_products.id'))
    variant_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_product_variants.id'))

    # Item Details (snapshot at time of order)
    product_name = Column(String(255), nullable=False)
    variant_name = Column(String(255))
    sku = Column(String(100))

    # Pricing
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)

    # Digital Product
    download_url = Column(String(500))
    download_count = Column(Integer, default=0)
    download_expires_at = Column(DateTime)

    # Custom Order Upload
    custom_design_url = Column(String(500))

    # Fulfillment
    is_fulfilled = Column(Boolean, default=False)
    gangsheet_generated = Column(Boolean, default=False)
    gangsheet_file_path = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"
