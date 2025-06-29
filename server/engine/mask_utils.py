import numpy as np
import cv2
import json
import os
from typing import List, Dict, Any, Tuple, Optional

def convert_react_mask_to_opencv(mask_points: List[Dict[str, float]], image_shape: Tuple[int, int]) -> np.ndarray:
    """
    Convert mask points from React frontend format to OpenCV mask format.
    
    Args:
        mask_points: List of points with x, y coordinates from React
        image_shape: Tuple of (height, width) of the original image
    
    Returns:
        OpenCV mask as numpy array
    """
    if not mask_points or len(mask_points) < 3:
        raise ValueError("Need at least 3 points to create a mask")
    
    # Convert points to the format expected by OpenCV
    points = np.array([[point['x'], point['y']] for point in mask_points], dtype=np.int32)
    
    # Create mask
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [points], 255)
    
    return mask

def save_mask_data(masks_data: List[List[Dict[str, float]]], image_type: str, file_path: Optional[str] = None) -> str:
    """
    Save mask data to JSON file in the format expected by the mockup engine.
    
    Args:
        masks_data: List of masks, each containing list of points
        image_type: Type of image (e.g., 'UVDTF 16oz')
        file_path: Optional custom file path, defaults to project root
    
    Returns:
        Path to the saved file
    """
    if file_path is None:
        # Default to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(project_root, "mockup_mask_data.json")
    
    # Convert to the format expected by the mockup engine
    mask_data_structure = {
        image_type: {
            "masks": masks_data,
            "points": masks_data,  # Points are the same as masks in this case
            "starting_name": 100
        }
    }
    
    # Save to JSON file
    with open(file_path, 'w') as f:
        json.dump(mask_data_structure, f, indent=2)
    
    return file_path

def load_mask_data(file_path: str, image_type: str) -> Tuple[List[np.ndarray], List[List[Tuple[int, int]]]]:
    """
    Load mask data from JSON file and convert to format expected by mockup engine.
    
    Args:
        file_path: Path to the JSON file
        image_type: Type of image to load masks for
    
    Returns:
        Tuple of (masks, points) where masks are numpy arrays and points are lists of tuples
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if image_type not in data:
        raise ValueError(f"No mask data found for image type: {image_type}")
    
    image_data = data[image_type]
    masks = []
    points_list = []
    
    # Convert masks to numpy arrays
    for mask_points in image_data.get("masks", []):
        if mask_points:
            # Convert to numpy array for OpenCV operations
            mask_array = np.array(mask_points, dtype=np.int32)
            masks.append(mask_array)
            
            # Convert points to list of tuples
            points = [(int(point[0]), int(point[1])) for point in mask_points]
            points_list.append(points)
    
    return masks, points_list

def validate_mask_points(points: List[Dict[str, float]], min_points: int = 3) -> bool:
    """
    Validate that mask points are valid.
    
    Args:
        points: List of points with x, y coordinates
        min_points: Minimum number of points required
    
    Returns:
        True if points are valid, False otherwise
    """
    if len(points) < min_points:
        return False
    
    # Check that all points have x and y coordinates
    for point in points:
        if 'x' not in point or 'y' not in point:
            return False
        if not isinstance(point['x'], (int, float)) or not isinstance(point['y'], (int, float)):
            return False
    
    return True

def scale_points_to_original(points: List[Dict[str, float]], scale_factor: float) -> List[Dict[str, float]]:
    """
    Scale points back to original image size.
    
    Args:
        points: List of points with x, y coordinates (display coordinates)
        scale_factor: Scale factor used for display
    
    Returns:
        List of points scaled to original image coordinates
    """
    return [
        {
            'x': point['x'] / scale_factor,
            'y': point['y'] / scale_factor
        }
        for point in points
    ] 