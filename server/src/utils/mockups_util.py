"""
Mockup processing utilities for creating mockup images from design files.
"""
import os, cv2, re, logging, json
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from server.src.utils.cropping import crop_transparent
from server.src.utils.resizing import resize_image_by_inches
from server.src.entities.designs import DesignImages
from server.src.entities.mockup import Mockups
from server.src.utils.util import (
    save_single_image,
    find_png_files
)


class MockupTemplateCache:
    """Cache for mockup templates and watermarks"""
    def __init__(self):
        self.mockups = {}
        self.watermarks = {}
    
    def get_mockup(self, path):
        if path not in self.mockups:
            import os
            import logging
            logger = logging.getLogger(__name__)

            # Check if path exists and log details for debugging
            if not os.path.exists(path):
                logger.error(f"QNAP NAS: File does not exist: {path}")
                return None

            logger.info(f"QNAP NAS: Loading mockup from path: {path}")
            mockup_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

            if mockup_image is None:
                logger.error(f"QNAP NAS: Failed to read image with cv2.imread: {path}")
                # Try alternative method if cv2 fails
                try:
                    from PIL import Image
                    import numpy as np
                    pil_image = Image.open(path)
                    if pil_image.mode == 'RGBA':
                        mockup_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
                    else:
                        mockup_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    logger.info(f"QNAP NAS: Successfully loaded with PIL fallback: {path}")
                except Exception as e:
                    logger.error(f"QNAP NAS: PIL fallback also failed: {path}, error: {e}")
                    return None
            else:
                logger.info(f"QNAP NAS: Successfully loaded with cv2: {path}")

            self.mockups[path] = mockup_image

        if self.mockups[path] is None:
            return None
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

    def create_mockup(self, mask_points_list, points_list, image_type=None, image=None, index=0, is_cropped_list=None, alignment_list=None):
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
        
        background = self.get_background(index)
        if background.shape[2] == 3:
            background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)

        result = background.copy()

        # Process each mask with its own settings
        for i, (mask_points, points) in enumerate(zip(mask_points_list, points_list)):
            # Get mask-specific properties
            is_cropped = is_cropped_list[i] if is_cropped_list else False
            alignment = alignment_list[i] if alignment_list else 'center'

            # Create mask
            if not mask_points or len(mask_points) < 3:
                continue
            
            points = np.array(mask_points, dtype=np.int32)
            mask = np.zeros(background.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [points], (255,))

            # Get mask bounds
            mask_indices = np.argwhere(mask)
            y_min, x_min = mask_indices.min(axis=0)
            y_max, x_max = mask_indices.max(axis=0)
            mask_height = y_max - y_min
            mask_width = x_max - x_min

            if is_cropped:
                # When cropped: crop the image within the mask bounds, maintaining aspect ratio
                design_aspect = design_img.shape[1] / design_img.shape[0]
                mask_aspect = mask_width / mask_height
                
                if design_aspect > mask_aspect:
                    # Design is wider than mask - fit by height and crop width
                    scale = mask_height / design_img.shape[0]
                    scaled_width = int(design_img.shape[1] * scale)
                    scaled_height = mask_height
                    design_resized = cv2.resize(design_img, (scaled_width, scaled_height), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Calculate cropping bounds based on alignment
                    if alignment == 'left':
                        start_x = 0
                        end_x = min(mask_width, scaled_width)
                    elif alignment == 'right':
                        start_x = max(0, scaled_width - mask_width)
                        end_x = scaled_width
                    else:  # center
                        center_x = scaled_width // 2
                        half_mask_width = mask_width // 2
                        start_x = max(0, center_x - half_mask_width)
                        end_x = min(scaled_width, center_x + half_mask_width)
                    
                    design_to_place = design_resized[:, start_x:end_x]
                else:
                    # Design is taller than mask - fit by width and crop height
                    scale = mask_width / design_img.shape[1]
                    scaled_width = mask_width
                    scaled_height = int(design_img.shape[0] * scale)
                    design_resized = cv2.resize(design_img, (scaled_width, scaled_height), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Calculate cropping bounds based on vertical alignment (assume center for now)
                    if scaled_height > mask_height:
                        center_y = scaled_height // 2
                        half_mask_height = mask_height // 2
                        start_y = max(0, center_y - half_mask_height)
                        end_y = min(scaled_height, center_y + half_mask_height)
                        design_to_place = design_resized[start_y:end_y, :]
                    else:
                        design_to_place = design_resized
                        
                # Ensure the design fits exactly in the mask dimensions
                if design_to_place.shape[0] != mask_height or design_to_place.shape[1] != mask_width:
                    design_to_place = cv2.resize(design_to_place, (mask_width, mask_height), interpolation=cv2.INTER_LANCZOS4)
            else:
                # When not cropped: resize the image to fit within the mask area, centered
                design_aspect = design_img.shape[1] / design_img.shape[0]
                mask_aspect = mask_width / mask_height
                
                if design_aspect > mask_aspect:
                    # Design is wider - fit by width
                    scale = mask_width / design_img.shape[1]
                    scaled_width = mask_width
                    scaled_height = int(design_img.shape[0] * scale)
                else:
                    # Design is taller - fit by height
                    scale = mask_height / design_img.shape[0]
                    scaled_width = int(design_img.shape[1] * scale)
                    scaled_height = mask_height
                
                design_resized = cv2.resize(design_img, (scaled_width, scaled_height), interpolation=cv2.INTER_LANCZOS4)
                
                # Center the resized design within the mask dimensions
                pad_top = (mask_height - scaled_height) // 2
                pad_bottom = mask_height - scaled_height - pad_top
                pad_left = (mask_width - scaled_width) // 2
                pad_right = mask_width - scaled_width - pad_left
                
                design_to_place = cv2.copyMakeBorder(
                    design_resized,
                    pad_top, pad_bottom, pad_left, pad_right,
                    cv2.BORDER_CONSTANT,
                    value=[0,0,0,0] if design_resized.shape[2] == 4 else [0,0,0]
                )

            # Calculate placement coordinates
            x_offset = x_min
            y_offset = y_min
            
            # Ensure coordinates are within bounds
            y_end = min(y_offset + design_to_place.shape[0], result.shape[0])
            x_end = min(x_offset + design_to_place.shape[1], result.shape[1])
            y_start = max(y_offset, 0)
            x_start = max(x_offset, 0)
            
            # Update design region coordinates
            w_y_start = y_start - y_offset
            w_x_start = x_start - x_offset
            w_y_end = w_y_start + (y_end - y_start)
            w_x_end = w_x_start + (x_end - x_start)
            
            # Only apply design where the mask is active
            mask_region = mask[y_start:y_end, x_start:x_end]
            
            # Composite the design onto the background where mask is active
            if design_to_place.shape[2] == 4:  # Has alpha channel
                alpha = design_to_place[w_y_start:w_y_end, w_x_start:w_x_end, 3] / 255.0
                alpha = alpha * (mask_region > 0)  # Only apply where mask is active
                for c in range(3):
                    result[y_start:y_end, x_start:x_end, c] = (
                        design_to_place[w_y_start:w_y_end, w_x_start:w_x_end, c] * alpha +
                        result[y_start:y_end, x_start:x_end, c] * (1.0 - alpha)
                    )

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
    design_file_paths: List[str],
    template_name: str,
    mockup_id: str,
    root_path: str,
    starting_name: int,
    mask_data: Dict[str, Any],
    watermark_path: Optional[str] = None
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
        watermark_path: Path to the watermark file (if not provided, uses default)
    
    Returns:
        List of dictionaries with mockup image information
    """
    # Set up paths
    mockup_path = f"{root_path}Mockups/BaseMockups/{template_name}/"
    if watermark_path is None:
        watermark_path = f"{root_path}Mockups/BaseMockups/Watermarks/Rectangle Watermark.png"
    temp_design_path_list = []
    temp_deisgn_filename_list = []
    
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

    for design_file_path in design_file_paths:
        
        # Process the design image
        if not os.path.exists(design_file_path):
            raise FileNotFoundError(f"Design file not found: {design_file_path}")
        
        # Resize and crop the design image
        resized_image = process_design_image(design_file_path, template_name)
    
        # Create temporary design file for mockup processing
        temp_design_dir = f"{root_path}Temp/"
        os.makedirs(temp_design_dir, exist_ok=True)
        temp_design_filename = f"temp_design_{mockup_id}_{os.path.basename(design_file_path)}"
        temp_design_path = f"{temp_design_dir}{temp_design_filename}"
        temp_design_path_list.append(temp_design_path)
        temp_deisgn_filename_list.append(temp_design_filename)
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

def create_mockups_for_etsy(
    designs: List[DesignImages],
    mockup: Mockups,
    template_name: str,
    root_path: str,
    mask_data: Dict[str, Any]
) -> Tuple[str, Dict[str, List[str]], List[str]]:
    
    # Extract mask data from the provided dictionary
    type_pattern = r"UV\s*DTF|UV"
    id_number = mockup.starting_name
    mockup_return = dict()

    mockup_file_paths = set()
    mockup_filenames = list()
    watermark_path = set()
    for mockup_image in mockup.mockup_images:
        if mockup_image.file_path:
            mockup_file_paths.add(mockup_image.file_path)
        if mockup_image.filename:
            mockup_filenames.append(mockup_image.filename)
        if mockup_image.watermark_path:
            watermark_path.add(mockup_image.watermark_path)
    if len(watermark_path) > 1:
        raise ValueError(f"More than one watermark file path {watermark_path}")
    mockup_file_paths = list(mockup_file_paths)
    watermark_path = str(watermark_path.pop())

    design_file_paths = set()
    design_filenames = list()
    design_image_path_list = list()
    for design_image in designs:
        if design_image.file_path:
            split_path = design_image.file_path.split('/')
            split_path.pop()  # Remove filename
            split_path = ['/'.join(split_path)]+['/']
            design_file_paths.add(''.join(split_path))
        if design_image.filename:
            design_filenames.append(design_image.filename)
        if design_image.is_digital:
            design_image_path_list.append(design_image.file_path)
    if len(design_file_paths) > 1:
        raise ValueError(f"More than one design file path {design_file_paths}")
    design_file_paths = str(design_file_paths.pop())

    mockup_processor = MockupImageProcessor(mockup_file_paths, design_file_paths)

    for n, filename in enumerate(design_filenames):
        current_id_number = str(n + id_number).zfill(3)
        generated_mockup_path_list = list()
        for i, mockup_image in enumerate(mockup.mockup_images):
            if mockup_image.id in mask_data:
                current_masks = []
                current_points = []
                current_is_cropped = []
                current_alignments = []
                # Get all masks with their individual properties
                for mask in mockup_image.mask_data:
                    if isinstance(mask.masks, str):
                        masks = json.loads(mask.masks)
                    else:
                        masks = mask.masks

                    if isinstance(mask.points, str):
                        points = json.loads(mask.points)
                    else:
                        points = mask.points

                    # Add each mask with its properties
                    for m, p in zip(masks, points):
                        current_masks.append(m)
                        current_points.append(p)
                        current_is_cropped.append(mask.is_cropped)
                        current_alignments.append(mask.alignment)
            else:
                # Fallback to empty defaults if no mask data
                current_masks = []
                current_points = []
                current_is_cropped = [False]
                current_alignments = ['center']

            # Create mockup with all masks
            logging.info(f"Creating mockup for {filename} with template {template_name} (ID: {current_id_number})")
            logging.info(f"Using {len(current_masks)} masks with properties:")
            for idx, (is_crop, align) in enumerate(zip(current_is_cropped, current_alignments)):
                logging.info(f"Mask {idx}: cropped={is_crop}, alignment={align}")

            assembled_mockup = mockup_processor.create_mockup(
                current_masks,
                current_points,
                image_type=template_name, 
                image=filename, 
                index=i,
                is_cropped_list=current_is_cropped,
                alignment_list=current_alignments
            )
            
            # Add watermark
            assembled_mockup_with_watermark = mockup_processor.add_watermark(
                assembled_mockup, 
                watermark_path, 
                current_points,
                current_masks,
                image_type=template_name,
                opacity=0.45
            )
            
            # Resize for display
            height, width = assembled_mockup_with_watermark.shape[:2]
            scale_factor = min(2000 / width, 2000 / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            resized_result = cv2.resize(assembled_mockup_with_watermark, new_size, interpolation=cv2.INTER_LANCZOS4)

            # Determine color suffix
            postfix = "_".join(template_name.split()+[current_id_number]+[f"BG_{i}"])
            prefix = "UV" if re.search(type_pattern, template_name) else "DTF"
            
            # Generate mockup filename and path
            mockup_filename = f"{prefix} {current_id_number} {postfix}.jpg"
            generated_mockup_path = f'{root_path}Mockups/{template_name}/{mockup_filename}'
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(generated_mockup_path), exist_ok=True)
            
            generated_mockup_path_list.append(generated_mockup_path)

            # Save the mockup image
            cv2.imwrite(generated_mockup_path, resized_result, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        mockup_return[filename] = generated_mockup_path_list

    return current_id_number, mockup_return, design_image_path_list