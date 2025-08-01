import os
import json
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/etsydb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    root_folder = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tokens = relationship('OAuthToken', back_populates='user')
    mask_data_path = Column(String, nullable=True)
    mockup_blank_path = Column(String, nullable=True)
    watermark_path = Column(String, nullable=True)
    etsy_templates = relationship('EtsyTemplate', order_by='EtsyTemplate.id', back_populates='user')
    mockup_masks = relationship('MockupMaskData', order_by='MockupMaskData.id', back_populates='user')
    mockup_images = relationship('MockupImage', order_by='MockupImage.id', back_populates='user')
    canvas_configs = relationship('CanvasConfig', order_by='CanvasConfig.id', back_populates='user')
    size_configs = relationship('SizeConfig', order_by='SizeConfig.id', back_populates='user')

class OAuthToken(Base):
    __tablename__ = 'oauth_tokens'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship('User', back_populates='tokens')
    __table_args__ = (UniqueConstraint('user_id', 'access_token', name='_user_token_uc'),)

class CanvasConfig(Base):
    __tablename__ = 'canvas_configs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    template_name = Column(String, nullable=False)  # e.g., 'UVDTF Decal'
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship('User', back_populates='canvas_configs')
    __table_args__ = (UniqueConstraint('user_id', 'template_name', name='_user_canvas_template_uc'),)

class SizeConfig(Base):
    __tablename__ = 'size_configs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    template_name = Column(String, nullable=False)  # e.g., 'UVDTF 16oz'
    size_name = Column(String, nullable=True)  # e.g., 'Adult+', 'Adult', 'Youth', 'Toddler', 'Pocket'
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship('User', back_populates='size_configs')
    __table_args__ = (UniqueConstraint('user_id', 'template_name', 'size_name', name='_user_size_template_uc'),)

class EtsyTemplate(Base):
    __tablename__ = 'etsy_templates'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)  # e.g., 'UVDTF 16oz'
    template_title = Column(String, nullable=True)  # User-friendly template name/key
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    who_made = Column(String, nullable=True)
    when_made = Column(String, nullable=True)
    taxonomy_id = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    materials = Column(Text, nullable=True)  # Store as comma-separated or JSON string
    shop_section_id = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)  # Store as comma-separated or JSON string
    item_weight = Column(Float, nullable=True)
    item_weight_unit = Column(String, nullable=True)
    item_length = Column(Float, nullable=True)
    item_width = Column(Float, nullable=True)
    item_height = Column(Float, nullable=True)
    item_dimensions_unit = Column(String, nullable=True)
    is_taxable = Column(Boolean, nullable=True)
    type = Column(String, nullable=True)
    processing_min = Column(Integer, nullable=True)
    processing_max = Column(Integer, nullable=True)
    return_policy_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship('User', back_populates='etsy_templates')

class MockupMaskData(Base):
    __tablename__ = 'mockup_mask_data'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    template_name = Column(String, nullable=False)  # e.g., 'UVDTF 16oz' - same as EtsyTemplate.name
    masks = Column(JSON, nullable=False)  # Store mask data as JSON array
    points = Column(JSON, nullable=False)  # Store points data as JSON array
    starting_name = Column(Integer, default=100)  # Starting ID for generated files
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship('User', back_populates='mockup_masks')

class MockupImage(Base):
    __tablename__ = 'mockup_images'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    template_name = Column(String, nullable=False)  # e.g., 'UVDTF 16oz'
    filename = Column(String, nullable=False)  # Original filename
    file_path = Column(String, nullable=False)  # Full path to the mockup image
    mask_data = Column(JSON, nullable=True)  # Store mask data as JSON
    points_data = Column(JSON, nullable=True)  # Store points data as JSON
    image_type = Column(String, nullable=True)  # e.g., 'UVDTF 16oz'
    design_id = Column(String, nullable=True)  # ID of the design this mockup was created from
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship('User', back_populates='mockup_images')
    __table_args__ = (UniqueConstraint('user_id', 'filename', name='_user_mockup_filename_uc'),)

# Create tables
# Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    email: str
    password: str
    shop_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class CanvasConfigCreate(BaseModel):
    template_name: str
    width_inches: float
    height_inches: float
    description: Optional[str] = None

class CanvasConfigUpdate(BaseModel):
    template_name: Optional[str] = None
    width_inches: Optional[float] = None
    height_inches: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CanvasConfigOut(BaseModel):
    id: int
    template_name: str
    width_inches: float
    height_inches: float
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SizeConfigCreate(BaseModel):
    template_name: str
    size_name: Optional[str] = None
    width_inches: float
    height_inches: float
    description: Optional[str] = None

class SizeConfigUpdate(BaseModel):
    template_name: Optional[str] = None
    size_name: Optional[str] = None
    width_inches: Optional[float] = None
    height_inches: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SizeConfigOut(BaseModel):
    id: int
    template_name: str
    size_name: Optional[str] = None
    width_inches: float
    height_inches: float
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 