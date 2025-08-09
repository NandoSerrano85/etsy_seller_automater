from typing import List, Annotated
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Depends
from . import model
from server.src.entities.template import EtsyProductTemplate
from server.src.routes.auth.service import CurrentUser
from server.src.message import (
    EtsyProductTemplateAlreadyExists, 
    EtsyProductTemplateCreateError,
    EtsyProductTemplateGetAllError,
    EtsyProductTemplateNotFound,
    EtsyProductTemplateGetByIdError,
    EtsyProductTemplateUpdateError,
    EtsyProductTemplateDeleteError,
)
import logging

def create_etsy_product_template(product_template: model.EtsyProductTemplateCreate, user_id: UUID, db: Session) -> EtsyProductTemplate:
    """Create a new template for the current user."""
    try:
        # Check if template name already exists for this user
        existing_template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.name == product_template.name
        ).first()
        
        if existing_template:
            logging.warning(f"The template your trying to create with the name: {product_template.name} for user ID: {user_id} already exists with template ID: {existing_template.id}")
            raise EtsyProductTemplateAlreadyExists(existing_template.id)
        
        # Handle materials and tags conversion
        materials_str = None
        if product_template.materials:
            if isinstance(product_template.materials, list):
                materials_str = ','.join(str(item) for item in product_template.materials if item)
            else:
                materials_str = str(product_template.materials)
        
        tags_str = None
        if product_template.tags:
            if isinstance(product_template.tags, list):
                tags_str = ','.join(str(item) for item in product_template.tags if item)
            else:
                tags_str = str(product_template.tags)
        
        db_template = EtsyProductTemplate(
            user_id=user_id,
            name=product_template.name,
            title=product_template.title,
            description=product_template.description,
            who_made=product_template.who_made,
            when_made=product_template.when_made,
            taxonomy_id=product_template.taxonomy_id,
            price=product_template.price,
            materials=materials_str,
            shop_section_id=product_template.shop_section_id,
            quantity=product_template.quantity,
            tags=tags_str,
            item_weight=product_template.item_weight,
            item_weight_unit=product_template.item_weight_unit,
            item_length=product_template.item_length,
            item_width=product_template.item_width,
            item_height=product_template.item_height,
            item_dimensions_unit=product_template.item_dimensions_unit,
            is_taxable=product_template.is_taxable,
            type=product_template.type,
            processing_min=product_template.processing_min,
            processing_max=product_template.processing_max,
            return_policy_id=product_template.return_policy_id
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        logging.info(f"Successfully created new etsy product template with name: {product_template.name} for user ID: {user_id}")

        return db_template
    except Exception as e:
        logging.error(f"Failed to create template for user ID: {user_id}. Error: {str(e)}")
        raise EtsyProductTemplateCreateError()

def get_etsy_product_templates(user_id: UUID, db: Session) -> List[EtsyProductTemplate]:
    """Get all templates for the current user."""
    try:
        templates = db.query(EtsyProductTemplate).filter(EtsyProductTemplate.user_id == user_id).all()
        logging.info(f"Successfully gathered all templates for user ID: {user_id}")
        return templates
    except Exception as e:
        logging.error(f"Faied to get etsy product templates for user ID: {user_id}. Error: {str(e)}")
        raise EtsyProductTemplateGetAllError()

def get_etsy_product_template_by_id(product_template_id: UUID, user_id: UUID, db: Session) -> EtsyProductTemplate:
    """Get a specific template by ID for the current user."""
    try:
        template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == product_template_id, 
            EtsyProductTemplate.user_id == user_id
        ).first()
        
        if not template:
            logging.warning(f"Could not find etsy product template with template ID: {product_template_id} for user ID: {user_id}")
            raise EtsyProductTemplateNotFound(product_template_id)
        logging.info(f"Successfully retrieved etsy product template with ID: {product_template_id} and user ID: {user_id}")

        return template
    except Exception as e:
        logging.error(f"Error fetching template {product_template_id}: {str(e)}")
        raise EtsyProductTemplateGetByIdError(product_template_id)

def get_current_product_template(product_template_id: UUID, current_user: CurrentUser, db: Session) -> EtsyProductTemplate:
    """Get the current product template for dependency injection."""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise ValueError("User ID cannot be None")
    product_template = get_etsy_product_template_by_id(product_template_id, user_id, db)
    return product_template

def get_default_product_template(current_user: CurrentUser, db: Session) -> model.EtsyProductTemplateData:
    """Get the default product template for dependency injection when no specific template ID is provided."""
    user_id = current_user.get_uuid()
    if user_id is None:
        raise ValueError("User ID cannot be None")
    # Get the first template for this user
    product_template = db.query(EtsyProductTemplate).filter(
        EtsyProductTemplate.user_id == user_id
    ).first()
    if product_template is None:
        raise ValueError("No product template found for this user")
    return model.EtsyProductTemplateData(product_template_id=str(product_template.id))


CurrentProductTemplate = Annotated[EtsyProductTemplate, Depends(get_current_product_template)]
DefaultProductTemplate = Annotated[model.EtsyProductTemplateData, Depends(get_default_product_template)]

def update_etsy_product_template(product_template: model.EtsyProductTemplateUpdate, user_id: UUID, product_template_id: UUID, db: Session) -> EtsyProductTemplate:
    """Update an existing template for the current user."""
    try:
        db_template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == product_template_id, 
            EtsyProductTemplate.user_id == user_id
        ).first()
        
        if not db_template:
            logging.warning(f"Could not find etsy product template with template ID: {product_template_id} for user ID: {user_id}")
            raise EtsyProductTemplateNotFound(product_template_id)
        
        # Check if new name conflicts with existing template (excluding current template)
        if product_template.name != db_template.name:
            existing_template = db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.name == product_template.name,
                EtsyProductTemplate.id != product_template_id
            ).first()
            
            if existing_template:
                logging.warning(f"The name your trying to change your template to: {product_template.name} is already b eing used by tmeplate ID: {existing_template.id} for user ID: {user_id}")
                raise EtsyProductTemplateAlreadyExists(product_template_id)
        
        # Update template fields
        for field, value in product_template.dict(exclude_unset=True).items():
            if field == 'materials' and value is not None:
                if isinstance(value, list):
                    setattr(db_template, field, ','.join(str(item) for item in value if item))
                else:
                    setattr(db_template, field, str(value))
            elif field == 'tags' and value is not None:
                if isinstance(value, list):
                    setattr(db_template, field, ','.join(str(item) for item in value if item))
                else:
                    setattr(db_template, field, str(value))
            else:
                setattr(db_template, field, value)
        
        db.commit()
        db.refresh(db_template)
        
        logging.info(f"Successfully update etsy product template with ID: {product_template_id} for user ID: {user_id}")

        return db_template
   
    except Exception as e:
        logging.error(f"Error updating template {product_template_id}: {str(e)}")
        raise EtsyProductTemplateUpdateError(product_template_id)

def delete_etsy_product_template(user_id: UUID, product_template_id: UUID, db: Session) -> None:
    """Delete a template for the current user."""
    try:
        db_template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == product_template_id, 
            EtsyProductTemplate.user_id == user_id
        ).first()
        
        if not db_template:
            logging.warning(f"Could not find etsy product template with template ID: {product_template_id} for user ID: {user_id}")
            raise EtsyProductTemplateNotFound(product_template_id)
        
        db.delete(db_template)
        db.commit()
        logging.info(f"Successfully delted etsy product template with template ID: {product_template_id} for user ID: {user_id}")

    except Exception as e:
        logging.error(f"Error deleting template {product_template_id}: {str(e)}")
        raise EtsyProductTemplateDeleteError(product_template_id)