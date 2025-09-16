from sqlalchemy import Column, DateTime, func, ForeignKey, Text, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class ShopifyStore(Base):
    __tablename__ = 'shopify_stores'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    shop_domain = Column(String(255), nullable=False)
    shop_name = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='shopify_stores')
    products = relationship('ShopifyProduct', back_populates='store')