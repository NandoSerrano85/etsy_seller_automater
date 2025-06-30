import numpy as np
import cv2, os
from datetime import date
from functools import lru_cache
from server.engine.util import inches_to_pixels, rotate_image_90, save_single_image
from server.engine.resizing import resize_image_by_inches


os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
GANG_SHEET_MAX_WIDTH = 23
GANG_SHEET_SPACING = {'UVDTF 16oz':{'width': 0.32, 'height': 0.5}}
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

