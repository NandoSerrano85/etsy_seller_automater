from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from . import model
from server.src.entities.size_config import SizeConfig
from server.src.entities.template import EtsyProductTemplate
from server.src.message import(
    SizeConfigAlreadyExists,
    SizeConfigCreateError,
    SizeConfigGetAllError,
    SizeConfigNotFound,
    SizeConfigGetByIdError,
    SizeConfigUpdateError,
    SizeConfigDeleteError
)
import logging

def create_size_config(
        size_config: model.SizeConfigCreate,
        product_template_id: UUID,
        canvas_id: UUID, 
        db: Session
    ) -> SizeConfig:
    """Create a new size configuration."""
    try:
        # Check if template and size combination already exists for this user
        existing_config = db.query(SizeConfig).filter(
            SizeConfig.product_template_id == product_template_id,
            SizeConfig.canvas_id == canvas_id,
            SizeConfig.name == size_config.name,
            SizeConfig.is_active == True
        ).first()
        
        if existing_config:
            logging.warning(f"Based on the active name used there exists a size config with ID: {existing_config.id}")
            raise SizeConfigAlreadyExists(existing_config.id)
        
        new_size_config = SizeConfig(
            product_template_id=product_template_id,
            canvas_id=canvas_id,
            name=size_config.name,
            width_inches=size_config.width_inches,
            height_inches=size_config.height_inches,
            description=size_config.description,
            is_active=size_config.is_active if size_config.is_active is not None else True
        )
        
        db.add(new_size_config)
        db.commit()
        db.refresh(new_size_config)
        
        return new_size_config
    except Exception as e:
        logging.error(f"Error creating size config: {str(e)}")
        raise SizeConfigCreateError()

def get_size_configs_list(
        canvas_config_id: UUID, 
        product_template_id: UUID,
        db: Session 
    ):
    """List all size configurations for the current user and product template."""
    try:
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id,
            SizeConfig.is_active == True
        ).all()
        return size_configs
    except Exception as e:
        logging.error(f"Error listing size configs: {str(e)}")
        raise SizeConfigGetAllError()

def get_size_config_by_id(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session
    ):
    """Get a specific size configuration by ID."""
    try:
        size_config = db.query(SizeConfig).filter(
            SizeConfig.id == size_config_id,
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id
        ).first()
        
        if not size_config:
            logging.warning(f"Could not find size config with ID: {size_config_id}")
            raise SizeConfigNotFound(size_config_id)
        
        return size_config
    except Exception as e:
        logging.error(f"Error getting size config {size_config_id}: {str(e)}")
        raise SizeConfigGetByIdError(size_config_id)

def update_size_config(
        size_config: model.SizeConfigUpdate, 
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session
    ):
    """Update an existing size configuration."""
    try:
        db_size_config = db.query(SizeConfig).filter(
            SizeConfig.id == size_config_id,
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id
        ).first()
        
        if not db_size_config:
            logging.warning(f"Could not find size config with ID: {size_config_id}")
            raise SizeConfigNotFound(size_config_id)
        
        # Update fields if provided
        for field, value in size_config.dict(exclude_unset=True).items():
            setattr(db_size_config, field, value)
        
        db.commit()
        db.refresh(db_size_config)
        
        return db_size_config
    except Exception as e:
        logging.error(f"Error updating size config {size_config_id}: {str(e)}")
        raise SizeConfigUpdateError(size_config_id)

def get_size_configs_with_relations(
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session 
    ):
    """List all size configurations with related data for the current user and product template."""
    try:
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id,
            SizeConfig.is_active == True
        ).all()
        
        # Add related data to each size config
        for size_config in size_configs:
            # Add product template name
            if size_config.product_template:
                size_config.product_template_name = size_config.product_template.name
            
            # Add canvas config name
            if size_config.canvas_config:
                size_config.canvas_config_name = size_config.canvas_config.name
            
            # Add design images count
            size_config.design_images_count = len(size_config.design_images) if size_config.design_images else 0
        
        return size_configs
    except Exception as e:
        logging.error(f"Error listing size configs with relations: {str(e)}")
        raise SizeConfigGetAllError()

def delete_size_config(
        size_config_id: UUID,
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session
    ):
    """Delete a size configuration (soft delete by setting is_active to False)."""
    try:
        db_size_config = db.query(SizeConfig).filter(
            SizeConfig.id == size_config_id,
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id
        ).first()
        
        if not db_size_config:
            logging.warning(f"Could not find size config with ID: {size_config_id}")
            raise SizeConfigNotFound(size_config_id)
        
        # Soft delete by setting is_active to False
        setattr(db_size_config, 'is_active', False)
        db.commit()
        logging.info(f"Successfully deleted size config with ID: {size_config_id} and product template ID: {product_template_id} for user ID: {canvas_config_id}")
  
    except Exception as e:
        logging.error(f"Error deleting size config {size_config_id}: {str(e)}")
        raise SizeConfigDeleteError(size_config_id)

def get_resizing_size_configs(db: Session, canvas_config_id: UUID, product_template_id: UUID):
    """
    Return a dict of {name: {width, height}} for all SizeConfig for a user and product_template_id.
    All keys and values are plain Python types.
    """
    try:
        size_configs = db.query(SizeConfig).filter(
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id,
            SizeConfig.is_active == True
        ).all()
        return {str(s.name): {'width': s.width_inches, 'height': s.height_inches} for s in size_configs}
    except Exception as e:
        logging.error(f"Error fetching resizing size configs: {e}")
        return {}

def get_size_config_by_id_with_relations(
        size_config_id: UUID, 
        canvas_config_id: UUID,
        product_template_id: UUID,
        db: Session
    ):
    """Get a specific size configuration by ID with related data."""
    try:
        size_config = db.query(SizeConfig).filter(
            SizeConfig.id == size_config_id,
            SizeConfig.canvas_id == canvas_config_id,
            SizeConfig.product_template_id == product_template_id
        ).first()
        
        if not size_config:
            logging.warning(f"Could not find size config with ID: {size_config_id}")
            raise SizeConfigNotFound(size_config_id)
        
        # Add related data
        if size_config.product_template:
            size_config.product_template_name = size_config.product_template.name
        
        if size_config.canvas_config:
            size_config.canvas_config_name = size_config.canvas_config.name
        
        size_config.design_images_count = len(size_config.design_images) if size_config.design_images else 0
        
        return size_config
    except Exception as e:
        logging.error(f"Error getting size config {size_config_id}: {str(e)}")
        raise SizeConfigGetByIdError(size_config_id)

def get_all_size_configs(user_id: UUID, db: Session) -> list[model.SizeConfigResponse]:
    """Get all size configs for the current user."""
    try:
        db_size_config_list = db.query(SizeConfig).join(EtsyProductTemplate, SizeConfig.product_template_id == EtsyProductTemplate.id)
        db_size_config_list = db_size_config_list.filter(
            EtsyProductTemplate.user_id == user_id
        ).all()
        logging.info(f"Successfully gathered all size configs for user ID: {user_id}")
        return [model.SizeConfigResponse.model_validate(size_config) for size_config in db_size_config_list]
    except Exception as e:
        logging.error(f"Failed to get size configs for user ID: {user_id}. Error: {str(e)}")
        raise SizeConfigGetAllError()

