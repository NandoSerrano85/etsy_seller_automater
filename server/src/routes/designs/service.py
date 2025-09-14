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


async def create_design(db: Session, user_id: UUID, design_data: model.DesignImageCreate, files: List[UploadFile]) -> model.DesignImageListResponse:
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
            """Build a database of image hashes from a directory"""
            hash_db = {}
            try:
                image_files = list_images_in_dir(directory_path)
                for image_file in image_files:
                    image_path = os.path.join(directory_path, image_file)
                    try:
                        with Image.open(image_path) as img:
                            img_hash = imagehash.phash(img)
                            hash_db[image_path] = img_hash
                    except Exception as e:
                        logging.error(f"Error processing image {image_path}: {str(e)}")
                        continue
            except Exception as e:
                logging.error(f"Error building hash database for {directory_path}: {str(e)}")
            return hash_db
        
        def check_for_duplicate(new_image_path, existing_hash_db, threshold=5):
            """Check if a new image is a duplicate of any existing images"""
            try:
                with Image.open(new_image_path) as new_img:
                    new_hash = imagehash.phash(new_img)
                    
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
        
        # Build hash database of existing designs in the directory
        existing_hash_db = build_hash_db(designs_path)
        
        design_results = []
        duplicate_count = 0
        
        for i, file in enumerate(files):
            logging.info(f"Processing file: {file.filename}")
            if design_data.is_digital:
                file_path, filename = await process_image_digital(i, file, design_data.starting_name)
            else:
                file_path, filename = await process_image_physical(i, file, design_data.starting_name)
            
            logging.info(f"filename: {filename}, file_path: {file_path}, is_digital: {design_data.is_digital}")
            if not file_path or not filename:
                logging.error(f"Failed to process image for user ID: {user_id}")
                raise DesignCreateError()
            
            # Check for duplicates before storing in database
            duplicate_match = check_for_duplicate(file_path, existing_hash_db, threshold=5)
            if duplicate_match:
                logging.warning(f"Skipping duplicate image: {filename} (matches existing {os.path.basename(duplicate_match)})")
                # Remove the processed duplicate file
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error removing duplicate file {file_path}: {str(e)}")
                duplicate_count += 1
                continue
            
            # Add the new image hash to the database for subsequent duplicate checks
            try:
                with Image.open(file_path) as img:
                    img_hash = imagehash.phash(img)
                    existing_hash_db[file_path] = img_hash
            except Exception as e:
                logging.error(f"Error adding hash to database for {file_path}: {str(e)}")
            
            design_data.file_path = file_path
            design_data.filename = filename
            design = DesignImages(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                description=design_data.description,
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

        # Return test data to verify frontend display
        test_mockups = [
            model.EtsyMockupImage(
                filename="test_listing_123_image_1.jpg",
                url="https://via.placeholder.com/400x400/FF6B6B/ffffff?text=Etsy+Mockup+1",
                path="https://via.placeholder.com/400x400/FF6B6B/ffffff?text=Etsy+Mockup+1",
                etsy_listing_id="123",
                image_id="1"
            ),
            model.EtsyMockupImage(
                filename="test_listing_456_image_2.jpg",
                url="https://via.placeholder.com/400x400/4ECDC4/ffffff?text=Etsy+Mockup+2",
                path="https://via.placeholder.com/400x400/4ECDC4/ffffff?text=Etsy+Mockup+2",
                etsy_listing_id="456",
                image_id="2"
            )
        ]

        test_files = [
            model.DesignFile(
                filename="test_design_1.png",
                path="/nas/test_shop/UVDTF 16oz/test_design_1.png",
                url="/api/designs/nas-file/test_shop/UVDTF 16oz/test_design_1.png",
                template_name="UVDTF 16oz",
                nas_path="UVDTF 16oz/test_design_1.png",
                file_size=1024000,
                last_modified=None
            ),
            model.DesignFile(
                filename="test_design_2.png",
                path="/nas/test_shop/Digital/UVDTF 16oz/test_design_2.png",
                url="/api/designs/nas-file/test_shop/Digital/UVDTF 16oz/test_design_2.png",
                template_name="UVDTF 16oz",
                nas_path="Digital/UVDTF 16oz/test_design_2.png",
                file_size=2048000,
                last_modified=None
            )
        ]

        return model.DesignGalleryResponse(
            mockups=test_mockups,
            files=test_files,
            total_mockups=len(test_mockups),
            total_files=len(test_files)
        )

    except Exception as e:
        logging.error(f"Error fetching design gallery data for user {user_id}: {e}")
        import traceback
        logging.error(f"Gallery error traceback: {traceback.format_exc()}")
        raise DesignGetAllError()


def get_user_by_id(db: Session, user_id: UUID) -> User:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()
