import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from server.api.models import MockupMaskData, User
import cv2

def save_mask_data_to_db(
    db: Session, 
    user_id: int, 
    template_name: str, 
    masks_data: List[List[Dict[str, float]]], 
    starting_name: int = 100,
    image_shape=(1000, 1000)  # Default, or pass from frontend if needed
) -> MockupMaskData:
    """
    Save mask data to database for a specific user and template.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template (e.g., 'UVDTF 16oz')
        masks_data: List of masks, each containing list of points
        starting_name: Starting ID for generated files
        image_shape: Shape of the image for generating masks
    
    Returns:
        MockupMaskData object
    """
    # Convert points to mask arrays
    masks = []
    points = []
    for mask_points in masks_data:
        mask_coords = [[point['x'], point['y']] for point in mask_points]
        points.append(mask_coords)
        mask = points_to_mask(mask_coords, image_shape)
        masks.append(mask)
    
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
            masks=json.dumps(masks),
            points=json.dumps(points),
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
) -> Tuple[List[List[List[int]]], List[List[Tuple[int, int]]], int]:
    """
    Load mask data from database for a specific user and template.
    Returns:
        Tuple of (points, points_list, starting_name) where points is a list of lists of [x, y] pairs
    """
    mask_data = db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id,
        MockupMaskData.template_name == template_name
    ).first()
    if not mask_data:
        raise ValueError(f"No mask data found for user {user_id} and template {template_name}")
    # Parse JSON if needed
    points_data = mask_data.points
    if isinstance(points_data, str):
        points_data = json.loads(points_data)
    # Ensure all points are lists of [x, y]
    points_data = [ [ [int(coord[0]), int(coord[1])] for coord in mask ] for mask in points_data ]
    # For compatibility, also return points_list as list of tuples
    points_list = [ [ (int(coord[0]), int(coord[1])) for coord in mask ] for mask in points_data ]
    return points_data, points_list, mask_data.starting_name

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

def inspect_mask_data(db: Session, user_id: int, template_name: str) -> dict:
    """
    Inspect mask data in the database for debugging purposes.
    
    Args:
        db: Database session
        user_id: ID of the user
        template_name: Name of the template
    
    Returns:
        Dictionary with inspection results
    """
    mask_data = db.query(MockupMaskData).filter(
        MockupMaskData.user_id == user_id,
        MockupMaskData.template_name == template_name
    ).first()
    
    if not mask_data:
        return {"found": False, "error": f"No mask data found for user {user_id} and template {template_name}"}
    
    inspection = {
        "found": True,
        "user_id": mask_data.user_id,
        "template_name": mask_data.template_name,
        "starting_name": mask_data.starting_name,
        "created_at": str(mask_data.created_at),
        "updated_at": str(mask_data.updated_at),
        "masks_count": len(mask_data.masks) if mask_data.masks else 0,
        "points_count": len(mask_data.points) if mask_data.points else 0,
        "masks_data": mask_data.masks,
        "points_data": mask_data.points
    }
    
    # Try to infer image size from the first mask array
    masks_data = mask_data.masks
    if isinstance(masks_data, str):
        masks_data = json.loads(masks_data)
    if masks_data and isinstance(masks_data[0], list) and len(masks_data[0]) > 0:
        inspection["image_height"] = len(masks_data[0])
        inspection["image_width"] = len(masks_data[0][0]) if len(masks_data[0]) > 0 else 0
    
    # Analyze each mask
    if masks_data:
        inspection["mask_analysis"] = []
        for i, mask_array in enumerate(masks_data):
            if mask_array:
                all_zeros = all(all(val == 0 for val in row) for row in mask_array)
                point_count = sum(sum(1 for val in row if val > 0) for row in mask_array)
                min_x = min_y = float('inf')
                max_x = max_y = float('-inf')
                for y, row in enumerate(mask_array):
                    for x, val in enumerate(row):
                        if val > 0:
                            min_x = min(min_x, x)
                            max_x = max(max_x, x)
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
                bounds = {"min_x": int(min_x) if min_x != float('inf') else 0,
                          "max_x": int(max_x) if max_x != float('-inf') else 0,
                          "min_y": int(min_y) if min_y != float('inf') else 0,
                          "max_y": int(max_y) if max_y != float('-inf') else 0}
                inspection["mask_analysis"].append({
                    "mask_index": i,
                    "point_count": point_count,
                    "all_zeros": all_zeros,
                    "bounds": bounds,
                    "mask_array": mask_array
                })
    
    return inspection

def points_to_mask(points, image_shape):
    """
    Convert a list of (x, y) points to a 2D binary mask array.
    Accepts image_shape as (height, width) or (width, height).
    """
    # Ensure image_shape is (height, width)
    if len(image_shape) == 2:
        h, w = image_shape
        if w < 20 and h > 100:  # likely (width, height) by mistake
            h, w = w, h
    else:
        h, w = 1000, 1000
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(points, dtype=np.int32)
    cv2.fillPoly(mask, [pts], (255,))
    return mask.tolist()  # Convert to list for JSON storage 