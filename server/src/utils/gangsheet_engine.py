import numpy as np
import cv2, os
from datetime import date
from functools import lru_cache
from server.src.utils.util import inches_to_pixels, rotate_image_90, save_single_image
# from src.utils.resizing import resize_image_by_inches
from server.src.routes.mockups import service as mockup_service
from sqlalchemy.orm import Session


os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
GANG_SHEET_MAX_WIDTH = 23
GANG_SHEET_SPACING = {
    'UVDTF 16oz': {'width': 0.32, 'height': 0.5},
    # Add more template spacing configurations here as needed
}
GANG_SHEET_MAX_HEIGHT = 215
STD_DPI = 400

@lru_cache(maxsize=None)
def cached_inches_to_pixels(inches, dpi):
   return inches_to_pixels(inches, dpi)

def process_image(img_path):
   if os.path.exists(img_path):
       img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
       if img is None:
           return None
       if img.shape[2] == 3:
           img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
       img = rotate_image_90(img, 1)
       return img
   return None


def get_mockup_images_with_mask_data_from_service(db, user_id, template_name):
    """
    Helper to fetch mockup images with mask data using the service layer.
    Returns a list of dicts with keys: id, filename, file_path, template_name, image_type, design_id, mask_data, points_data, created_at
    """
    # Get all mockups for the user
    mockups_list = mockup_service.get_mockups_by_user_id(db, user_id).mockups
    result = []
    for mockup in mockups_list:
        # Filter by template name if provided
        if template_name and getattr(mockup, 'product_template_id', None):
            # Get the template name from the template entity if needed
            # For now, assume template_name is the id or name
            # You may need to adapt this if template_name is not the id
            pass  # Add filtering logic if needed
        # Get all images for this mockup
        images_resp = mockup_service.get_mockup_images_by_mockup_id(db, mockup.id, user_id)
        for image in images_resp.mockup_images:
            # Get mask data for this image
            mask_data_resp = mockup_service.get_mockup_mask_data_by_image_id(db, image.id, user_id)
            mask_data_list = mask_data_resp.mask_data if hasattr(mask_data_resp, 'mask_data') else []
            for mask_data in mask_data_list:
                result.append({
                    'id': image.id,
                    'filename': image.filename,
                    'file_path': image.file_path,
                    'template_name': image.image_type,  # or use template_name
                    'image_type': image.image_type,
                    'design_id': getattr(image, 'design_id', None),
                    'mask_data': mask_data.masks,
                    'points_data': mask_data.points,
                    'created_at': image.created_at
                })
    return result


def create_gang_sheets_from_db(db: Session, user_id: int, template_name: str, output_path: str, dpi: int = 400, text: str = 'Single '):
   """
   Create gang sheets from mockup images stored in the database.
   
   Args:
       db: Database session
       user_id: ID of the user
       template_name: Name of the template (e.g., 'UVDTF 16oz')
       output_path: Path where gang sheets will be saved
       dpi: DPI for the gang sheets
       text: Text to include in the filename
   """
   # Get mockup images with mask data from service
   mockup_images = get_mockup_images_with_mask_data_from_service(db, user_id, template_name)
   
   if not mockup_images:
       print(f"No mockup images found for user {user_id} and template {template_name}")
       return None
   
   # Pre-calculate common values
   width_px = cached_inches_to_pixels(GANG_SHEET_MAX_WIDTH, dpi)
   height_px = cached_inches_to_pixels(GANG_SHEET_MAX_HEIGHT, dpi)

   # Group mockup images by design_id to handle multiple mockups per design
   design_groups = {}
   for mockup in mockup_images:
       design_id = mockup.get('design_id', mockup['filename'])
       if design_id not in design_groups:
           design_groups[design_id] = []
       design_groups[design_id].append(mockup)

   # Create a list of image data for gangsheet processing
   image_data = {
       'Title': [],
       'Size': [],
       'Total': []
   }
   
   processed_images = {}
   image_index = 0
   
   for design_id, mockups in design_groups.items():
       for mockup in mockups:
           # Use the first mockup's mask data for this design
           mask_data = mockup.get('mask_data')
           points_data = mockup.get('points_data')
           
           if mask_data and points_data:
               # Process the mockup image
               img_path = mockup['file_path']
               processed_img = process_image(img_path)
               
               if processed_img is not None:
                   image_data['Title'].append(img_path)
                   image_data['Size'].append(template_name)
                   image_data['Total'].append(1)  # Each mockup counts as 1
                   processed_images[image_index] = processed_img
                   image_index += 1

   if not image_data['Title']:
       print(f"No valid mockup images found for gangsheet creation")
       return None

   # Create gang sheets using the existing logic
   return create_gang_sheets(image_data, template_name, output_path, len(image_data['Title']), dpi, text)


def create_gang_sheets(image_data, image_type, output_path, total_images, dpi=400, text='Single '):
   # Pre-calculate common values
   width_px = cached_inches_to_pixels(GANG_SHEET_MAX_WIDTH, dpi)
   height_px = cached_inches_to_pixels(GANG_SHEET_MAX_HEIGHT, dpi)

   image_index, part = 0, 1
   current_image_amount_left = 0
   visited = dict()
   for title, size in zip(image_data['Title'], image_data['Size']):
       if f"{title} {size}" in visited:
           visited[f"{title} {size}"] += 1
       else:
           visited[f"{title} {size}"] = 1

   # Pre-process images sequentially
   processed_images = {}
   for i in range(len(image_data['Title'])):
       processed_images[i] = process_image(image_data['Title'][i])

   while len(visited) > 0:
        gang_sheet = np.zeros((height_px, width_px, 4), dtype=np.uint8)
        gang_sheet[:, :, 3] = 0
     
        current_x, current_y = 0, 0
        row_height = 0
        for i in range(image_index, len(image_data['Title'])):
            img = processed_images[i]
            key = f"{image_data['Title'][i]} {image_data['Size'][i]}"
            visited[key] -= 1
            if visited[key] == 0:
                del visited[key]
            if image_index != i:
                current_image_amount_left = 0
            if img is not None:
                spacing_width_px = cached_inches_to_pixels(GANG_SHEET_SPACING[image_type]['width'], dpi)
                spacing_height_px = cached_inches_to_pixels(GANG_SHEET_SPACING[image_type]['height'], dpi)

                img_height, img_width = img.shape[:2]

                total_images = image_data['Total'][i]

                for amount_index in range(current_image_amount_left, total_images):
                    if current_x + img_width > width_px:
                        current_x, current_y = 0, current_y + row_height + spacing_width_px
                        row_height = 0

                    if current_y + img_height + spacing_height_px > height_px:
                        image_index = i
                        if key not in visited:
                            visited[key] = 1
                        else:
                            visited[key] += 1
                        current_image_amount_left = amount_index
                        break

                    gang_sheet[current_y:current_y+img_height, current_x:current_x+img_width] = img
                    current_x += img_width + spacing_width_px
                    row_height = max(row_height, img_height)

                if current_y + img_height + spacing_height_px > height_px:
                    break
        # Save the gang sheet
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
            scale_factor = STD_DPI / dpi
            new_width, new_height = int((xmax - xmin + 1) * scale_factor), int((ymax - ymin + 1) * scale_factor)
            resized_gang_sheet = cv2.resize(cropped_gang_sheet, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            today = date.today()
            save_single_image(
                resized_gang_sheet,
                output_path,
                f"NookTransfers {today.strftime('%m%d%Y')} UVDTF {image_type} {text} part {part}.png"
            )
            part += 1
        else:
            print(f"Warning: Sheet {part} is empty (all transparent). Skipping.")
   return None

