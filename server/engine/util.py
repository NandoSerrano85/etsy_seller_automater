import cv2, os, numpy as np, struct, zlib, math
from PIL import Image

STD_DPI = 400
def inches_to_pixels(inches, dpi):
    return int(round(inches * dpi))

# def get_dpi_from_image(image_path):
#     # Default DPI for PNG images if not specified
#     default_dpi = 400

#     # Open the image file in binary mode
#     with open(image_path, 'rb') as f:
#         # Read the first 24 bytes to check the PNG signature and IHDR chunk
#         header = f.read(24)
#         if header[:8] != b'\x89PNG\r\n\x1a\n':
#             return default_dpi, default_dpi

#         # Read chunks until we find the pHYs chunk
#         while True:
#             chunk_length = int.from_bytes(f.read(4), 'big')
#             chunk_type = f.read(4)
#             if chunk_type == b'pHYs':
#                 # Read the pHYs chunk data
#                 ppu_x = int.from_bytes(f.read(4), 'big')
#                 ppu_y = int.from_bytes(f.read(4), 'big')
#                 unit_specifier = f.read(1)
#                 if unit_specifier == b'\x01':  # Meters
#                     dpi_x = ppu_x * 0.0254
#                     dpi_y = ppu_y * 0.0254
#                     return dpi_x, dpi_y
#                 else:
#                     return default_dpi, default_dpi
#             else:
#                 # Skip the chunk data and CRC
#                 f.seek(chunk_length + 4, os.SEEK_CUR)
#             if chunk_type == b'IEND':
#                 break

    # return default_dpi, default_dpi

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