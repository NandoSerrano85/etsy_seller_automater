import os
import tempfile
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from server.src.utils.shopify_client import ShopifyClient, ShopifyAPIError
from server.src.entities.shopify_store import ShopifyStore
from server.src.entities.shopify_product import ShopifyProduct
from server.src.entities.template import EtsyProductTemplate
from server.src.entities.mockup import Mockups, MockupImage
from server.src.entities.designs import DesignImages
from server.src.utils.mockups_util import create_mockup_images, process_design_image
from server.src.utils.file_storage import file_storage
import cv2
import numpy as np
from PIL import Image
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class ShopifyTemplateProductService:
    """
    Service for creating Shopify products using predefined templates and user designs.
    Handles mockup generation, image uploads, and product creation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = ShopifyClient(db)

    def get_available_templates(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get available product templates for a user.

        Args:
            user_id: User UUID

        Returns:
            List of template dictionaries
        """
        templates = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id
        ).all()

        return [
            {
                'id': str(template.id),
                'name': template.name,
                'template_title': template.template_title,
                'description': template.description,
                'price': template.price,
                'type': template.type,
                'created_at': template.created_at.isoformat() if template.created_at else None
            }
            for template in templates
        ]

    def get_template_mockups(self, template_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get mockup configurations for a template.

        Args:
            template_id: Template UUID
            user_id: User UUID

        Returns:
            List of mockup dictionaries with mask data
        """
        mockups = self.db.query(Mockups).filter(
            Mockups.product_template_id == template_id,
            Mockups.user_id == user_id
        ).all()

        mockup_data = []
        for mockup in mockups:
            mockup_images = []
            for img in mockup.mockup_images:
                # Collect mask data for this mockup image
                masks = []
                for mask_data in img.mask_data:
                    mask_info = {
                        'masks': mask_data.masks,
                        'points': mask_data.points,
                        'is_cropped': mask_data.is_cropped,
                        'alignment': mask_data.alignment
                    }
                    masks.append(mask_info)

                mockup_images.append({
                    'id': str(img.id),
                    'filename': img.filename,
                    'file_path': img.file_path,
                    'watermark_path': img.watermark_path,
                    'image_type': img.image_type,
                    'masks': masks
                })

            mockup_data.append({
                'id': str(mockup.id),
                'name': mockup.name,
                'starting_name': mockup.starting_name,
                'images': mockup_images
            })

        return mockup_data

    def process_design_files(self, design_files: List[UploadFile],
                           template_name: str) -> List[str]:
        """
        Process and save uploaded design files.

        Args:
            design_files: List of uploaded design files
            template_name: Name of the template for processing

        Returns:
            List of processed design file paths
        """
        processed_files = []

        for design_file in design_files:
            # Validate file type
            if not design_file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {design_file.filename} must be an image"
                )

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_{design_file.filename}"
            ) as temp_file:
                # Save uploaded file
                content = design_file.file.read()
                temp_file.write(content)
                temp_file.flush()

                # Process the design image using existing utilities
                try:
                    processed_image = process_design_image(temp_file.name, template_name)

                    # Save processed image to a new temporary file
                    processed_path = f"{temp_file.name}_processed.png"
                    cv2.imwrite(processed_path, processed_image)
                    processed_files.append(processed_path)

                except Exception as e:
                    logger.error(f"Failed to process design file {design_file.filename}: {e}")
                    # Clean up temp file
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to process design file {design_file.filename}"
                    )
                finally:
                    # Clean up original temp file
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass

        return processed_files

    def generate_mockup_preview(self, template_id: UUID, design_files: List[UploadFile],
                              user_id: UUID) -> Dict[str, Any]:
        """
        Generate mockup preview without creating the actual product.

        Args:
            template_id: Template UUID
            design_files: List of uploaded design files
            user_id: User UUID

        Returns:
            Dictionary containing mockup preview data
        """
        # Get template
        template = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == template_id,
            EtsyProductTemplate.user_id == user_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Get mockups for this template
        mockups = self.get_template_mockups(template_id, user_id)
        if not mockups:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No mockups found for this template"
            )

        # Process design files
        processed_files = self.process_design_files(design_files, template.name)

        try:
            # Generate mockups using existing utility
            mockup_data = mockups[0]  # Use first mockup for preview

            # Prepare mask data in the format expected by create_mockup_images
            mask_info = {
                'masks': [],
                'points': [],
                'is_cropped': False,
                'alignment': 'center'
            }

            if mockup_data['images']:
                first_image = mockup_data['images'][0]
                if first_image['masks']:
                    first_mask = first_image['masks'][0]
                    mask_info = {
                        'masks': first_mask['masks'] if isinstance(first_mask['masks'], list) else json.loads(first_mask['masks']),
                        'points': first_mask['points'] if isinstance(first_mask['points'], list) else json.loads(first_mask['points']),
                        'is_cropped': first_mask['is_cropped'],
                        'alignment': first_mask['alignment']
                    }

            # Generate mockup images
            root_path = os.getenv('LOCAL_ROOT_PATH', '/tmp/')
            generated_mockups = create_mockup_images(
                design_file_paths=processed_files,
                template_name=template.name,
                mockup_id=str(template_id),
                root_path=root_path,
                starting_name=mockup_data['starting_name'],
                mask_data=mask_info
            )

            # Convert images to base64 for preview
            preview_images = []
            for mockup in generated_mockups:
                try:
                    with open(mockup['file_path'], 'rb') as img_file:
                        img_data = img_file.read()
                        encoded_img = base64.b64encode(img_data).decode('utf-8')
                        preview_images.append({
                            'filename': mockup['filename'],
                            'data': f"data:image/jpeg;base64,{encoded_img}",
                            'type': mockup.get('color', 'default')
                        })
                except Exception as e:
                    logger.warning(f"Failed to encode mockup image: {e}")

            return {
                'template': {
                    'id': str(template.id),
                    'name': template.name,
                    'template_title': template.template_title
                },
                'mockups': preview_images,
                'design_count': len(design_files)
            }

        finally:
            # Clean up processed files
            for file_path in processed_files:
                try:
                    os.unlink(file_path)
                except:
                    pass

    def create_shopify_product_from_template(
        self,
        user_id: UUID,
        template_id: UUID,
        design_files: List[UploadFile],
        product_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a Shopify product using a template and design files.

        Args:
            user_id: User UUID
            template_id: Template UUID
            design_files: List of uploaded design files
            product_details: Product details (title, price, description, variants)

        Returns:
            Created product information
        """
        # Get user's Shopify store
        store = self.db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.is_active == True
        ).first()

        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found"
            )

        # Get template
        template = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == template_id,
            EtsyProductTemplate.user_id == user_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Get mockups for this template
        mockups = self.get_template_mockups(template_id, user_id)
        if not mockups:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No mockups found for this template"
            )

        # Process design files
        processed_files = self.process_design_files(design_files, template.name)

        try:
            # Generate mockup images
            mockup_data = mockups[0]  # Use first mockup

            # Prepare mask data
            mask_info = {
                'masks': [],
                'points': [],
                'is_cropped': False,
                'alignment': 'center'
            }

            if mockup_data['images']:
                first_image = mockup_data['images'][0]
                if first_image['masks']:
                    first_mask = first_image['masks'][0]
                    mask_info = {
                        'masks': first_mask['masks'] if isinstance(first_mask['masks'], list) else json.loads(first_mask['masks']),
                        'points': first_mask['points'] if isinstance(first_mask['points'], list) else json.loads(first_mask['points']),
                        'is_cropped': first_mask['is_cropped'],
                        'alignment': first_mask['alignment']
                    }

            # Generate mockup images
            root_path = os.getenv('LOCAL_ROOT_PATH', '/tmp/')
            generated_mockups = create_mockup_images(
                design_file_paths=processed_files,
                template_name=template.name,
                mockup_id=str(template_id),
                root_path=root_path,
                starting_name=mockup_data['starting_name'],
                mask_data=mask_info
            )

            # Prepare product data for Shopify
            shopify_product_data = {
                'title': product_details.get('title', template.template_title or template.name),
                'body_html': product_details.get('description', template.description or ''),
                'vendor': product_details.get('vendor', 'Custom Design Store'),
                'product_type': template.type or 'Custom Product',
                'tags': product_details.get('tags', template.tags or ''),
                'variants': []
            }

            # Add variants
            variants = product_details.get('variants', [])
            if not variants:
                # Create default variant
                variants = [{
                    'price': str(product_details.get('price', template.price or 25.00)),
                    'sku': f"{template.name}-{datetime.now().strftime('%Y%m%d%H%M')}",
                    'inventory_quantity': 100,
                    'title': 'Default'
                }]

            shopify_product_data['variants'] = variants

            # Create product in Shopify
            created_product = self.client.create_product(
                store_id=str(store.id),
                product_data=shopify_product_data
            )

            # Upload mockup images to Shopify
            uploaded_images = []
            for i, mockup in enumerate(generated_mockups):
                try:
                    with open(mockup['file_path'], 'rb') as img_file:
                        uploaded_image = self.client.upload_product_image(
                            store_id=str(store.id),
                            product_id=str(created_product['id']),
                            image_file=img_file,
                            filename=mockup['filename'],
                            alt_text=f"{template.name} mockup {i+1}",
                            position=i+1
                        )
                        uploaded_images.append(uploaded_image)
                except Exception as e:
                    logger.error(f"Failed to upload image {mockup['filename']}: {e}")

            # Store product metadata in database
            shopify_product = ShopifyProduct(
                user_id=user_id,
                store_id=store.id,
                template_id=template.id,
                shopify_product_id=str(created_product['id']),
                title=created_product['title'],
                handle=created_product.get('handle'),
                description=created_product.get('body_html'),
                vendor=created_product.get('vendor'),
                product_type=created_product.get('product_type'),
                tags=created_product.get('tags'),
                variants=created_product.get('variants'),
                design_files=[f.filename for f in design_files],
                mockup_images=[img['src'] for img in uploaded_images],
                status=created_product.get('status', 'draft'),
                published_at=datetime.fromisoformat(created_product['published_at'].replace('Z', '+00:00')) if created_product.get('published_at') else None
            )

            self.db.add(shopify_product)
            self.db.commit()
            self.db.refresh(shopify_product)

            return {
                'shopify_product': created_product,
                'local_product': {
                    'id': str(shopify_product.id),
                    'shopify_product_id': shopify_product.shopify_product_id,
                    'title': shopify_product.title,
                    'status': shopify_product.status,
                    'created_at': shopify_product.created_at.isoformat()
                },
                'mockup_images': uploaded_images,
                'template_used': {
                    'id': str(template.id),
                    'name': template.name
                }
            }

        except ShopifyAPIError as e:
            logger.error(f"Shopify API error creating product: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create product in Shopify: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating product from template: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create product: {str(e)}"
            )
        finally:
            # Clean up processed files
            for file_path in processed_files:
                try:
                    os.unlink(file_path)
                except:
                    pass

    def get_user_shopify_products(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all Shopify products created by a user.

        Args:
            user_id: User UUID

        Returns:
            List of product dictionaries
        """
        products = self.db.query(ShopifyProduct).filter(
            ShopifyProduct.user_id == user_id
        ).order_by(ShopifyProduct.created_at.desc()).all()

        return [
            {
                'id': str(product.id),
                'shopify_product_id': product.shopify_product_id,
                'title': product.title,
                'handle': product.handle,
                'description': product.description,
                'vendor': product.vendor,
                'product_type': product.product_type,
                'tags': product.tags,
                'status': product.status,
                'published_at': product.published_at.isoformat() if product.published_at else None,
                'created_at': product.created_at.isoformat(),
                'template': {
                    'id': str(product.template.id) if product.template else None,
                    'name': product.template.name if product.template else None
                },
                'mockup_images': product.mockup_images,
                'design_files': product.design_files
            }
            for product in products
        ]