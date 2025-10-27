import numpy as np
import cv2, os, tempfile
from datetime import date
from functools import lru_cache
from server.src.utils.util import inches_to_pixels, rotate_image_90, save_single_image

# Optional memory monitoring (install with: pip install psutil)
# This provides detailed memory usage reporting and prevents out-of-memory errors
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore
# from src.utils.resizing import resize_image_by_inches
from server.src.routes.mockups import service as mockup_service
from sqlalchemy.orm import Session


os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

# DEPRECATED: These constants are being replaced with dynamic values from printer and canvas_config
# They remain here only for backward compatibility during migration
GANG_SHEET_MAX_WIDTH = 23  # inches - USE printer.max_width_inches instead
GANG_SHEET_SPACING = {
    'UVDTF 16oz': {'width': 0.32, 'height': 0.5},
    # Add more template spacing configurations here as needed
}
GANG_SHEET_MAX_HEIGHT = 215  # inches - USE printer.max_height_inches instead
STD_DPI = 400  # USE printer.dpi or canvas_config.dpi instead

@lru_cache(maxsize=None)
def cached_inches_to_pixels(inches, dpi):
   return inches_to_pixels(inches, dpi)

def process_image(img_path, normalize_dpi=True, target_dpi=400):
   """
   Process a single image: load, convert to BGRA, normalize DPI, and rotate.

   Args:
       img_path: Path to the image file
       normalize_dpi: If True, normalize DPI metadata to target_dpi (default: True)
       target_dpi: Target DPI for normalization (default: 400)

   Returns:
       Processed image as numpy array or None if failed
   """
   import logging
   if os.path.exists(img_path):
       img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
       if img is None:
           logging.warning(f"Failed to load image: {img_path}")
           return None

       # Ensure image has alpha channel (BGRA)
       if len(img.shape) == 2:
           # Grayscale - convert to BGRA
           img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
       elif img.shape[2] == 3:
           # BGR - convert to BGRA
           img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
       elif img.shape[2] == 4:
           # Already BGRA, do nothing
           pass

       # CRITICAL FIX: Normalize DPI to handle mixed DPI images
       # Images with 72 DPI, 96 DPI, 300 DPI, 400 DPI etc. can cause issues
       # when combined in a gang sheet even if pixel dimensions are identical
       if normalize_dpi:
           try:
               from PIL import Image
               # Read DPI metadata using PIL
               with Image.open(img_path) as pil_img:
                   current_dpi = pil_img.info.get('dpi', (target_dpi, target_dpi))
                   if isinstance(current_dpi, (int, float)):
                       current_dpi = (current_dpi, current_dpi)

                   # Log DPI normalization
                   if current_dpi[0] != target_dpi or current_dpi[1] != target_dpi:
                       logging.info(f"Normalizing DPI: {img_path} from {current_dpi} to ({target_dpi}, {target_dpi})")

                       # Calculate scale factor based on DPI difference
                       # If image is 72 DPI but we want 400 DPI, we need to scale it up
                       # to maintain the same physical size
                       scale_x = target_dpi / current_dpi[0]
                       scale_y = target_dpi / current_dpi[1]

                       # Only scale if there's a significant difference (> 1% variation)
                       if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
                           h, w = img.shape[:2]
                           new_w = int(w * scale_x)
                           new_h = int(h * scale_y)

                           # Use high-quality interpolation
                           interpolation = cv2.INTER_CUBIC if scale_x > 1 else cv2.INTER_AREA
                           img = cv2.resize(img, (new_w, new_h), interpolation=interpolation)
                           logging.info(f"Resized from {w}x{h} to {new_w}x{new_h} (scale: {scale_x:.2f}x, {scale_y:.2f}x)")
           except Exception as e:
               logging.warning(f"Failed to normalize DPI for {img_path}: {e}")

       # Rotate image
       img = rotate_image_90(img, 1)
       return img
   return None

@lru_cache(maxsize=128)
def process_image_cached(img_path):
   """Cached version of process_image for frequently accessed images."""
   return process_image(img_path)

def process_images_parallel(img_paths, max_workers=4):
   """
   OPTIMIZATION: Process multiple images in parallel using ThreadPoolExecutor.
   Returns a dict mapping index to processed image.

   Args:
       img_paths: List of image paths to process
       max_workers: Maximum number of concurrent threads (default: 4)

   Returns:
       Dict mapping image index to processed numpy array
   """
   import logging
   from concurrent.futures import ThreadPoolExecutor, as_completed

   processed = {}

   # Filter out None values and track indices
   valid_paths = [(i, path) for i, path in enumerate(img_paths) if path is not None]

   if not valid_paths:
       return processed

   logging.info(f"Processing {len(valid_paths)} images in parallel with {max_workers} workers")

   with ThreadPoolExecutor(max_workers=max_workers) as executor:
       # Submit all image processing tasks
       future_to_index = {
           executor.submit(process_image, path): i
           for i, path in valid_paths
       }

       # Collect results as they complete
       for future in as_completed(future_to_index):
           index = future_to_index[future]
           try:
               result = future.result()
               if result is not None:
                   processed[index] = result
           except Exception as e:
               logging.warning(f"Error processing image at index {index}: {e}")

   logging.info(f"Successfully processed {len(processed)}/{len(valid_paths)} images")
   return processed


def get_mockup_images_with_mask_data_from_service(db, user_id, template_name):
    """
    OPTIMIZED: Fetch mockup images with mask data using bulk queries with eager loading.
    Returns a list of dicts with keys: id, filename, file_path, template_name, image_type, design_id, mask_data, points_data, created_at
    """
    import logging
    from sqlalchemy.orm import joinedload
    from server.src.entities.mockup import Mockup, MockupImage, MockupMaskData

    try:
        # OPTIMIZATION: Use a single query with eager loading instead of N+1 queries
        # This loads mockups, images, and mask data in one database round-trip
        query = db.query(MockupImage).join(
            Mockup, MockupImage.mockup_id == Mockup.id
        ).filter(
            Mockup.user_id == user_id
        ).options(
            joinedload(MockupImage.mask_data)  # Eager load mask data
        )

        # Filter by template if provided
        if template_name:
            query = query.filter(MockupImage.image_type == template_name)

        images = query.all()

        result = []
        for image in images:
            # Each image can have multiple mask data entries
            mask_data_list = image.mask_data if hasattr(image, 'mask_data') else []

            if mask_data_list:
                for mask_data in mask_data_list:
                    result.append({
                        'id': image.id,
                        'filename': image.filename,
                        'file_path': image.file_path,
                        'template_name': image.image_type,
                        'image_type': image.image_type,
                        'design_id': getattr(image, 'design_id', None),
                        'mask_data': mask_data.masks,
                        'points_data': mask_data.points,
                        'created_at': image.created_at
                    })
            else:
                # Include images without mask data
                result.append({
                    'id': image.id,
                    'filename': image.filename,
                    'file_path': image.file_path,
                    'template_name': image.image_type,
                    'image_type': image.image_type,
                    'design_id': getattr(image, 'design_id', None),
                    'mask_data': None,
                    'points_data': None,
                    'created_at': image.created_at
                })

        logging.info(f"Loaded {len(result)} mockup images with mask data in single optimized query")
        return result

    except Exception as e:
        logging.error(f"Error loading mockup images with mask data: {e}")
        # Fallback to old method if there's an error
        return get_mockup_images_with_mask_data_from_service_fallback(db, user_id, template_name)


def get_mockup_images_with_mask_data_from_service_fallback(db, user_id, template_name):
    """
    Fallback method using the service layer (slower but more compatible).
    """
    import logging
    logging.warning("Using fallback method for fetching mockup images")

    # Get all mockups for the user
    mockups_list = mockup_service.get_mockups_by_user_id(db, user_id).mockups
    result = []
    for mockup in mockups_list:
        # Get all images for this mockup
        images_resp = mockup_service.get_mockup_images_by_mockup_id(db, mockup.id, user_id)
        for image in images_resp.mockup_images:
            # Filter by template
            if template_name and image.image_type != template_name:
                continue

            # Get mask data for this image
            mask_data_resp = mockup_service.get_mockup_mask_data_by_image_id(db, image.id, user_id)
            mask_data_list = mask_data_resp.mask_data if hasattr(mask_data_resp, 'mask_data') else []
            for mask_data in mask_data_list:
                result.append({
                    'id': image.id,
                    'filename': image.filename,
                    'file_path': image.file_path,
                    'template_name': image.image_type,
                    'image_type': image.image_type,
                    'design_id': getattr(image, 'design_id', None),
                    'mask_data': mask_data.masks,
                    'points_data': mask_data.points,
                    'created_at': image.created_at
                })
    return result


def create_gang_sheets_from_db(
    db: Session,
    user_id: int,
    template_name: str,
    output_path: str,
    printer_id=None,
    canvas_config_id=None,
    dpi: int = None,
    text: str = 'Single '
):
   """
   Create gang sheets from mockup images stored in the database.

   Args:
       db: Database session
       user_id: ID of the user
       template_name: Name of the template (e.g., 'UVDTF 16oz')
       output_path: Path where gang sheets will be saved
       printer_id: Optional printer ID to get dimensions and DPI from
       canvas_config_id: Optional canvas config ID to get spacing from
       dpi: DPI for the gang sheets (defaults to printer.dpi or canvas_config.dpi or 400)
       text: Text to include in the filename
   """
   import logging
   from server.src.entities.printer import Printer
   from server.src.entities.canvas_config import CanvasConfig

   # Get printer configuration if provided
   printer = None
   if printer_id:
       printer = db.query(Printer).filter(Printer.id == printer_id).first()
       if not printer:
           logging.warning(f"Printer {printer_id} not found, using default dimensions")

   # Get canvas configuration if provided
   canvas_config = None
   if canvas_config_id:
       canvas_config = db.query(CanvasConfig).filter(CanvasConfig.id == canvas_config_id).first()
       if not canvas_config:
           logging.warning(f"Canvas config {canvas_config_id} not found, using default spacing")

   # Determine gang sheet dimensions from printer or defaults
   max_width = printer.max_width_inches if printer else GANG_SHEET_MAX_WIDTH
   max_height = printer.max_height_inches if printer else GANG_SHEET_MAX_HEIGHT

   # Determine DPI from canvas_config, printer, or parameter
   if dpi is None:
       if canvas_config and canvas_config.dpi:
           dpi = canvas_config.dpi
       elif printer and printer.dpi:
           dpi = printer.dpi
       else:
           dpi = STD_DPI

   # Determine spacing from canvas_config or defaults
   if canvas_config:
       spacing_width = canvas_config.spacing_width_inches
       spacing_height = canvas_config.spacing_height_inches
   elif template_name in GANG_SHEET_SPACING:
       spacing_width = GANG_SHEET_SPACING[template_name]['width']
       spacing_height = GANG_SHEET_SPACING[template_name]['height']
   else:
       # Default spacing
       spacing_width = 0.125
       spacing_height = 0.125

   logging.info(f"Gang sheet config: {max_width}\"x{max_height}\" @ {dpi} DPI, spacing: {spacing_width}\"x{spacing_height}\"")

   # Get mockup images with mask data from service
   mockup_images = get_mockup_images_with_mask_data_from_service(db, user_id, template_name)

   if not mockup_images:
       print(f"No mockup images found for user {user_id} and template {template_name}")
       return None

   # Pre-calculate common values
   width_px = cached_inches_to_pixels(max_width, dpi)
   height_px = cached_inches_to_pixels(max_height, dpi)

   # Group mockup images by design_id to handle multiple mockups per design
   design_groups = {}
   for mockup in mockup_images:
       design_id = mockup.get('design_id', mockup['filename'])
       if design_id not in design_groups:
           design_groups[design_id] = []
       design_groups[design_id].append(mockup)

   # OPTIMIZATION: Collect all image paths first, then process in parallel
   image_paths_to_process = []
   path_to_mockup = {}  # Map path to mockup data for later reference

   for design_id, mockups in design_groups.items():
       for mockup in mockups:
           mask_data = mockup.get('mask_data')
           points_data = mockup.get('points_data')

           if mask_data and points_data:
               img_path = mockup['file_path']
               image_paths_to_process.append(img_path)
               path_to_mockup[img_path] = mockup

   if not image_paths_to_process:
       logging.warning(f"No valid mockup images found for gangsheet creation")
       return None

   # OPTIMIZATION: Process all images in parallel
   logging.info(f"Processing {len(image_paths_to_process)} images in parallel...")
   import time
   start_time = time.time()
   processed_images = process_images_parallel(image_paths_to_process, max_workers=6)
   processing_time = time.time() - start_time
   logging.info(f"Parallel image processing completed in {processing_time:.2f}s ({len(processed_images)} images)")

   # Build image_data structure from processed images
   image_data = {
       'Title': [],
       'Size': [],
       'Total': []
   }

   for idx, img_path in enumerate(image_paths_to_process):
       if idx in processed_images:
           image_data['Title'].append(img_path)
           image_data['Size'].append(template_name)
           image_data['Total'].append(1)  # Each mockup counts as 1

   if not image_data['Title']:
       logging.warning(f"No valid images were successfully processed")
       return None

   # Create gang sheets using the existing logic with dynamic parameters
   # Pass pre-processed images to avoid re-processing
   return create_gang_sheets(
       image_data=image_data,
       image_type=template_name,
       output_path=output_path,
       total_images=len(image_data['Title']),
       max_width_inches=max_width,
       max_height_inches=max_height,
       spacing_width_inches=spacing_width,
       spacing_height_inches=spacing_height,
       dpi=dpi,
       std_dpi=dpi,  # Use same DPI for output
       text=text,
       processed_images=processed_images  # Pass pre-processed images
   )


def create_gang_sheets(
    image_data,
    image_type,
    output_path,
    total_images,
    max_width_inches=None,
    max_height_inches=None,
    spacing_width_inches=None,
    spacing_height_inches=None,
    dpi=400,
    std_dpi=None,
    text='Single ',
    processed_images=None
):
   """
   Create gang sheets from image data.

   Args:
       image_data: Dictionary with 'Title', 'Size', and optionally 'Total' keys
       image_type: Type/name of the template
       output_path: Directory to save gang sheets
       total_images: Total number of images to process
       max_width_inches: Maximum width of gang sheet (defaults to GANG_SHEET_MAX_WIDTH)
       max_height_inches: Maximum height of gang sheet (defaults to GANG_SHEET_MAX_HEIGHT)
       spacing_width_inches: Horizontal spacing between images (defaults to template config or 0.125)
       spacing_height_inches: Vertical spacing between images (defaults to template config or 0.125)
       dpi: DPI for gang sheet creation
       std_dpi: Standard DPI for output scaling (defaults to dpi)
       text: Text prefix for output filename
   """
   import logging

   # Use defaults if not provided
   if max_width_inches is None:
       max_width_inches = GANG_SHEET_MAX_WIDTH
   if max_height_inches is None:
       max_height_inches = GANG_SHEET_MAX_HEIGHT
   if std_dpi is None:
       std_dpi = dpi

   # Determine spacing
   if spacing_width_inches is None or spacing_height_inches is None:
       if image_type in GANG_SHEET_SPACING:
           spacing_width_inches = spacing_width_inches or GANG_SHEET_SPACING[image_type]['width']
           spacing_height_inches = spacing_height_inches or GANG_SHEET_SPACING[image_type]['height']
       else:
           spacing_width_inches = spacing_width_inches or 0.125
           spacing_height_inches = spacing_height_inches or 0.125

   try:
       
       # Validate input data
       if not image_data or not isinstance(image_data, dict):
           logging.error("Invalid image_data: must be a non-empty dictionary")
           return None
       
       required_keys = ['Title', 'Size']
       for key in required_keys:
           if key not in image_data:
               logging.error(f"Missing required key '{key}' in image_data")
               return None
           if not isinstance(image_data[key], (list, tuple)) or len(image_data[key]) == 0:
               logging.error(f"Key '{key}' must be a non-empty list or tuple")
               return None
       
       # Ensure output directory exists
       os.makedirs(output_path, exist_ok=True)
       
       # Pre-calculate common values with safety checks
       try:
           width_px = cached_inches_to_pixels(max_width_inches, dpi)
           height_px = cached_inches_to_pixels(max_height_inches, dpi)
           logging.info(f"Gang sheet dimensions: {max_width_inches}\"×{max_height_inches}\" = {width_px}×{height_px} pixels at {dpi} DPI")
       except Exception as e:
           logging.error(f"Error calculating dimensions: {e}")
           return None
       
       # Validate dimensions are positive (but allow large dimensions for legitimate use cases)
       if width_px <= 0 or height_px <= 0:
           logging.error(f"Invalid dimensions: {width_px}x{height_px} (must be positive)")
           return None
       
       # Calculate memory requirement and warn if very large
       memory_gb = (width_px * height_px * 4) / (1024**3)  # 4 bytes per pixel (RGBA)
       if memory_gb > 5.0:  # Warn for sheets > 5GB
           logging.warning(f"Large gang sheet will use ~{memory_gb:.1f}GB of memory")
       if memory_gb > 20.0:  # Error for sheets > 20GB
           logging.error(f"Gang sheet too large: {memory_gb:.1f}GB would exceed reasonable memory limits")
           return None

       image_index, part = 0, 1
       current_image_amount_left = 0
       visited = dict()
       
       # Build visited dictionary with proper validation
       titles = image_data['Title']
       sizes = image_data['Size']
       if len(titles) != len(sizes):
           logging.error("Title and Size lists must have the same length")
           return None

       for title, size in zip(titles, sizes):
           if title is None or size is None:
               logging.warning(f"Skipping None values: title={title}, size={size}")
               continue
           # Skip placeholder files that don't actually exist
           if "MISSING_" in str(title):
               logging.warning(f"Skipping placeholder file in visited dictionary: {title}")
               continue
           # BUGFIX: Strip whitespace from title to match how paths are processed
           title_clean = str(title).strip()
           key = f"{title_clean} {size}"
           visited[key] = visited.get(key, 0) + 1

       if not visited:
           logging.error("No valid title/size pairs found")
           return None

       # OPTIMIZATION: Use pre-processed images if provided, otherwise load on-demand
       if processed_images is None:
           processed_images = {}
           logging.info("No pre-processed images provided, will load on-demand")
       else:
           logging.info(f"Using {len(processed_images)} pre-processed images")

       image_cache_limit = 10  # Keep max 10 images in memory at once

       def get_processed_image(index):
           """Load image on-demand with memory management (or return pre-processed)"""
           if index not in processed_images:
               try:
                   if index < len(titles) and titles[index] is not None:
                       # Memory management: if cache is full, remove oldest images
                       if len(processed_images) >= image_cache_limit:
                           # Remove images that are no longer needed
                           current_processing_range = range(max(0, image_index-2), min(len(titles), image_index+image_cache_limit))
                           keys_to_remove = [k for k in processed_images.keys() if k not in current_processing_range]
                           for k in keys_to_remove[:len(keys_to_remove)//2]:  # Remove half of unused images
                               if k in processed_images:
                                   del processed_images[k]
                                   logging.debug(f"Removed image {k} from cache to free memory")

                       processed_images[index] = process_image(titles[index])
                   else:
                       processed_images[index] = None
               except Exception as e:
                   logging.warning(f"Error processing image {index}: {e}")
                   processed_images[index] = None
           return processed_images[index]
       
       # Add safety counter to prevent infinite loops
       max_iterations = len(visited) * 2 + 10  # Safety margin
       iteration_count = 0
       
       while len(visited) > 0 and iteration_count < max_iterations:
           iteration_count += 1
           
           try:
               # Advanced memory optimization before allocation
               import gc
               
               # Force aggressive garbage collection
               for _ in range(3):  # Multiple GC cycles
                   gc.collect()
               
               # Check available memory if psutil is available
               if PSUTIL_AVAILABLE:
                   try:
                       process = psutil.Process(os.getpid())
                       memory_info = process.memory_info()
                       available_memory_gb = psutil.virtual_memory().available / (1024**3)
                       current_memory_gb = memory_info.rss / (1024**3)
                       
                       logging.info(f"Memory before allocation: {current_memory_gb:.2f}GB used, {available_memory_gb:.2f}GB available")
                       
                       if memory_gb > available_memory_gb * 0.8:  # Don't use more than 80% of available memory
                           logging.error(f"Insufficient memory: need {memory_gb:.2f}GB, only {available_memory_gb:.2f}GB available")
                           return None
                   except Exception as e:
                       logging.debug(f"Memory monitoring error: {e}")
               else:
                   logging.info(f"Memory monitoring unavailable (install psutil for detailed memory info)")
               
               # Use memory-mapped array for very large sheets
               temp_filename = None
               if memory_gb > 1.0:  # Use memory mapping for sheets > 1GB
                   temp_file = tempfile.NamedTemporaryFile(delete=False)
                   temp_filename = temp_file.name
                   temp_file.close()
                   gang_sheet = np.memmap(temp_filename, dtype=np.uint8, mode='w+', shape=(height_px, width_px, 4))
                   gang_sheet.fill(0)  # Initialize to transparent
                   # Store filename for cleanup
                   gang_sheet._temp_filename = temp_filename
                   logging.info(f"Using memory-mapped gang sheet: {memory_gb:.2f}GB -> {temp_filename}")
               else:
                   # Use regular array for smaller sheets
                   gang_sheet = np.zeros((height_px, width_px, 4), dtype=np.uint8)
                   logging.info(f"Using in-memory gang sheet: {memory_gb:.2f}GB")
               
               # Verify allocation succeeded
               if PSUTIL_AVAILABLE:
                   try:
                       memory_after = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                       logging.info(f"Gang sheet allocated successfully. Memory usage: {memory_after:.2f}GB (+{memory_after-current_memory_gb:.2f}GB)")
                   except:
                       logging.info("Gang sheet allocated successfully")
               else:
                   logging.info("Gang sheet allocated successfully")
               
           except MemoryError:
               logging.error(f"Out of memory creating gang sheet {width_px}x{height_px} ({memory_gb:.1f}GB)")
               logging.error("Try reducing GANG_SHEET_MAX_HEIGHT or processing fewer items at once")
               return None
           except Exception as e:
               logging.error(f"Error creating gang sheet: {e}")
               return None
        
           current_x, current_y = 0, 0
           row_height = 0
           
           logging.info(f"Starting part {part} with image_index={image_index}, current_image_amount_left={current_image_amount_left}")
           logging.info(f"Processing range: {image_index} to {len(titles)-1}")
           
           images_processed_in_part = 0
           for i in range(image_index, len(titles)):
               try:
                   img = get_processed_image(i)
                   if img is None:
                       continue

                   # BUGFIX: Strip whitespace from title to match visited dictionary keys
                   title_clean = str(titles[i]).strip()
                   key = f"{title_clean} {sizes[i]}"
                   if key not in visited:
                       continue  # Skip if key was already processed
                   
                   # Only reset current_image_amount_left if we've moved to a new image
                   # and this image wasn't the one that caused the previous sheet to be full
                   if i != image_index:
                       current_image_amount_left = 0
                   
                   logging.debug(f"Processing image {i}: key={key}, current_image_amount_left={current_image_amount_left}")

                   # Use provided spacing configuration
                   spacing_width_px = cached_inches_to_pixels(spacing_width_inches, dpi)
                   spacing_height_px = cached_inches_to_pixels(spacing_height_inches, dpi)

                   img_height, img_width = img.shape[:2]

                   # Check if Total field exists and get value safely
                   total_images_for_item = 1  # Default value
                   if 'Total' in image_data and i < len(image_data['Total']):
                       total_images_for_item = image_data['Total'][i]

                   logging.info(f"Processing image {i}: total_images_for_item={total_images_for_item}, current_image_amount_left={current_image_amount_left}")
                   
                   # Check if we have any items left to process for this image
                   if current_image_amount_left >= total_images_for_item:
                       logging.info(f"Skipping image {i}: already processed all {total_images_for_item} items")
                       continue

                   sheet_is_full = False
                   for amount_index in range(current_image_amount_left, total_images_for_item):
                       logging.debug(f"Placing item {amount_index+1}/{total_images_for_item} at position ({current_x}, {current_y})")
                       
                       if current_x + img_width > width_px:
                           current_x, current_y = 0, current_y + row_height + spacing_width_px
                           row_height = 0
                           logging.debug(f"Moving to new row at y={current_y}")

                       if current_y + img_height + spacing_height_px > height_px:
                           # Sheet is full, need to start a new part
                           logging.info(f"Sheet full at image {i}, amount_index {amount_index} (item {amount_index+1}/{total_images_for_item})")
                           image_index = i
                           current_image_amount_left = amount_index
                           # Don't modify visited[key] here - we'll handle it after the loop
                           sheet_is_full = True
                           break

                       # Memory-optimized image placement
                       try:
                           y_end = min(current_y + img_height, height_px)
                           x_end = min(current_x + img_width, width_px)
                           
                           # Place image on gang sheet
                           gang_sheet[current_y:y_end, current_x:x_end] = img[:y_end-current_y, :x_end-current_x]
                           
                           # For memory-mapped arrays, flush data periodically
                           if hasattr(gang_sheet, '_temp_filename'):  # Memory-mapped array
                               if images_processed_in_part % 10 == 0:  # Flush every 10 images
                                   gang_sheet.flush()
                           
                           images_processed_in_part += 1
                       except Exception as e:
                           logging.warning(f"Error placing image on gang sheet: {e}")
                           
                       current_x += img_width + spacing_width_px
                       row_height = max(row_height, img_height)

                   if sheet_is_full:
                       # Don't modify visited here - we'll handle it outside the image loop
                       logging.info(f"Sheet full at image {i}, breaking to start new part")
                       break
                   else:
                       # We completed all copies of this image occurrence, remove it from visited
                       if key in visited:
                           del visited[key]
                           logging.info(f"Completed all items for key {key}")
                       
               except Exception as e:
                   logging.error(f"Error processing image {i}: {e}")
                   continue
           
           logging.info(f"Finished processing part {part}: {images_processed_in_part} images placed on sheet")
           
           # Handle the case where we broke out due to sheet being full
           # In this case, we need to check if we completely finished the current image or not
           if images_processed_in_part > 0:  # Only if we processed something
               # Check if the last image we were working on is complete
               if image_index < len(titles):
                   # BUGFIX: Strip whitespace from title to match visited dictionary keys
                   title_clean = str(titles[image_index]).strip()
                   current_key = f"{title_clean} {sizes[image_index]}"
                   current_total = 1
                   if 'Total' in image_data and image_index < len(image_data['Total']):
                       current_total = image_data['Total'][image_index]
                   
                   # If we finished all copies of the current image, remove it from visited
                   if current_image_amount_left >= current_total:
                       if current_key in visited:
                           del visited[current_key]
                           logging.info(f"Completed processing for {current_key} after sheet became full")
           
           # If no images were processed in this part, we might have a problem
           if images_processed_in_part == 0:
               logging.warning(f"No images processed in part {part} - checking if this is the end or an error")
               # Check if there are actually items left to process
               remaining_total = sum(visited.values())
               if remaining_total > 0:
                   logging.error(f"ERROR: No images processed but {remaining_total} items remain. This indicates a logic error.")
                   logging.error(f"Current state: image_index={image_index}, current_image_amount_left={current_image_amount_left}")
                   logging.error(f"Visited dictionary: {visited}")
                   # Break to prevent infinite loop
                   break
               else:
                   logging.info("No items processed because all items are complete - this is normal")
           
           # Save the gang sheet
           try:
               alpha_channel = gang_sheet[:,:,3]
               rows, cols = np.any(alpha_channel, axis=1), np.any(alpha_channel, axis=0)
               if np.any(rows) and np.any(cols):
                   ymin, ymax = np.where(rows)[0][[0, -1]]
                   xmin, xmax = np.where(cols)[0][[0, -1]]
                   ymin = int(ymin)
                   ymax = int(ymax)
                   xmin = int(xmin)
                   xmax = int(xmax)
                   margin = 10  # Add a 10-pixel margin
                   ymin = max(ymin - margin, 0)
                   ymax = min(ymax + margin, gang_sheet.shape[0] - 1)
                   xmin = max(xmin - margin, 0)
                   xmax = min(xmax + margin, gang_sheet.shape[1] - 1)
                   cropped_gang_sheet = gang_sheet[ymin:ymax+1, xmin:xmax+1]
                   print(f"dpi: {dpi}")
                   print(f"std_dpi: {std_dpi}")
                   scale_factor = std_dpi / dpi
                   new_width, new_height = int((xmax - xmin + 1) * scale_factor), int((ymax - ymin + 1) * scale_factor)
                   
                   if new_width > 0 and new_height > 0:
                       resized_gang_sheet = cv2.resize(cropped_gang_sheet, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                       today = date.today()
                       filename = f"NookTransfers {today.strftime('%m%d%Y')} UVDTF {image_type} {text} part {part}.png"
                       save_single_image(
                           resized_gang_sheet,
                           output_path,
                           filename,
                           target_dpi=(dpi, dpi)
                       )
                       logging.info(f"Successfully created gang sheet: {filename}")
                       
                       # CRITICAL: Immediately free memory after successful save
                       # This frees up the ~2.95GB gang sheet memory before starting next part
                       memory_before_dump = None
                       if PSUTIL_AVAILABLE:
                           try:
                               memory_before_dump = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                           except:
                               pass
                       
                       # Delete processed arrays to free memory immediately
                       del resized_gang_sheet
                       del cropped_gang_sheet
                       
                       # Force immediate garbage collection
                       import gc
                       for _ in range(2):
                           gc.collect()
                       
                       if PSUTIL_AVAILABLE and memory_before_dump:
                           try:
                               memory_after_dump = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                               memory_freed = memory_before_dump - memory_after_dump
                               logging.info(f"Immediately freed {memory_freed:.2f}GB after saving part {part}")
                           except:
                               logging.info(f"Memory freed after saving part {part}")
                       else:
                           logging.info(f"Memory freed after saving part {part}")
                       
                       part += 1
                   else:
                       logging.warning(f"Invalid dimensions for gang sheet {part}: {new_width}x{new_height}")
               else:
                   logging.warning(f"Sheet {part} is empty (all transparent). Skipping.")
           except Exception as e:
               logging.error(f"Error saving gang sheet {part}: {e}")
               continue
           finally:
               # PRIORITY: Dump main gang sheet memory IMMEDIATELY after save attempt
               # This is the critical 2.95GB memory that must be freed before next iteration
               try:
                   memory_before_main_dump = None
                   if PSUTIL_AVAILABLE:
                       try:
                           memory_before_main_dump = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                       except:
                           pass
                   
                   # Delete the main gang sheet array (2.95GB)
                   if 'gang_sheet' in locals():
                       # Clean up memory-mapped file if used
                       if hasattr(gang_sheet, '_temp_filename'):
                           temp_filename = gang_sheet._temp_filename
                           del gang_sheet
                           try:
                               os.unlink(temp_filename)
                               logging.debug(f"Cleaned up temporary memory-mapped file: {temp_filename}")
                           except Exception as e:
                               logging.debug(f"Failed to clean up temp file {temp_filename}: {e}")
                       else:
                           del gang_sheet
                   
                   # Force immediate GC of the main gang sheet
                   import gc
                   for _ in range(2):
                       gc.collect()
                   
                   if PSUTIL_AVAILABLE and memory_before_main_dump:
                       try:
                           memory_after_main_dump = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                           main_memory_freed = memory_before_main_dump - memory_after_main_dump
                           logging.info(f"MAIN GANG SHEET: Freed {main_memory_freed:.2f}GB (gang sheet array)")
                       except:
                           logging.info("MAIN GANG SHEET: Memory freed")
                   else:
                       logging.info("MAIN GANG SHEET: Memory freed")
               except Exception as e:
                   logging.debug(f"Main gang sheet cleanup error: {e}")
               # Additional cleanup of processed images cache
               try:
                   memory_before = None
                   if PSUTIL_AVAILABLE:
                       try:
                           memory_before = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                       except:
                           pass
                   
                   # Aggressive cleanup of processed images cache
                   images_to_keep = 5  # Keep only 5 most recent images
                   if len(processed_images) > images_to_keep:
                       # Keep only images we might need for the next part
                       keys_to_keep = list(range(max(0, image_index-2), min(len(titles), image_index+images_to_keep)))
                       keys_to_remove = [k for k in processed_images.keys() if k not in keys_to_keep]
                       
                       for idx in keys_to_remove:
                           if idx in processed_images:
                               del processed_images[idx]
                       
                       logging.info(f"Aggressive cleanup: removed {len(keys_to_remove)} images from cache, kept {len(processed_images)}")
                   
                   # Force aggressive garbage collection
                   import gc
                   for _ in range(3):
                       collected = gc.collect()
                       if collected == 0:
                           break
                   
                   if PSUTIL_AVAILABLE and memory_before:
                       try:
                           memory_after = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                           memory_freed = memory_before - memory_after
                           logging.info(f"Image cache cleanup: {memory_after:.2f}GB (-{memory_freed:.2f}GB freed)")
                       except:
                           logging.info("Image cache cleanup completed")
                   else:
                       logging.info("Image cache cleanup completed")
                   
                   # Log total memory status after all cleanup
                   if PSUTIL_AVAILABLE:
                       try:
                           final_memory = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
                           available_memory = psutil.virtual_memory().available / (1024**3)
                           logging.info(f"PART {part-1} COMPLETE: Using {final_memory:.2f}GB, {available_memory:.2f}GB available for next part")
                       except:
                           pass
                   
               except Exception as e:
                   logging.debug(f"Memory cleanup error (non-critical): {e}")
               
               # Check if we're approaching memory limits
               if PSUTIL_AVAILABLE:
                   try:
                       available_memory = psutil.virtual_memory().available / (1024**3)
                       if available_memory < 2.0:  # Less than 2GB available
                           logging.warning(f"Low memory warning: only {available_memory:.2f}GB available")
                           # Force more aggressive cleanup if needed
                           processed_images.clear()
                           for _ in range(5):
                               gc.collect()
                   except:
                       pass
           
           # Log remaining items for debugging
           remaining_items = sum(visited.values())
           if remaining_items > 0:
               logging.info(f"Continuing to next part. Remaining items: {remaining_items}")
               logging.info(f"Visited dictionary: {visited}")
           else:
               logging.info("All items processed, finishing gang sheet creation")
       
       # Check if we hit the iteration limit (potential infinite loop)
       if iteration_count >= max_iterations:
           logging.error(f"Hit maximum iterations ({max_iterations}), stopping to prevent infinite loop")
           return None
       
       sheets_created = part - 1
       logging.info(f"Successfully created {sheets_created} gang sheet parts")
       return {"success": True, "sheets_created": sheets_created}
       
   except Exception as e:
       logging.error(f"Fatal error in create_gang_sheets: {e}")
       return None

