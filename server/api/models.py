import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

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
    root_folder = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tokens = relationship('OAuthToken', back_populates='user')
    mask_data_path = Column(String, nullable=True)
    mockup_blank_path = Column(String, nullable=True)
    watermark_path = Column(String, nullable=True)

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

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 