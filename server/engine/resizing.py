import cv2, os
import numpy as np
from server.engine.util import (
    inches_to_pixels, 
    rotate_image_90,
    check_image_array,
    get_width_and_height,
)

os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
SIZING = {'UVDTF 16oz': { 'width': 9.5, 'height': 4.33 },}
CANVAS = {'UVDTF Decal': { 'height': 4.0, 'width': 4.0 },}
STD_DPI = 400
"""
    This function creates a canvas and centers the image into the canvas
"""
def fit_image_to_center_canvas(resized_img, new_width_px, new_height_px, target_dpi, image_type, image_size=None):
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
def resize_image_by_inches(image_path, image_type, image_size=None, image=None, target_dpi=STD_DPI, is_new_mk=False):
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
        return fit_image_to_center_canvas(resized_img, new_width_px, new_height_px, target_dpi, image_type)
    elif image_type == 'MK' or image_type == 'MK Tapered' or image_type == 'MK Rectangle' or image_type == 'UVDTF Shot':
        if (new_width_px > new_height_px) and is_new_mk:
            rotated_img = rotate_image_90(resized_img)
            return fit_image_to_center_canvas(rotated_img, rotated_img.shape[1], rotated_img.shape[0], target_dpi, image_type)
        else:
            return fit_image_to_center_canvas(resized_img, new_width_px, new_height_px, target_dpi, image_type)

        
    return resized_img