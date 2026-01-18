"""Product image upload endpoints for CraftFlow Commerce."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import os
import uuid
from pathlib import Path

from server.src.database.core import get_db
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.routes.auth.plan_access import require_pro_plan
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/admin/product-images',
    tags=['Ecommerce Admin - Product Images']
)


class ImageUploadResponse(BaseModel):
    """Response model for image upload."""
    url: str
    filename: str
    size: int


@router.post('/upload', response_model=ImageUploadResponse)
async def upload_product_image(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Upload a product mockup image.

    Stores the image in a user-specific folder and returns a URL that can be used
    in the product images array and accessed by the storefront.
    In production, this should store to NAS. For now, stores locally.

    Requires: Pro plan or higher
    """
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Read file content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Limit file size to 10MB
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else '.jpg'
    unique_filename = f"product_{uuid.uuid4().hex}{file_extension}"

    # User-specific folder path
    user_folder = str(current_user.id)

    # Check if NAS storage is available
    nas_enabled = os.getenv('QNAP_HOST') and os.getenv('QNAP_USERNAME') and os.getenv('QNAP_PASSWORD')

    if nas_enabled:
        # Store to NAS
        try:
            from server.src.services.nas_service import get_nas_service
            nas_service = get_nas_service()

            # Upload to NAS in user-specific product_mockups folder
            nas_path = f"product_mockups/{user_folder}/{unique_filename}"
            nas_service.upload_file(content, nas_path)

            # Return NAS URL
            file_url = f"/nas/product_mockups/{user_folder}/{unique_filename}"
        except Exception as e:
            # Fallback to local storage if NAS fails
            print(f"NAS upload failed: {e}. Falling back to local storage.")
            file_url = _store_locally(content, unique_filename, user_folder)
    else:
        # Store locally if NAS not configured
        file_url = _store_locally(content, unique_filename, user_folder)

    return ImageUploadResponse(
        url=file_url,
        filename=unique_filename,
        size=len(content)
    )


def _store_locally(content: bytes, filename: str, user_folder: str) -> str:
    """Store file locally in user-specific folder."""
    # Create user-specific uploads directory if it doesn't exist
    upload_dir = Path(f"uploads/product_mockups/{user_folder}")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = upload_dir / filename
    with open(file_path, "wb") as f:
        f.write(content)

    # Return relative URL
    return f"/uploads/product_mockups/{user_folder}/{filename}"


@router.post('/upload-multiple', response_model=List[ImageUploadResponse])
async def upload_multiple_product_images(
    files: List[UploadFile] = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Upload multiple product mockup images at once.

    Maximum 10 images per request.

    Requires: Pro plan or higher
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images per upload")

    results = []
    for file in files:
        try:
            result = await upload_product_image(file, db, current_user)
            results.append(result)
        except HTTPException as e:
            # Skip failed uploads but continue with others
            print(f"Failed to upload {file.filename}: {e.detail}")
            continue

    if not results:
        raise HTTPException(status_code=400, detail="All uploads failed")

    return results
