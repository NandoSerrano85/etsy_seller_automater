import os
import base64
import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from PIL import Image, ImageDraw
import io
import json

from server.src.entities.template import EtsyProductTemplate
from server.src.entities.user import User
from server.src.utils.file_storage import file_storage
from .model import (
    TemplateEditorCreate,
    TemplateEditorUpdate,
    TemplateEditorResponse,
    TemplatePreview,
    TemplatePreviewResponse,
    DesignArea
)

logger = logging.getLogger(__name__)

class TemplateEditorService:
    """Service for managing template editor functionality"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(self, template_data: TemplateEditorCreate, user_id: UUID) -> TemplateEditorResponse:
        """Create a new template with background and design areas"""

        try:
            # Decode and save background image
            background_url = self._save_background_image(
                template_data.background_image_data,
                template_data.background_filename,
                user_id
            )

            # Create template record
            template = EtsyProductTemplate(
                id=uuid4(),
                user_id=user_id,
                name=template_data.name,
                description=template_data.description,
                template_title=template_data.name,
                type="custom_template"
            )

            self.db.add(template)
            self.db.flush()

            # Store design areas and metadata in template description as JSON
            # (We could create a separate table for this, but using JSON for simplicity)
            template_metadata = {
                "background_image_url": background_url,
                "background_filename": template_data.background_filename,
                "design_areas": [area.model_dump() for area in template_data.design_areas],
                "category": template_data.category,
                "metadata": template_data.metadata or {}
            }

            # Store metadata as JSON in materials field (repurposing existing field)
            template.materials = json.dumps(template_metadata)

            self.db.commit()

            return self._convert_to_response(template)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating template: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create template: {str(e)}"
            )

    def get_templates(self, user_id: UUID, page: int = 1, per_page: int = 20) -> List[TemplateEditorResponse]:
        """Get user's templates"""

        offset = (page - 1) * per_page

        templates = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.type == "custom_template"
        ).offset(offset).limit(per_page).all()

        return [self._convert_to_response(template) for template in templates]

    def get_template_by_id(self, template_id: UUID, user_id: UUID) -> TemplateEditorResponse:
        """Get specific template by ID"""

        template = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == template_id,
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.type == "custom_template"
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        return self._convert_to_response(template)

    def update_template(self, template_id: UUID, template_data: TemplateEditorUpdate, user_id: UUID) -> TemplateEditorResponse:
        """Update existing template"""

        template = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == template_id,
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.type == "custom_template"
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        try:
            # Parse existing metadata
            existing_metadata = json.loads(template.materials or "{}")

            # Update basic fields
            if template_data.name:
                template.name = template_data.name
                template.template_title = template_data.name

            if template_data.description is not None:
                template.description = template_data.description

            # Update background image if provided
            if template_data.background_image_data and template_data.background_filename:
                background_url = self._save_background_image(
                    template_data.background_image_data,
                    template_data.background_filename,
                    user_id
                )
                existing_metadata["background_image_url"] = background_url
                existing_metadata["background_filename"] = template_data.background_filename

            # Update design areas if provided
            if template_data.design_areas is not None:
                existing_metadata["design_areas"] = [area.model_dump() for area in template_data.design_areas]

            # Update category if provided
            if template_data.category is not None:
                existing_metadata["category"] = template_data.category

            # Update metadata if provided
            if template_data.metadata is not None:
                existing_metadata["metadata"] = template_data.metadata

            # Save updated metadata
            template.materials = json.dumps(existing_metadata)
            template.updated_at = datetime.now(timezone.utc)

            self.db.commit()

            return self._convert_to_response(template)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating template: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update template: {str(e)}"
            )

    def delete_template(self, template_id: UUID, user_id: UUID) -> None:
        """Delete template"""

        template = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == template_id,
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.type == "custom_template"
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        try:
            # TODO: Also delete associated files
            self.db.delete(template)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting template: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete template: {str(e)}"
            )

    def generate_preview(self, preview_data: TemplatePreview, user_id: UUID) -> TemplatePreviewResponse:
        """Generate preview with design overlay"""

        # Get template
        template = self.get_template_by_id(preview_data.template_id, user_id)

        try:
            # Load background image
            background_path = self._get_file_path_from_url(template.background_image_url)
            background_img = Image.open(background_path)

            # Create copy for preview
            preview_img = background_img.copy()

            # If design image provided, overlay it on design areas
            if preview_data.design_image_data:
                design_img = self._decode_image(preview_data.design_image_data)

                # Overlay design on each design area
                for area in template.design_areas:
                    resized_design = design_img.resize(
                        (int(area.width), int(area.height)),
                        Image.Resampling.LANCZOS
                    )

                    # Apply rotation if specified
                    if area.rotation and area.rotation != 0:
                        resized_design = resized_design.rotate(area.rotation, expand=True)

                    # Paste design onto preview
                    preview_img.paste(resized_design, (int(area.x), int(area.y)), resized_design)

            else:
                # Draw placeholder rectangles for design areas
                draw = ImageDraw.Draw(preview_img)
                for area in template.design_areas:
                    # Draw semi-transparent rectangle
                    bbox = [int(area.x), int(area.y), int(area.x + area.width), int(area.y + area.height)]
                    draw.rectangle(bbox, fill=(255, 0, 0, 100), outline=(255, 0, 0, 200), width=2)

            # Save preview image
            preview_url = self._save_preview_image(preview_img, user_id)

            return TemplatePreviewResponse(
                preview_image_url=preview_url,
                template_data=template
            )

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate preview: {str(e)}"
            )

    def _save_background_image(self, image_data: str, filename: str, user_id: UUID) -> str:
        """Save background image and return URL"""

        # Decode base64 image
        img = self._decode_image(image_data)

        # Generate unique filename
        file_extension = os.path.splitext(filename)[1] or '.png'
        unique_filename = f"template_bg_{uuid4()}{file_extension}"

        # Save using file storage service
        file_path = f"templates/{user_id}/backgrounds/{unique_filename}"

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Save file
        saved_path = file_storage.save_file(file_path, img_bytes)

        # Return URL (assuming file_storage returns relative path)
        return f"/api/files/{saved_path}"

    def _save_preview_image(self, img: Image.Image, user_id: UUID) -> str:
        """Save preview image and return URL"""

        # Generate unique filename
        unique_filename = f"template_preview_{uuid4()}.png"

        # Save using file storage service
        file_path = f"templates/{user_id}/previews/{unique_filename}"

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Save file
        saved_path = file_storage.save_file(file_path, img_bytes)

        # Return URL
        return f"/api/files/{saved_path}"

    def _decode_image(self, image_data: str) -> Image.Image:
        """Decode base64 image data"""

        # Remove data URL prefix if present
        if image_data.startswith('data:'):
            image_data = image_data.split(',')[1]

        # Decode base64
        img_bytes = base64.b64decode(image_data)

        # Open with PIL
        return Image.open(io.BytesIO(img_bytes))

    def _get_file_path_from_url(self, url: str) -> str:
        """Convert file URL to local file path"""
        # This is a simplified implementation
        # In production, you'd want proper URL to path conversion
        if url.startswith('/api/files/'):
            return url.replace('/api/files/', file_storage.base_path + '/')
        return url

    def _convert_to_response(self, template: EtsyProductTemplate) -> TemplateEditorResponse:
        """Convert database model to response model"""

        # Parse metadata from materials field
        try:
            metadata = json.loads(template.materials or "{}")
        except json.JSONDecodeError:
            metadata = {}

        # Extract design areas
        design_areas = []
        for area_data in metadata.get("design_areas", []):
            design_areas.append(DesignArea(**area_data))

        return TemplateEditorResponse(
            id=template.id,
            user_id=template.user_id,
            name=template.name,
            description=template.description,
            category=metadata.get("category"),
            background_image_url=metadata.get("background_image_url", ""),
            background_filename=metadata.get("background_filename", ""),
            design_areas=design_areas,
            metadata=metadata.get("metadata", {}),
            created_at=template.created_at,
            updated_at=template.updated_at
        )