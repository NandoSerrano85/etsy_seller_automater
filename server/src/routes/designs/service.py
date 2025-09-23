from server.src.entities.designs import DesignImages
from server.src.entities.canvas_config import CanvasConfig
from server.src.entities.size_config import SizeConfig
from server.src.entities.template import EtsyProductTemplate
from server.src.entities.user import User
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

def calculate_phash(image_path: str, hash_size: int = 16) -> str:
    """
    Calculate perceptual hash for an image file.

    Args:
        image_path: Path to the image file
        hash_size: Hash size for the perceptual hash

    Returns:
        String representation of the hash
    """
    try:
        with Image.open(image_path) as img:
            phash = imagehash.phash(img, hash_size=hash_size)
            return str(phash)
    except Exception as e:
        logging.error(f"Error calculating phash for {image_path}: {e}")
        return None

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


async def create_design(db: Session, user_id: UUID, design_data: model.DesignImageCreate, files: List[UploadFile], progress_callback=None) -> model.DesignImageListResponse:
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

        type_pattern = r"UV\s*DTF|UV"
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        if design_data.is_digital:
            designs_path = f"{local_root_path}{user.shop_name}/Digital/{template.name}/"
        else:
            designs_path = f"{local_root_path}{user.shop_name}/{template.name}/"
        os.makedirs(designs_path, exist_ok=True)
        
        async def process_image_physical(n, file, id_number):
            try:
                # Read the image file content
                contents = await file.read()
                nparr = np.frombuffer(contents, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                
                if image is None:
                    logging.error("Failed to decode image")
                    return None, None
                    
                # Crop transparent areas
                cropped_image = crop_transparent(image=image)
                if cropped_image is None:
                    logging.error("Failed to crop image")
                    return None, None
                    
                # Resize image
                resized_image = resize_image_by_inches(
                    image=cropped_image,
                    image_type=template.name,
                    db=db,
                    canvas_id=design_data.canvas_config_id,
                    product_template_id=design_data.product_template_id
                )
                
                # Generate filename
                current_id_number = str(n + id_number).zfill(3)
                prefix = "UV" if re.search(type_pattern, template.name) else "DTF"
                postfix = "_".join(str(template.name).split() + [current_id_number])
                filename = f"{prefix} {current_id_number} {postfix}.png"
                image_path = os.path.join(designs_path, filename)
                
                # Save the processed image
                save_single_image(resized_image, designs_path, filename, target_dpi=(400, 400))
                
                # Upload design to NAS
                try:
                    relative_path = f"{template.name}/{filename}" if not design_data.is_digital else f"Digital/{template.name}/{filename}"
                    success = nas_storage.upload_file(
                        local_file_path=image_path,
                        shop_name=user.shop_name,
                        relative_path=relative_path
                    )
                    if success:
                        logging.info(f"Successfully uploaded design to NAS: {relative_path}")
                    else:
                        logging.warning(f"Failed to upload design to NAS: {relative_path}")
                except Exception as e:
                    logging.error(f"Error uploading design to NAS: {e}")
                    # Don't fail the entire process if NAS upload fails
                
                # Reset file pointer
                await file.seek(0)
                
                return image_path, filename
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error(f"Error processing physical image: {str(e)}")
                return None, None

        def list_images_in_dir(directory_path):
            """List all image files in a directory"""
            try:
                if not os.path.exists(directory_path):
                    return []
                image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
                return [f for f in os.listdir(directory_path) 
                       if any(f.lower().endswith(ext) for ext in image_extensions)]
            except Exception as e:
                logging.error(f"Error listing images in directory {directory_path}: {str(e)}")
                return []
        
        def build_hash_db(directory_path):
            """Build a database of image hashes from a directory with size/DPI normalization"""
            hash_db = {}
            try:
                image_files = list_images_in_dir(directory_path)
                for image_file in image_files:
                    image_path = os.path.join(directory_path, image_file)
                    try:
                        with Image.open(image_path) as img:
                            # Resize to standard size for consistent comparison regardless of original size/DPI
                            img_normalized = img.resize((256, 256), Image.Resampling.LANCZOS)
                            img_hash = imagehash.phash(img_normalized, hash_size=16)  # Use consistent hash size
                            hash_db[image_path] = img_hash
                    except Exception as e:
                        logging.error(f"Error processing image {image_path}: {str(e)}")
                        continue
            except Exception as e:
                logging.error(f"Error building hash database for {directory_path}: {str(e)}")
            return hash_db
        
        def check_for_duplicate(new_image_path, existing_hash_db, threshold=5):
            """Check if a new image is a duplicate of any existing images with size/DPI normalization"""
            try:
                with Image.open(new_image_path) as new_img:
                    # Resize to standard size for consistent comparison regardless of original size/DPI
                    new_img_normalized = new_img.resize((256, 256), Image.Resampling.LANCZOS)
                    new_hash = imagehash.phash(new_img_normalized)

                    for existing_path, existing_hash in existing_hash_db.items():
                        hash_diff = new_hash - existing_hash
                        if hash_diff <= threshold:
                            return existing_path
                    return None
            except Exception as e:
                logging.error(f"Error checking duplicate for {new_image_path}: {str(e)}")
                return None

        async def process_image_digital(n, file, id_number):
            """Process digital product images"""
            try:
                # Read the image file content
                contents = await file.read()
                nparr = np.frombuffer(contents, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                
                if image is None:
                    logging.error("Failed to decode image")
                    return None, None
                    
                # Crop transparent areas
                cropped_image = crop_transparent(image=image)
                if cropped_image is None:
                    logging.error("Failed to crop image")
                    return None, None
                    
                # Get DPI and handle 16-bit images
                target_dpi = get_dpi_from_image(image)
                if cropped_image.dtype == np.uint16:
                    cropped_image = (cropped_image / 256).astype(np.uint8)

                # Calculate dimensions and resize
                current_width_inches, current_height_inches = get_width_and_height(cropped_image, target_dpi[0])
                resized_image = cv2.resize(
                    cropped_image, 
                    (
                        inches_to_pixels(current_width_inches, target_dpi[0]),
                        inches_to_pixels(current_height_inches, target_dpi[1])
                    ),
                    interpolation=cv2.INTER_CUBIC
                )
                
                # Generate filename
                digital_id_number = str(n + id_number).zfill(3)
                filename = f"Digital {digital_id_number}.png"
                image_path = os.path.join(designs_path, filename)
                
                # Save the processed image
                save_single_image(resized_image, designs_path, filename, target_dpi=target_dpi)
                
                # Upload design to NAS
                try:
                    relative_path = f"Digital/{template.name}/{filename}"
                    success = nas_storage.upload_file(
                        local_file_path=image_path,
                        shop_name=user.shop_name,
                        relative_path=relative_path
                    )
                    if success:
                        logging.info(f"Successfully uploaded digital design to NAS: {relative_path}")
                    else:
                        logging.warning(f"Failed to upload digital design to NAS: {relative_path}")
                except Exception as e:
                    logging.error(f"Error uploading digital design to NAS: {e}")
                    # Don't fail the entire process if NAS upload fails
                
                # Reset file pointer
                await file.seek(0)
                
                return image_path, filename
        
            except Exception as e:
                logging.error(f"Error processing digital image: {str(e)}")
                return None, None
        
        # Step 1: Check for duplicates before any processing
        if progress_callback:
            progress_callback(0, "Checking for duplicates")

        # Build comprehensive hash database from multiple sources
        existing_hash_db = {}

        # 1. Build hash from local directory files (if exists)
        if os.path.exists(designs_path):
            local_hash_db = build_hash_db(designs_path)
            existing_hash_db.update(local_hash_db)
            logging.info(f"Found {len(local_hash_db)} existing local files")

        # 2. Build hash from NAS files for this template
        nas_hash_db = {}
        try:
            if nas_storage.enabled:
                # Get files from NAS for this specific template path
                template_relative_path = f"Digital/{template.name}" if design_data.is_digital else template.name
                nas_files = nas_storage.list_files(user.shop_name, template_relative_path)

                if nas_files:
                    logging.info(f"Found {len(nas_files)} files in NAS for template {template.name}")
                    for file_info in nas_files:
                        if isinstance(file_info, dict):
                            filename = file_info.get('filename', '')
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                                # Download file content from NAS for hashing
                                try:
                                    file_content = nas_storage.download_file_to_memory(user.shop_name, f"{template_relative_path}/{filename}")
                                    if file_content:
                                        # Create hash from NAS file content without DPI/size dependency
                                        nparr = np.frombuffer(file_content, np.uint8)
                                        nas_image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                                        if nas_image is not None:
                                            # Normalize image for consistent hashing regardless of size/DPI
                                            if len(nas_image.shape) == 3 and nas_image.shape[2] == 4:
                                                # Convert BGRA to RGB for PIL
                                                nas_image_rgb = cv2.cvtColor(nas_image, cv2.COLOR_BGRA2RGB)
                                            elif len(nas_image.shape) == 3:
                                                # Convert BGR to RGB for PIL
                                                nas_image_rgb = cv2.cvtColor(nas_image, cv2.COLOR_BGR2RGB)
                                            else:
                                                nas_image_rgb = nas_image

                                            pil_image = Image.fromarray(nas_image_rgb)
                                            # Resize to standard size for consistent comparison regardless of original size/DPI
                                            pil_image = pil_image.resize((256, 256), Image.Resampling.LANCZOS)
                                            nas_hash = imagehash.phash(pil_image, hash_size=16)
                                            nas_path = f"NAS:{user.shop_name}/{template_relative_path}/{filename}"
                                            nas_hash_db[nas_path] = nas_hash
                                            logging.info(f"Added NAS file to hash db: {filename}")
                                except Exception as e:
                                    logging.warning(f"Failed to hash NAS file {filename}: {e}")
                                    continue

                existing_hash_db.update(nas_hash_db)
                logging.info(f"Added {len(nas_hash_db)} NAS files to hash database")
        except Exception as e:
            logging.warning(f"Failed to check NAS files for duplicates: {e}")

        logging.info(f"Total files in hash database: {len(existing_hash_db)}")

        # Get existing phashes from database for this user
        from server.src.entities.designs import DesignImages
        from sqlalchemy import and_

        existing_designs = db.query(DesignImages).filter(
            and_(
                DesignImages.user_id == user_id,
                DesignImages.is_active == True,
                DesignImages.phash.isnot(None)
            )
        ).all()

        # Create database phash lookup
        db_phashes = {}
        for design in existing_designs:
            try:
                # Convert string phash back to ImageHash object for comparison
                phash_obj = imagehash.hex_to_hash(design.phash)

                # Check if this is an 8x8 hash (64 characters) vs 16x16 hash (256 characters)
                if len(design.phash) == 16:  # 8x8 hash (64 bits = 16 hex chars)
                    logging.info(f"Skipping 8x8 phash for design {design.filename} - will be recalculated with 16x16")
                    continue
                elif len(design.phash) == 64:  # 16x16 hash (256 bits = 64 hex chars)
                    db_phashes[phash_obj] = design
                else:
                    logging.warning(f"Unexpected phash length {len(design.phash)} for design {design.id}")
                    continue

            except Exception as e:
                logging.warning(f"Invalid phash in database for design {design.id}: {e}")
                continue

        logging.info(f"Found {len(existing_hash_db)} existing files in directory and {len(db_phashes)} designs with phashes in database")

        # Check for duplicates in uploaded files before processing
        non_duplicate_files = []
        duplicate_count = 0

        for i, file in enumerate(files):
            logging.info(f"Checking file for duplicates: {file.filename}")

            # Read file content to create hash
            contents = await file.read()
            await file.seek(0)  # Reset file pointer for later use

            # Create hash from uploaded content
            try:
                nparr = np.frombuffer(contents, np.uint8)
                temp_image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

                if temp_image is not None:
                    # Normalize image for consistent hashing regardless of size/DPI
                    if len(temp_image.shape) == 3 and temp_image.shape[2] == 4:
                        # Convert BGRA to RGB for PIL
                        temp_image_rgb = cv2.cvtColor(temp_image, cv2.COLOR_BGRA2RGB)
                    elif len(temp_image.shape) == 3:
                        # Convert BGR to RGB for PIL
                        temp_image_rgb = cv2.cvtColor(temp_image, cv2.COLOR_BGR2RGB)
                    else:
                        temp_image_rgb = temp_image

                    pil_image = Image.fromarray(temp_image_rgb)
                    # Resize to standard size for consistent comparison regardless of original size/DPI
                    pil_image = pil_image.resize((256, 256), Image.Resampling.LANCZOS)

                    # Calculate hash
                    file_hash = imagehash.phash(pil_image, hash_size=16)

                    # Check against existing hashes (local files)
                    is_duplicate = False
                    duplicate_source = None

                    for existing_path, existing_hash in existing_hash_db.items():
                        hash_diff = file_hash - existing_hash
                        if hash_diff <= 5:  # threshold
                            if existing_path.startswith("NAS:"):
                                logging.warning(f"Skipping duplicate file: {file.filename} (matches NAS file {existing_path.split('/')[-1]}, hash distance: {hash_diff})")
                                duplicate_source = f"NAS file {existing_path.split('/')[-1]}"
                            else:
                                logging.warning(f"Skipping duplicate file: {file.filename} (matches local file {os.path.basename(existing_path)}, hash distance: {hash_diff})")
                                duplicate_source = f"local file {os.path.basename(existing_path)}"
                            duplicate_count += 1
                            is_duplicate = True
                            break

                    # Check against database phashes
                    if not is_duplicate:
                        for existing_phash, existing_design in db_phashes.items():
                            hash_diff = abs(file_hash - existing_phash)
                            if hash_diff <= 5:  # threshold
                                logging.warning(f"Skipping duplicate file: {file.filename} (matches database design {existing_design.filename}, distance: {hash_diff})")
                                duplicate_count += 1
                                is_duplicate = True
                                duplicate_source = f"database design {existing_design.filename}"
                                break

                    if not is_duplicate:
                        # Check against other uploaded files to avoid processing duplicates within the same upload
                        for j, (other_file, other_hash) in enumerate(non_duplicate_files):
                            if other_hash is not None:
                                hash_diff = file_hash - other_hash
                                if hash_diff <= 5:  # threshold
                                    logging.warning(f"Skipping duplicate file within upload: {file.filename} (matches {other_file.filename})")
                                    duplicate_count += 1
                                    is_duplicate = True
                                    duplicate_source = f"uploaded file {other_file.filename}"
                                    break

                        if not is_duplicate:
                            non_duplicate_files.append((file, file_hash))
                            existing_hash_db[f"temp_{i}"] = file_hash  # Add to prevent future duplicates in this batch
                            logging.info(f"File {file.filename} is unique, will be processed")
                    else:
                        logging.info(f"File {file.filename} is duplicate of {duplicate_source}")
                else:
                    logging.error(f"Failed to decode image for duplicate check: {file.filename}")
                    # Still process files that can't be decoded for duplicate checking
                    non_duplicate_files.append((file, None))

            except Exception as e:
                logging.error(f"Error checking duplicates for {file.filename}: {str(e)}")
                # Still process files that fail duplicate checking
                non_duplicate_files.append((file, None))

        design_results = []

        # Step 2: Process only non-duplicate files
        for i, (file, file_hash) in enumerate(non_duplicate_files):
            if progress_callback:
                progress_callback(1, f"Processing and formatting images ({i+1}/{len(non_duplicate_files)})")

            logging.info(f"Processing non-duplicate file: {file.filename}")
            if design_data.is_digital:
                file_path, filename = await process_image_digital(i, file, design_data.starting_name)
            else:
                file_path, filename = await process_image_physical(i, file, design_data.starting_name)

            logging.info(f"filename: {filename}, file_path: {file_path}, is_digital: {design_data.is_digital}")
            if not file_path or not filename:
                logging.error(f"Failed to process image for user ID: {user_id}")
                raise DesignCreateError()

            design_data.file_path = file_path
            design_data.filename = filename

            # Calculate perceptual hash for duplicate detection
            phash = calculate_phash(file_path)

            design = DesignImages(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                description=design_data.description,
                phash=phash,
                canvas_config_id=design_data.canvas_config_id,
                is_active=design_data.is_active
            )
            design_results.append(design)
            db.add(design)
        
        db.commit()
        
        if duplicate_count > 0:
            logging.info(f"Skipped {duplicate_count} duplicate designs out of {len(files)} total files")
        
        response = model.DesignImageListResponse(
            designs=[model.DesignImageResponse.model_validate(design) for design in design_results],
            total=len(design_results)
        )
        
        logging.info(f"Successfully created {len(design_results)} designs for user: {user_id}")
        return response
    except Exception as e:
        logging.error(f"Error creating design for user ID: {user_id}. Error: {e}")
        db.rollback()
        raise DesignCreateError()


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
        
        logging.info(f"Successfully retrieved {len(designs)} designs for user: {user_id}")
        # Convert SQLAlchemy objects to Pydantic models
        design_responses = [model.DesignImageResponse.model_validate(design) for design in designs]
        return model.DesignImageListResponse(designs=design_responses, total=total)
    except Exception as e:
        logging.error(f"Error getting designs for user ID: {user_id}. Error: {e}")
        raise DesignGetAllError()


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

        logging.info(f"Found user: {user.shop_name}")

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
                    # Get active listings with images
                    etsy_listings = etsy_api.get_all_active_listings_images()
                    logging.info(f"Etsy API returned: {type(etsy_listings)} with {len(etsy_listings) if etsy_listings else 0} listings")

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

            if nas_storage.enabled and user.shop_name:
                logging.info(f"NAS storage enabled, fetching design files for shop: {user.shop_name}")
                for template in templates:
                    template_name = template.name
                    logging.info(f"Processing template: {template_name}")
                    # List files from both regular and digital template paths
                    template_paths = [template_name, f"Digital/{template_name}"]

                    for template_path in template_paths:
                        try:
                            logging.info(f"Checking NAS path: {user.shop_name}/{template_path}")
                            # List files from NAS
                            file_list = nas_storage.list_files(user.shop_name, template_path)
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
                                                path=f"/api/designs/nas-file/{user.shop_name}/{template_path}/{filename}",  # Use API endpoint as path
                                                url=f"/api/designs/nas-file/{user.shop_name}/{template_path}/{filename}",  # Download endpoint
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
                logging.info(f"NAS conditions not met. NAS enabled: {nas_storage.enabled}, Shop name: '{user.shop_name}'")

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
