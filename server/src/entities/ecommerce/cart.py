"""Shopping cart entity for ecommerce platform."""

from sqlalchemy import Column, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from server.src.database.core import Base


class ShoppingCart(Base):
    """Shopping cart model."""

    __tablename__ = "ecommerce_shopping_carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'))
    session_id = Column(String(255), index=True)  # For guest carts

    # Cart Items (stored as JSON for simplicity)
    # [{id, product_id, variant_id, quantity, price, product_name, variant_name, image}, ...]
    items = Column(JSON, default=list)

    # Totals
    subtotal = Column(Float, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-delete after 30 days

    def __repr__(self):
        return f"<ShoppingCart session={self.session_id} items={len(self.items or [])}>"
