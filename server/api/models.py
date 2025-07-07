import os
import json
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
from pydantic import BaseModel

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

# Create tables
Base.metadata.create_all(bind=engine)

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