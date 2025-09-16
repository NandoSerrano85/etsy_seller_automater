from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload
from server.src.entities.mockup import Mockups, MockupImage, MockupMaskData
from server.src.entities.user import User
from server.src.entities.template import EtsyProductTemplate
from server.src.entities.designs import DesignImages
from server.src.message import (
    MockupNotFoundError,
    MockupCreateError,
    MockupGetAllError,
    MockupGetByIdError,
    MockupUpdateError,
    MockupDeleteError,
    MockupImageNotFoundError,
    MockupImageCreateError,
    MockupImageGetAllError,
    MockupImageGetByIdError,
    MockupImageUpdateError,
    MockupImageDeleteError,
    MockupMaskDataNotFoundError,
    MockupMaskDataCreateError,
    MockupMaskDataGetAllError,
    MockupMaskDataGetByIdError,
    MockupMaskDataUpdateError,
    MockupMaskDataDeleteError
)
from . import model
import logging, os, random, json
from server.src.utils.mockups_util import create_mockup_images, create_mockups_for_etsy
from server.src.utils.etsy_api_engine import EtsyAPI
from server.src.utils.nas_storage import nas_storage
from fastapi import UploadFile, HTTPException
from PIL import Image
import imagehash
from sqlalchemy import and_


def list_images_in_dir(directory, extensions={".jpg", ".jpeg", ".png", ".bmp", ".tiff"}):
    """
    List all image files in a directory (non-recursive).
    
    Parameters:
        directory (str): Path to directory
        extensions (set): Allowed image extensions
    
    Returns:
        list: Paths to image files
    """
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.splitext(f)[1].lower() in extensions
    ]


def build_hash_db(image_paths, hash_size=16):
    """
    Precompute perceptual hashes for a list of images.
    """
    hash_db = {}
    for path in image_paths:
        try:
            with Image.open(path) as img:
                hash_db[path] = imagehash.phash(img, hash_size=hash_size)
        except Exception as e:
            logging.warning(f"Skipping {path}: {e}")
    return hash_db


def check_duplicates(new_images, hash_db, threshold=5, hash_size=16):
    """
    Check if new images already exist in hash_db.

    Returns:
        dict: {new_image_path: matching_existing_path or None}
    """
    results = {}
    for new_path in new_images:
        match = None
        try:
            with Image.open(new_path) as img:
                new_hash = imagehash.phash(img, hash_size=hash_size)

            for existing_path, existing_hash in hash_db.items():
                if abs(new_hash - existing_hash) <= threshold:
                    match = existing_path
                    break
        except Exception as e:
            logging.warning(f"Skipping {new_path}: {e}")
        results[new_path] = match
    return results

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
        raise

def check_duplicates_in_database(db: Session, new_image_paths: List[str], user_id: UUID, threshold: int = 5) -> dict:
    """
    Check for duplicate images using database-stored phashes.

    Args:
        db: Database session
        new_image_paths: List of paths to new images to check
        user_id: User ID to scope the search
        threshold: Hamming distance threshold for considering images duplicates

    Returns:
        dict: {new_image_path: {'duplicate': bool, 'existing_design': DesignImages or None}}
    """
    results = {}

    # Get all existing phashes for this user from database
    existing_designs = db.query(DesignImages).filter(
        and_(
            DesignImages.user_id == user_id,
            DesignImages.is_active == True,
            DesignImages.phash.isnot(None)
        )
    ).all()

    # Create lookup of phash -> design record
    existing_phashes = {}
    for design in existing_designs:
        try:
            # Convert string phash back to ImageHash object for comparison
            phash_obj = imagehash.hex_to_hash(design.phash)
            existing_phashes[phash_obj] = design
        except Exception as e:
            logging.warning(f"Invalid phash in database for design {design.id}: {e}")
            continue

    # Check each new image
    for image_path in new_image_paths:
        try:
            # Calculate phash for new image
            new_phash_str = calculate_phash(image_path)
            new_phash = imagehash.hex_to_hash(new_phash_str)

            # Find closest match
            closest_design = None
            min_distance = float('inf')

            for existing_phash, design in existing_phashes.items():
                distance = abs(new_phash - existing_phash)
                if distance <= threshold and distance < min_distance:
                    min_distance = distance
                    closest_design = design

            results[image_path] = {
                'duplicate': closest_design is not None,
                'existing_design': closest_design,
                'distance': min_distance if closest_design else None,
                'new_phash': new_phash_str
            }

        except Exception as e:
            logging.error(f"Error checking duplicates for {image_path}: {e}")
            results[image_path] = {
                'duplicate': False,
                'existing_design': None,
                'error': str(e),
                'new_phash': None
            }

    return results


def _validate_user_owns_mockup(db: Session, user_id: UUID, mockup_id: UUID) -> bool:
    """Validate that mockup exists and belongs to the user"""
    mockup = db.query(Mockups).filter(
        Mockups.id == mockup_id,
        Mockups.user_id == user_id
    ).first()
    return mockup is not None


def _validate_user_owns_image(db: Session, user_id: UUID, image_id: UUID) -> bool:
    """Validate that mockup image exists and belongs to the user"""
    image = db.query(MockupImage).join(Mockups).filter(
        MockupImage.id == image_id,
        Mockups.user_id == user_id
    ).first()
    return image is not None


def _validate_user_owns_mask_data(db: Session, user_id: UUID, mask_data_id: UUID) -> bool:
    """Validate that mask data exists and belongs to the user"""
    mask_data = db.query(MockupMaskData).join(MockupImage).join(Mockups).filter(
        MockupMaskData.id == mask_data_id,
        Mockups.user_id == user_id
    ).first()
    return mask_data is not None


def _validate_template_exists(db: Session, user_id: UUID, template_id: UUID) -> bool:
    """Validate that template exists and belongs to the user"""
    template = db.query(EtsyProductTemplate).filter(
        EtsyProductTemplate.id == template_id,
        EtsyProductTemplate.user_id == user_id
    ).first()
    return template is not None


def _get_mask_data_for_mockup_image(db: Session, mockup_image_id: UUID):
    """
    Fetch all mask data for a specific mockup image.
    """
    mask_data = db.query(MockupMaskData).filter(
        MockupMaskData.mockup_image_id == mockup_image_id
    ).all()  # Get all masks instead of just first()
    
    if not mask_data:
        raise ValueError(f"No mask data found for mockup image {mockup_image_id}")
    
    # Combine all masks and points
    all_masks = []
    all_points = []
    is_cropped = False
    alignment = 'center'
    
    for data in mask_data:
        masks_data = data.masks
        points_data = data.points
        
        if isinstance(masks_data, str):
            masks_data = json.loads(masks_data)
        if isinstance(points_data, str):
            points_data = json.loads(points_data)
            
        all_masks.extend(masks_data)
        all_points.extend(points_data)
        is_cropped = is_cropped or data.is_cropped
        if data.alignment != 'center':
            alignment = data.alignment
    
    return all_masks, all_points, is_cropped, alignment

def _get_template_mask_data_by_name(db: Session, template_name: str):
    """
    Get template mask data by template name. This is a fallback function
    that looks for any mockup image with the given template name.
    Returns (masks, points, is_cropped, alignment) for the template.
    """
    # Find a mockup image with the given template name
    mockup_image = db.query(MockupImage).filter(
        MockupImage.image_type == template_name
    ).first()
    
    if not mockup_image:
        raise ValueError(f"No mockup image found for template {template_name}")
    
    # Get mask data for this mockup image
    mockup_image_id = mockup_image.id
    if not isinstance(mockup_image_id, UUID):
        mockup_image_id = UUID(str(mockup_image_id))
    return _get_mask_data_for_mockup_image(db, mockup_image_id)

def _create_template_mask_data(db: Session, template_name: str, masks: List, points: List, alignment: str = "center"):
    """
    Create template mask data by creating a mockup image and associated mask data.
    This is used when we need to store template-level mask data.
    """
    # Create a template mockup image (this would need a proper mockup_id)
    # For now, we'll use a placeholder approach
    template_mockup_image = MockupImage(
        mockups_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
        filename=f"template_{template_name}",
        file_path=f"/templates/{template_name}",
        image_type=template_name
    )
    db.add(template_mockup_image)
    db.flush()  # Get the ID without committing
    
    # Create mask data
    mask_data = MockupMaskData(
        mockup_image_id=template_mockup_image.id,
        masks=masks,
        points=points,
        is_cropped=False,
        alignment=alignment
    )
    db.add(mask_data)
    db.commit()
    db.refresh(mask_data)
    
    return mask_data

# Update the existing function to work with the current entity structure
def _get_mask_data_for_user_and_template(db: Session, user_id: int, template_name: str):
    """
    Fetch mask data for a user and template name. This function now works with
    the current MockupMaskData entity structure.
    Returns (masks, points, starting_name, is_cropped, alignment)
    """
    try:
        # First try to get template mask data
        masks, points, is_cropped, alignment = _get_template_mask_data_by_name(db, template_name)
        return masks, points, 100, is_cropped, alignment  # Default starting name
    except ValueError:
        # If no template data exists, we need to create it or use defaults
        # For now, we'll raise an error indicating no template data exists
        raise ValueError(f"No template mask data found for template {template_name}. Please create template mask data first.")


def ensure_float_coords(data):
    """
    Recursively convert all coordinates in a list of masks/points to float.
    Expects data as List[List[List[float or int]]].
    """
    if not data:
        return []
    return [
        [
            [float(coord[0]), float(coord[1])] for coord in mask
        ] for mask in data
    ]

# Mockups CRUD operations
def create_mockup_group(db: Session, user_id: UUID, mockup_data: model.MockupsCreate) -> model.MockupsResponse:
    """
    Create a new mockup group/metadata record (does not generate images).
    """
    try:
        # Validate template exists and belongs to user
        if not _validate_template_exists(db, user_id, mockup_data.product_template_id):
            logging.warning(f"Invalid template ID: {mockup_data.product_template_id} for user: {user_id}")
            raise MockupCreateError()
        mockup = Mockups(
            user_id=user_id,
            name=mockup_data.name,
            product_template_id=mockup_data.product_template_id,
            starting_name=mockup_data.starting_name
        )
        db.add(mockup)
        db.commit()
        db.refresh(mockup)
        logging.info(f"Successfully created mockup group with ID: {mockup.id} for user: {user_id}")
        return model.MockupsResponse.model_validate(mockup)
    except Exception as e:
        logging.error(f"Error creating mockup group for user ID: {user_id}. Error: {e}")
        db.rollback()
        raise MockupCreateError()


def create_mockup(db: Session, user_id: UUID, mockup_data: model.MockupFullCreate) -> model.MockupImageResponse:
    """
    Create and store a complete mockup: generates the image, saves it to disk, and creates DB records for both Mockups and MockupImage.
    """
    import shutil
    try:
        # 1. Validate template exists and belongs to user
        if not _validate_template_exists(db, user_id, mockup_data.product_template_id):
            logging.warning(f"Invalid template ID: {mockup_data.product_template_id} for user: {user_id}")
            raise MockupCreateError()
        # 2. Create the mockup group/metadata record
        starting_name = 100
        mockup = Mockups(
            user_id=user_id,
            product_template_id=mockup_data.product_template_id,
            starting_name=starting_name
        )
        db.add(mockup)
        db.flush()  # Get mockup.id
        # 3. Get user/shop and template info
        user = db.query(User).filter(User.id == user_id).first()
        template = db.query(EtsyProductTemplate).filter(EtsyProductTemplate.id == mockup.product_template_id).first()
        if not user or not template:
            logging.warning(f"User or template not found for mockup creation")
            raise MockupCreateError()
        template_name = template.name
        # 4. Build root path and ensure directory exists
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        if not local_root_path:
            logging.error("LOCAL_ROOT_PATH environment variable not set")
            raise MockupCreateError()
        root_path = f"{local_root_path}{user.shop_name}/"
        target_dir = os.path.join(root_path, f"Mockups/BaseMockups/{template_name}/")
        os.makedirs(target_dir, exist_ok=True)
        # 5. Check if design file exists
        design_file_paths = mockup_data.design_file_path
        for design_file_path in design_file_paths:
            if not os.path.exists(design_file_path):
                logging.warning(f"Design file not found: {design_file_path}")
                raise MockupCreateError()
        # 6. Get mask data for this template
        try:
            mask_points_list, points_list, _, is_cropped, alignment = _get_mask_data_for_user_and_template(db, int(user_id), str(template_name))
            mask_data = {
                'masks': mask_points_list,
                'points': points_list,
                'is_cropped': is_cropped,
                'alignment': alignment
            }
            logging.info(f"Loaded mask data for template {template_name}")
        except Exception as e:
            logging.error(f"Failed to load mask data for template {template_name}: {e}")
            raise MockupCreateError()
        # 7. Generate and save mockup images
        try:
            generated_mockups = create_mockup_images(
                design_file_paths=design_file_paths,
                template_name=str(template_name),
                mockup_id=str(mockup.id),
                root_path=root_path,
                starting_name=starting_name,
                mask_data=mask_data,
                watermark_path=mockup_data.watermark_path
            )
        except Exception as e:
            logging.error(f"Failed to generate mockup images: {e}")
            raise MockupCreateError()
        # 8. Save mockup images to database and upload to NAS
        mockup_images = []
        for mockup_img in generated_mockups:
            mockup_image = MockupImage(
                mockups_id=mockup.id,
                filename=mockup_img['filename'],
                file_path=mockup_img['file_path'],
                watermark_path=mockup_img['watermark_path'],
                image_type=mockup_img['image_type']
            )
            db.add(mockup_image)
            mockup_images.append(mockup_image)
            
            # Upload mockup image to NAS
            try:
                relative_path = f"Mockups/BaseMockups/{template_name}/{mockup_img['filename']}"
                success = nas_storage.upload_file(
                    local_file_path=mockup_img['file_path'],
                    shop_name=user.shop_name,
                    relative_path=relative_path
                )
                if success:
                    logging.info(f"Successfully uploaded mockup to NAS: {relative_path}")
                else:
                    logging.warning(f"Failed to upload mockup to NAS: {relative_path}")
            except Exception as e:
                logging.error(f"Error uploading mockup to NAS: {e}")
                # Don't fail the entire process if NAS upload fails
        # 9. Commit
        db.commit()
        logging.info(f"Successfully created and stored complete mockup for user: {user_id}")
        if not mockup_images:
            raise MockupCreateError()
        return model.MockupImageResponse.model_validate(mockup_images[0])
    except Exception as e:
        logging.error(f"Error creating and storing complete mockup for user ID: {user_id}. Error: {e}")
        db.rollback()
        raise MockupCreateError()


def get_mockups_by_user_id(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> model.MockupsListResponse:
    try:
        mockups = db.query(Mockups).filter(
            Mockups.user_id == user_id
        ).offset(skip).limit(limit).all()
        
        total = db.query(Mockups).filter(
            Mockups.user_id == user_id
        ).count()
        
        # For each mockup, get related data
        for mockup in mockups:
            # Get related mockup images with their mask data
            mockup_images = db.query(MockupImage).filter(
                MockupImage.mockups_id == mockup.id
            ).all()
            
            # For each image, get its mask data
            for image in mockup_images:
                mask_data = db.query(MockupMaskData).filter(
                    MockupMaskData.mockup_image_id == image.id
                ).all()
                # Set the mask_data attribute on the image
                image.mask_data = mask_data
            
            # Set the mockup_images attribute on the mockup
            mockup.mockup_images = mockup_images
            
            # Get template name if available
            if mockup.product_template_id:
                template = db.query(EtsyProductTemplate).filter(
                    EtsyProductTemplate.id == mockup.product_template_id
                ).first()
                if template:
                    mockup.template_name = template.name
        
        logging.info(f"Successfully retrieved {len(mockups)} mockups for user: {user_id}")
        mockup_responses = [model.MockupsResponse.model_validate(mockup) for mockup in mockups]
        return model.MockupsListResponse(mockups=mockup_responses, total=total)
    except Exception as e:
        logging.error(f"Error getting mockups for user ID: {user_id}. Error: {e}")
        raise MockupGetAllError()


def get_mockup_by_id(db: Session, mockup_id: UUID, user_id: UUID) -> model.MockupsResponse:
    try:
        # Get mockup with related data (images and mask data)
        mockup = db.query(Mockups).filter(
            Mockups.id == mockup_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mockup:
            logging.warning(f"Mockup not found with ID: {mockup_id} for user: {user_id}")
            raise MockupNotFoundError(mockup_id)
        
        # Get related mockup images with their mask data
        mockup_images = db.query(MockupImage).filter(
            MockupImage.mockups_id == mockup_id
        ).all()
        
        # For each image, get its mask data
        for image in mockup_images:
            mask_data = db.query(MockupMaskData).filter(
                MockupMaskData.mockup_image_id == image.id
            ).all()
            # Set the mask_data attribute on the image
            image.mask_data = mask_data
        
        # Set the mockup_images attribute on the mockup
        mockup.mockup_images = mockup_images
        
        # Get template name if available
        if mockup.product_template_id:
            template = db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.id == mockup.product_template_id
            ).first()
            if template:
                mockup.template_name = template.name
        
        logging.info(f"Successfully retrieved mockup with ID: {mockup_id} and {len(mockup_images)} images")
        return mockup
    except Exception as e:
        if isinstance(e, MockupNotFoundError):
            raise e
        logging.error(f"Error getting mockup with ID: {mockup_id}. Error: {e}")
        raise MockupGetByIdError(mockup_id)


def update_mockup(db: Session, mockup_id: UUID, user_id: UUID, mockup_data: model.MockupsUpdate) -> model.MockupsResponse:
    try:
        mockup = db.query(Mockups).filter(
            Mockups.id == mockup_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mockup:
            logging.warning(f"Mockup not found with ID: {mockup_id} for user: {user_id}")
            raise MockupNotFoundError(mockup_id)
        
        # Update only provided fields
        update_data = mockup_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mockup, field, value)
        
        db.commit()
        db.refresh(mockup)
        
        # Get related data after update
        mockup_images = db.query(MockupImage).filter(
            MockupImage.mockups_id == mockup_id
        ).all()
        
        # For each image, get its mask data
        for image in mockup_images:
            mask_data = db.query(MockupMaskData).filter(
                MockupMaskData.mockup_image_id == image.id
            ).all()
            # Set the mask_data attribute on the image
            image.mask_data = mask_data
        
        # Set the mockup_images attribute on the mockup
        mockup.mockup_images = mockup_images
        
        # Get template name if available
        if mockup.product_template_id:
            template = db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.id == mockup.product_template_id
            ).first()
            if template:
                mockup.template_name = template.name
        
        logging.info(f"Successfully updated mockup with ID: {mockup_id}")
        return mockup
    except Exception as e:
        if isinstance(e, MockupNotFoundError):
            raise e
        logging.error(f"Error updating mockup with ID: {mockup_id}. Error: {e}")
        db.rollback()
        raise MockupUpdateError(mockup_id)


def delete_mockup(db: Session, mockup_id: UUID, user_id: UUID) -> None:
    try:
        mockup = db.query(Mockups).filter(
            Mockups.id == mockup_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mockup:
            logging.warning(f"Mockup not found with ID: {mockup_id} for user: {user_id}")
            raise MockupNotFoundError(mockup_id)
        
        # Get all related mockup images for this mockup
        mockup_images = db.query(MockupImage).filter(
            MockupImage.mockups_id == mockup_id
        ).all()
        
        # Delete all mask data for each image
        for image in mockup_images:
            mask_data_entries = db.query(MockupMaskData).filter(
                MockupMaskData.mockup_image_id == image.id
            ).all()
            for mask_data in mask_data_entries:
                db.delete(mask_data)
        
        # Delete all mockup images
        for image in mockup_images:
            db.delete(image)
        
        # Delete the mockup itself
        db.delete(mockup)
        db.commit()
        
        logging.info(f"Successfully deleted mockup with ID: {mockup_id} and {len(mockup_images)} related images")
    except Exception as e:
        if isinstance(e, MockupNotFoundError):
            raise e
        logging.error(f"Error deleting mockup with ID: {mockup_id}. Error: {e}")
        db.rollback()
        raise MockupDeleteError(mockup_id)


# Mockup Images CRUD operations
def create_mockup_image(db: Session, mockup_id: UUID, user_id: UUID, image_data: model.MockupImageCreate) -> model.MockupImageResponse:
    """
    Create a single mockup image: save the image file to disk (if needed) and create a single MockupImage DB entry.
    """
    import shutil
    try:
        # 1. Validate user owns the mockup
        if not _validate_user_owns_mockup(db, user_id, mockup_id):
            logging.warning(f"User {user_id} does not own mockup {mockup_id}")
            raise MockupImageCreateError()
        # 2. Validate the mockup_id matches
        if image_data.mockups_id != mockup_id:
            logging.warning(f"Mockup ID mismatch: {image_data.mockups_id} != {mockup_id}")
            raise MockupImageCreateError()
        # 3. Get mockup and user information
        mockup = db.query(Mockups).filter(Mockups.id == mockup_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not mockup or not user:
            logging.warning(f"Mockup or user not found")
            raise MockupImageCreateError()
        # 4. Get template information
        template = db.query(EtsyProductTemplate).filter(EtsyProductTemplate.id == mockup.product_template_id).first()
        if not template:
            logging.warning(f"Template not found for mockup {mockup_id}")
            raise MockupImageCreateError()
        template_name = template.name
        # 5. Build root path and ensure directory exists
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        if not local_root_path:
            logging.error("LOCAL_ROOT_PATH environment variable not set")
            raise MockupImageCreateError()
        root_path = f"{local_root_path}{user.shop_name}/"
        target_dir = os.path.join(root_path, f"Mockups/BaseMockups/{template_name}/")
        os.makedirs(target_dir, exist_ok=True)
        # 6. Save the image file to disk if needed
        src_path = image_data.design_file_path
        dest_path = os.path.join(target_dir, os.path.basename(src_path))
        if not os.path.exists(dest_path):
            try:
                shutil.copy2(src_path, dest_path)
                logging.info(f"Copied image file to {dest_path}")
            except Exception as file_err:
                logging.error(f"Failed to copy image file: {file_err}")
                raise MockupImageCreateError()
        # 7. Create the MockupImage DB entry
        mockup_image = MockupImage(
            mockups_id=mockup_id,
            filename=os.path.basename(dest_path),
            file_path=dest_path,
            watermark_path=None,
            image_type=template_name
        )
        db.add(mockup_image)
        db.commit()
        db.refresh(mockup_image)
        logging.info(f"Successfully created mockup image with ID: {mockup_image.id} for mockup: {mockup_id}")
        return model.MockupImageResponse.model_validate(mockup_image)
    except Exception as e:
        logging.error(f"Error creating mockup image for mockup ID: {mockup_id}. Error: {e}")
        db.rollback()
        raise MockupImageCreateError()


def get_mockup_images_by_mockup_id(db: Session, mockup_id: UUID, user_id: UUID, skip: int = 0, limit: int = 100) -> model.MockupImageListResponse:
    """
    Retrieve all mockup images for a given mockup, with pagination.
    """
    try:
        # Validate user owns the mockup
        if not _validate_user_owns_mockup(db, user_id, mockup_id):
            logging.warning(f"User {user_id} does not own mockup {mockup_id}")
            raise MockupImageGetAllError()
        mockup_images = db.query(MockupImage).filter(
            MockupImage.mockups_id == mockup_id
        ).offset(skip).limit(limit).all()
        total = db.query(MockupImage).filter(
            MockupImage.mockups_id == mockup_id
        ).count()
        logging.info(f"Successfully retrieved {len(mockup_images)} mockup images for mockup: {mockup_id}")
        image_responses = [model.MockupImageResponse.model_validate(image) for image in mockup_images]
        return model.MockupImageListResponse(mockup_images=image_responses, total=total)
    except Exception as e:
        logging.error(f"Error getting mockup images for mockup ID: {mockup_id}. Error: {e}")
        raise MockupImageGetAllError()


def get_mockup_image_by_id(db: Session, image_id: UUID, user_id: UUID) -> model.MockupImageResponse:
    """
    Retrieve a specific mockup image by its ID for the current user.
    """
    try:
        mockup_image = db.query(MockupImage).join(Mockups).filter(
            MockupImage.id == image_id,
            Mockups.user_id == user_id
        ).first()
        if not mockup_image:
            logging.warning(f"Mockup image not found with ID: {image_id} for user: {user_id}")
            raise MockupImageNotFoundError(image_id)
        logging.info(f"Successfully retrieved mockup image with ID: {image_id}")
        return model.MockupImageResponse.model_validate(mockup_image)
    except Exception as e:
        if isinstance(e, MockupImageNotFoundError):
            raise e
        logging.error(f"Error getting mockup image with ID: {image_id}. Error: {e}")
        raise MockupImageGetByIdError(image_id)


def update_mockup_image(db: Session, image_id: UUID, user_id: UUID, image_data: model.MockupImageUpdate) -> model.MockupImageResponse:
    """
    Update metadata for a specific mockup image by its ID for the current user.
    """
    try:
        mockup_image = db.query(MockupImage).join(Mockups).filter(
            MockupImage.id == image_id,
            Mockups.user_id == user_id
        ).first()
        if not mockup_image:
            logging.warning(f"Mockup image not found with ID: {image_id} for user: {user_id}")
            raise MockupImageNotFoundError(image_id)
        # Update only provided fields
        update_data = image_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mockup_image, field, value)
        db.commit()
        db.refresh(mockup_image)
        logging.info(f"Successfully updated mockup image with ID: {image_id}")
        return model.MockupImageResponse.model_validate(mockup_image)
    except Exception as e:
        if isinstance(e, MockupImageNotFoundError):
            raise e
        logging.error(f"Error updating mockup image with ID: {image_id}. Error: {e}")
        db.rollback()
        raise MockupImageUpdateError(image_id)


def update_mockup_image_watermark(db: Session, image_id: UUID, user_id: UUID, watermark_path: str) -> model.MockupImageResponse:
    """
    Update the watermark_path for a specific MockupImage.
    """
    try:
        mockup_image = db.query(MockupImage).join(Mockups).filter(
            MockupImage.id == image_id,
            Mockups.user_id == user_id
        ).first()
        if not mockup_image:
            logging.warning(f"Mockup image not found with ID: {image_id} for user: {user_id}")
            raise MockupImageNotFoundError(image_id)
        setattr(mockup_image, "watermark_path", watermark_path)
        db.commit()
        db.refresh(mockup_image)
        logging.info(f"Updated watermark_path for mockup image {image_id}")
        return model.MockupImageResponse.model_validate(mockup_image)
    except Exception as e:
        logging.error(f"Error updating watermark_path for mockup image {image_id}: {e}")
        db.rollback()
        raise MockupImageUpdateError(image_id)


def delete_mockup_image(db: Session, image_id: UUID, user_id: UUID) -> None:
    """
    Delete a specific mockup image by its ID for the current user, and remove the file from disk if it exists.
    """
    import os
    try:
        mockup_image = db.query(MockupImage).join(Mockups).filter(
            MockupImage.id == image_id,
            Mockups.user_id == user_id
        ).first()
        if not mockup_image:
            logging.warning(f"Mockup image not found with ID: {image_id} for user: {user_id}")
            raise MockupImageNotFoundError(image_id)
        # Attempt to delete the file from disk
        file_path = str(mockup_image.file_path) if getattr(mockup_image, 'file_path', None) is not None else None
        if file_path and file_path != '' and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Deleted mockup image file from disk: {file_path}")
            except Exception as file_err:
                logging.error(f"Failed to delete mockup image file from disk: {file_err}")
        db.delete(mockup_image)
        db.commit()
        logging.info(f"Successfully deleted mockup image with ID: {image_id}")
    except Exception as e:
        if isinstance(e, MockupImageNotFoundError):
            raise e
        logging.error(f"Error deleting mockup image with ID: {image_id}. Error: {e}")
        db.rollback()
        raise MockupImageDeleteError(image_id)


# Mockup Mask Data CRUD operations
def create_mockup_mask_data(db: Session, image_id: UUID, user_id: UUID, mask_data: model.MockupMaskDataCreate) -> model.MockupMaskDataResponse:
    try:
        # Validate user owns the image
        if not _validate_user_owns_image(db, user_id, image_id):
            logging.warning(f"User {user_id} does not own image {image_id}")
            raise MockupMaskDataCreateError()
        
        # Validate the image_id matches
        if mask_data.mockup_image_id != image_id:
            logging.warning(f"Image ID mismatch: {mask_data.mockup_image_id} != {image_id}")
            raise MockupMaskDataCreateError()
        
        # Ensure all coordinates are floats for masks and points
        masks = ensure_float_coords(mask_data.masks)
        points = ensure_float_coords(mask_data.points)
        
        mockup_mask_data = MockupMaskData(
            mockup_image_id=image_id,
            masks=masks,  # List[List[List[float]]]
            points=points,  # List[List[List[float]]]
            is_cropped=mask_data.is_cropped,
            alignment=mask_data.alignment
        )
        
        db.add(mockup_mask_data)
        db.commit()
        db.refresh(mockup_mask_data)
        
        logging.info(f"Successfully created mockup mask data with ID: {mockup_mask_data.id} for image: {image_id}")
        return model.MockupMaskDataResponse.model_validate(mockup_mask_data)
    except Exception as e:
        logging.error(f"Error creating mockup mask data for image ID: {image_id}. Error: {e}")
        db.rollback()
        raise MockupMaskDataCreateError()


def get_mockup_mask_data_by_image_id(db: Session, image_id: UUID, user_id: UUID, skip: int = 0, limit: int = 100) -> model.MockupMaskDataListResponse:
    try:
        # Validate user owns the image
        if not _validate_user_owns_image(db, user_id, image_id):
            logging.warning(f"User {user_id} does not own image {image_id}")
            raise MockupMaskDataGetAllError()
        
        mask_data_list = db.query(MockupMaskData).filter(
            MockupMaskData.mockup_image_id == image_id
        ).offset(skip).limit(limit).all()
        
        total = db.query(MockupMaskData).filter(
            MockupMaskData.mockup_image_id == image_id
        ).count()
        
        logging.info(f"Successfully retrieved {len(mask_data_list)} mask data entries for image: {image_id}")
        mask_data_responses = [model.MockupMaskDataResponse.model_validate(mask_data) for mask_data in mask_data_list]
        return model.MockupMaskDataListResponse(mask_data=mask_data_responses, total=total)
    except Exception as e:
        logging.error(f"Error getting mask data for image ID: {image_id}. Error: {e}")
        raise MockupMaskDataGetAllError()


def get_mockup_mask_data_by_id(db: Session, mask_data_id: UUID, user_id: UUID) -> model.MockupMaskDataResponse:
    try:
        mask_data = db.query(MockupMaskData).join(MockupImage).join(Mockups).filter(
            MockupMaskData.id == mask_data_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mask_data:
            logging.warning(f"Mask data not found with ID: {mask_data_id} for user: {user_id}")
            raise MockupMaskDataNotFoundError(mask_data_id)
        
        logging.info(f"Successfully retrieved mask data with ID: {mask_data_id}")
        return model.MockupMaskDataResponse.model_validate(mask_data)
    except Exception as e:
        if isinstance(e, MockupMaskDataNotFoundError):
            raise e
        logging.error(f"Error getting mask data with ID: {mask_data_id}. Error: {e}")
        raise MockupMaskDataGetByIdError(mask_data_id)


def update_mockup_mask_data(db: Session, mask_data_id: UUID, user_id: UUID, mask_data: model.MockupMaskDataUpdate) -> model.MockupMaskDataResponse:
    try:
        mask_data_obj = db.query(MockupMaskData).join(MockupImage).join(Mockups).filter(
            MockupMaskData.id == mask_data_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mask_data_obj:
            logging.warning(f"Mask data not found with ID: {mask_data_id} for user: {user_id}")
            raise MockupMaskDataNotFoundError(mask_data_id)
        
        # Update only provided fields, ensuring float conversion for masks/points
        update_data = mask_data.model_dump(exclude_unset=True)
        if 'masks' in update_data:
            update_data['masks'] = ensure_float_coords(update_data['masks'])
        if 'points' in update_data:
            update_data['points'] = ensure_float_coords(update_data['points'])
        for field, value in update_data.items():
            setattr(mask_data_obj, field, value)
        
        db.commit()
        db.refresh(mask_data_obj)
        
        logging.info(f"Successfully updated mask data with ID: {mask_data_id}")
        return model.MockupMaskDataResponse.model_validate(mask_data_obj)
    except Exception as e:
        if isinstance(e, MockupMaskDataNotFoundError):
            raise e
        logging.error(f"Error updating mask data with ID: {mask_data_id}. Error: {e}")
        db.rollback()
        raise MockupMaskDataUpdateError(mask_data_id)


def delete_mockup_mask_data(db: Session, mask_data_id: UUID, user_id: UUID) -> None:
    try:
        mask_data = db.query(MockupMaskData).join(MockupImage).join(Mockups).filter(
            MockupMaskData.id == mask_data_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mask_data:
            logging.warning(f"Mask data not found with ID: {mask_data_id} for user: {user_id}")
            raise MockupMaskDataNotFoundError(mask_data_id)
        
        db.delete(mask_data)
        db.commit()
        
        logging.info(f"Successfully deleted mask data with ID: {mask_data_id}")
    except Exception as e:
        if isinstance(e, MockupMaskDataNotFoundError):
            raise e
        logging.error(f"Error deleting mask data with ID: {mask_data_id}. Error: {e}")
        db.rollback()
        raise MockupMaskDataDeleteError(mask_data_id)


async def upload_mockup_image_watermark(db: Session, image_id: UUID, user_id: UUID, watermark: UploadFile) -> model.MockupImageResponse:
    """
    Save the uploaded watermark file and update the watermark_path for the MockupImage.
    """
    try:
        mockup_image = db.query(MockupImage).join(Mockups).filter(
            MockupImage.id == image_id,
            Mockups.user_id == user_id
        ).first()
        if not mockup_image:
            logging.warning(f"Mockup image not found with ID: {image_id} for user: {user_id}")
            raise MockupImageNotFoundError(image_id)
        
        # Determine save directory (e.g., alongside the mockup image or in a Watermarks/ subfolder)
        base_file_path = str(mockup_image.file_path) if getattr(mockup_image, 'file_path', None) is not None else ''
        base_dir = os.path.dirname(base_file_path)
        watermark_filename_str = str(watermark.filename) if watermark.filename else 'watermark.png'
        ext = os.path.splitext(watermark_filename_str)[1] or ".png"
        watermark_dir = os.path.join(base_dir, "Watermarks")
        os.makedirs(watermark_dir, exist_ok=True)
        
        # Save the uploaded file
        watermark_filename = f"watermark_{image_id}{ext}"
        watermark_path = os.path.join(watermark_dir, watermark_filename)
        
        # Read and save the file content
        file_content = await watermark.read()
        with open(watermark_path, "wb") as f:
            f.write(file_content)
        
        # Update DB
        setattr(mockup_image, "watermark_path", watermark_path)
        db.commit()
        db.refresh(mockup_image)
        logging.info(f"Uploaded and set watermark for mockup image {image_id} at path: {watermark_path}")
        return model.MockupImageResponse.model_validate(mockup_image)
    except Exception as e:
        logging.error(f"Error uploading watermark for mockup image {image_id}: {e}")
        db.rollback()
        raise MockupImageUpdateError(image_id)


async def update_mockup_watermark(db: Session, mockup_id: UUID, user_id: UUID, watermark: UploadFile) -> model.MockupsResponse:
    """
    Update the watermark for all images in a mockup.
    """
    try:
        # Validate user owns the mockup
        mockup = db.query(Mockups).filter(
            Mockups.id == mockup_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mockup:
            logging.warning(f"Mockup not found with ID: {mockup_id} for user: {user_id}")
            raise MockupNotFoundError(mockup_id)
        
        # Get all mockup images for this mockup
        mockup_images = db.query(MockupImage).filter(
            MockupImage.mockups_id == mockup_id
        ).all()
        
        if not mockup_images:
            logging.warning(f"No mockup images found for mockup {mockup_id}")
            return model.MockupsResponse.model_validate(mockup)
        
        # Determine save directory from first image
        base_file_path = str(mockup_images[0].file_path) if getattr(mockup_images[0], 'file_path', None) is not None else ''
        base_dir = os.path.dirname(base_file_path)
        watermark_filename_str = str(watermark.filename) if watermark.filename else 'watermark.png'
        ext = os.path.splitext(watermark_filename_str)[1] or ".png"
        watermark_dir = os.path.join(base_dir, "Watermarks")
        os.makedirs(watermark_dir, exist_ok=True)
        
        # Save the uploaded file with a unique name for the mockup
        watermark_filename = f"watermark_mockup_{mockup_id}{ext}"
        watermark_path = os.path.join(watermark_dir, watermark_filename)
        
        # Read and save the file content
        file_content = await watermark.read()
        with open(watermark_path, "wb") as f:
            f.write(file_content)
        
        # Update all mockup images to use the new watermark
        for image in mockup_images:
            setattr(image, "watermark_path", watermark_path)
        
        db.commit()
        
        # Refresh the mockup with related data
        updated_mockup = get_mockup_by_id(db, mockup_id, user_id)
        
        logging.info(f"Updated watermark for mockup {mockup_id} with {len(mockup_images)} images")
        return updated_mockup
        
    except Exception as e:
        if isinstance(e, MockupNotFoundError):
            raise e
        logging.error(f"Error updating watermark for mockup {mockup_id}: {e}")
        db.rollback()
        raise MockupUpdateError(mockup_id)


async def upload_mockup_files(db: Session, user_id: UUID, files: List[UploadFile], mockup_id: UUID, watermark_file: UploadFile):
    """
    Upload mockup files and create mockup images for a specific mockup group.
    """
    try:
        # Validate that the mockup exists and belongs to the user
        mockup = db.query(Mockups).filter(
            Mockups.id == mockup_id,
            Mockups.user_id == user_id
        ).first()
        
        if not mockup:
            logging.warning(f"Mockup {mockup_id} not found for user {user_id}")
            raise MockupNotFoundError(mockup_id)

        if len(files) == 0:
            logging.warning("No files were passed in")
            raise ValueError("No files provided")

        # Get user and template information
        user = db.query(User).filter(User.id == user_id).first()
        template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == mockup.product_template_id
        ).first()
        
        if not user or not template:
            logging.warning(f"User or template not found for mockup {mockup_id}")
            raise MockupCreateError()

        template_name = template.name
        
        # Build root path and ensure directory exists (optional for production)
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        use_local_storage = bool(local_root_path)
        
        if use_local_storage:
            # Development/local mode: use local storage + NAS backup
            root_path = f"{local_root_path}{user.shop_name}/"
            target_dir = os.path.join(root_path, f"Mockups/BaseMockups/{template_name}/")
            os.makedirs(target_dir, exist_ok=True)
        else:
            # Production mode: NAS only
            if not nas_storage.enabled:
                logging.error("Neither local storage nor NAS storage is available")
                raise MockupCreateError()
            logging.info("Production mode: saving files directly to NAS")
        # Handle watermark file
        watermark_content = await watermark_file.read()
        watermark_filename = watermark_file.filename or "watermark.png"
        
        if use_local_storage:
            # Local + NAS mode
            watermark_dir = os.path.join(root_path, f"Mockups/BaseMockups/Watermarks/")
            os.makedirs(watermark_dir, exist_ok=True)
            watermark_path = os.path.join(watermark_dir, watermark_filename)
            with open(watermark_path, "wb") as f:
                f.write(watermark_content)
        else:
            # NAS only mode
            watermark_relative_path = f"Mockups/BaseMockups/Watermarks/{watermark_filename}"
            success, watermark_path = nas_storage.save_file_content(
                file_content=watermark_content,
                shop_name=user.shop_name,
                relative_path=watermark_relative_path,
                local_root_path=None
            )
            if not success:
                logging.error("Failed to save watermark to NAS")
                raise MockupCreateError()
        # Process each uploaded file
        mockup_images = []
        for i, file in enumerate(files):
            if not file.filename:
                logging.warning(f"Skipping file {i} - no filename")
                continue

            # Generate a unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ".png"
            unique_filename = f"mockup_{mockup_id}_{i}{file_extension}"
            file_content = await file.read()
            
            if use_local_storage:
                # Local + NAS mode
                file_path = os.path.join(target_dir, unique_filename)
                with open(file_path, "wb") as f:
                    f.write(file_content)
                    
                # Upload mockup image to NAS
                try:
                    relative_path = f"Mockups/BaseMockups/{template_name}/{unique_filename}"
                    success = nas_storage.upload_file(
                        local_file_path=file_path,
                        shop_name=user.shop_name,
                        relative_path=relative_path
                    )
                    if success:
                        logging.info(f"Successfully uploaded mockup file to NAS: {relative_path}")
                    else:
                        logging.warning(f"Failed to upload mockup file to NAS: {relative_path}")
                except Exception as e:
                    logging.error(f"Error uploading mockup file to NAS: {e}")
                    # Don't fail the entire process if NAS upload fails
            else:
                # NAS only mode
                relative_path = f"Mockups/BaseMockups/{template_name}/{unique_filename}"
                success, file_path = nas_storage.save_file_content(
                    file_content=file_content,
                    shop_name=user.shop_name,
                    relative_path=relative_path,
                    local_root_path=None
                )
                if not success:
                    logging.error(f"Failed to save mockup file to NAS: {relative_path}")
                    continue  # Skip this file but continue with others

            # Create mockup image record
            mockup_image = MockupImage(
                mockups_id=mockup_id,
                filename=unique_filename,
                file_path=file_path,
                image_type=template_name,
                watermark_path=watermark_path
            )
            db.add(mockup_image)
            db.flush()  # Get the ID
            mockup_images.append(mockup_image)

        db.commit()
        
        # Return all uploaded mockup images
        if mockup_images:
            # Convert all mockup images to response models
            mockup_image_responses = [model.MockupImageResponse.model_validate(img) for img in mockup_images]
            logging.info(f"Returning {len(mockup_image_responses)} uploaded images: {[img.id for img in mockup_image_responses]}")
            return model.MockupImageUploadResponse(
                uploaded_images=mockup_image_responses,
                total=len(mockup_image_responses)
            )
        else:
            raise ValueError("No valid files were processed")

    except Exception as e:
        logging.error(f"Error uploading mockup files: {e}")
        db.rollback()
        raise MockupCreateError()


async def upload_mockup_files_to_etsy(
        db: Session, 
        user_id: UUID, 
        product_data: model.UploadToEtsyRequest):
    """
    Upload mockup files, process them, and create Etsy listings.
    This function replicates the functionality of the original upload_mockup endpoint.
    """
    try:
        ten_seconds_ago = datetime.utcnow() - timedelta(seconds=200)

        mockup_with_images = (
            db.query(Mockups)
            .options(
                joinedload(Mockups.mockup_images)
                .joinedload(MockupImage.mask_data)
            )
            .filter(
                Mockups.id == product_data.mockup_id,
                Mockups.user_id == user_id
            )
            .first()
        )

        # Get template to check if it's digital
        result = (
            db.query(
                User.shop_name,
                EtsyProductTemplate,
                Mockups,
                func.array_agg(DesignImages.id).label('design_ids')  # Aggregate designs into an array
            )
            .join(EtsyProductTemplate, EtsyProductTemplate.user_id == User.id)
            .join(Mockups, Mockups.product_template_id == EtsyProductTemplate.id)
            .join(DesignImages, DesignImages.user_id == User.id)  # Changed to inner join
            .filter(
                User.id == user_id,
                EtsyProductTemplate.id == product_data.product_template_id,
                Mockups.id == product_data.mockup_id,
                DesignImages.is_active == True,  # Only get active designs
                DesignImages.created_at >= ten_seconds_ago  
            )
            .group_by(
                User.shop_name,
                EtsyProductTemplate.id,
                Mockups.id
            )
            .order_by(desc(func.max(DesignImages.created_at)))  # Order by most recent design
            .first()
        )

        print(result)
        # Defensive check: if the call returned None or an unexpected structure, log and fail cleanly
        if not result or not hasattr(result, "__getitem__") or len(result) == 0:
            logging.error("upload_mockup_files_to_etsy: expected shop info from Etsy, got %r", result)
            # return or raise a FastAPI HTTPException so caller gets a clear error
            raise HTTPException(status_code=502, detail="Failed to retrieve shop information from Etsy")
        shop_name = result[0]
        template = result[1]
        mockup = result[2]
        design_ids = result[3]
        designs = (
            db.query(DesignImages)
            .filter(DesignImages.id.in_(design_ids))
            .all()
        )

        # Duplicate detection is now handled at the design side, so we use all designs
        logging.info(f"Processing {len(designs)} design(s) - duplicate detection handled at design level")
        
        # Check if we have any designs
        if not designs:
            logging.warning("No designs available for processing")
            return model.UploadToEtsyResponse(
                success=False,
                success_code=400,
                message="No designs available for processing. No Etsy listings created.",
            )

        mockup_mask_data = {}
        for mockup_image in mockup_with_images.mockup_images:
            if mockup_image.mask_data:
                all_masks = []
                all_points = []
                is_cropped = False
                alignment = 'center'
                
                for mask in mockup_image.mask_data:
                    masks_data = json.loads(mask.masks) if isinstance(mask.masks, str) else mask.masks
                    points_data = json.loads(mask.points) if isinstance(mask.points, str) else mask.points
                    all_masks.extend(masks_data)
                    all_points.extend(points_data)
                    is_cropped |= mask.is_cropped
                    if mask.alignment != 'center':
                        alignment = mask.alignment
                
                mockup_mask_data[mockup_image.id] = {
                    'masks': all_masks,
                    'points': all_points,
                    'is_cropped': is_cropped,
                    'alignment': alignment
                }
        
        # Create appropriate directories based on template type
        local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
        if not local_root_path:
            pass
            # raise HTTPException(status_code=500, detail="LOCAL_ROOT_PATH environment variable not set")
        
        mask_points_list, points_list, _, is_cropped, alignment = _get_mask_data_for_user_and_template(db, int(user_id), str(template.name))
        mask_data = {
            'masks': mask_points_list,
            'points': points_list,
            'is_cropped': is_cropped,
            'alignment': alignment
        }
        
        current_id_number, mockup_data, digital_image_paths = (create_mockups_for_etsy(
            designs=designs,
            mockup=mockup,
            root_path=f"{os.getenv('LOCAL_ROOT_PATH')}{shop_name}/",
            template_name=template.name,
            mask_data=mockup_mask_data
        ))
        is_digital = len(digital_image_paths) > 0
        current_id_number = int(current_id_number)
        logging.info(f"DEBUG API: process_uploaded_mockups returned: {result}")
        
        logging.info(f"DEBUG API: finished processing uploaded files")
        logging.info(f"DEBUG API: Starting Etsy API calls")
        etsy_api = EtsyAPI(user_id, db)
        
        # Parse materials and tags from string to list if needed
        materials = template.materials.split(',') if template.materials else []
        tags = template.tags.split(',') if template.tags else []
        
        logging.info(f"DEBUG API: Creating Etsy listings for {mockup_data} designs")
        for i,(design, mockups) in enumerate(mockup_data.items()):
            logging.info(f"DEBUG API: Creating listing {i+1}/{len(result)} for design: {design}")
            title = design.split(' ')[:2] if not is_digital else design.split('.')[0]
            listing_response = etsy_api.create_draft_listing(
                title=' '.join(title + [template.title]) if template.title else ' '.join(title),
                description=template.description,
                price=template.price,
                quantity=template.quantity,
                tags=tags,
                materials=materials,
                is_digital=is_digital,
                when_made=template.when_made,
                item_weight=template.item_weight,
                item_length=template.item_length,
                item_width=template.item_width,
                item_height=template.item_height,
                item_weight_unit=template.item_weight_unit,
                item_dimensions_unit=template.item_dimensions_unit,
                return_policy_id=template.return_policy_id,
            )
            listing_id = listing_response["listing_id"]
            logging.info(f"DEBUG API: Created listing {listing_id}, uploading {len(mockups)} images")
            
            # Upload images to the listing
            for j, mockup_image in enumerate(random.sample(mockups, len(mockups))):
                logging.info(f"DEBUG API: Uploading image {j+1}/{len(mockups)} to listing {listing_id}")
                etsy_api.upload_listing_image(listing_id, mockup_image)
            logging.info(f"DEBUG API: Completed listing {i+1}")

            # Upload digital file(s) if digital template
            if is_digital:
                # The digital file path and name are the key (design) in result.items()
                digital_file_path = os.path.join(f"{os.getenv('LOCAL_ROOT_PATH')}{shop_name}/Digital/{template.name}/", design)
                digital_file_name = design
                logging.info(f"DEBUG API: Uploading digital file {digital_file_name} to listing {listing_id}")
                try:
                    etsy_api.upload_listing_file(listing_id, digital_file_path, digital_file_name)
                    logging.info(f"DEBUG API: Successfully uploaded digital file {digital_file_name} to listing {listing_id}")
                except Exception as e:
                    logging.error(f"DEBUG API: Failed to upload digital file {digital_file_name} to listing {listing_id}: {e}")

        setattr(mockup, "starting_name", current_id_number)
        
        db.commit()
        db.refresh(mockup)

        logging.info(f"DEBUG API: Returning success response")
        return model.UploadToEtsyResponse(
            success=True,
            success_code=200,
            message="Successfully processed mockup files and created Etsy listings.",
        )
        
    except Exception as e:
        logging.error(f"DEBUG API: Error in upload-mockup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )
