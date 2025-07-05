import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from server.api.models import MockupMaskData, User

def save_mask_data_to_db(
    db: Session, 
    user_id: int, 
    template_name: str, 
    masks_data: List[List[Dict[str, float]]], 
    starting_name: int = 100
) -> MockupMaskData:
    """
    Save mask data to database for a specific user and template.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template (e.g., 'UVDTF 16oz')
        masks_data: List of masks, each containing list of points
        starting_name: Starting ID for generated files
    
    Returns:
        MockupMaskData object
    """
    # Convert masks_data to the format expected by the mockup engine
    masks = []
    points = []
    
    for mask_points in masks_data:
        # Convert to list of [x, y] coordinates for storage
        mask_coords = [[point['x'], point['y']] for point in mask_points]
        masks.append(mask_coords)
        points.append(mask_coords)  # Points are the same as masks in this case
    
    # Check if mask data already exists for this user and template
    existing_mask = db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id,
        MockupMaskData.template_name == template_name
    ).first()
    
    if existing_mask:
        # Update existing record
        existing_mask.masks = masks
        existing_mask.points = points
        existing_mask.starting_name = starting_name
        db.commit()
        return existing_mask
    else:
        # Create new record
        mask_data = MockupMaskData(
            user_id=user_id,
            template_name=template_name,
            masks=masks,
            points=points,
            starting_name=starting_name
        )
        db.add(mask_data)
        db.commit()
        db.refresh(mask_data)
        return mask_data

def load_mask_data_from_db(
    db: Session, 
    user_id: int, 
    template_name: str
) -> Tuple[List[np.ndarray], List[List[Tuple[int, int]]], int]:
    """
    Load mask data from database for a specific user and template.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template
    
    Returns:
        Tuple of (masks, points, starting_name) where masks are numpy arrays and points are lists of tuples
    """
    mask_data = db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id,
        MockupMaskData.template_name == template_name
    ).first()
    
    if not mask_data:
        raise ValueError(f"No mask data found for user {user_id} and template {template_name}")
    
    masks = []
    points_list = []
    
    # Convert stored data to numpy arrays and points
    for mask_points in mask_data.masks:
        if mask_points:
            # Convert to numpy array for OpenCV operations
            mask_array = np.array(mask_points, dtype=np.int32)
            masks.append(mask_array)
            
            # Convert points to list of tuples
            points = [(int(point[0]), int(point[1])) for point in mask_points]
            points_list.append(points)
    
    return masks, points_list, mask_data.starting_name

def update_starting_name(
    db: Session, 
    user_id: int, 
    template_name: str, 
    new_starting_name: int
) -> bool:
    """
    Update the starting_name for a user's template mask data.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template
        new_starting_name: New starting name value
    
    Returns:
        True if updated successfully, False otherwise
    """
    mask_data = db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id,
        MockupMaskData.template_name == template_name
    ).first()
    
    if mask_data:
        mask_data.starting_name = new_starting_name
        db.commit()
        return True
    
    return False

def get_user_mask_data(db: Session, user_id: int) -> List[MockupMaskData]:
    """
    Get all mask data for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
    
    Returns:
        List of MockupMaskData objects
    """
    return db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id
    ).all()

def delete_mask_data(db: Session, user_id: int, template_name: str) -> bool:
    """
    Delete mask data for a specific user and template.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template
    
    Returns:
        True if deleted successfully, False otherwise
    """
    mask_data = db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id,
        MockupMaskData.template_name == template_name
    ).first()
    
    if mask_data:
        db.delete(mask_data)
        db.commit()
        return True
    
    return False 