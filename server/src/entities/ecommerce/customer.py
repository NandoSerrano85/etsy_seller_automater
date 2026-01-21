"""Customer entity models for ecommerce platform."""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from server.src.database.core import Base


class Customer(Base):
    """Customer model for ecommerce platform."""

    __tablename__ = "ecommerce_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Owner/Isolation
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For multi-tenant isolation

    # Basic Info
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
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
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.email}>"


class CustomerAddress(Base):
    """Customer address model."""

    __tablename__ = "ecommerce_customer_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'), nullable=False)

    # Address Info
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    address1 = Column(String(255), nullable=False)
    address2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), default="United States")
    phone = Column(String(20))

    # Defaults
    is_default_shipping = Column(Boolean, default=False)
    is_default_billing = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="addresses")

    def __repr__(self):
        return f"<CustomerAddress {self.city}, {self.state}>"
