"""
Mockup processing utilities for creating mockup images from design files.
"""
import os, cv2, re
import numpy as np
from typing import List, Tuple, Dict, Any
from server.src.utils.cropping import crop_transparent
from server.src.utils.resizing import resize_image_by_inches
from server.src.utils.util import save_single_image


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


class MockupImageProcessor:
    template_cache = MockupTemplateCache()

    def __init__(self, mockup_image_paths, design_image_path):
        self.mockup_image_paths = mockup_image_paths
        self.design_image_path = design_image_path
        self.max_display_size = 1500

    def get_background(self, index):
        """Cached background image loading"""
        return self.template_cache.get_mockup(self.mockup_image_paths[index])

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
            optimal_width = width * 0.95
            optimal_height = height * 0.95
        else:  # Second mask - use resize dimensions
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

    def create_mockup(self, mask_points_list, points_list, image_type=None, image=None, index=0, is_cropped=False, alignment='center'):
        """
        Create mockup by replacing masked areas with design image
        
        Args:
            mask_points_list: List of mask point arrays
            points_list: List of point arrays
            image_type: Type of image template
            image: Image filename
            index: Mockup index
            is_cropped: Whether to crop the design image to non-transparent area
            alignment: Alignment of design within mask ('left', 'center', 'right')
        """
        if image is None:
            design_img = cv2.imread(self.design_image_path, cv2.IMREAD_UNCHANGED)
        else:
            design_img = cv2.imread(f"{self.design_image_path}{image}", cv2.IMREAD_UNCHANGED)
        
        # Apply cropping if requested
        if is_cropped and design_img is not None and design_img.shape[2] == 4:
            # Crop to non-transparent area
            alpha = design_img[:, :, 3]
            rows = np.any(alpha != 0, axis=1)
            cols = np.any(alpha != 0, axis=0)
            if np.any(rows) and np.any(cols):
                ymin, ymax = np.where(rows)[0][[0, -1]]
                xmin, xmax = np.where(cols)[0][[0, -1]]
                design_img = design_img[ymin:ymax+1, xmin:xmax+1]
        
        background = self.get_background(index)
        if background.shape[2] == 3:
            background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)

        result = background.copy()

        # Create masks from points
        masks = []
        for i, mask_points in enumerate(mask_points_list):
            if not mask_points or len(mask_points) < 3:
                continue
            
            points = np.array(mask_points, dtype=np.int32)
            mask = np.zeros(background.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [points], (255,))
            masks.append(mask)
        
        for i, (mask, points) in enumerate(zip(masks, points_list)):
            placement = self.get_optimal_placement_area(mask, points, image_type, mask_index=i)
            design_aspect = design_img.shape[1] / design_img.shape[0]
            
            if is_cropped:
                # First mask - crop and resize
                new_width = int(placement['width'])
                new_height = int(placement['height'])
                if design_aspect > (placement['width'] / placement['height']):
                    new_width = int(placement['width'])
                    new_height = int(new_width / design_aspect)
                else:
                    new_height = int(placement['height'])
                    new_width = int(new_height * design_aspect)
                design_to_place = cv2.resize(design_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                
                # Calculate x_offset based on alignment
                if alignment == 'left':
                    x_offset = int(placement['bounds'][0])  # Left edge of mask
                elif alignment == 'right':
                    x_offset = int(placement['bounds'][2] - new_width)  # Right edge of mask
                else:  # center (default)
                    x_offset = int(placement['center'][0] - new_width / 2)
                
                y_offset = int(placement['center'][1] - new_height / 2)
            else:
                # Second mask - match height to mask, center, crop horizontally
                mask_indices = np.argwhere(mask)
                y_min, x_min = mask_indices.min(axis=0)
                y_max, x_max = mask_indices.max(axis=0)
                mask_h = y_max - y_min
                mask_w = x_max - x_min
                
                scale = mask_h / design_img.shape[0]
                resized_width = int(design_img.shape[1] * scale)
                resized_height = mask_h
                resized = cv2.resize(design_img, (resized_width, resized_height), interpolation=cv2.INTER_LANCZOS4)
                
                center_x = (x_max + x_min) // 2
                
                # Calculate crop position based on alignment
                if alignment == 'left':
                    crop_x1 = 0
                    crop_x2 = min(mask_w, resized.shape[1])
                elif alignment == 'right':
                    crop_x1 = max(0, resized.shape[1] - mask_w)
                    crop_x2 = resized.shape[1]
                else:  # center (default)
                    crop_x1 = max(0, (resized.shape[1] - mask_w) // 2)
                    crop_x2 = crop_x1 + mask_w
                
                cropped = resized[:, crop_x1:crop_x2]
                
                if cropped.shape[1] < mask_w:
                    pad_left = (mask_w - cropped.shape[1]) // 2
                    pad_right = mask_w - cropped.shape[1] - pad_left
                    cropped = cv2.copyMakeBorder(cropped, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0,0,0,0])
                
                design_to_place = cropped
                new_width = mask_w
                new_height = mask_h
                x_offset = x_min
                y_offset = y_min
            
            # Ensure coordinates are within bounds
            y_end = min(y_offset + new_height, result.shape[0])
            x_end = min(x_offset + new_width, result.shape[1])
            y_start = max(y_offset, 0)
            x_start = max(x_offset, 0)
            
            # Update design region coordinates
            w_y_start = y_start - y_offset
            w_x_start = x_start - x_offset
            w_y_end = w_y_start + (y_end - y_start)
            w_x_end = w_x_start + (x_end - x_start)
            
            # Composite the design onto the background
            if design_to_place.shape[2] == 4:  # Has alpha channel
                alpha = design_to_place[w_y_start:w_y_end, w_x_start:w_x_end, 3] / 255.0
                for c in range(3):
                    result[y_start:y_end, x_start:x_end, c] = (
                        design_to_place[w_y_start:w_y_end, w_x_start:w_x_end, c] * alpha +
                        result[y_start:y_end, x_start:x_end, c] * (1.0 - alpha)
                    )
            else:  # No alpha channel
                result[y_start:y_end, x_start:x_end, :3] = design_to_place[w_y_start:w_y_end, w_x_start:w_x_end]
        
        return result

    def add_watermark(self, image, watermark_path, points_list, mask_points_list, image_type, opacity=0.5):
        """Add watermark to the mockup image"""
        if not os.path.exists(watermark_path):
            return image
        
        watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
        if watermark is None:
            return image
        
        if watermark.shape[2] == 3:
            watermark = cv2.cvtColor(watermark, cv2.COLOR_BGR2BGRA)
        
        # Use first mask for watermark placement
        if not mask_points_list or not points_list:
            return image
        
        mask_points = mask_points_list[0]
        points = points_list[0]
        
        if not mask_points or len(mask_points) < 3:
            return image
        
        points_array = np.array(mask_points, dtype=np.int32)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points_array], (255,))
        
        # Find mask bounds
        mask_indices = np.argwhere(mask)
        if len(mask_indices) == 0:
            return image
        
        y_min, x_min = mask_indices.min(axis=0)
        y_max, x_max = mask_indices.max(axis=0)
        
        # Resize watermark to fit mask
        mask_width = x_max - x_min
        mask_height = y_max - y_min
        
        watermark_resized = cv2.resize(watermark, (mask_width, mask_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Place watermark at mask position
        y_start = max(y_min, 0)
        y_end = min(y_max, image.shape[0])
        x_start = max(x_min, 0)
        x_end = min(x_max, image.shape[1])
        
        w_y_start = y_start - y_min
        w_x_start = x_start - x_min
        w_y_end = w_y_start + (y_end - y_start)
        w_x_end = w_x_start + (x_end - x_start)
        
        # Get design alpha channel
        design_alpha = image[y_start:y_end, x_start:x_end, 3] / 255.0
        visible_mask = (design_alpha > 0) & (mask[y_start:y_end, x_start:x_end] > 0)
        
        # Watermark alpha
        alpha = watermark_resized[w_y_start:w_y_end, w_x_start:w_x_end, 3] / 255.0 * opacity
        alpha = alpha * visible_mask
        
        for c in range(3):
            image[y_start:y_end, x_start:x_end, c] = (
                watermark_resized[w_y_start:w_y_end, w_x_start:w_x_end, c] * alpha +
                image[y_start:y_end, x_start:x_end, c] * (1.0 - alpha)
            )
        
        return image


def find_png_files(folder_path: str) -> Tuple[List[str], List[str]]:
    """Find all PNG files in a directory"""
    folder_path = os.path.join(folder_path, '')
    png_filepath = []
    png_filenames = []
    
    for root, dirs, files in os.walk(folder_path):
        png_filepath.extend([os.path.join(root, file) for file in files if file.lower().endswith('.png')])
        png_filenames.extend([file for file in files if file.lower().endswith('.png')])
    
    return png_filepath, png_filenames


def process_design_image(design_file_path: str, template_name: str) -> Tuple[np.ndarray, str]:
    """
    Process a design image for mockup creation.
    
    Args:
        design_file_path: Path to the design file
        template_name: Name of the template for resizing
    
    Returns:
        Tuple of (processed_image, temp_file_path)
    """
    
    # Process the design image
    design_image = crop_transparent(design_file_path)
    if design_image is None:
        raise ValueError(f"Failed to process design image: {design_file_path}")
    
    # Resize the design image
    resized_image = resize_image_by_inches(
        image_path=design_file_path, 
        image_type=template_name, 
        image=design_image
    )
    
    return resized_image


def create_mockup_images(
    design_file_path: str,
    template_name: str,
    mockup_id: str,
    root_path: str,
    starting_name: int,
    mask_data: Dict[str, Any]
) -> List[dict]:
    """
    Create mockup images from a design file.
    
    Args:
        design_file_path: Path to the design file
        template_name: Name of the template
        mockup_id: Mockup ID for file naming
        root_path: Root path for file operations
        starting_name: Starting name for file numbering
        mask_data: Dictionary containing 'masks', 'points', 'is_cropped', and 'alignment'
    
    Returns:
        List of dictionaries with mockup image information
    """
    # Set up paths
    mockup_path = f"{root_path}Mockups/BaseMockups/{template_name}/"
    watermark_path = f"{root_path}Mockups/BaseMockups/Watermarks/Rectangle Watermark.png"
    
    # Check if design file exists
    if not os.path.exists(design_file_path):
        raise FileNotFoundError(f"Design file not found: {design_file_path}")
    
    # Extract mask data from the provided dictionary
    mask_points_list = mask_data.get('masks', [])
    points_list = mask_data.get('points', [])
    is_cropped = mask_data.get('is_cropped', False)
    alignment = mask_data.get('alignment', 'center')
    
    if not mask_points_list or not points_list:
        raise ValueError(f"No mask data provided for template {template_name}")
    
    # Find mockup files
    mockup_file_paths, _ = find_png_files(mockup_path)
    if not mockup_file_paths:
        raise FileNotFoundError(f"No mockup files found in {mockup_path}")
    
    # Process the design image
    resized_image = process_design_image(design_file_path, template_name)
    
    # Create temporary design file for mockup processing
    temp_design_dir = f"{root_path}Temp/"
    os.makedirs(temp_design_dir, exist_ok=True)
    temp_design_filename = f"temp_design_{mockup_id}_{os.path.basename(design_file_path)}"
    temp_design_path = f"{temp_design_dir}{temp_design_filename}"
    
    # Save the processed design image
    save_single_image(resized_image, temp_design_dir, temp_design_filename, target_dpi=(400, 400))
    
    # Create mockup processor
    mockup_processor = MockupImageProcessor(mockup_file_paths, temp_design_dir)
    
    # Generate mockups for each template
    generated_mockups = []
    cup_wrap_id_number = str(starting_name).zfill(3)
    
    for i, mockup_file_path in enumerate(mockup_file_paths):
        # Create mockup
        assembled_mockup = mockup_processor.create_mockup(
            mask_points_list, 
            points_list, 
            image_type=template_name, 
            image=temp_design_filename, 
            index=i,
            is_cropped=is_cropped,
            alignment=alignment
        )
        
        # Add watermark
        assembled_mockup_with_watermark = mockup_processor.add_watermark(
            assembled_mockup, 
            watermark_path, 
            points_list, 
            mask_points_list, 
            image_type=template_name,
            opacity=0.45
        )
        
        # Resize for display
        height, width = assembled_mockup_with_watermark.shape[:2]
        scale_factor = min(2000 / width, 2000 / height)
        new_size = (int(width * scale_factor), int(height * scale_factor))
        resized_result = cv2.resize(assembled_mockup_with_watermark, new_size, interpolation=cv2.INTER_LANCZOS4)
        
        # Determine color suffix
        color = "_Coffee"
        if re.search('Checkered', mockup_file_path):
            color = "_Checkered"
        elif re.search('Matcha', mockup_file_path):
            color = "_Matcha"
        
        # Generate mockup filename and path
        mockup_filename = f"UV {cup_wrap_id_number} Cup_Wrap{cup_wrap_id_number}{color}.jpg"
        generated_mockup_path = f'{root_path}Mockups/Cup Wraps/{mockup_filename}'
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(generated_mockup_path), exist_ok=True)
        
        # Save the mockup image
        cv2.imwrite(generated_mockup_path, resized_result, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        
        generated_mockups.append({
            'filename': mockup_filename,
            'file_path': generated_mockup_path,
            'watermark_path': watermark_path,
            'image_type': template_name,
            'color': color
        })
    
    # Clean up temporary design file
    try:
        os.remove(temp_design_path)
    except OSError:
        pass
    
    return generated_mockups
