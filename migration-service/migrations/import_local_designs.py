#!/usr/bin/env python3
"""
Local Design Migration for Migration Service

This migration imports existing design files from LOCAL_ROOT_PATH into the design_images table.
It integrates with the existing migration service architecture.

Directory structure expected:
LOCAL_ROOT_PATH/
├── shop1/
│   ├── template1/
│   │   ├── design1.png
│   │   └── design2.png
│   ├── template2/
│   │   └── design3.png
│   └── Digital/
│       └── template3/
│           └── digital_design1.png
└── shop2/
    └── template4/
        └── design4.png

Environment Variables:
- LOCAL_ROOT_PATH: Required. Path to root directory containing shop folders
- LOCAL_MIGRATION_DRY_RUN: Optional. Set to 'true' for dry run mode
- LOCAL_MIGRATION_SHOP: Optional. Migrate only specific shop
- LOCAL_MIGRATION_TEMPLATE: Optional. Migrate only specific template
"""

import os
import sys
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

def crop_transparent_simple(img):
    """Simple crop transparent function that doesn't require complex imports"""
    import numpy as np

    if len(img.shape) < 3 or img.shape[2] != 4:
        return img

    alpha = img[:, :, 3]
    rows = np.any(alpha != 0, axis=1)
    cols = np.any(alpha != 0, axis=0)

    if not np.any(rows) or not np.any(cols):
        return img

    ymin, ymax = np.where(rows)[0][[0, -1]]
    xmin, xmax = np.where(cols)[0][[0, -1]]

    return img[ymin:ymax+1, xmin:xmax+1]


def generate_hashes(image_array, hash_size=16):
    """Generate multiple perceptual hashes for an image array"""
    try:
        import cv2
        import numpy as np
        from PIL import Image
        import imagehash

        # Convert OpenCV image to PIL
        if len(image_array.shape) == 3 and image_array.shape[2] == 4:
            # BGRA to RGBA
            pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGRA2RGBA))
        elif len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # BGR to RGB
            pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
        else:
            # Grayscale
            pil_image = Image.fromarray(image_array)

        # Generate hashes
        return {
            'phash': str(imagehash.phash(pil_image, hash_size=hash_size)),
            'ahash': str(imagehash.average_hash(pil_image, hash_size=hash_size)),
            'dhash': str(imagehash.dhash(pil_image, hash_size=hash_size)),
            'whash': str(imagehash.whash(pil_image, hash_size=hash_size))
        }
    except ImportError as e:
        logger.error(f"Required dependencies not available: {e}")
        logger.error("Install: pip install opencv-python pillow imagehash")
        return {'phash': None, 'ahash': None, 'dhash': None, 'whash': None}
    except Exception as e:
        logger.error(f"Error generating hashes: {e}")
        return {'phash': None, 'ahash': None, 'dhash': None, 'whash': None}


def simple_resize(img, target_width=3000, target_height=3000):
    """Simple resize that maintains aspect ratio"""
    import cv2

    h, w = img.shape[:2]

    # Calculate scale to fit within target dimensions
    scale = min(target_width / w, target_height / h)

    if scale < 1:  # Only resize if image is larger than target
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return img


def process_image_file(file_path):
    """Process a single image file to get hash information"""
    try:
        import cv2

        # Load image
        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            logger.error(f"Could not load image: {file_path}")
            return None

        # Crop transparent areas
        cropped_img = crop_transparent_simple(img)

        # Simple resize to standardize for hash generation
        resized_img = simple_resize(cropped_img)

        # Generate hashes
        hashes = generate_hashes(resized_img)

        return hashes

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None


def find_design_files(local_root_path, target_shop=None, target_template=None):
    """Find all design files in the LOCAL_ROOT_PATH directory structure"""
    design_files = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}

    if not os.path.exists(local_root_path):
        logger.error(f"LOCAL_ROOT_PATH does not exist: {local_root_path}")
        return design_files

    # Iterate through shop directories
    for shop_name in os.listdir(local_root_path):
        if target_shop and shop_name != target_shop:
            continue

        shop_path = os.path.join(local_root_path, shop_name)
        if not os.path.isdir(shop_path):
            continue

        logger.info(f"Scanning shop: {shop_name}")

        # Look for template directories
        for item in os.listdir(shop_path):
            item_path = os.path.join(shop_path, item)

            # Skip non-directories
            if not os.path.isdir(item_path):
                continue

            # Handle Digital directory
            if item == 'Digital':
                digital_path = item_path
                if os.path.exists(digital_path):
                    for digital_template in os.listdir(digital_path):
                        if target_template and digital_template != target_template:
                            continue

                        digital_template_path = os.path.join(digital_path, digital_template)
                        if os.path.isdir(digital_template_path):
                            # Scan digital template directory
                            for file in os.listdir(digital_template_path):
                                file_path = os.path.join(digital_template_path, file)
                                if os.path.isfile(file_path):
                                    file_ext = os.path.splitext(file)[1].lower()
                                    if file_ext in image_extensions:
                                        design_files.append({
                                            'file_path': file_path,
                                            'shop_name': shop_name,
                                            'template_name': digital_template,
                                            'filename': file,
                                            'is_digital': True
                                        })

            # Handle regular template directories (skip Mockups)
            elif item != 'Mockups':
                if target_template and item != target_template:
                    continue

                template_path = item_path
                template_name = item

                # Scan template directory for images
                if os.path.exists(template_path):
                    for file in os.listdir(template_path):
                        file_path = os.path.join(template_path, file)
                        if os.path.isfile(file_path):
                            file_ext = os.path.splitext(file)[1].lower()
                            if file_ext in image_extensions:
                                design_files.append({
                                    'file_path': file_path,
                                    'shop_name': shop_name,
                                    'template_name': template_name,
                                    'filename': file,
                                    'is_digital': False
                                })

    logger.info(f"Found {len(design_files)} design files total")
    return design_files


def get_existing_hashes(conn):
    """Get all existing design hashes from database"""
    try:
        from sqlalchemy import text

        result = conn.execute(text("""
            SELECT DISTINCT phash, ahash, dhash, whash
            FROM design_images
            WHERE is_active = true
            AND (phash IS NOT NULL OR ahash IS NOT NULL OR dhash IS NOT NULL OR whash IS NOT NULL)
        """))

        existing_hashes = set()
        for row in result.fetchall():
            phash, ahash, dhash, whash = row
            if phash:
                existing_hashes.add(phash)
            if ahash:
                existing_hashes.add(ahash)
            if dhash:
                existing_hashes.add(dhash)
            if whash:
                existing_hashes.add(whash)

        return existing_hashes
    except Exception as e:
        logger.error(f"Error getting existing hashes: {e}")
        return set()


def get_user_template_mapping(conn):
    """Get mapping of shop_name -> user_id and template_name -> template_id"""
    user_mapping = {}
    template_mapping = {}

    try:
        from sqlalchemy import text

        # Get users
        result = conn.execute(text("SELECT id, shop_name FROM users WHERE shop_name IS NOT NULL"))
        for row in result.fetchall():
            user_mapping[row[1]] = str(row[0])  # shop_name -> user_id

        # Get templates
        result = conn.execute(text("""
            SELECT t.id, t.name, t.user_id, u.shop_name
            FROM etsy_product_templates t
            JOIN users u ON t.user_id = u.id
            WHERE u.shop_name IS NOT NULL
        """))
        for row in result.fetchall():
            template_id, template_name, user_id, shop_name = row
            key = f"{shop_name}|{template_name}"
            template_mapping[key] = {
                'template_id': str(template_id),
                'user_id': str(user_id)
            }

    except Exception as e:
        logger.error(f"Error getting user/template mapping: {e}")

    return user_mapping, template_mapping


def is_duplicate(hashes, existing_hashes):
    """Check if any hash already exists"""
    for hash_value in hashes.values():
        if hash_value and hash_value in existing_hashes:
            return True
    return False


def insert_design_batch(conn, designs_batch):
    """Insert a batch of designs into the database"""
    try:
        from sqlalchemy import text

        # Check if multi-tenant is enabled
        multi_tenant = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

        if multi_tenant:
            # Get org_ids for all users in this batch
            user_ids = list(set(design['user_id'] for design in designs_batch))
            user_org_map = {}

            for user_id in user_ids:
                result = conn.execute(text("SELECT org_id FROM users WHERE id = :user_id"),
                                    {"user_id": user_id})
                org_row = result.fetchone()
                user_org_map[user_id] = org_row[0] if org_row else None

            # Insert with org_id
            for design_data in designs_batch:
                org_id = user_org_map.get(design_data['user_id'])
                conn.execute(text("""
                    INSERT INTO design_images
                    (id, user_id, org_id, filename, file_path, phash, ahash, dhash, whash,
                     is_active, is_digital, created_at, updated_at)
                    VALUES (:id, :user_id, :org_id, :filename, :file_path, :phash, :ahash,
                            :dhash, :whash, :is_active, :is_digital, :created_at, :updated_at)
                """), {**design_data, 'org_id': org_id})
        else:
            # Insert without org_id
            for design_data in designs_batch:
                conn.execute(text("""
                    INSERT INTO design_images
                    (id, user_id, filename, file_path, phash, ahash, dhash, whash,
                     is_active, is_digital, created_at, updated_at)
                    VALUES (:id, :user_id, :filename, :file_path, :phash, :ahash,
                            :dhash, :whash, :is_active, :is_digital, :created_at, :updated_at)
                """), design_data)

        return True
    except Exception as e:
        logger.error(f"Error inserting design batch: {e}")
        return False


def upgrade(conn):
    """Main migration function"""
    logger.info("🚀 Starting local design migration")

    # Get environment variables
    local_root_path = os.getenv('LOCAL_ROOT_PATH')
    dry_run = os.getenv('LOCAL_MIGRATION_DRY_RUN', 'false').lower() == 'true'
    target_shop = os.getenv('LOCAL_MIGRATION_SHOP')
    target_template = os.getenv('LOCAL_MIGRATION_TEMPLATE')

    if not local_root_path:
        logger.warning("LOCAL_ROOT_PATH environment variable not set, skipping local design migration")
        return

    logger.info(f"LOCAL_ROOT_PATH: {local_root_path}")
    logger.info(f"Dry run mode: {dry_run}")
    if target_shop:
        logger.info(f"Target shop: {target_shop}")
    if target_template:
        logger.info(f"Target template: {target_template}")

    try:
        # Check dependencies
        try:
            import cv2
            import numpy as np
            from PIL import Image
            import imagehash
        except ImportError as e:
            logger.error(f"Required dependencies not available: {e}")
            logger.error("Install: pip install opencv-python pillow imagehash numpy")
            return

        # Get existing data
        logger.info("📊 Loading existing data from database...")
        existing_hashes = get_existing_hashes(conn)
        user_mapping, template_mapping = get_user_template_mapping(conn)

        logger.info(f"Found {len(existing_hashes)} existing design hashes")
        logger.info(f"Found {len(user_mapping)} users and {len(template_mapping)} templates")

        # Find design files
        logger.info("🔍 Scanning for design files...")
        design_files = find_design_files(local_root_path, target_shop, target_template)

        if not design_files:
            logger.info("No design files found")
            return

        # Process files
        logger.info(f"🔄 Processing {len(design_files)} design files...")

        created_count = 0
        skipped_count = 0
        error_count = 0
        batch_size = 50
        designs_to_create = []

        for i, file_info in enumerate(design_files):
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(design_files)} files processed")

            shop_name = file_info['shop_name']
            template_name = file_info['template_name']

            # Check if user and template exist
            user_id = user_mapping.get(shop_name)
            template_key = f"{shop_name}|{template_name}"
            template_info = template_mapping.get(template_key)

            if not user_id:
                logger.warning(f"No user found for shop: {shop_name}")
                skipped_count += 1
                continue

            if not template_info:
                logger.warning(f"No template found for: {shop_name}|{template_name}")
                skipped_count += 1
                continue

            # Process image
            hashes = process_image_file(file_info['file_path'])
            if not hashes or not any(hashes.values()):
                error_count += 1
                continue

            # Check for duplicates
            if is_duplicate(hashes, existing_hashes):
                logger.debug(f"Skipping duplicate: {file_info['filename']}")
                skipped_count += 1
                continue

            # Prepare design data
            design_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'filename': file_info['filename'],
                'file_path': file_info['file_path'],
                'phash': hashes['phash'],
                'ahash': hashes['ahash'],
                'dhash': hashes['dhash'],
                'whash': hashes['whash'],
                'is_active': True,
                'is_digital': file_info['is_digital'],
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }

            designs_to_create.append(design_data)

            # Add hashes to existing set to prevent duplicates in this batch
            for hash_value in hashes.values():
                if hash_value:
                    existing_hashes.add(hash_value)

            # Process batch
            if len(designs_to_create) >= batch_size:
                if not dry_run:
                    if insert_design_batch(conn, designs_to_create):
                        created_count += len(designs_to_create)
                    else:
                        error_count += len(designs_to_create)
                else:
                    logger.info(f"[DRY RUN] Would create batch of {len(designs_to_create)} designs")
                    created_count += len(designs_to_create)

                designs_to_create = []

        # Process remaining designs
        if designs_to_create:
            if not dry_run:
                if insert_design_batch(conn, designs_to_create):
                    created_count += len(designs_to_create)
                else:
                    error_count += len(designs_to_create)
            else:
                logger.info(f"[DRY RUN] Would create final batch of {len(designs_to_create)} designs")
                created_count += len(designs_to_create)

        # Final summary
        logger.info("=" * 60)
        logger.info("LOCAL DESIGN MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files found: {len(design_files)}")
        logger.info(f"Designs created: {created_count}")
        logger.info(f"Designs skipped (duplicates/missing templates): {skipped_count}")
        logger.info(f"Errors: {error_count}")

        if dry_run:
            logger.info("🔍 DRY RUN COMPLETED - No changes were made")
        else:
            logger.info("✅ Local design migration completed successfully!")

    except Exception as e:
        logger.error(f"Local design migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == '__main__':
    """For standalone testing"""
    import psycopg2
    from sqlalchemy import create_engine

    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Create engine and run migration
    engine = create_engine(database_url)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            upgrade(conn)
            if os.getenv('LOCAL_MIGRATION_DRY_RUN', 'false').lower() != 'true':
                trans.commit()
                print("✅ Migration committed")
            else:
                trans.rollback()
                print("🔍 Dry run - changes rolled back")
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise