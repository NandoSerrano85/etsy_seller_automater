"""
Database utilities for resizing.py to get canvas and size configurations.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.api.models import CanvasConfig, SizeConfig, User
from dotenv import load_dotenv

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/etsydb')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_user_by_shop_name(shop_name: str):
    """Get user by shop name."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.shop_name == shop_name).first()
        return user
    finally:
        db.close()

def get_canvas_configs_for_user(user_id: int):
    """Get all canvas configurations for a user, formatted for resizing.py."""
    db = SessionLocal()
    try:
        canvas_configs = db.query(CanvasConfig).filter(
            CanvasConfig.user_id == user_id,
            CanvasConfig.is_active == True
        ).all()
        
        # Format as dictionary for resizing.py compatibility
        canvas_dict = {}
        for config in canvas_configs:
            canvas_dict[config.template_name] = {
                'width': config.width_inches,
                'height': config.height_inches
            }
        
        return canvas_dict
    finally:
        db.close()

def get_size_configs_for_user(user_id: int):
    """Get all size configurations for a user, formatted for resizing.py."""
    db = SessionLocal()
    try:
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.user_id == user_id,
            SizeConfig.is_active == True
        ).all()
        
        # Format as dictionary for resizing.py compatibility
        sizing_dict = {}
        for config in size_configs:
            if config.size_name is not None:
                # For templates with size names (e.g., DTF, Sublimation)
                if config.template_name not in sizing_dict:
                    sizing_dict[config.template_name] = {}
                sizing_dict[config.template_name][config.size_name] = {
                    'width': config.width_inches,
                    'height': config.height_inches
                }
            else:
                # For templates without size names (e.g., UVDTF 16oz)
                sizing_dict[config.template_name] = {
                    'width': config.width_inches,
                    'height': config.height_inches
                }
        
        return sizing_dict
    finally:
        db.close()

def get_resizing_configs_for_template(user_id: int, template_name: str):
    """Get canvas and size configurations for a specific template, formatted for resizing.py."""
    db = SessionLocal()
    try:
        # Get canvas configuration
        canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.user_id == user_id,
            CanvasConfig.template_name == template_name,
            CanvasConfig.is_active == True
        ).first()
        
        # Get size configurations
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.user_id == user_id,
            SizeConfig.template_name == template_name,
            SizeConfig.is_active == True
        ).all()
        
        # Format for resizing.py compatibility
        canvas_data = {}
        if canvas_config:
            canvas_data = {
                'width': canvas_config.width_inches,
                'height': canvas_config.height_inches
            }
        
        sizing_data = {}
        for size_config in size_configs:
            if size_config.size_name is not None:
                sizing_data[size_config.size_name] = {
                    'width': size_config.width_inches,
                    'height': size_config.height_inches
                }
            else:
                # For templates without size names, use template name as key
                sizing_data[template_name] = {
                    'width': size_config.width_inches,
                    'height': size_config.height_inches
                }
        
        return {
            'canvas': canvas_data,
            'sizing': sizing_data
        }
    finally:
        db.close()

def get_all_resizing_configs_for_user(user_id: int):
    """Get all canvas and size configurations for a user, formatted for resizing.py."""
    canvas_configs = get_canvas_configs_for_user(user_id)
    size_configs = get_size_configs_for_user(user_id)
    
    return {
        'CANVAS': canvas_configs,
        'SIZING': size_configs
    }

def get_user_resizing_configs(shop_name: str):
    """Get all resizing configurations for a user by shop name."""
    user = get_user_by_shop_name(shop_name)
    if not user:
        return None
    
    user_id = user.id
    return get_all_resizing_configs_for_user(user_id) 