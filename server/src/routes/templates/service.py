from typing import List, Annotated
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from . import model
from server.src.entities.template import EtsyProductTemplate, ShopifyProductTemplate, CraftFlowCommerceTemplate
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
        for field, value in product_template.model_dump(exclude_unset=True).items():
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


# Shopify Product Template Service Functions
def create_shopify_product_template(product_template: model.ShopifyProductTemplateCreate, user_id: UUID, db: Session) -> ShopifyProductTemplate:
    """Create a new Shopify template for the current user."""
    try:
        # Check if template name already exists for this user
        existing_template = db.query(ShopifyProductTemplate).filter(
            ShopifyProductTemplate.user_id == user_id,
            ShopifyProductTemplate.name == product_template.name
        ).first()

        if existing_template:
            logging.warning(f"Shopify template with name: {product_template.name} for user ID: {user_id} already exists with ID: {existing_template.id}")
            raise HTTPException(status_code=400, detail=f"Template with name '{product_template.name}' already exists")

        # Handle tags and option values conversion
        tags_str = None
        if product_template.tags:
            if isinstance(product_template.tags, list):
                tags_str = ','.join(str(item) for item in product_template.tags if item)
            else:
                tags_str = str(product_template.tags)

        # Convert option values to comma-separated strings
        option1_values_str = None
        if product_template.option1_values:
            if isinstance(product_template.option1_values, list):
                option1_values_str = ','.join(str(item) for item in product_template.option1_values if item)
            else:
                option1_values_str = str(product_template.option1_values)

        option2_values_str = None
        if product_template.option2_values:
            if isinstance(product_template.option2_values, list):
                option2_values_str = ','.join(str(item) for item in product_template.option2_values if item)
            else:
                option2_values_str = str(product_template.option2_values)

        option3_values_str = None
        if product_template.option3_values:
            if isinstance(product_template.option3_values, list):
                option3_values_str = ','.join(str(item) for item in product_template.option3_values if item)
            else:
                option3_values_str = str(product_template.option3_values)

        db_template = ShopifyProductTemplate(
            user_id=user_id,
            name=product_template.name,
            template_title=product_template.template_title,
            description=product_template.description,
            vendor=product_template.vendor,
            product_type=product_template.product_type,
            tags=tags_str,
            price=product_template.price,
            compare_at_price=product_template.compare_at_price,
            cost_per_item=product_template.cost_per_item,
            sku_prefix=product_template.sku_prefix,
            barcode_prefix=product_template.barcode_prefix,
            track_inventory=product_template.track_inventory,
            inventory_quantity=product_template.inventory_quantity,
            inventory_policy=product_template.inventory_policy,
            fulfillment_service=product_template.fulfillment_service,
            requires_shipping=product_template.requires_shipping,
            weight=product_template.weight,
            weight_unit=product_template.weight_unit,
            has_variants=product_template.has_variants,
            option1_name=product_template.option1_name,
            option1_values=option1_values_str,
            option2_name=product_template.option2_name,
            option2_values=option2_values_str,
            option3_name=product_template.option3_name,
            option3_values=option3_values_str,
            status=product_template.status,
            published_scope=product_template.published_scope,
            seo_title=product_template.seo_title,
            seo_description=product_template.seo_description,
            is_taxable=product_template.is_taxable,
            tax_code=product_template.tax_code,
            gift_card=product_template.gift_card,
            template_suffix=product_template.template_suffix,
            variant_configs=product_template.variant_configs
        )

        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        logging.info(f"Successfully created Shopify product template with name: {product_template.name} for user ID: {user_id}")

        return db_template
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to create Shopify template for user ID: {user_id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create Shopify template")


def get_shopify_product_templates(user_id: UUID, db: Session) -> List[ShopifyProductTemplate]:
    """Get all Shopify templates for the current user."""
    try:
        templates = db.query(ShopifyProductTemplate).filter(ShopifyProductTemplate.user_id == user_id).all()
        logging.info(f"Successfully gathered all Shopify templates for user ID: {user_id}")
        return templates
    except Exception as e:
        logging.error(f"Failed to get Shopify product templates for user ID: {user_id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Shopify templates")


def get_shopify_product_template_by_id(product_template_id: UUID, user_id: UUID, db: Session) -> ShopifyProductTemplate:
    """Get a specific Shopify template by ID for the current user."""
    try:
        template = db.query(ShopifyProductTemplate).filter(
            ShopifyProductTemplate.id == product_template_id,
            ShopifyProductTemplate.user_id == user_id
        ).first()

        if not template:
            logging.warning(f"Could not find Shopify product template with ID: {product_template_id} for user ID: {user_id}")
            raise HTTPException(status_code=404, detail=f"Shopify template with ID {product_template_id} not found")

        logging.info(f"Successfully retrieved Shopify product template with ID: {product_template_id} for user ID: {user_id}")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching Shopify template {product_template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Shopify template")


def update_shopify_product_template(product_template: model.ShopifyProductTemplateUpdate, user_id: UUID, product_template_id: UUID, db: Session) -> ShopifyProductTemplate:
    """Update an existing Shopify template for the current user."""
    try:
        db_template = db.query(ShopifyProductTemplate).filter(
            ShopifyProductTemplate.id == product_template_id,
            ShopifyProductTemplate.user_id == user_id
        ).first()

        if not db_template:
            logging.warning(f"Could not find Shopify product template with ID: {product_template_id} for user ID: {user_id}")
            raise HTTPException(status_code=404, detail=f"Shopify template with ID {product_template_id} not found")

        # Check if new name conflicts with existing template (excluding current template)
        if product_template.name != db_template.name:
            existing_template = db.query(ShopifyProductTemplate).filter(
                ShopifyProductTemplate.user_id == user_id,
                ShopifyProductTemplate.name == product_template.name,
                ShopifyProductTemplate.id != product_template_id
            ).first()

            if existing_template:
                logging.warning(f"Shopify template name '{product_template.name}' is already used by template ID: {existing_template.id} for user ID: {user_id}")
                raise HTTPException(status_code=400, detail=f"Template with name '{product_template.name}' already exists")

        # Update template fields
        for field, value in product_template.model_dump(exclude_unset=True).items():
            if field == 'tags' and value is not None:
                if isinstance(value, list):
                    setattr(db_template, field, ','.join(str(item) for item in value if item))
                else:
                    setattr(db_template, field, str(value))
            elif field in ['option1_values', 'option2_values', 'option3_values'] and value is not None:
                if isinstance(value, list):
                    setattr(db_template, field, ','.join(str(item) for item in value if item))
                else:
                    setattr(db_template, field, str(value))
            elif field == 'variant_configs':
                # variant_configs is a JSON field, set it directly
                setattr(db_template, field, value)
            else:
                setattr(db_template, field, value)

        db.commit()
        db.refresh(db_template)

        logging.info(f"Successfully updated Shopify product template with ID: {product_template_id} for user ID: {user_id}")
        return db_template
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating Shopify template {product_template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update Shopify template")


def delete_shopify_product_template(user_id: UUID, product_template_id: UUID, db: Session) -> None:
    """Delete a Shopify template for the current user."""
    try:
        db_template = db.query(ShopifyProductTemplate).filter(
            ShopifyProductTemplate.id == product_template_id,
            ShopifyProductTemplate.user_id == user_id
        ).first()

        if not db_template:
            logging.warning(f"Could not find Shopify product template with ID: {product_template_id} for user ID: {user_id}")
            raise HTTPException(status_code=404, detail=f"Shopify template with ID {product_template_id} not found")

        db.delete(db_template)
        db.commit()
        logging.info(f"Successfully deleted Shopify product template with ID: {product_template_id} for user ID: {user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting Shopify template {product_template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete Shopify template")


# CraftFlow Commerce Template Service Functions
def create_craftflow_commerce_template(product_template: model.CraftFlowCommerceTemplateCreate, user_id: UUID, db: Session) -> CraftFlowCommerceTemplate:
    """Create a new CraftFlow Commerce template for the current user."""
    try:
        # Check if template name already exists for this user
        existing_template = db.query(CraftFlowCommerceTemplate).filter(
            CraftFlowCommerceTemplate.user_id == user_id,
            CraftFlowCommerceTemplate.name == product_template.name
        ).first()

        if existing_template:
            logging.warning(f"CraftFlow Commerce template with name: {product_template.name} for user ID: {user_id} already exists with ID: {existing_template.id}")
            raise HTTPException(status_code=400, detail=f"Template with name '{product_template.name}' already exists")

        db_template = CraftFlowCommerceTemplate(
            user_id=user_id,
            name=product_template.name,
            template_title=product_template.template_title,
            description=product_template.description,
            short_description=product_template.short_description,
            product_type=product_template.product_type,
            print_method=product_template.print_method,
            category=product_template.category,
            price=product_template.price,
            compare_at_price=product_template.compare_at_price,
            cost=product_template.cost,
            track_inventory=product_template.track_inventory,
            inventory_quantity=product_template.inventory_quantity,
            allow_backorder=product_template.allow_backorder,
            digital_file_url=product_template.digital_file_url,
            download_limit=product_template.download_limit,
            meta_title=product_template.meta_title,
            meta_description=product_template.meta_description,
            is_active=product_template.is_active,
            is_featured=product_template.is_featured
        )

        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        logging.info(f"Successfully created CraftFlow Commerce template with name: {product_template.name} for user ID: {user_id}")

        return db_template
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to create CraftFlow Commerce template for user ID: {user_id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create CraftFlow Commerce template")


def get_craftflow_commerce_templates(user_id: UUID, db: Session) -> List[CraftFlowCommerceTemplate]:
    """Get all CraftFlow Commerce templates for the current user."""
    try:
        templates = db.query(CraftFlowCommerceTemplate).filter(
            CraftFlowCommerceTemplate.user_id == user_id
        ).all()
        logging.info(f"Successfully gathered all CraftFlow Commerce templates for user ID: {user_id}")
        return templates
    except Exception as e:
        logging.error(f"Failed to get CraftFlow Commerce templates for user ID: {user_id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get CraftFlow Commerce templates")


def get_craftflow_commerce_template_by_id(product_template_id: UUID, user_id: UUID, db: Session) -> CraftFlowCommerceTemplate:
    """Get a specific CraftFlow Commerce template by ID for the current user."""
    try:
        template = db.query(CraftFlowCommerceTemplate).filter(
            CraftFlowCommerceTemplate.id == product_template_id,
            CraftFlowCommerceTemplate.user_id == user_id
        ).first()

        if not template:
            logging.warning(f"Could not find CraftFlow Commerce template with ID: {product_template_id} for user ID: {user_id}")
            raise HTTPException(status_code=404, detail=f"CraftFlow Commerce template with ID {product_template_id} not found")

        logging.info(f"Successfully retrieved CraftFlow Commerce template with ID: {product_template_id} for user ID: {user_id}")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching CraftFlow Commerce template {product_template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get CraftFlow Commerce template")


def update_craftflow_commerce_template(product_template: model.CraftFlowCommerceTemplateUpdate, user_id: UUID, product_template_id: UUID, db: Session) -> CraftFlowCommerceTemplate:
    """Update an existing CraftFlow Commerce template for the current user."""
    try:
        db_template = db.query(CraftFlowCommerceTemplate).filter(
            CraftFlowCommerceTemplate.id == product_template_id,
            CraftFlowCommerceTemplate.user_id == user_id
        ).first()

        if not db_template:
            logging.warning(f"Could not find CraftFlow Commerce template with ID: {product_template_id} for user ID: {user_id}")
            raise HTTPException(status_code=404, detail=f"CraftFlow Commerce template with ID {product_template_id} not found")

        # Check if new name conflicts with existing template (excluding current template)
        if product_template.name != db_template.name:
            existing_template = db.query(CraftFlowCommerceTemplate).filter(
                CraftFlowCommerceTemplate.user_id == user_id,
                CraftFlowCommerceTemplate.name == product_template.name,
                CraftFlowCommerceTemplate.id != product_template_id
            ).first()

            if existing_template:
                logging.warning(f"Template name '{product_template.name}' already exists for user ID: {user_id}")
                raise HTTPException(status_code=400, detail=f"Template with name '{product_template.name}' already exists")

        # Update all fields
        db_template.name = product_template.name
        db_template.template_title = product_template.template_title
        db_template.description = product_template.description
        db_template.short_description = product_template.short_description
        db_template.product_type = product_template.product_type
        db_template.print_method = product_template.print_method
        db_template.category = product_template.category
        db_template.price = product_template.price
        db_template.compare_at_price = product_template.compare_at_price
        db_template.cost = product_template.cost
        db_template.track_inventory = product_template.track_inventory
        db_template.inventory_quantity = product_template.inventory_quantity
        db_template.allow_backorder = product_template.allow_backorder
        db_template.digital_file_url = product_template.digital_file_url
        db_template.download_limit = product_template.download_limit
        db_template.meta_title = product_template.meta_title
        db_template.meta_description = product_template.meta_description
        db_template.is_active = product_template.is_active
        db_template.is_featured = product_template.is_featured

        db.commit()
        db.refresh(db_template)
        logging.info(f"Successfully updated CraftFlow Commerce template with ID: {product_template_id} for user ID: {user_id}")

        return db_template
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating CraftFlow Commerce template {product_template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update CraftFlow Commerce template")


def delete_craftflow_commerce_template(user_id: UUID, product_template_id: UUID, db: Session) -> None:
    """Delete a CraftFlow Commerce template for the current user."""
    try:
        db_template = db.query(CraftFlowCommerceTemplate).filter(
            CraftFlowCommerceTemplate.id == product_template_id,
            CraftFlowCommerceTemplate.user_id == user_id
        ).first()

        if not db_template:
            logging.warning(f"Could not find CraftFlow Commerce template with ID: {product_template_id} for user ID: {user_id}")
            raise HTTPException(status_code=404, detail=f"CraftFlow Commerce template with ID {product_template_id} not found")

        db.delete(db_template)
        db.commit()
        logging.info(f"Successfully deleted CraftFlow Commerce template with ID: {product_template_id} for user ID: {user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting CraftFlow Commerce template {product_template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete CraftFlow Commerce template")