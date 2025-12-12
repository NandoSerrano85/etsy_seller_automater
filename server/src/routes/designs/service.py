from server.src.entities.designs import DesignImages
from server.src.entities.canvas_config import CanvasConfig
from server.src.entities.size_config import SizeConfig
from server.src.entities.template import EtsyProductTemplate, ShopifyProductTemplate
from server.src.entities.user import User
from server.src.entities.etsy_store import EtsyStore
from server.src.message import (
    DesignNotFoundError,
    DesignCreateError,
    DesignGetAllError,
    DesignGetByIdError,
    DesignUpdateError,
    DesignDeleteError,
    InvalidUserToken
)
from server.src.utils.util import (
    save_single_image,
    get_dpi_from_image,
    get_width_and_height,
    inches_to_pixels
)
from server.src.utils.nas_storage import nas_storage
from server.src.utils.resizing import resize_image_by_inches
from server.src.utils.cropping import crop_transparent
from uuid import UUID
from sqlalchemy.orm import Session
from . import model
import logging, numpy as np, cv2, os, re
from typing import Optional, List
from fastapi import UploadFile
from PIL import Image
import imagehash
import os
import cv2
from server.src.utils.cropping import crop_transparent
from server.src.utils.resizing import resize_image_by_inches
from server.src.utils.util import find_png_files
from server.src.utils.railway_cache import railway_cached, cache_design_list, get_cached_design_list, invalidate_user_cache


def get_etsy_shop_name(db: Session, user_id: UUID) -> str:
    """Get the Etsy shop name for a user from etsy_stores table (not users.shop_name which may be Shopify)"""
    etsy_store = db.query(EtsyStore).filter(
        EtsyStore.user_id == user_id,
        EtsyStore.is_active == True
    ).order_by(EtsyStore.created_at.desc()).first()

    if etsy_store and etsy_store.shop_name:
        logging.info(f"Using Etsy shop name from etsy_stores: {etsy_store.shop_name}")
        return etsy_store.shop_name

    # Fallback to user_id if no Etsy store found
    fallback_name = f"user_{str(user_id)[:8]}"
    logging.warning(f"No Etsy store found for user {user_id}, using fallback: {fallback_name}")
    return fallback_name

def calculate_multiple_hashes(image_path: str = None, image=None, hash_size: int = 16) -> dict:
    """
    Calculate multiple perceptual hashes for better duplicate detection.

    Args:
        image_path: Path to the image file (optional if image provided)
        image: PIL Image object (optional if image_path provided)
        hash_size: Hash size for the perceptual hashes

    Returns:
        Dict containing phash, ahash, dhash, whash as strings
    """
    try:
        if image is None:
            if image_path is None:
                raise ValueError("Either image_path or image must be provided")
            image = Image.open(image_path)

        return {
            'phash': str(imagehash.phash(image, hash_size=hash_size)),
            'ahash': str(imagehash.average_hash(image, hash_size=hash_size)),
            'dhash': str(imagehash.dhash(image, hash_size=hash_size)),
            'whash': str(imagehash.whash(image, hash_size=hash_size))
        }
    except Exception as e:
        logging.error(f"Error calculating hashes for {image_path}: {e}")
        raise

def calculate_phash(image_path: str, hash_size: int = 16) -> str:
    """
    Calculate perceptual hash for an image file (legacy function for backward compatibility).

    Args:
        image_path: Path to the image file
        hash_size: Hash size for the perceptual hash

    Returns:
        String representation of the hash
    """
    try:
        hashes = calculate_multiple_hashes(image_path=image_path, hash_size=hash_size)
        return hashes['phash']
    except Exception as e:
        logging.error(f"Error calculating phash for {image_path}: {e}")
        return None


def process_images_for_comparison(image_paths, db=None, canvas_id=None, product_template_id=None, target_dpi=400):
    """
    Process images by cropping transparency and resizing before comparison.

    Parameters:
        image_paths: List of image file paths
        db: Database session for resizing configuration
        canvas_id: Canvas ID for resizing configuration
        product_template_id: Product template ID for resizing configuration
        target_dpi: Target DPI for resizing

    Returns:
        list: List of processed image arrays
    """
    processed_images = []

    for image_path in image_paths:
        try:
            # Step 1: Crop transparent areas
            cropped_image = crop_transparent(image_path)

            if cropped_image is not None:
                # Step 2: Resize the cropped image
                resized_image = resize_image_by_inches(
                    image_path=image_path,
                    image_type="UVDTF 16oz",  # Default type
                    db=db,
                    canvas_id=canvas_id,
                    product_template_id=product_template_id,
                    image_size="",
                    image=cropped_image,
                    target_dpi=target_dpi
                )
                processed_images.append(resized_image)
            else:
                logging.warning(f"Failed to crop image: {image_path}")
                processed_images.append(None)

        except Exception as e:
            logging.error(f"Error processing {image_path}: {e}")
            processed_images.append(None)

    return processed_images


def build_hash_db_from_processed(image_paths, processed_images, hash_size=16):
    """
    Build hash database from processed images.
    """
    hash_db = {}
    for i, path in enumerate(image_paths):
        if i < len(processed_images) and processed_images[i] is not None:
            try:
                # Convert OpenCV image (BGR/BGRA) to RGB for PIL
                img_array = processed_images[i]
                if len(img_array.shape) == 3:
                    if img_array.shape[2] == 4:  # BGRA
                        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGBA)
                    else:  # BGR
                        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                else:  # Grayscale
                    img_rgb = img_array

                # Convert to PIL Image
                pil_img = Image.fromarray(img_rgb)

                hash_db[path] = {
                    'phash': imagehash.phash(pil_img, hash_size=hash_size),
                    'ahash': imagehash.average_hash(pil_img, hash_size=hash_size),
                    'dhash': imagehash.dhash(pil_img, hash_size=hash_size),
                    'whash': imagehash.whash(pil_img, hash_size=hash_size)
                }
            except Exception as e:
                logging.error(f"Skipping hash generation for {path}: {e}")
    return hash_db


def check_duplicates_processed(new_image_paths, processed_new_images, hash_db, threshold=5, hash_size=16, min_matches=2):
    """
    Check duplicates using processed images.
    """
    results = {}

    for i, new_path in enumerate(new_image_paths):
        best_match = None
        best_score = 0

        if i < len(processed_new_images) and processed_new_images[i] is not None:
            try:
                # Convert OpenCV image to PIL format
                img_array = processed_new_images[i]
                if len(img_array.shape) == 3:
                    if img_array.shape[2] == 4:  # BGRA
                        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGBA)
                    else:  # BGR
                        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                else:  # Grayscale
                    img_rgb = img_array

                pil_img = Image.fromarray(img_rgb)

                new_hashes = {
                    'phash': imagehash.phash(pil_img, hash_size=hash_size),
                    'ahash': imagehash.average_hash(pil_img, hash_size=hash_size),
                    'dhash': imagehash.dhash(pil_img, hash_size=hash_size),
                    'whash': imagehash.whash(pil_img, hash_size=hash_size)
                }

                for existing_path, existing_hashes in hash_db.items():
                    matches = 0
                    total_distance = 0

                    for hash_type in new_hashes:
                        distance = abs(new_hashes[hash_type] - existing_hashes[hash_type])
                        if distance <= threshold:
                            matches += 1
                        total_distance += distance

                    if matches >= min_matches:
                        confidence = matches + (1.0 / (1.0 + total_distance / len(new_hashes)))
                        if confidence > best_score:
                            best_score = confidence
                            best_match = (existing_path, confidence)

            except Exception as e:
                logging.error(f"Error processing {new_path}: {e}")

        results[new_path] = best_match
    return results


def enhanced_duplicate_detection(db: Session, new_image_paths: List[str], user_id: UUID,
                                 canvas_id: UUID = None, product_template_id: UUID = None,
                                 threshold: int = 5, min_matches: int = 2) -> dict:
    """
    Enhanced duplicate detection using multiple hash algorithms and image preprocessing.

    Args:
        db: Database session
        new_image_paths: List of paths to new images to check
        user_id: User ID to scope the search
        canvas_id: Canvas ID for resizing configuration
        product_template_id: Product template ID for resizing configuration
        threshold: Hamming distance threshold for considering images duplicates
        min_matches: Minimum number of hash algorithms that must match

    Returns:
        dict: {new_image_path: {'duplicate': bool, 'existing_design': DesignImages or None, 'confidence': float}}
    """
    results = {}

    try:
        # Get all existing designs with multiple hashes for this user
        existing_designs = db.query(DesignImages).filter(
            DesignImages.user_id == user_id,
            DesignImages.is_active == True,
            DesignImages.phash.isnot(None)
        ).all()

        # Build existing images database with their file paths for processing
        existing_paths = []
        existing_designs_map = {}

        for design in existing_designs:
            if design.file_path and os.path.exists(design.file_path):
                existing_paths.append(design.file_path)
                existing_designs_map[design.file_path] = design
            else:
                logging.warning(f"Design file not found: {design.file_path}")

        if not existing_paths:
            # No existing images to compare against
            for image_path in new_image_paths:
                results[image_path] = {
                    'duplicate': False,
                    'existing_design': None,
                    'confidence': 0.0
                }
            return results

        # Step 1: Process existing images (crop and resize)
        logging.info(f"Processing {len(existing_paths)} existing images for comparison...")
        processed_existing = process_images_for_comparison(
            existing_paths, db=db, canvas_id=canvas_id,
            product_template_id=product_template_id
        )

        # Step 2: Process new images (crop and resize)
        logging.info(f"Processing {len(new_image_paths)} new images for comparison...")
        processed_new = process_images_for_comparison(
            new_image_paths, db=db, canvas_id=canvas_id,
            product_template_id=product_template_id
        )

        # Step 3: Build hash database from processed existing images
        logging.info("Building hash database from processed images...")
        hash_db = build_hash_db_from_processed(existing_paths, processed_existing)

        # Step 4: Check duplicates using processed new images
        logging.info("Checking for duplicates using enhanced detection...")
        duplicate_results = check_duplicates_processed(
            new_image_paths, processed_new, hash_db,
            threshold=threshold, min_matches=min_matches
        )

        # Step 5: Map results back to design objects
        for image_path, match_result in duplicate_results.items():
            if match_result:
                existing_path, confidence = match_result
                existing_design = existing_designs_map.get(existing_path)
                results[image_path] = {
                    'duplicate': True,
                    'existing_design': existing_design,
                    'confidence': confidence
                }
            else:
                results[image_path] = {
                    'duplicate': False,
                    'existing_design': None,
                    'confidence': 0.0
                }

    except Exception as e:
        logging.error(f"Enhanced duplicate detection failed: {e}")
        # Fallback to basic duplicate detection for all images
        for image_path in new_image_paths:
            results[image_path] = {
                'duplicate': False,
                'existing_design': None,
                'confidence': 0.0,
                'error': str(e)
            }

    return results


def _validate_canvas_config(db: Session, product_template_id: UUID, canvas_config_id: UUID) -> bool:
    """Validate that canvas config exists and belongs to the user"""
    canvas_config = db.query(CanvasConfig).filter(
        CanvasConfig.id == canvas_config_id,
        CanvasConfig.product_template_id == product_template_id,
        CanvasConfig.is_active == True
    ).first()
    return canvas_config is not None


def _validate_size_config(db: Session, product_template_id: UUID, size_config_id: UUID, canvas_config_id: Optional[UUID] = None) -> bool:
    """Validate that size config exists, belongs to the user, and is associated with the canvas config if provided"""
    query = db.query(SizeConfig).filter(
        SizeConfig.id == size_config_id,
        SizeConfig.product_template_id == product_template_id,
        SizeConfig.is_active == True
    )
    
    if canvas_config_id:
        query = query.filter(SizeConfig.canvas_id == canvas_config_id)
    
    size_config = query.first()
    return size_config is not None


def _detect_platform_from_template(db: Session, template_id: UUID) -> str:
    """
    Detect whether a template belongs to Etsy or Shopify platform

    Args:
        db: Database session
        template_id: UUID of the template

    Returns:
        'etsy' or 'shopify' based on which table contains the template
    """
    # Check if template exists in Etsy templates
    etsy_template = db.query(EtsyProductTemplate).filter(
        EtsyProductTemplate.id == template_id
    ).first()

    if etsy_template:
        return 'etsy'

    # Check if template exists in Shopify templates
    shopify_template = db.query(ShopifyProductTemplate).filter(
        ShopifyProductTemplate.id == template_id
    ).first()

    if shopify_template:
        return 'shopify'

    # Default to 'etsy' for backward compatibility if template not found
    logging.warning(f"Template {template_id} not found in either Etsy or Shopify tables, defaulting to 'etsy'")
    return 'etsy'


async def create_design(db: Session, user_id: UUID, design_data: model.DesignImageCreate, files: List[UploadFile], progress_callback=None) -> model.DesignImageListResponse:
    """
    Enhanced create_design function that integrates the new comprehensive workflow
    while maintaining backward compatibility with existing frontend
    """
    # Auto-detect platform from template if not already set
    if design_data.platform == 'etsy' and design_data.product_template_id:
        detected_platform = _detect_platform_from_template(db, design_data.product_template_id)
        design_data.platform = detected_platform
        logging.info(f"🔍 Auto-detected platform: {detected_platform} for template {design_data.product_template_id}")

    # Check if we should use the new comprehensive workflow
    use_new_workflow = os.getenv('USE_COMPREHENSIVE_WORKFLOW', 'true').lower() == 'true'

    # Check minimum file threshold for comprehensive workflow
    min_files = int(os.getenv('COMPREHENSIVE_WORKFLOW_MIN_FILES', '2'))

    if use_new_workflow and len(files) >= min_files:
        # Use the new comprehensive workflow for multiple files
        return await _create_design_with_comprehensive_workflow(db, user_id, design_data, files, progress_callback)
    else:
        # Use original workflow for single files or when disabled
        return await _create_design_original(db, user_id, design_data, files, progress_callback)


async def _create_design_with_comprehensive_workflow(db: Session, user_id: UUID, design_data: model.DesignImageCreate, files: List[UploadFile], progress_callback=None) -> model.DesignImageListResponse:
    """
    New comprehensive workflow implementation
    """
    try:
        from server.src.services.image_upload_workflow import create_workflow, UploadedImage
        from datetime import datetime, timezone

        if progress_callback:
            progress_callback(0, "Starting comprehensive image processing workflow")

        # Convert UploadFiles to UploadedImage objects for the workflow
        uploaded_images = []
        for file in files:
            content = await file.read()
            await file.seek(0)  # Reset for potential reuse

            uploaded_image = UploadedImage(
                original_filename=file.filename or "upload.png",
                content=content,
                size=len(content),
                upload_time=datetime.now(timezone.utc),
                user_id=str(user_id),
                template_id=str(design_data.product_template_id) if design_data.product_template_id else None
            )
            uploaded_images.append(uploaded_image)

        # Create workflow with database session and progress callback
        max_threads = int(os.getenv('COMPREHENSIVE_WORKFLOW_MAX_THREADS', '4'))
        workflow = create_workflow(user_id=str(user_id), db_session=db, max_threads=max_threads, progress_callback=progress_callback)

        # Create progress callback wrapper that matches existing interface
        def workflow_progress_callback(step: int, message: str, total_steps: int = 4, file_progress: float = 0):
            if progress_callback:
                # Map workflow steps to existing frontend steps
                step_mapping = {
                    1: "Checking for duplicates",
                    2: "Processing and formatting images",
                    3: "Creating product mockups",
                    4: "Uploading to Etsy store"
                }
                mapped_message = step_mapping.get(step, message)
                progress_callback(step - 1, mapped_message, total_steps, file_progress)

        # Process images through the comprehensive workflow
        if progress_callback:
            progress_callback(0, "Processing images with duplicate detection")

        result = workflow.process_images(uploaded_images, design_data)

        if progress_callback:
            progress_callback(1, f"Processed {result.processed_images} images, skipped {result.skipped_duplicates} duplicates")

        # Convert workflow results back to the expected format
        design_results = []

        # Query database for all recently created designs by this workflow
        # Since the comprehensive workflow creates designs directly in the database during processing,
        # we need to find them by querying for recent designs created in the last few minutes

        from datetime import timedelta
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        try:
            # Get all designs created recently by this user
            recent_designs_query = db.query(DesignImages).filter(
                DesignImages.user_id == user_id,
                DesignImages.created_at >= recent_time,
                DesignImages.is_active == True
            ).order_by(DesignImages.created_at.desc())

            recent_designs = recent_designs_query.limit(result.processed_images + 5).all()

            # Take the most recent designs up to the number processed
            design_results = recent_designs[:result.processed_images] if result.processed_images > 0 else []

            logging.info(f"Found {len(design_results)} recently created designs for comprehensive workflow result")

        except Exception as e:
            logging.error(f"Error querying recent designs: {e}")
            design_results = []

        # If no designs were found in DB (fallback), create them using original method
        if not design_results:
            logging.warning("Comprehensive workflow completed but no designs found in DB, falling back to original method")
            return await _create_design_original(db, user_id, design_data, files, progress_callback)

        if progress_callback:
            progress_callback(2, f"Successfully created {len(design_results)} designs")

        response = model.DesignImageListResponse(
            designs=[model.DesignImageResponse.model_validate(design) for design in design_results],
            total=len(design_results)
        )

        logging.info(f"Comprehensive workflow completed: {len(design_results)} designs created for user: {user_id}")
        return response

    except Exception as e:
        logging.error(f"Comprehensive workflow failed, falling back to original: {e}")
        # Fallback to original workflow if the new one fails
        return await _create_design_original(db, user_id, design_data, files, progress_callback)


async def _create_design_original(db: Session, user_id: UUID, design_data: model.DesignImageCreate, files: List[UploadFile], progress_callback=None) -> model.DesignImageListResponse:
    """
    Original design creation workflow (preserved for backward compatibility and single files)
    """
    try:
        # Validate canvas config if provided
        if design_data.canvas_config_id:
            if not _validate_canvas_config(db, design_data.product_template_id, design_data.canvas_config_id):
                logging.warning(f"Invalid canvas config ID: {design_data.canvas_config_id} for user: {user_id}")
                raise DesignCreateError()
        
        # Validate size config if provided
        if design_data.size_config_id:
            if not _validate_size_config(db, design_data.product_template_id, design_data.size_config_id, design_data.canvas_config_id):
                logging.warning(f"Invalid size config ID: {design_data.size_config_id} for user: {user_id}")
                raise DesignCreateError()
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.error(f"User not found with ID: {user_id}")
            raise InvalidUserToken()
        template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == design_data.product_template_id,
            EtsyProductTemplate.user_id == user_id,
        ).first()

        # Get Etsy shop name from etsy_stores table (not users.shop_name which may be Shopify)
        etsy_shop_name = get_etsy_shop_name(db, user_id)

        type_pattern = r"UV\s*DTF|UV"
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        if design_data.is_digital:
            designs_path = f"{local_root_path}{etsy_shop_name}/Digital/{template.name}/"
        else:
            designs_path = f"{local_root_path}{etsy_shop_name}/{template.name}/"
        os.makedirs(designs_path, exist_ok=True)
        
        async def resize_and_hash_physical(file):
            """Resize image and calculate hashes (before duplicate check) - no upload yet"""
            import time
            start_time = time.time()

            try:
                # Read the image file content
                logging.info(f"📥 Resizing and hashing: {file.filename}")
                contents = await file.read()
                await file.seek(0)  # Reset for later use

                nparr = np.frombuffer(contents, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

                if image is None:
                    logging.error("❌ Failed to decode image")
                    return None

                # Crop transparent areas
                crop_start = time.time()
                cropped_image = crop_transparent(image=image)
                if cropped_image is None:
                    logging.error("❌ Failed to crop image")
                    return None
                logging.info(f"✂️ Cropped in {time.time() - crop_start:.2f}s")

                # Resize image
                resize_start = time.time()
                resized_image = resize_image_by_inches(
                    image=cropped_image,
                    image_type=template.name,
                    db=db,
                    canvas_id=design_data.canvas_config_id,
                    product_template_id=design_data.product_template_id
                )
                logging.info(f"📐 Resized in {time.time() - resize_start:.2f}s")

                # Convert to PIL for hashing
                hash_start = time.time()
                if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                    img_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGRA2RGB)
                elif len(resized_image.shape) == 3:
                    img_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
                else:
                    img_rgb = resized_image

                pil_img = Image.fromarray(img_rgb)
                pil_img_normalized = pil_img.resize((256, 256), Image.Resampling.LANCZOS)

                # Calculate all 4 hash types
                phash = str(imagehash.phash(pil_img_normalized, hash_size=16))
                ahash = str(imagehash.average_hash(pil_img_normalized, hash_size=16))
                dhash = str(imagehash.dhash(pil_img_normalized, hash_size=16))
                whash = str(imagehash.whash(pil_img_normalized, hash_size=16))

                logging.info(f"🔐 Generated hashes in {time.time() - hash_start:.2f}s: phash={phash[:8]}...")

                # Store resized image for later upload (if not duplicate)
                total_time = time.time() - start_time
                logging.info(f"✅ Resize & hash completed in {total_time:.2f}s")

                return {
                    'resized_image': resized_image,
                    'phash': phash,
                    'ahash': ahash,
                    'dhash': dhash,
                    'whash': whash,
                    'original_filename': file.filename
                }

            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error(f"❌ Error resizing/hashing physical image: {str(e)}")
                return None

        async def upload_processed_image_physical(processed_data, index, id_number):
            """Upload previously resized image to NAS with generated filename"""
            import time
            upload_start = time.time()

            try:
                resized_image = processed_data['resized_image']

                # Generate filename
                current_id_number = str(index + id_number).zfill(3)
                prefix = "UV" if re.search(type_pattern, template.name) else "DTF"
                postfix = "_".join(str(template.name).split() + [current_id_number])
                filename = f"{prefix} {current_id_number} {postfix}.png"

                logging.info(f"📤 Uploading to NAS: {filename}")

                # Encode to bytes with DPI metadata
                encode_start = time.time()

                # Convert OpenCV image to PIL for proper DPI metadata
                # CRITICAL: Ensure images are saved with 400 DPI for consistency
                if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                    # BGRA to RGBA
                    pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGRA2RGBA))
                elif len(resized_image.shape) == 3 and resized_image.shape[2] == 3:
                    # BGR to RGB
                    pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))
                else:
                    # Grayscale
                    pil_image = Image.fromarray(resized_image)

                # Save with DPI metadata
                from io import BytesIO
                buffer = BytesIO()
                pil_image.save(buffer, format='PNG', optimize=True, compress_level=3, dpi=(400, 400))
                image_bytes = buffer.getvalue()
                logging.info(f"💾 Encoded in {time.time() - encode_start:.2f}s ({len(image_bytes) / 1024 / 1024:.2f}MB) with DPI: 400x400")

                # Upload to NAS
                nas_start = time.time()
                relative_path = f"{template.name}/{filename}"
                success = nas_storage.upload_file_content(
                    file_content=image_bytes,
                    shop_name=etsy_shop_name,
                    relative_path=relative_path
                )
                if success:
                    logging.info(f"✅ Uploaded to NAS in {time.time() - nas_start:.2f}s: {relative_path}")
                else:
                    logging.warning(f"⚠️ Failed to upload to NAS: {relative_path}")
                    return None, None, None

                total_time = time.time() - upload_start
                logging.info(f"✅ Upload completed in {total_time:.2f}s")

                return filename, relative_path, image_bytes

            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error(f"❌ Error uploading physical image: {str(e)}")
                return None, None, None

        def check_duplicate_in_database(phash_hex: str, platform: str = 'etsy') -> bool:
            """Check if image already exists in database using indexed queries (optimized for ≤2 images)"""
            from sqlalchemy import text
            import time

            check_start = time.time()
            try:
                # Use indexed query for exact match - O(log n) instead of O(n)
                # NOW FILTERS BY PLATFORM to keep Shopify and Etsy designs separate
                result = db.execute(text("""
                    SELECT 1 FROM design_images
                    WHERE user_id = :user_id
                    AND platform = :platform
                    AND is_active = true
                    AND phash = :phash
                    LIMIT 1
                """), {"user_id": str(user_id), "platform": platform, "phash": phash_hex})

                is_duplicate = result.fetchone() is not None
                logging.info(f"🔍 Database duplicate check ({platform}) completed in {time.time() - check_start:.3f}s: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
                return is_duplicate

            except Exception as e:
                logging.error(f"❌ Error checking database duplicates: {e}")
                return False

        def check_hamming_distance_in_database(phash_hex: str, platform: str = 'etsy', threshold: int = None) -> tuple[bool, Optional[str]]:
            """Check Hamming distance against recent database entries (last 1000 images only)"""
            from sqlalchemy import text
            import time

            # Use configurable threshold, default to 15 (was 5, too strict)
            if threshold is None:
                threshold = int(os.getenv('DUPLICATE_HAMMING_THRESHOLD', '15'))

            check_start = time.time()
            try:
                # Query only last 1000 images for Hamming distance check
                # NOW FILTERS BY PLATFORM to keep Shopify and Etsy designs separate
                result = db.execute(text("""
                    SELECT phash, filename FROM design_images
                    WHERE user_id = :user_id
                    AND platform = :platform
                    AND is_active = true
                    AND phash IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 1000
                """), {"user_id": str(user_id), "platform": platform})

                rows = result.fetchall()
                logging.info(f"🔍 Checking Hamming distance (threshold={threshold}) against {len(rows)} recent {platform} images")

                # Convert uploaded hash to ImageHash object
                try:
                    new_hash = imagehash.hex_to_hash(phash_hex)
                except Exception as e:
                    logging.warning(f"⚠️ Failed to convert phash to ImageHash: {e}")
                    return False, None

                # Check each existing hash
                for row in rows:
                    try:
                        existing_phash = row[0]
                        existing_filename = row[1]

                        # Skip if hash format doesn't match (16x16 = 64 hex chars)
                        if len(existing_phash) != 64:
                            continue

                        existing_hash = imagehash.hex_to_hash(existing_phash)
                        distance = new_hash - existing_hash

                        if distance <= threshold:
                            logging.info(f"🔍 Hamming check completed in {time.time() - check_start:.3f}s: DUPLICATE (distance={distance}, match={existing_filename})")
                            return True, existing_filename

                    except Exception as e:
                        logging.debug(f"Error comparing hash: {e}")
                        continue

                logging.info(f"🔍 Hamming check completed in {time.time() - check_start:.3f}s: UNIQUE")
                return False, None

            except Exception as e:
                logging.error(f"❌ Error checking Hamming distance: {e}")
                return False, None

        async def resize_and_hash_digital(file):
            """Resize digital image and calculate hashes (before duplicate check) - no upload yet"""
            import time
            start_time = time.time()

            try:
                # Read the image file content
                logging.info(f"📥 Resizing and hashing digital: {file.filename}")
                contents = await file.read()
                await file.seek(0)  # Reset for later use

                nparr = np.frombuffer(contents, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

                if image is None:
                    logging.error("❌ Failed to decode image")
                    return None

                # Crop transparent areas
                crop_start = time.time()
                cropped_image = crop_transparent(image=image)
                if cropped_image is None:
                    logging.error("❌ Failed to crop image")
                    return None
                logging.info(f"✂️ Cropped in {time.time() - crop_start:.2f}s")

                # Get DPI and handle 16-bit images
                target_dpi = get_dpi_from_image(image)
                if cropped_image.dtype == np.uint16:
                    cropped_image = (cropped_image / 256).astype(np.uint8)

                # Calculate dimensions and resize
                resize_start = time.time()
                current_width_inches, current_height_inches = get_width_and_height(cropped_image, target_dpi[0])
                resized_image = cv2.resize(
                    cropped_image,
                    (
                        inches_to_pixels(current_width_inches, target_dpi[0]),
                        inches_to_pixels(current_height_inches, target_dpi[1])
                    ),
                    interpolation=cv2.INTER_CUBIC
                )
                logging.info(f"📐 Resized in {time.time() - resize_start:.2f}s")

                # Convert to PIL for hashing
                hash_start = time.time()
                if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                    img_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGRA2RGB)
                elif len(resized_image.shape) == 3:
                    img_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
                else:
                    img_rgb = resized_image

                pil_img = Image.fromarray(img_rgb)
                pil_img_normalized = pil_img.resize((256, 256), Image.Resampling.LANCZOS)

                # Calculate all 4 hash types
                phash = str(imagehash.phash(pil_img_normalized, hash_size=16))
                ahash = str(imagehash.average_hash(pil_img_normalized, hash_size=16))
                dhash = str(imagehash.dhash(pil_img_normalized, hash_size=16))
                whash = str(imagehash.whash(pil_img_normalized, hash_size=16))

                logging.info(f"🔐 Generated hashes in {time.time() - hash_start:.2f}s: phash={phash[:8]}...")

                # Store resized image for later upload (if not duplicate)
                total_time = time.time() - start_time
                logging.info(f"✅ Resize & hash completed in {total_time:.2f}s")

                return {
                    'resized_image': resized_image,
                    'phash': phash,
                    'ahash': ahash,
                    'dhash': dhash,
                    'whash': whash,
                    'original_filename': file.filename
                }

            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error(f"❌ Error resizing/hashing digital image: {str(e)}")
                return None

        async def upload_processed_image_digital(processed_data, index, id_number):
            """Upload previously resized digital image to NAS with generated filename"""
            import time
            upload_start = time.time()

            try:
                resized_image = processed_data['resized_image']

                # Generate filename
                digital_id_number = str(index + id_number).zfill(3)
                filename = f"Digital {digital_id_number}.png"

                logging.info(f"📤 Uploading to NAS: {filename}")

                # Encode to bytes with DPI metadata
                encode_start = time.time()

                # Convert OpenCV image to PIL for proper DPI metadata
                # CRITICAL: Ensure images are saved with 400 DPI for consistency
                if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                    # BGRA to RGBA
                    pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGRA2RGBA))
                elif len(resized_image.shape) == 3 and resized_image.shape[2] == 3:
                    # BGR to RGB
                    pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))
                else:
                    # Grayscale
                    pil_image = Image.fromarray(resized_image)

                # Save with DPI metadata
                from io import BytesIO
                buffer = BytesIO()
                pil_image.save(buffer, format='PNG', optimize=True, compress_level=3, dpi=(400, 400))
                image_bytes = buffer.getvalue()
                logging.info(f"💾 Encoded in {time.time() - encode_start:.2f}s ({len(image_bytes) / 1024 / 1024:.2f}MB) with DPI: 400x400")

                # Upload to NAS
                nas_start = time.time()
                relative_path = f"Digital/{template.name}/{filename}"
                success = nas_storage.upload_file_content(
                    file_content=image_bytes,
                    shop_name=etsy_shop_name,
                    relative_path=relative_path
                )
                if success:
                    logging.info(f"✅ Uploaded to NAS in {time.time() - nas_start:.2f}s: {relative_path}")
                else:
                    logging.warning(f"⚠️ Failed to upload to NAS: {relative_path}")
                    return None, None, None

                total_time = time.time() - upload_start
                logging.info(f"✅ Upload completed in {total_time:.2f}s")

                return filename, relative_path, image_bytes

            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error(f"❌ Error uploading digital image: {str(e)}")
                return None, None, None
        
        # Step 1: Resize and hash all images first
        if progress_callback:
            progress_callback(0, "Resizing and hashing images")

        logging.info(f"📦 Starting optimized workflow for {len(files)} files (≤2 images)")

        processed_images = []  # Store {file, processed_data} for non-duplicates

        for i, file in enumerate(files):
            import time
            step_start = time.time()
            logging.info(f"📦 [{i+1}/{len(files)}] Processing: {file.filename}")

            # Resize and hash (appropriate for digital vs physical)
            if design_data.is_digital:
                processed_data = await resize_and_hash_digital(file)
            else:
                processed_data = await resize_and_hash_physical(file)

            if not processed_data:
                logging.error(f"❌ Failed to resize/hash: {file.filename}")
                continue

            logging.info(f"✅ Processed {file.filename} in {time.time() - step_start:.2f}s")
            processed_images.append({'file': file, 'data': processed_data})

        # Step 2: Check for duplicates using the hashes from resized images
        if progress_callback:
            progress_callback(0, "Checking for duplicates using database indexes")

        logging.info(f"🔍 Checking {len(processed_images)} processed images for duplicates")

        non_duplicate_images = []
        duplicate_count = 0
        checked_hashes = {}  # Track {phash: filename} for batch duplicate detection

        for i, item in enumerate(processed_images):
            import time
            check_start = time.time()

            file = item['file']
            data = item['data']
            phash = data['phash']
            ahash = data['ahash']
            dhash = data['dhash']
            whash = data['whash']

            logging.info(f"🔍 [{i+1}/{len(processed_images)}] Checking for duplicates: {file.filename}")

            is_duplicate = False
            duplicate_source = None

            # 1. Check against other images in this batch first (fastest)
            batch_threshold = int(os.getenv('DUPLICATE_HAMMING_THRESHOLD', '15'))
            for other_phash, other_filename in checked_hashes.items():
                try:
                    hash_obj = imagehash.hex_to_hash(phash)
                    other_hash_obj = imagehash.hex_to_hash(other_phash)
                    distance = hash_obj - other_hash_obj
                    if distance <= batch_threshold:
                        logging.warning(f"⚠️ Duplicate within batch: {file.filename} matches {other_filename} (distance: {distance}, threshold: {batch_threshold})")
                        duplicate_count += 1
                        is_duplicate = True
                        duplicate_source = f"batch file {other_filename}"
                        break
                except Exception as e:
                    logging.debug(f"Error comparing batch hash: {e}")

            # 2. Check exact match in database using phash (O(log n) indexed query)
            if not is_duplicate:
                if check_duplicate_in_database(phash, platform=design_data.platform):
                    logging.warning(f"⚠️ Duplicate in database (exact match): {file.filename}")
                    duplicate_count += 1
                    is_duplicate = True
                    duplicate_source = "database (exact phash match)"

            # 3. Check Hamming distance against recent 1000 images
            if not is_duplicate:
                # Use configurable threshold (default 15, was 5 which was too strict)
                hamming_threshold = int(os.getenv('DUPLICATE_HAMMING_THRESHOLD', '15'))
                is_similar, similar_filename = check_hamming_distance_in_database(phash, platform=design_data.platform, threshold=hamming_threshold)
                if is_similar:
                    logging.warning(f"⚠️ Duplicate in database (similar): {file.filename} matches {similar_filename}")
                    duplicate_count += 1
                    is_duplicate = True
                    duplicate_source = f"database (similar to {similar_filename})"

            if not is_duplicate:
                non_duplicate_images.append(item)
                checked_hashes[phash] = file.filename
                check_time = time.time() - check_start
                logging.info(f"✅ {file.filename} is unique (checked in {check_time:.3f}s)")
            else:
                check_time = time.time() - check_start
                logging.info(f"⚠️ {file.filename} is duplicate of {duplicate_source} (checked in {check_time:.3f}s)")

        design_results = []

        # Step 3: Upload only non-duplicate images and save to database
        if progress_callback:
            progress_callback(1, f"Uploading {len(non_duplicate_images)} unique images to NAS")

        logging.info(f"📤 Uploading {len(non_duplicate_images)} unique images to NAS")

        for i, item in enumerate(non_duplicate_images):
            if progress_callback:
                progress_callback(1, f"Uploading images to NAS ({i+1}/{len(non_duplicate_images)})")

            file = item['file']
            data = item['data']

            logging.info(f"📤 [{i+1}/{len(non_duplicate_images)}] Uploading: {file.filename}")

            # Upload image (returns filename, nas_relative_path, image_bytes)
            if design_data.is_digital:
                filename, nas_relative_path, image_bytes = await upload_processed_image_digital(data, i, design_data.starting_name)
            else:
                filename, nas_relative_path, image_bytes = await upload_processed_image_physical(data, i, design_data.starting_name)

            if not filename or not nas_relative_path:
                logging.error(f"❌ Failed to upload image for user ID: {user_id}")
                raise DesignCreateError()

            logging.info(f"✅ Uploaded: {filename} to NAS path: {nas_relative_path}")

            # Use pre-calculated hashes from resize step
            phash = data['phash']
            ahash = data['ahash']
            dhash = data['dhash']
            whash = data['whash']

            logging.info(f"🔐 Using hashes: phash={phash[:8]}..., ahash={ahash[:8]}..., dhash={dhash[:8]}..., whash={whash[:8]}...")

            # Build NAS file path for storage (matching nas_storage.upload_file_content format)
            # nas_storage.base_path = "/share/Graphics"
            # upload_file_content builds: {base_path}/{shop_name}/{relative_path}
            # So actual path is: /share/Graphics/{etsy_shop_name}/{nas_relative_path}
            # Get Etsy shop name for this user
            etsy_shop_name = get_etsy_shop_name(db, user_id)
            nas_file_path = f"/share/Graphics/{etsy_shop_name}/{nas_relative_path}"

            design = DesignImages(
                user_id=user_id,
                filename=filename,
                file_path=nas_file_path,  # Store full NAS path
                description=design_data.description,
                phash=phash,
                ahash=ahash,
                dhash=dhash,
                whash=whash,
                canvas_config_id=design_data.canvas_config_id,
                platform=design_data.platform,  # Set platform (etsy or shopify)
                is_active=design_data.is_active
            )
            design_results.append(design)
            db.add(design)
            logging.info(f"✅ Added design to database: {filename}")
        
        db.commit()

        if duplicate_count > 0:
            logging.info(f"⚠️ Skipped {duplicate_count} duplicate designs out of {len(files)} total files")

        # Check if all images were duplicates
        if len(design_results) == 0 and len(files) > 0:
            logging.warning(f"⚠️ All {len(files)} uploaded images were duplicates - no new designs created")

        response = model.DesignImageListResponse(
            designs=[model.DesignImageResponse.model_validate(design) for design in design_results],
            total=len(design_results)
        )

        if len(design_results) > 0:
            logging.info(f"✅ Successfully created {len(design_results)} designs for user: {user_id}")
        logging.info(f"📊 Summary: {len(files)} uploaded, {duplicate_count} duplicates skipped, {len(design_results)} created")

        # Invalidate user cache after creating designs
        try:
            import asyncio
            asyncio.create_task(invalidate_user_cache(str(user_id)))
        except Exception as cache_error:
            logging.warning(f"Failed to invalidate cache for user {user_id}: {cache_error}")

        return response
    except Exception as e:
        logging.error(f"Error creating design for user ID: {user_id}. Error: {e}")
        db.rollback()
        raise DesignCreateError()


@railway_cached(expire_seconds=300, key_prefix="designs")
def get_designs_by_user_id(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> model.DesignImageListResponse:
    try:
        designs = db.query(DesignImages).filter(
            DesignImages.user_id == user_id,
            DesignImages.is_active == True
        ).offset(skip).limit(limit).all()

        total = db.query(DesignImages).filter(
            DesignImages.user_id == user_id,
            DesignImages.is_active == True
        ).count()

        logging.info(f"Successfully retrieved {len(designs)} designs for user: {user_id} (cached)")
        # Convert SQLAlchemy objects to Pydantic models
        design_responses = [model.DesignImageResponse.model_validate(design) for design in designs]
        return model.DesignImageListResponse(designs=design_responses, total=total)
    except Exception as e:
        logging.error(f"Error getting designs for user ID: {user_id}. Error: {e}")
        raise DesignGetAllError()


@railway_cached(expire_seconds=600, key_prefix="design")
def get_design_by_id(db: Session, design_id: UUID, user_id: UUID) -> model.DesignImageResponse:
    try:
        design = db.query(DesignImages).filter(
            DesignImages.id == design_id,
            DesignImages.user_id == user_id
        ).first()

        if not design:
            logging.warning(f"Design not found with ID: {design_id} for user: {user_id}")
            raise DesignNotFoundError(design_id)
        
        logging.info(f"Successfully retrieved design with ID: {design_id}")
        return design
    except Exception as e:
        if isinstance(e, DesignNotFoundError):
            raise e
        logging.error(f"Error getting design with ID: {design_id}. Error: {e}")
        raise DesignGetByIdError(design_id)


def update_design(db: Session, design_id: UUID, user_id: UUID, design_data: model.DesignImageUpdate) -> model.DesignImageResponse:
    try:
        design = db.query(DesignImages).filter(
            DesignImages.id == design_id,
            DesignImages.user_id == user_id
        ).first()
        
        if not design:
            logging.warning(f"Design not found with ID: {design_id} for user: {user_id}")
            raise DesignNotFoundError(design_id)
        
        # Validate canvas config if provided
        if design_data.canvas_config_id is not None:
            if not _validate_canvas_config(db, user_id, design_data.canvas_config_id):
                logging.warning(f"Invalid canvas config ID: {design_data.canvas_config_id} for user: {user_id}")
                raise DesignUpdateError(design_id)
        
        # Validate size config if provided
        if design_data.size_config_id is not None:
            canvas_config_id = design_data.canvas_config_id if design_data.canvas_config_id is not None else getattr(design, 'canvas_config_id', None)
            if not _validate_size_config(db, user_id, design_data.size_config_id, canvas_config_id):
                logging.warning(f"Invalid size config ID: {design_data.size_config_id} for user: {user_id}")
                raise DesignUpdateError(design_id)
        
        # Update only provided fields
        update_data = design_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(design, field, value)
        
        db.commit()
        db.refresh(design)
        
        logging.info(f"Successfully updated design with ID: {design_id}")
        return design
    except Exception as e:
        if isinstance(e, DesignNotFoundError):
            raise e
        logging.error(f"Error updating design with ID: {design_id}. Error: {e}")
        db.rollback()
        raise DesignUpdateError(design_id)


def delete_design(db: Session, design_id: UUID, user_id: UUID) -> None:
    try:
        design = db.query(DesignImages).filter(
            DesignImages.id == design_id,
            DesignImages.user_id == user_id
        ).first()
        
        if not design:
            logging.warning(f"Design not found with ID: {design_id} for user: {user_id}")
            raise DesignNotFoundError(design_id)
        
        # Soft delete by setting is_active to False
        setattr(design, 'is_active', False)
        db.commit()
        
        logging.info(f"Successfully deleted design with ID: {design_id}")
    except Exception as e:
        if isinstance(e, DesignNotFoundError):
            raise e
        logging.error(f"Error deleting design with ID: {design_id}. Error: {e}")
        db.rollback()
        raise DesignDeleteError(design_id)


async def get_design_gallery_data(db: Session, user_id: UUID) -> model.DesignGalleryResponse:
    """Get design gallery data including Etsy mockups and QNAP design files"""
    try:
        logging.info(f"Starting gallery data fetch for user {user_id}")

        # Get user and shop info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logging.error(f"User not found with ID: {user_id}")
            raise InvalidUserToken()

        # Get Etsy shop name from etsy_stores table
        etsy_shop_name = get_etsy_shop_name(db, user_id)

        logging.info(f"Found user with Etsy shop: {etsy_shop_name}")

        mockups = []
        design_files = []

        # Fetch Etsy mockups (product listing images)
        try:
            from server.src.utils.etsy_api_engine import EtsyAPI
            logging.info("Initializing Etsy API...")
            etsy_api = EtsyAPI(user_id, db)

            if etsy_api:
                logging.info("Etsy API initialized successfully")
                # Check if we have valid tokens
                if hasattr(etsy_api, 'oauth_token') and etsy_api.oauth_token:
                    logging.info("Etsy OAuth token found")
                    # TODO: Implement get_all_active_listings_images method in EtsyAPI
                    # For now, skip Etsy listings integration
                    logging.info("Etsy listings integration temporarily disabled - method not implemented")
                    etsy_listings = []

                    if etsy_listings and isinstance(etsy_listings, list):
                        logging.info("Processing Etsy listings...")
                        for i, listing in enumerate(etsy_listings):
                            logging.info(f"Processing listing {i+1}: {type(listing)}")
                            if isinstance(listing, dict):
                                listing_id = listing.get('listing_id', '')
                                listing_title = listing.get('title', 'Untitled')
                                images = listing.get('images', [])
                                logging.info(f"Listing {listing_id} has {len(images)} images")

                                if 'images' in listing:
                                    for j, image in enumerate(listing.get('images', [])):
                                        if isinstance(image, dict):
                                            image_id = image.get('image_id', '')
                                            image_url = image.get('url_fullxfull', '')
                                            logging.info(f"Image {j+1}: ID={image_id}, URL={image_url[:100] if image_url else 'None'}...")

                                            if image_url:  # Only add if we have a valid image URL
                                                mockups.append(model.EtsyMockupImage(
                                                    filename=f"{listing_title[:30]}_{listing_id}_{image_id}.jpg",
                                                    url=image_url,
                                                    path=image_url,  # For frontend compatibility
                                                    etsy_listing_id=str(listing_id),
                                                    image_id=str(image_id)
                                                ))
                                                logging.info(f"Added mockup: {listing_title[:30]}_{listing_id}_{image_id}.jpg")
                    else:
                        logging.warning(f"Etsy listings is not a valid list: {etsy_listings}")
                else:
                    logging.warning("No Etsy OAuth token found")
            else:
                logging.warning("Failed to initialize Etsy API")

        except Exception as e:
            logging.warning(f"Failed to fetch Etsy mockups for user {user_id}: {e}")
            import traceback
            logging.error(f"Etsy mockup error traceback: {traceback.format_exc()}")

        # Fetch design files from QNAP NAS based on templates
        try:
            from server.src.utils.nas_storage import nas_storage
            logging.info(f"NAS storage enabled: {nas_storage.enabled}")

            # Get user's product templates
            logging.info("Querying user product templates...")
            # Handle both multi-tenant and single-tenant scenarios
            template_query = db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id
            )

            # Add org_id filter if multi-tenant is enabled and user has an org_id
            if hasattr(user, 'org_id') and user.org_id:
                logging.info(f"User has org_id: {user.org_id}")
                template_query = template_query.filter(EtsyProductTemplate.org_id == user.org_id)
            else:
                logging.info("User has no org_id, using only user_id filter")

            templates = template_query.all()
            logging.info(f"Found {len(templates)} templates for user {user_id}")

            # Log template details
            for template in templates:
                logging.info(f"Template: {template.name} (ID: {template.id})")

            # If no templates found, let's check what's in the database
            if len(templates) == 0:
                all_templates = db.query(EtsyProductTemplate).all()
                logging.info(f"Total templates in database: {len(all_templates)}")
                for template in all_templates[:5]:  # Show first 5
                    logging.info(f"DB Template: {template.name} (User: {template.user_id}, Org: {getattr(template, 'org_id', 'N/A')})")

                # Check user's org_id
                logging.info(f"User org_id: {getattr(user, 'org_id', 'N/A')}")
                logging.info(f"User attributes: {[attr for attr in dir(user) if not attr.startswith('_')]}")

            if nas_storage.enabled and etsy_shop_name:
                logging.info(f"NAS storage enabled, fetching design files for shop: {etsy_shop_name}")
                for template in templates:
                    template_name = template.name
                    logging.info(f"Processing template: {template_name}")
                    # List files from both regular and digital template paths
                    template_paths = [template_name, f"Digital/{template_name}"]

                    for template_path in template_paths:
                        try:
                            logging.info(f"Checking NAS path: {etsy_shop_name}/{template_path}")
                            # List files from NAS
                            file_list = nas_storage.list_files(etsy_shop_name, template_path)
                            logging.info(f"NAS returned {len(file_list) if file_list else 0} items for path {template_path}")

                            if file_list:
                                logging.info(f"Files in {template_path}: {[f.get('filename', 'unnamed') if isinstance(f, dict) else str(f) for f in file_list[:5]]}...")
                                for file_info in file_list:
                                    if isinstance(file_info, dict):
                                        filename = file_info.get('filename', '')
                                        file_size = file_info.get('size', 0)
                                        logging.info(f"Checking file: {filename} (size: {file_size})")
                                        # Filter for image files
                                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                                            design_file = model.DesignFile(
                                                filename=filename,
                                                path=f"/api/designs/nas-file/{etsy_shop_name}/{template_path}/{filename}",  # Use API endpoint as path
                                                url=f"/api/designs/nas-file/{etsy_shop_name}/{template_path}/{filename}",  # Download endpoint
                                                template_name=template_name,
                                                nas_path=f"{template_path}/{filename}",
                                                file_size=file_info.get('size'),
                                                last_modified=file_info.get('modified')
                                            )
                                            design_files.append(design_file)
                                            logging.info(f"Added design file: {filename} from template {template_name}")
                                        else:
                                            logging.info(f"Skipped non-image file: {filename}")
                                    else:
                                        logging.warning(f"File info is not a dict: {type(file_info)} - {file_info}")
                            else:
                                logging.info(f"No files found in {template_path}")
                        except Exception as e:
                            logging.warning(f"Failed to list files from NAS path {template_path}: {e}")
                            import traceback
                            logging.error(f"NAS path error traceback: {traceback.format_exc()}")
            else:
                logging.info(f"NAS conditions not met. NAS enabled: {nas_storage.enabled}, Shop name: '{etsy_shop_name}'")

        except Exception as e:
            logging.warning(f"Failed to fetch design files from NAS for user {user_id}: {e}")
            import traceback
            logging.error(f"NAS design files error traceback: {traceback.format_exc()}")

        logging.info(f"Gallery data fetch complete: {len(mockups)} mockups, {len(design_files)} design files")

        return model.DesignGalleryResponse(
            mockups=mockups,
            files=design_files,
            total_mockups=len(mockups),
            total_files=len(design_files)
        )

    except Exception as e:
        logging.error(f"Error fetching design gallery data for user {user_id}: {e}")
        import traceback
        logging.error(f"Gallery error traceback: {traceback.format_exc()}")
        raise DesignGetAllError()


def get_user_by_id(db: Session, user_id: UUID) -> User:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()
