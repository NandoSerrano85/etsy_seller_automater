"""
Migration to create canvas and size configuration tables.
"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from dotenv import load_dotenv

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/etsydb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    __table_args__ = (UniqueConstraint('user_id', 'template_name', 'size_name', name='_user_size_template_uc'),)

def run_migration():
    """Run the migration to create the new tables."""
    try:
        print("Creating canvas_configs and size_configs tables...")
        Base.metadata.create_all(bind=engine)
        print("Migration completed successfully!")
        
        # Insert some default configurations
        db = SessionLocal()
        try:
            # Get the first user (assuming there's at least one user)
            from server.api.models import User
            user = db.query(User).first()
            
            if user:
                print(f"Adding default configurations for user: {user.shop_name}")
                
                # Add default canvas configurations
                default_canvas_configs = [
                    {
                        'template_name': 'UVDTF Decal',
                        'width_inches': 4.0,
                        'height_inches': 4.0,
                        'description': 'Default 4x4 inch decal canvas'
                    }
                ]
                
                for config_data in default_canvas_configs:
                    existing = db.query(CanvasConfig).filter(
                        CanvasConfig.user_id == user.id,
                        CanvasConfig.template_name == config_data['template_name']
                    ).first()
                    
                    if not existing:
                        canvas_config = CanvasConfig(
                            user_id=user.id,
                            **config_data
                        )
                        db.add(canvas_config)
                
                # Add default size configurations
                default_size_configs = [
                    {
                        'template_name': 'UVDTF 16oz',
                        'size_name': None,
                        'width_inches': 9.5,
                        'height_inches': 4.33,
                        'description': 'Default 16oz cup wrap size'
                    },
                    {
                        'template_name': 'DTF',
                        'size_name': 'Adult+',
                        'width_inches': 12.0,
                        'height_inches': 16.0,
                        'description': 'Adult+ DTF transfer size'
                    },
                    {
                        'template_name': 'DTF',
                        'size_name': 'Adult',
                        'width_inches': 10.0,
                        'height_inches': 14.0,
                        'description': 'Adult DTF transfer size'
                    },
                    {
                        'template_name': 'DTF',
                        'size_name': 'Youth',
                        'width_inches': 8.0,
                        'height_inches': 12.0,
                        'description': 'Youth DTF transfer size'
                    }
                ]
                
                for config_data in default_size_configs:
                    existing = db.query(SizeConfig).filter(
                        SizeConfig.user_id == user.id,
                        SizeConfig.template_name == config_data['template_name'],
                        SizeConfig.size_name == config_data['size_name']
                    ).first()
                    
                    if not existing:
                        size_config = SizeConfig(
                            user_id=user.id,
                            **config_data
                        )
                        db.add(size_config)
                
                db.commit()
                print("Default configurations added successfully!")
            else:
                print("No users found in database. Skipping default configuration insertion.")
                
        except Exception as e:
            print(f"Error adding default configurations: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration() 