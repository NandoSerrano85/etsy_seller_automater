import json
import os
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from server.api.models import MockupImage, User

def save_mockup_image_to_db(
    db: Session,
    user_id: int,
    template_name: str,
    filename: str,
    file_path: str,
    mask_data: Optional[List] = None,
    points_data: Optional[List] = None,
    image_type: Optional[str] = None,
    design_id: Optional[str] = None
) -> MockupImage:
    """
    Save mockup image data to database.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template (e.g., 'UVDTF 16oz')
        filename: Original filename
        file_path: Full path to the mockup image
        mask_data: Mask data as JSON-serializable list
        points_data: Points data as JSON-serializable list
        image_type: Type of image (e.g., 'UVDTF 16oz')
        design_id: ID of the design this mockup was created from
    
    Returns:
        MockupImage object
    """
    # Check if mockup image already exists for this user and filename
    existing_mockup = db.query(MockupImage).filter(
        MockupImage.user_id == user_id,
        MockupImage.filename == filename
    ).first()
    
    if existing_mockup:
        # Update existing record
        setattr(existing_mockup, "template_name", template_name)
        setattr(existing_mockup, "file_path", file_path)
        setattr(existing_mockup, "mask_data", json.dumps(mask_data) if mask_data else None)
        setattr(existing_mockup, "points_data", json.dumps(points_data) if points_data else None)
        setattr(existing_mockup, "image_type", image_type)
        setattr(existing_mockup, "design_id", design_id)
        db.commit()
        return existing_mockup
    else:
        # Create new record
        mockup_image = MockupImage(
            user_id=user_id,
            template_name=template_name,
            filename=filename,
            file_path=file_path,
            mask_data=json.dumps(mask_data) if mask_data else None,
            points_data=json.dumps(points_data) if points_data else None,
            image_type=image_type,
            design_id=design_id
        )
        db.add(mockup_image)
        db.commit()
        db.refresh(mockup_image)
        return mockup_image

def get_user_mockup_images(
    db: Session,
    user_id: int,
    template_name: Optional[str] = None
) -> List[MockupImage]:
    """
    Get mockup images for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Optional template name filter
    
    Returns:
        List of MockupImage objects
    """
    query = db.query(MockupImage).filter(MockupImage.user_id == user_id)
    
    if template_name:
        query = query.filter(MockupImage.template_name == template_name)
    
    return query.all()

def get_mockup_image_by_filename(
    db: Session,
    user_id: int,
    filename: str
) -> Optional[MockupImage]:
    """
    Get a specific mockup image by filename for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
        filename: Filename to search for
    
    Returns:
        MockupImage object or None if not found
    """
    return db.query(MockupImage).filter(
        MockupImage.user_id == user_id,
        MockupImage.filename == filename
    ).first()

def delete_mockup_image(
    db: Session,
    user_id: int,
    filename: str
) -> bool:
    """
    Delete a mockup image from database and file system.
    
    Args:
        db: Database session
        user_id: ID of the user
        filename: Filename to delete
    
    Returns:
        True if successful, False otherwise
    """
    mockup_image = get_mockup_image_by_filename(db, user_id, filename)
    
    if not mockup_image:
        return False
    
    # Delete file from file system
    file_path = getattr(mockup_image, "file_path")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass  # File might already be deleted
    
    # Delete from database
    db.delete(mockup_image)
    db.commit()
    
    return True

def get_mockup_images_with_mask_data(
    db: Session,
    user_id: int,
    template_name: Optional[str] = None
) -> List[Dict]:
    """
    Get mockup images with parsed mask data for gangsheet processing.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Optional template name filter
    
    Returns:
        List of dictionaries with mockup image data and parsed mask data
    """
    mockup_images = get_user_mockup_images(db, user_id, template_name)
    
    result = []
    for mockup in mockup_images:
        mask_data = None
        points_data = None
        
        mask_data_raw = getattr(mockup, "mask_data")
        if mask_data_raw:
            try:
                mask_data = json.loads(mask_data_raw)
            except (json.JSONDecodeError, TypeError):
                mask_data = None
        
        points_data_raw = getattr(mockup, "points_data")
        if points_data_raw:
            try:
                points_data = json.loads(points_data_raw)
            except (json.JSONDecodeError, TypeError):
                points_data = None
        
        result.append({
            'id': mockup.id,
            'filename': mockup.filename,
            'file_path': mockup.file_path,
            'template_name': mockup.template_name,
            'image_type': mockup.image_type,
            'design_id': mockup.design_id,
            'mask_data': mask_data,
            'points_data': points_data,
            'created_at': mockup.created_at
        })
    
    return result 