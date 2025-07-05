from collections import defaultdict
import cv2, json, os, csv, re
import numpy as np
from server.engine.cropping import crop_transparent 
from server.engine.resizing import resize_image_by_inches 
from server.engine.util import save_single_image
from concurrent.futures import ThreadPoolExecutor, as_completed
from server.engine.mask_creator_engine import MaskCreator
import platform
from functools import lru_cache
from tqdm import tqdm

# Disable Metal GPU acceleration to avoid Apple Silicon issues
USE_METAL = False

class MockupTemplateCache:
    """Cache for mockup templates and watermarks"""
    def __init__(self):
        self.mockups = {}
        self.watermarks = {}
    
    def get_mockup(self, path):
        if path not in self.mockups:
            self.mockups[path] = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        return self.mockups[path].copy()
    
    def get_watermark(self, path):
        if path not in self.watermarks:
            self.watermarks[path] = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        return self.watermarks[path].copy()

class MockupImage:
    template_cache = MockupTemplateCache()

    def __init__(self, mockup_image_path, design_image_path):
        self.mockup_image_paths = mockup_image_path
        self.design_image_path = design_image_path
        # Add max display size to prevent slow rendering of large images
        self.max_display_size = 1500

    @lru_cache(maxsize=32)
    def get_background(self, index):
        """Cached background image loading"""
        return self.template_cache.get_mockup(self.mockup_image_paths[index])

    def check_image_fit(self, image_size, bounds, center, margin=0.05):
        """Check if image would be cropped by the bounds"""
        img_h, img_w = image_size
        x, y = center
        
        # Add safety margin
        img_w *= (1 + margin)
        img_h *= (1 + margin)
        
        # Check if image extends beyond bounds
        left = x - img_w/2
        right = x + img_w/2
        top = y - img_h/2
        bottom = y + img_h/2
        
        x_overflow = max(0, -left) + max(0, right - bounds[1])
        y_overflow = max(0, -top) + max(0, bottom - bounds[0])
        
        return (x_overflow, y_overflow)

    def find_largest_inscribed_rectangle(self, points, design_aspect=1.0):
        """
        Find the largest rectangle that can fit inside the points.
        Adjusts for aspect ratio and ensures no cropping.
        """
        points_array = np.array(points)
        x_coords = points_array[:, 0]
        y_coords = points_array[:, 1]
        
        # Get the bounding rectangle dimensions
        left, top = np.min(x_coords), np.min(y_coords)
        right, bottom = np.max(x_coords), np.max(y_coords)
        
        # Initial dimensions
        width = right - left
        height = bottom - top
        
        height_scale = 0.55 if design_aspect <= 1.23 else 0.4
        # Calculate center point (aligned to top)
        center_x = (left + right) / 2
        center_y = top + (height * height_scale)  # Place higher in the rectangle
        
        # Apply initial safety margin
        # width *= 0.95
        # height *= 0.95
        
        return (center_x, center_y), width, height

    def match_dpi(self, original_img, new_img):
        """
        Scale the new image to match the DPI of the original image.
        Assumes both images represent the same physical size.
        """
        # Calculate pixels per inch (approximate based on image dimensions)
        orig_ppi = np.sqrt(original_img.shape[0] * original_img.shape[1])
        new_ppi = np.sqrt(new_img.shape[0] * new_img.shape[1])
        
        # Calculate scaling factor
        scale_factor = orig_ppi / new_ppi
        
        # Resize new image to match original's DPI
        new_height = int(new_img.shape[0] * scale_factor)
        new_width = int(new_img.shape[1] * scale_factor)
        
        return cv2.resize(new_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

    def get_optimal_placement_area(self, mask, points, image_type=None, mask_index=0):
        """Calculate optimal placement area using both mask and points"""
        if image_type == 'UVDTF 16oz':
            y_offset_top = 0.5
        else:
            y_offset_top = 0.35
        
        # Get mask bounds
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        # Calculate dimensions
        width = x_max - x_min
        height = y_max - y_min
        
        if mask_index == 0:  # First mask - use crop dimensions
            # Use full mask dimensions for cropping
            optimal_width = width * 0.95
            optimal_height = height * 0.95
        else:  # Second mask - use resize dimensions
            # Use slightly smaller dimensions for resize to ensure fit
            optimal_width = width
            optimal_height = height
        
        # Calculate center position
        center_x = (x_max + x_min) // 2
        center_y = y_min + height * y_offset_top
        
        return {
            'center': (center_x, center_y),
            'width': optimal_width,
            'height': optimal_height,
            'bounds': (x_min, y_min, x_max, y_max)
        }

    def create_mockup(self, masks, points_list, image_type=None, image=None, index=0):
        """
        Replaces the masked areas in the original image with the design image.
        First mask crops the image, second mask zooms and centers the image, cropping horizontally to the mask.
        """
        if image is None:
            design_img = cv2.imread(self.design_image_path, cv2.IMREAD_UNCHANGED)
        else:
            design_img = cv2.imread("{}{}".format(self.design_image_path, image), cv2.IMREAD_UNCHANGED)
        
        background = self.get_background(index)
        if background.shape[2] == 3:
            background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)

        result = background.copy()

        # Convert masks to numpy arrays if they're lists
        if isinstance(masks, list):
            masks = [np.array(mask) for mask in masks]
        elif isinstance(masks[0], list):
            masks = [np.array(mask) for mask in masks]
        
        for i, (mask, points) in enumerate(zip(masks, points_list)):
            if isinstance(mask, list):
                mask = np.array(mask)
            # Get optimal placement information
            placement = self.get_optimal_placement_area(mask, points, image_type, mask_index=i)
            design_aspect = design_img.shape[1] / design_img.shape[0]
            if i == 0:
                # First mask - crop and resize as before
                new_width = int(placement['width'])
                new_height = int(placement['height'])
                if design_aspect > (placement['width'] / placement['height']):
                    new_width = int(placement['width'])
                    new_height = int(new_width / design_aspect)
                else:
                    new_height = int(placement['height'])
                    new_width = int(new_height * design_aspect)
                design_to_place = cv2.resize(design_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                # Centered placement as before
                x_offset = int(placement['center'][0] - new_width / 2)
                y_offset = int(placement['center'][1] - new_height / 2)
            else:
                # Second mask - match height to mask, center, crop horizontally
                mask_indices = np.argwhere(mask)
                y_min, x_min = mask_indices.min(axis=0)
                y_max, x_max = mask_indices.max(axis=0)
                mask_h = y_max - y_min
                mask_w = x_max - x_min
                # 1. Resize design so its height matches mask height
                scale = mask_h / design_img.shape[0]
                resized_width = int(design_img.shape[1] * scale)
                resized_height = mask_h
                resized = cv2.resize(design_img, (resized_width, resized_height), interpolation=cv2.INTER_LANCZOS4)
                # 2. Center the resized image horizontally on the mask
                center_x = (x_max + x_min) // 2
                left = center_x - mask_w // 2
                right = center_x + mask_w // 2
                # 3. Crop horizontally to mask width
                crop_x1 = max(0, (resized.shape[1] - mask_w) // 2)
                crop_x2 = crop_x1 + mask_w
                cropped = resized[:, crop_x1:crop_x2]
                # If crop is out of bounds, pad as needed
                if cropped.shape[1] < mask_w:
                    pad_left = (mask_w - cropped.shape[1]) // 2
                    pad_right = mask_w - cropped.shape[1] - pad_left
                    cropped = cv2.copyMakeBorder(cropped, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0,0,0,0])
                design_to_place = cropped
                new_width = mask_w
                new_height = mask_h
                # Place at the mask's bounding box
                x_offset = x_min
                y_offset = y_min
            # Ensure coordinates are within bounds
            y_end = min(y_offset + new_height, result.shape[0])
            x_end = min(x_offset + new_width, result.shape[1])
            y_start = max(y_offset, 0)
            x_start = max(x_offset, 0)
            # Update design region coordinates
            design_y_start = y_start - y_offset
            design_x_start = x_start - x_offset
            design_y_end = design_y_start + (y_end - y_start)
            design_x_end = design_x_start + (x_end - x_start)
            # Only blend within the masked area
            mask_region = mask[y_start:y_end, x_start:x_end] > 0
            alpha_mask = design_to_place[design_y_start:design_y_end, design_x_start:design_x_end, 3] / 255.0
            # Blend the images
            for c in range(3):
                result[y_start:y_end, x_start:x_end, c] = np.where(
                    mask_region,
                    (1 - alpha_mask) * result[y_start:y_end, x_start:x_end, c] +
                    alpha_mask * design_to_place[design_y_start:design_y_end, design_x_start:design_x_end, c],
                    result[y_start:y_end, x_start:x_end, c]
                )
            # Update alpha channel
            result[y_start:y_end, x_start:x_end, 3] = np.where(
                mask_region,
                np.maximum(
                    result[y_start:y_end, x_start:x_end, 3],
                    design_to_place[design_y_start:design_y_end, design_x_start:design_x_end, 3]
                ),
                result[y_start:y_end, x_start:x_end, 3]
            )
        return result

    def add_watermark(self, image, watermark_path, points_list, masks, image_type, opacity=0.5):
        """
        Add a watermark to the image using the same points as the design placement.
        Watermark is applied to both masks/points, but only covers the visible design area (not the entire mask).
        Args:
            image: The image to add the watermark to
            watermark_path: Path to the watermark image
            points_list: The points used for the design placement
            masks: The masks used for the design placement
            image_type: The type of image (for placement)
            opacity: Opacity of the watermark (0-1)
        """
        watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
        print(watermark)
        result = image.copy()
        for i, (mask, points) in enumerate(zip(masks, points_list)):
            if isinstance(mask, list):
                mask = np.array(mask)
            placement = self.get_optimal_placement_area(mask, points, image_type)
            mask_indices = np.argwhere(mask)
            y_min, x_min = mask_indices.min(axis=0)
            y_max, x_max = mask_indices.max(axis=0)
            mask_h = y_max - y_min
            mask_w = x_max - x_min
            # Resize watermark so its height matches mask height
            scale = mask_h / watermark.shape[0]
            resized_width = int(watermark.shape[1] * scale)
            resized_height = mask_h
            resized = cv2.resize(watermark, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
            # Center horizontally and crop to mask width
            crop_x1 = max(0, (resized.shape[1] - mask_w) // 2)
            crop_x2 = crop_x1 + mask_w
            cropped = resized[:, crop_x1:crop_x2]
            if cropped.shape[1] < mask_w:
                pad_left = (mask_w - cropped.shape[1]) // 2
                pad_right = mask_w - cropped.shape[1] - pad_left
                cropped = cv2.copyMakeBorder(cropped, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0,0,0,0])
            watermark_to_place = cropped
            new_width = mask_w
            new_height = mask_h
            x_offset = x_min
            y_offset = y_min
            # Ensure coordinates are within bounds
            y_end = min(y_offset + new_height, result.shape[0])
            x_end = min(x_offset + new_width, result.shape[1])
            y_start = max(y_offset, 0)
            x_start = max(x_offset, 0)
            w_y_start = y_start - y_offset
            w_x_start = x_start - x_offset
            w_y_end = w_y_start + (y_end - y_start)
            w_x_end = w_x_start + (x_end - x_start)
            # Only apply watermark where design is visible (alpha > 0 and inside mask)
            # Get the design alpha channel from the composited image
            design_alpha = result[y_start:y_end, x_start:x_end, 3] / 255.0
            # Mask: only where design is visible and inside the mask
            visible_mask = (design_alpha > 0) & (mask[y_start:y_end, x_start:x_end] > 0)
            # Watermark alpha
            alpha = watermark_to_place[w_y_start:w_y_end, w_x_start:w_x_end, 3] / 255.0 * opacity
            # Combine with visible_mask
            alpha = alpha * visible_mask
            for c in range(3):
                result[y_start:y_end, x_start:x_end, c] = (
                    watermark_to_place[w_y_start:w_y_end, w_x_start:w_x_end, c] * alpha +
                    result[y_start:y_end, x_start:x_end, c] * (1.0 - alpha)
                )
        return result
    
def find_png_files(folder_path):
    # Ensure the path ends with a slash
    folder_path = os.path.join(folder_path, '')
    
    png_filepath = []
    png_filenames = []

    # Walks through dirtectory searchjing for PNG files and adds path to png_filepath
    for root, dirs, files in os.walk(folder_path):
        png_filepath.extend([os.path.join(root, file) for file in files if file.lower().endswith('.png')])
        png_filenames.extend([file for file in files if file.lower().endswith('.png')])
    
    return png_filepath, png_filenames

def process_uploaded_mockups(file_paths, root_path, template_name="UVDTF 16oz", user_id=None, db=None):
        print(file_paths)
        print(root_path)
        print(f"Using template: {template_name}")
        
        mockup_path = f"{root_path}Mockups/BaseMockups/UVDTF/"
        watermark_path = f"{root_path}Mockups/BaseMockups/Watermarks/Rectangle Watermark.png"
        designs_path = f"{root_path}{template_name}/"
        designs_path_list = []
        designs_filename_list = []
        
        # Create designs directory if it doesn't exist
        os.makedirs(designs_path, exist_ok=True)
        
        # Load mask data from database if available, otherwise fallback to JSON file
        masks = []
        points_list = []
        id_number = 100
        
        if user_id and db:
            try:
                from server.engine.mask_db_utils import load_mask_data_from_db
                masks, points_list, id_number = load_mask_data_from_db(db, user_id, template_name)
                print(f"Loaded mask data from database for user {user_id}, template {template_name}")
            except Exception as e:
                print(f"Failed to load mask data from database: {e}")
                # Fallback to JSON file
                try:
                    with open(f'{root_path}mockup_mask_data.json', 'r') as f:
                        data = json.load(f)
                        # Use template_name as key, fallback to 'UVDTF 16oz' for backward compatibility
                        template_key = template_name if template_name in data else 'UVDTF 16oz'
                        
                        for key in data[template_key].keys():
                            if key.startswith('mask'):
                                masks.append(np.array(data[template_key][key][0]))
                            elif key.startswith('points'):
                                points_list.append(data[template_key][key][0])
                        id_number = 100 if "starting_name" not in data[template_key] else data[template_key]['starting_name']
                except Exception as json_error:
                    print(f"Failed to load mask data from JSON file: {json_error}")
                    raise ValueError(f"No mask data found for template {template_name}")
        else:
            # Fallback to JSON file for backward compatibility
            try:
                with open(f'{root_path}mockup_mask_data.json', 'r') as f:
                    data = json.load(f)
                    # Use template_name as key, fallback to 'UVDTF 16oz' for backward compatibility
                    template_key = template_name if template_name in data else 'UVDTF 16oz'
                    
                    for key in data[template_key].keys():
                        if key.startswith('mask'):
                            masks.append(np.array(data[template_key][key][0]))
                        elif key.startswith('points'):
                            points_list.append(data[template_key][key][0])
                    id_number = 100 if "starting_name" not in data[template_key] else data[template_key]['starting_name']
            except Exception as e:
                print(f"Failed to load mask data from JSON file: {e}")
                raise ValueError(f"No mask data found for template {template_name}")
            
        def process_image(n):
            image = crop_transparent(file_paths[n])
            resized_image = resize_image_by_inches(image_path=file_paths[n], image_type=template_name, image=image)
            cup_wrap_id_number = str(n + id_number).zfill(3)
            filename = f"UV {cup_wrap_id_number} Cup_Wrap_{cup_wrap_id_number}.png"
            image_path = f"{designs_path}{filename}"
            save_single_image(resized_image, designs_path, filename, target_dpi=(400, 400))
            return image_path, filename

        for i in range(len(file_paths)):
            image_path, filename = process_image(i)
            designs_path_list.append(image_path)
            designs_filename_list.append(filename)

        mockupFilePath, _ = find_png_files(mockup_path)

        mockup = MockupImage(mockupFilePath, designs_path)

        def process_mockup(i):
            mockups_list = []
            for n in range(len(mockupFilePath)):
                assembled_mockup = mockup.create_mockup(masks, points_list, image_type=template_name, image=designs_filename_list[i], index=n)
                print("starting watermark")
                print(watermark_path)
                assembled_mockup_with_watermark = mockup.add_watermark(
                    assembled_mockup, 
                    watermark_path, 
                    points_list,  # Use first mask for watermark
                    masks,  # Use first mask for watermark
                    image_type=template_name,
                    opacity=0.45
                )
                height, width = assembled_mockup_with_watermark.shape[:2]
                scale_factor = min(2000 / width, 2000 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                resized_result = cv2.resize(assembled_mockup_with_watermark, new_size, interpolation=cv2.INTER_LANCZOS4)
                cup_wrap_id_number = str(id_number + i).zfill(3)
                color = "_Coffee"
                if re.search('Checkered', mockupFilePath[n]):
                    color = "_Checkered"
                elif re.search('Matcha', mockupFilePath[n]):
                    color = "_Matcha"
                generated_mockup_path = f'{root_path}Mockups/Cup Wraps/UV {cup_wrap_id_number} Cup_Wrap{cup_wrap_id_number}{color}.jpg'
                mockups_list.append(generated_mockup_path)
                cv2.imwrite(generated_mockup_path, resized_result, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            return mockups_list
        
        all_mockups_list = dict()
        for i in range(len(designs_filename_list)):
            all_mockups_list[designs_filename_list[i]] = process_mockup(i)

        # Update starting_name in database if available, otherwise fallback to JSON file
        new_starting_name = id_number + len(file_paths)
        
        if user_id and db:
            try:
                from server.engine.mask_db_utils import update_starting_name
                update_starting_name(db, user_id, template_name, new_starting_name)
                print(f"Updated starting_name in database to {new_starting_name}")
            except Exception as e:
                print(f"Failed to update starting_name in database: {e}")
                # Fallback to JSON file
                try:
                    with open(f"{root_path}mockup_mask_data.json", "w") as f:
                        data[template_key]["starting_name"] = new_starting_name
                        json.dump(data, f)
                except Exception as json_error:
                    print(f"Failed to update starting_name in JSON file: {json_error}")
        else:
            # Fallback to JSON file for backward compatibility
            try:
                with open(f"{root_path}mockup_mask_data.json", "w") as f:
                    data[template_key]["starting_name"] = new_starting_name
                    json.dump(data, f)
            except Exception as e:
                print(f"Failed to update starting_name in JSON file: {e}")
        
        return all_mockups_list
