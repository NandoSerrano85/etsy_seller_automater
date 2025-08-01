"""
Example of how resizing.py can be modified to use database configurations.
This is a demonstration of the integration pattern.
"""
import cv2, os
import numpy as np
from server.src.utils.util import (
    inches_to_pixels, 
    rotate_image_90,
    get_width_and_height,
)
from server.src.routes.canvas_sizes.service import get_resizing_canvas_configs
from server.src.routes.size_config.service import get_resizing_size_configs

os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
STD_DPI = 400

def get_resizing_configs_from_db(db, canvas_id, product_template_id):
    """
    Get canvas and size configurations from database for a specific user and template.
    Returns (CANVAS, SIZING) dicts.
    """
    CANVAS = get_resizing_canvas_configs(db, product_template_id)
    SIZING = get_resizing_size_configs(db, canvas_id, product_template_id)
    if CANVAS and SIZING:
        return CANVAS, SIZING
    else:
        return get_default_configs()

def get_default_configs():
    """Get default hardcoded configurations as fallback."""
    SIZING = {
        'UVDTF 16oz': { 'width': 9.5, 'height': 4.33 },
        # Add more template sizes here as needed
    }
    CANVAS = {'UVDTF Decal': { 'height': 4.0, 'width': 4.0 },}
    return CANVAS, SIZING

"""
    This function creates a canvas and centers the image into the canvas
"""
def fit_image_to_center_canvas(resized_img, new_width_px, new_height_px, target_dpi, image_type, db, canvas_id, product_template_id, image_size=None, shop_name=None):
    """
    This function creates a canvas and centers the image into the canvas.
    Now requires db, user_id, and product_template_id to fetch configs from DB.
    """
    # Get canvas configs from database or fallback to defaults
    if db and canvas_id and product_template_id:
        CANVAS, _ = get_resizing_configs_from_db(db, canvas_id, product_template_id)
    else:
        CANVAS, _ = get_default_configs()
    
    if image_type not in CANVAS:
        raise ValueError(f"No canvas configuration found for image type: {image_type}")
    
    canvas_width_px = inches_to_pixels(CANVAS[image_type]['width'], target_dpi)
    canvas_height_px = inches_to_pixels(CANVAS[image_type]['height'], target_dpi)

    background = np.zeros((canvas_height_px, canvas_width_px, 4), dtype=np.uint8)

    # Calculate the position to place the resized image in the center
    x_offset = (canvas_width_px - new_width_px) // 2
    y_offset = (canvas_height_px - new_height_px) // 2
    
    # Copy the resized image onto the transparent background
    background[y_offset:y_offset+new_height_px, x_offset:x_offset+new_width_px] = resized_img

    return background

"""
    This function resizes an image based on inches
"""
def resize_image_by_inches(image_path, image_type, db=None, canvas_id=None, product_template_id=None, image_size=None, image=None, target_dpi=STD_DPI, is_new_mk=False, shop_name=None):
    """
    This function resizes an image based on inches.
    Now requires db, user_id, and product_template_id to fetch configs from DB.
    """
    # Get sizing configs from database or fallback to defaults
    if db and canvas_id and product_template_id:
        _, SIZING = get_resizing_configs_from_db(db, canvas_id, product_template_id)
    else:
        _, SIZING = get_default_configs()
    
    # Use the provided image array if available, otherwise load from disk
    if isinstance(image, np.ndarray):
        img = image
    else:
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    # Ensure the image was loaded correctly
    if img is None:
        raise ValueError(f"Image could not be loaded from array or path: {image_path}")

    # Convert 16-bit images to 8-bit if needed
    if img.dtype == np.uint16:
        img = (img / 256).astype(np.uint8)

    # Handle grayscale images (single channel)
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    # Handle 3-channel images (BGR)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    # If already 4 channels, do nothing
    # If more than 4 channels, take first 4 (rare, but for robustness)
    elif img.shape[2] > 4:
        img = img[:, :, :4]

    current_width_inches, current_height_inches = get_width_and_height(img, image_path, target_dpi)

    if current_width_inches >= current_height_inches:
        current_largest_side_inches = current_width_inches
    else:
        current_largest_side_inches = current_height_inches

    # Check if image_type exists in SIZING config
    if image_type not in SIZING:
        raise ValueError(f"No sizing configuration found for image type: {image_type}")

    if image_type == 'DTF' or image_type == 'Sublimation':
        if image_size in SIZING[image_type]:
            target_largest_side_inches = SIZING[image_type][image_size]['height']
        else:
            raise Exception("Missing Size Value. Please add an image_size value of 'Adult+', 'Adult', 'Youth', 'Toddler' or 'Pocket'.")
    elif image_type == 'UVDTF 40oz Top' or image_type == 'UVDTF 40oz Bottom':
        target_largest_side_inches = SIZING[image_type]['width']
    elif image_type == 'UVDTF Mirror':
        if image_size in SIZING[image_type]:
            target_largest_side_inches = SIZING[image_type][image_size]['height']
    else:
        if SIZING[image_type]['width'] >= SIZING[image_type]['height']:
            target_largest_side_inches = SIZING[image_type]['width']
        else:
            target_largest_side_inches = SIZING[image_type]['height']

    # Calculate scale factor
    scale_factor = target_largest_side_inches / current_largest_side_inches

    if image_type == 'DTF' or image_type == 'Sublimation' or image_type == 'UVDTF Decal' or image_type == 'UVDTF Lid' or image_type == 'Custom 2x2' or image_type == 'UVDTF Ornament' or image_type == 'UVDTF Logo Cup Care Decal' or image_type == 'UVDTF Logo Bottom Shot Decal' or image_type == 'UVDTF Mirror' or image_type == 'UVDTF Logo Sticker':
        # Calculate new dimensions
        new_width_inches = (current_width_inches * scale_factor)
        new_height_inches = (current_height_inches * scale_factor)

        # Calculate new size in pixels based on new dimensions inches and DPI
        new_width_px = inches_to_pixels(new_width_inches, target_dpi)
        new_height_px = inches_to_pixels(new_height_inches, target_dpi)
    elif image_type == 'MK' or image_type == 'UVDTF Bookmark' or image_type == 'MK Tapered' or image_type == 'UVDTF Shot':
        current_width = inches_to_pixels(current_width_inches, target_dpi)
        current_height = inches_to_pixels(current_height_inches, target_dpi)

        target_width = inches_to_pixels(SIZING[image_type]['width'], target_dpi)
        target_height = inches_to_pixels(SIZING[image_type]['height'], target_dpi)

        # Calculate scaling factor
        scale_width = target_width / current_width
        scale_height = target_height / current_height
        scale_factor = min(scale_width, scale_height)

        new_width_px = int(current_width * scale_factor)
        new_height_px = int(current_height * scale_factor)
    else:
        # Calculate new size in pixels based on target inches and DPI
        new_width_px = inches_to_pixels(SIZING[image_type]['width'], target_dpi)
        new_height_px = inches_to_pixels(SIZING[image_type]['height'], target_dpi)

    interpolation = cv2.INTER_CUBIC if scale_factor > 1 else cv2.INTER_AREA 

    # Resize the image
    resized_img = cv2.resize(img, (new_width_px, new_height_px), interpolation=interpolation)

    # Fit the resized images into a canvas
    if image_type == 'UVDTF Decal' or image_type == 'UVDTF Bookmark' or image_type == 'UVDTF Lid' or image_type == 'Custom 2x2' or image_type == 'UVDTF Ornament' or image_type == 'UVDTF Logo Cup Care Decal' or image_type == 'UVDTF Logo Bottom Shot Decal' or image_type == 'UVDTF Logo Sticker':
        return fit_image_to_center_canvas(resized_img, new_width_px, new_height_px, target_dpi, image_type, db, user_id, product_template_id, shop_name=shop_name)
    elif image_type == 'MK' or image_type == 'MK Tapered' or image_type == 'MK Rectangle' or image_type == 'UVDTF Shot':
        if (new_width_px > new_height_px) and is_new_mk:
            rotated_img = rotate_image_90(resized_img)
            return fit_image_to_center_canvas(rotated_img, rotated_img.shape[1], rotated_img.shape[0], target_dpi, image_type, db, user_id, product_template_id, shop_name=shop_name)
        else:
            return fit_image_to_center_canvas(resized_img, new_width_px, new_height_px, target_dpi, image_type, db, user_id, product_template_id, shop_name=shop_name)

    return resized_img 