from sqlalchemy import Column, DateTime, func, ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class EtsyStore(Base):
    """
    Stores Etsy shop/store business information.
    Separated from authentication credentials in PlatformConnection.
    """
    __tablename__ = 'etsy_stores'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey('platform_connections.id'), nullable=False)

    # Etsy store identification
    etsy_shop_id = Column(String(50), nullable=False, unique=True)  # Etsy's internal shop ID
    shop_name = Column(String(255), nullable=False)  # Display name of the shop

    # Store information
    shop_url = Column(String(255), nullable=True)  # Full URL to the Etsy shop
    currency_code = Column(String(3), nullable=True)  # ISO currency code (USD, EUR, etc.)
    country_code = Column(String(2), nullable=True)  # ISO country code
    language = Column(String(10), nullable=True)  # Shop language

    # Store status
    is_active = Column(Boolean, default=True, nullable=False)
    is_vacation_mode = Column(Boolean, default=False, nullable=False)

    # Store metrics (optional, can be updated periodically)
    total_listings = Column(Integer, nullable=True)
    total_sales = Column(Integer, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - TODO: Fix after implementing proper User relationships
    # user = relationship('User', back_populates='etsy_stores')
    # connection = relationship('PlatformConnection', back_populates='etsy_stores')

    def __repr__(self):
        return f"<EtsyStore(id={self.id}, shop_name={self.shop_name}, etsy_shop_id={self.etsy_shop_id})>"