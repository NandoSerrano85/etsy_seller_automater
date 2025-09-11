from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    etsy_shop_id = Column(String, nullable=True)  # Store Etsy shop ID
    is_active = Column(Boolean, default=True)
    root_folder = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    third_party_tokens = relationship('ThirdPartyOAuthToken', back_populates='user')
    etsy_product_templates = relationship('EtsyProductTemplate', order_by='EtsyProductTemplate.id', back_populates='user')
    mockups = relationship('Mockups', order_by='Mockups.id', back_populates='user')
    design_images = relationship('DesignImages', order_by='DesignImages.id', back_populates='user')