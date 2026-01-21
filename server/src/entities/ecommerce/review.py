"""Product review entity for ecommerce platform."""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from server.src.database.core import Base


class ProductReview(Base):
    """Product review model."""

    __tablename__ = "ecommerce_product_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_products.id'), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('ecommerce_customers.id'), nullable=False)

    # Review
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255))
    body = Column(Text)

    # Verification
    verified_purchase = Column(Boolean, default=False)

    # Moderation
    is_approved = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="reviews")
    customer = relationship("Customer")

    def __repr__(self):
        return f"<ProductReview {self.rating}★ for {self.product_id}>"
