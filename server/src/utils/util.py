import cv2, os, numpy as np, struct, zlib, math
from PIL import Image
from typing import Tuple, List

STD_DPI = 400
def inches_to_pixels(inches, dpi):
    return int(round(inches * dpi))

def rotate_image_90(image, rotations=1):
    """
    Rotate an image by 90 degrees clockwise.
    
    :param image: Input image
    :param rotations: Number of 90 degree rotations. Positive for clockwise, negative for counterclockwise.
    :return: Rotated image
    """
    # Ensure rotations is between -3 and 3
    rotations = rotations % 4
    
    if rotations == 0:
        return image
    elif rotations == 1:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif rotations == 2:
        return cv2.rotate(image, cv2.ROTATE_180)
    else:  # rotations == 3 or -1
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

def check_image_array(image_array):
    if image_array is None or len(image_array) == 0:
        return True
    
    for img in image_array:
        if img is None or not isinstance(img, np.ndarray):
            return True
    
    return False

def get_width_and_height(image, image_path, target_dpi=None):
    # Get current image size in pixels
    height_px, width_px = image.shape[:2]
    
    if target_dpi:
        dpi_x = dpi_y = target_dpi
    else:
        # Try to get DPI information using PIL
        dpi_x, dpi_y = get_dpi_from_image(image_path)
        
        if dpi_x is None or dpi_y is None:
            dpi_x = dpi_y = 400  # Default to 300 DPI if not found
    
    # Calculate and return current size in inches
    return width_px / dpi_x, height_px / dpi_y

def save_single_image(image, folder_path, filename, target_dpi=(STD_DPI,STD_DPI)):

    output_path = os.path.join(folder_path, filename)

    cv2.imwrite(output_path, image)

    retval, buffer = cv2.imencode(".png", image)
    s = buffer.tostring()

    # Find start of IDAT chunk
    IDAToffset = s.find(b'IDAT') - 4

    pHYs = b'pHYs' + struct.pack('!IIc',int(target_dpi[0]/0.0254),int(target_dpi[1]/0.0254),b"\x01" ) 
    pHYs = struct.pack('!I',9) + pHYs + struct.pack('!I',zlib.crc32(pHYs))

    with open(output_path, "wb") as out:
        out.write(buffer[0:IDAToffset])
        out.write(pHYs)
        out.write(buffer[IDAToffset:])

def get_dpi_from_image(image_path):
    # Default DPI for PNG images if not specified
    with Image.open(image_path) as img:
        dpi_x, dpi_y = img.info.get('dpi', (400, 400))
        return math.ceil(dpi_x), math.ceil(dpi_y)
    
def find_png_files(folder_path: str) -> Tuple[List[str], List[str]]:
    """Find all PNG files in a directory"""
    folder_path = os.path.join(folder_path, '')
    png_filepath = []
    png_filenames = []
    
    for root, dirs, files in os.walk(folder_path):
        png_filepath.extend([os.path.join(root, file) for file in files if file.lower().endswith('.png')])
        png_filenames.extend([file for file in files if file.lower().endswith('.png')])
    
    return png_filepath, png_filenames