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

def save_image_with_format(image, folder_path, filename, file_format='PNG', target_dpi=(STD_DPI, STD_DPI), placed_images=None):
    """
    Save image in specified format (PNG, SVG, or PSD).

    Args:
        image: numpy array image data
        folder_path: output directory path
        filename: base filename (extension will be added based on format)
        file_format: output format ('PNG', 'SVG', or 'PSD')
        target_dpi: DPI tuple for the output image
        placed_images: list of dicts with individual image metadata for layered formats
                       Each dict contains: label, x, y, width, height, image_data
    """
    import logging

    # Ensure output directory exists
    os.makedirs(folder_path, exist_ok=True)

    # Validate image
    if image is None or not isinstance(image, np.ndarray):
        raise ValueError("Invalid image data")

    if image.size == 0:
        raise ValueError("Empty image array")

    # Remove existing extension from filename if present
    base_filename = os.path.splitext(filename)[0]

    # Log image info
    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) > 2 else 1
    size_mb = (height * width * channels) / (1024 * 1024)
    logging.info(f"Saving image: {width}x{height}x{channels} ({size_mb:.1f}MB) -> {base_filename}.{file_format.lower()}")

    file_format = file_format.upper()

    if file_format == 'PNG':
        output_path = os.path.join(folder_path, f"{base_filename}.png")
        save_single_image(image, folder_path, f"{base_filename}.png", target_dpi)
    elif file_format == 'SVG':
        output_path = os.path.join(folder_path, f"{base_filename}.svg")
        _save_as_svg(image, output_path, target_dpi, placed_images)
    elif file_format == 'PSD':
        output_path = os.path.join(folder_path, f"{base_filename}.psd")
        _save_as_psd(image, output_path, target_dpi, placed_images)
    else:
        raise ValueError(f"Unsupported format: {file_format}. Use PNG, SVG, or PSD")

    logging.info(f"Successfully saved image in {file_format} format: {output_path}")
    return output_path


def _save_as_svg(image, output_path, target_dpi=(STD_DPI, STD_DPI), placed_images=None):
    """Convert numpy array image to SVG format with individual labeled layers."""
    import logging
    import base64

    try:
        # Get image dimensions
        height, width = image.shape[:2]

        # Convert pixels to inches for SVG dimensions
        width_inches = width / target_dpi[0]
        height_inches = height / target_dpi[1]

        # Start SVG content with inkscape namespace for layer labels
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="{width_inches}in" height="{height_inches}in"
     viewBox="0 0 {width} {height}">
'''

        # If we have individual image data, create separate layers for each
        if placed_images and len(placed_images) > 0:
            logging.info(f"Creating SVG with {len(placed_images)} individual labeled layers")

            # Create a group for each individual image
            for idx, img_info in enumerate(placed_images):
                label = img_info.get('label', f'Image_{idx}')
                x = img_info.get('x', 0)
                y = img_info.get('y', 0)
                img_width = img_info.get('width', 0)
                img_height = img_info.get('height', 0)
                img_data = img_info.get('image_data')

                if img_data is not None and isinstance(img_data, np.ndarray):
                    # Encode individual image as PNG
                    retval, buffer = cv2.imencode(".png", img_data)
                    if retval:
                        png_base64 = base64.b64encode(buffer).decode('utf-8')

                        # Create a labeled group for this image
                        # Using id and inkscape:label for compatibility with design software
                        svg_content += f'''  <g id="{label}" inkscape:label="{label}">
    <image x="{x}" y="{y}" width="{img_width}" height="{img_height}"
           xlink:href="data:image/png;base64,{png_base64}"/>
  </g>
'''

            logging.info(f"Created {len(placed_images)} labeled layers in SVG")
        else:
            # Fallback: save entire image as single layer
            logging.info("No individual image data provided, saving as single layer")
            retval, buffer = cv2.imencode(".png", image)
            if not retval:
                raise RuntimeError("Failed to encode image to PNG for SVG embedding")

            png_base64 = base64.b64encode(buffer).decode('utf-8')
            svg_content += f'''  <image width="{width}" height="{height}"
         xlink:href="data:image/png;base64,{png_base64}"/>
'''

        # Close SVG
        svg_content += '</svg>'

        # Write to file
        with open(output_path, 'w') as f:
            f.write(svg_content)

        logging.info(f"Successfully saved SVG: {output_path}")
    except Exception as e:
        logging.error(f"Error saving SVG {output_path}: {e}")
        raise


def _save_as_psd(image, output_path, target_dpi=(STD_DPI, STD_DPI), placed_images=None):
    """Convert numpy array image to PSD format with individual labeled layers."""
    import logging

    try:
        # Try using psd-tools library first (if available)
        try:
            from psd_tools import PSDImage
            from psd_tools.api.layers import PixelLayer

            # Get canvas dimensions
            height, width = image.shape[:2]

            # Create PSD document
            psd = PSDImage.new("RGBA", (width, height))

            # If we have individual image data, create separate layers for each
            if placed_images and len(placed_images) > 0:
                logging.info(f"Creating PSD with {len(placed_images)} individual labeled layers")

                # Create a layer for each individual image
                for idx, img_info in enumerate(placed_images):
                    label = img_info.get('label', f'Image_{idx}')
                    x = img_info.get('x', 0)
                    y = img_info.get('y', 0)
                    img_width = img_info.get('width', 0)
                    img_height = img_info.get('height', 0)
                    img_data = img_info.get('image_data')

                    if img_data is not None and isinstance(img_data, np.ndarray):
                        # Convert OpenCV BGR(A) to RGB(A) for PIL
                        if img_data.shape[2] == 4:
                            img_rgb = cv2.cvtColor(img_data, cv2.COLOR_BGRA2RGBA)
                        else:
                            img_rgb = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)
                            # Add alpha channel
                            img_rgb = np.dstack([img_rgb, np.ones((img_rgb.shape[0], img_rgb.shape[1], 1), dtype=np.uint8) * 255])

                        # Create PIL image for this layer
                        layer_pil = Image.fromarray(img_rgb, 'RGBA')

                        # Create a blank canvas and paste the image at the correct position
                        canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                        canvas.paste(layer_pil, (x, y))

                        # Create layer from canvas
                        layer = PixelLayer.frompil(canvas, psd, label)

                logging.info(f"Created {len(placed_images)} labeled layers in PSD")
            else:
                # Fallback: create single layer with entire image
                logging.info("No individual image data provided, creating single layer")

                # Convert OpenCV BGR(A) to RGB(A) for PIL
                if image.shape[2] == 4:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                else:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Create PIL image
                pil_image = Image.fromarray(image_rgb)
                pil_image.info['dpi'] = target_dpi

                # Create single layer
                layer = PixelLayer.frompil(pil_image, psd, "Background")

            # Save PSD
            psd.save(output_path)
            logging.info(f"Successfully saved PSD using psd-tools: {output_path}")
            return
        except ImportError:
            logging.warning("psd-tools not available, falling back to PIL method")

        # Fallback: Save as layered TIFF using PIL (Photoshop compatible)
        # Convert OpenCV BGR(A) to RGB(A)
        if image.shape[2] == 4:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            mode = 'RGBA'
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mode = 'RGB'

        # Create PIL image and save
        pil_image = Image.fromarray(image_rgb, mode)
        pil_image.info['dpi'] = target_dpi

        # PIL doesn't have native PSD support, so we'll save as TIFF with layers
        # which is compatible with Photoshop
        logging.warning("Saving as multi-layer TIFF (Photoshop compatible) instead of native PSD")
        logging.warning("For full PSD layer support, install psd-tools: pip install psd-tools")
        tiff_path = output_path.replace('.psd', '.tif')
        pil_image.save(tiff_path, format='TIFF', dpi=target_dpi, compression='tiff_lzw')

        # If user expects .psd, also save a copy with .psd extension
        # (it's actually a TIFF but Photoshop can open it)
        import shutil
        shutil.copy2(tiff_path, output_path)

        logging.info(f"Successfully saved PSD-compatible TIFF: {output_path}")
    except Exception as e:
        logging.error(f"Error saving PSD {output_path}: {e}")
        raise


def save_single_image(image, folder_path, filename, target_dpi=(STD_DPI,STD_DPI)):
    import logging
    output_path = os.path.join(folder_path, filename)

    try:
        # Ensure output directory exists
        os.makedirs(folder_path, exist_ok=True)

        # Validate image
        if image is None or not isinstance(image, np.ndarray):
            raise ValueError("Invalid image data")

        if image.size == 0:
            raise ValueError("Empty image array")

        # Log image info for debugging large images
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        size_mb = (height * width * channels) / (1024 * 1024)
        logging.info(f"Saving image: {width}x{height}x{channels} ({size_mb:.1f}MB) -> {filename}")
        cv2.imwrite(output_path, image)
        # # For very large images, use simpler saving method to avoid memory issues
        # if size_mb > 500:  # > 500MB images
        #     logging.info(f"Large image detected, using simplified save method")
        #     success = cv2.imwrite(output_path, image)
        #     if not success:
        #         raise RuntimeError("cv2.imwrite failed for large image")
        #     logging.info(f"Successfully saved large image: {filename}")
        #     return
        
        # Use the original DPI method for smaller images
        retval, buffer = cv2.imencode(".png", image)
        if not retval:
            raise RuntimeError("Failed to encode image to PNG")
        
        s = buffer.tostring()
        
        # Find start of IDAT chunk
        IDAToffset = s.find(b'IDAT') - 4
        # if IDAToffset < 0:
        #     logging.warning(f"Could not find IDAT chunk in {filename}, using simple save")
        #     success = cv2.imwrite(output_path, image)
        #     if not success:
        #         raise RuntimeError("cv2.imwrite failed")
        #     return
        
        # Create pHYs chunk for DPI
        pHYs = b'pHYs' + struct.pack('!IIc',int(target_dpi[0]/0.0254),int(target_dpi[1]/0.0254),b"\x01")
        pHYs = struct.pack('!I',9) + pHYs + struct.pack('!I',zlib.crc32(pHYs))
        
        # Write file with DPI information
        with open(output_path, "wb") as out:
            out.write(buffer[0:IDAToffset])
            out.write(pHYs)
            out.write(buffer[IDAToffset:])
            
        logging.info(f"Successfully saved image with DPI: {filename}")
        
    except Exception as e:
        logging.error(f"Error saving image {filename}: {e}")
        # Try fallback simple save
        try:
            logging.info(f"Attempting fallback save for {filename}")
            success = cv2.imwrite(output_path, image)
            if not success:
                raise RuntimeError("Fallback cv2.imwrite also failed")
            logging.info(f"Fallback save successful: {filename}")
        except Exception as fallback_error:
            logging.error(f"Fallback save also failed for {filename}: {fallback_error}")
            raise RuntimeError(f"Failed to save image {filename}: {e}, fallback also failed: {fallback_error}")

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
    
    for root, _, files in os.walk(folder_path):
        png_filepath.extend([os.path.join(root, file) for file in files if file.lower().endswith('.png')])
        png_filenames.extend([file for file in files if file.lower().endswith('.png')])
    
    return png_filepath, png_filenames