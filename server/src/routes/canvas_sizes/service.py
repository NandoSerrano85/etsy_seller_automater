from typing import List, Annotated, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session

from server.src.routes.auth.service import CurrentUser
from server.src.routes.templates.service import CurrentProductTemplate
from . import model
from server.src.entities.canvas_config import CanvasConfig
from server.src.entities.template import EtsyProductTemplate
from server.src.message import(
    CanvasConfigAlreadyExists,
    CanvasConfigCreateError,
    CanvasConfigGetAllError,
    CanvasConfigNotFound,
    CanvasConfigGetByIdError,
    CanvasConfigUpdateError,
    CanvasConfigDeleteError
)
import logging

def create_canvas_config(canvas_config: model.CanvasConfigCreate, product_template_id: UUID, db: Session) -> model.CanvasConfigResponse:
    """Create a new template for the current user."""
    try:
        # Check if template name already exists for this product template
        existing_canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.product_template_id == product_template_id,
            CanvasConfig.name == canvas_config.name,
            CanvasConfig.is_active == True
        ).first()
        
        if existing_canvas_config:
            logging.warning(f"The canvas you're trying to create with the name: {canvas_config.name} for product_template ID: {product_template_id} already exists with template ID: {existing_canvas_config.id}")
            raise CanvasConfigAlreadyExists()
        
        db_canvas_config = CanvasConfig(
            product_template_id=product_template_id,
            name=canvas_config.name,
            width_inches=canvas_config.width_inches,
            height_inches=canvas_config.height_inches,
            description=canvas_config.description,
            is_active=canvas_config.is_active,
            is_stretch=canvas_config.is_stretch,
            dpi=canvas_config.dpi,
            spacing_width_inches=canvas_config.spacing_width_inches,
            spacing_height_inches=canvas_config.spacing_height_inches
        )
        
        db.add(db_canvas_config)
        db.commit()
        db.refresh(db_canvas_config)
        logging.info(f"Successfully created new canvas config with name: {canvas_config.name} for product_template ID: {product_template_id}")

        return model.CanvasConfigResponse.model_validate(db_canvas_config)
    except Exception as e:
        logging.error(f"Failed to create canvas config for product_template ID: {product_template_id}. Error: {str(e)}")
        raise CanvasConfigCreateError()

def get_all_canvas_configs(user_id: UUID, db: Session) -> list[model.CanvasConfigResponse]:
    """Get all canvas configs for the current user."""
    try:
        db_canvas_config_list = db.query(CanvasConfig).join(EtsyProductTemplate, CanvasConfig.product_template_id == EtsyProductTemplate.id)
        db_canvas_config_list = db_canvas_config_list.filter(
            EtsyProductTemplate.user_id == user_id
        ).all()
        logging.info(f"Successfully gathered all canvas configs for user ID: {user_id}")
        return [model.CanvasConfigResponse.model_validate(canvas_config) for canvas_config in db_canvas_config_list]
    except Exception as e:
        logging.error(f"Failed to get canvas config for user ID: {user_id}. Error: {str(e)}")
        raise CanvasConfigGetAllError()

def get_canvas_config_by_id(canvas_config_id: UUID, product_template_id: UUID, db: Session):
    """Get a specific template by ID for the current user."""
    try:
        db_canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.id == canvas_config_id, 
            CanvasConfig.product_template_id == product_template_id
        ).first()
        
        if not db_canvas_config:
            logging.warning(f"Could not find canvas config with ID: {canvas_config_id} and product template ID: {product_template_id}")
            raise CanvasConfigNotFound()
        
        logging.info(f"Successfully retrieved canvas config with ID: {canvas_config_id} and product template with ID: {product_template_id}")

        return db_canvas_config
    except Exception as e:
        logging.error(f"Error fetching canvas config {canvas_config_id}. Error: {str(e)}")
        raise CanvasConfigGetByIdError()

def update_canvas_config(canvas_config: model.CanvasConfigUpdate, canvas_config_id: UUID, product_template_id: UUID, db: Session) -> model.CanvasConfigResponse:
    """Update an existing template for the current user."""
    try:
        db_canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.id == canvas_config_id, 
            CanvasConfig.product_template_id == product_template_id
        ).first()
        
        if not db_canvas_config:
            logging.warning(f"Could not find canvas config with ID: {canvas_config_id} and product template ID: {product_template_id}")
            raise CanvasConfigNotFound()
        
        # Check if new name conflicts with existing template (excluding current template)
        if canvas_config.name != db_canvas_config.name:
            existing_canvas_config = db.query(CanvasConfig).filter(
                CanvasConfig.id != canvas_config_id,
                CanvasConfig.name == canvas_config.name,
                CanvasConfig.product_template_id == product_template_id
            ).first()
            
            if existing_canvas_config:
                logging.warning(f"The canvas you're trying to create with the name: {canvas_config.name} for product_template ID: {product_template_id} already exists with template ID: {existing_canvas_config.id}")
                raise CanvasConfigAlreadyExists()
        
        # Update template fields
        for field, value in canvas_config.dict(exclude_unset=True).items():
            setattr(db_canvas_config, field, value)
        
        db.commit()
        db.refresh(db_canvas_config)
        
        logging.info(f"Successfully updated canvas config with ID: {product_template_id}")

        return model.CanvasConfigResponse.model_validate(db_canvas_config)
   
    except Exception as e:
        logging.error(f"Error updating canvas config {canvas_config_id}. Error: {str(e)}")
        raise CanvasConfigUpdateError()

def delete_canvas_config(canvas_config_id: UUID, product_template_id: UUID, db: Session) -> None:
    """Delete a template for the current user."""
    try:
        db_canvas_config = db.query(CanvasConfig).filter(
            CanvasConfig.id == canvas_config_id, 
            CanvasConfig.product_template_id == product_template_id
        ).first()
        
        if not db_canvas_config:
            logging.warning(f"Could not find canvas config with ID: {canvas_config_id} and product template ID: {product_template_id}")
            raise CanvasConfigNotFound()
        
        db.delete(db_canvas_config)
        db.commit()
        logging.info(f"Successfully deleted canvas config with ID: {canvas_config_id} and product template ID: {product_template_id}")

    except Exception as e:
        logging.error(f"Error deleting canvas config ID: {canvas_config_id}. Error: {str(e)}")
        raise CanvasConfigDeleteError()

def get_current_canvas_config(
        canvas_config_id: UUID,
        product_template: CurrentProductTemplate,
        current_user: CurrentUser,
        db: Session
    ) -> model.CanvasConfigData:
    """Get the current canvas config for dependency injection."""
    user_id = current_user.get_uuid()
    product_template_id = product_template.get_uuid()
    if user_id is None:
        raise ValueError("User ID cannot be None")
    selected_canvas_config = get_canvas_config_by_id(canvas_config_id, product_template_id, db)
    return model.CanvasConfigData(canvas_config_id=str(selected_canvas_config.id))

def get_default_canvas_config(
        product_template: CurrentProductTemplate,
        current_user: CurrentUser,
        db: Session
    ) -> model.CanvasConfigData:
    """Get the default canvas config for dependency injection when no specific canvas ID is provided."""
    user_id = current_user.get_uuid()
    product_template_id = product_template.get_uuid()
    if user_id is None:
        raise ValueError("User ID cannot be None")
    # Get the first active canvas config for this user and template
    canvas_config = db.query(CanvasConfig).join(EtsyProductTemplate).filter(
        EtsyProductTemplate.user_id == user_id,
        CanvasConfig.product_template_id == product_template_id,
        CanvasConfig.is_active == True
    ).first()
    if canvas_config is None:
        raise ValueError("No active canvas config found for this user and template")
    return model.CanvasConfigData(canvas_config_id=str(canvas_config.id))
    
CurrentCanvasSize = Annotated[model.CanvasConfigData, Depends(get_current_canvas_config)]
DefaultCanvasSize = Annotated[model.CanvasConfigData, Depends(get_default_canvas_config)]

def get_resizing_canvas_configs(db: Session, product_template_id: UUID):
    """
    Return a dict of {name: {width, height}} for all CanvasConfig for a product_template_id.
    All keys and values are plain Python types.
    """
    try:
        canvas_configs = db.query(CanvasConfig).filter(
            CanvasConfig.product_template_id == product_template_id,
            CanvasConfig.is_active == True
        ).all()
        return {str(c.name): {'width': c.width_inches, 'height': c.height_inches} for c in canvas_configs}
    except Exception as e:
        logging.error(f"Error fetching resizing canvas configs: {e}")
        return {}