#!/usr/bin/env python3
"""
Simple Design Migration Script

This script discovers existing design files from LOCAL_ROOT_PATH and adds them to the design_images table.
It generates proper hashes and handles duplicate detection.

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

Usage:
    python simple_design_migration.py

Environment variables required:
    - LOCAL_ROOT_PATH: Path to the root directory containing shop folders
    - DATABASE_URL: PostgreSQL connection string
"""

import os
import sys
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import cv2
import numpy as np
from PIL import Image
import imagehash

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def crop_transparent_simple(img):
    """Simple crop transparent function that doesn't require imports"""
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
    except Exception as e:
        logger.error(f"Error generating hashes: {e}")
        return {'phash': None, 'ahash': None, 'dhash': None, 'whash': None}


def simple_resize(img, target_width=3000, target_height=3000):
    """Simple resize that maintains aspect ratio"""
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


def find_design_files(local_root_path):
    """Find all design files in the LOCAL_ROOT_PATH directory structure"""
    design_files = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}

    if not os.path.exists(local_root_path):
        logger.error(f"LOCAL_ROOT_PATH does not exist: {local_root_path}")
        return design_files

    # Iterate through shop directories
    for shop_name in os.listdir(local_root_path):
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
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT phash, ahash, dhash, whash
                FROM design_images
                WHERE is_active = true
                AND (phash IS NOT NULL OR ahash IS NOT NULL OR dhash IS NOT NULL OR whash IS NOT NULL)
            """)

            existing_hashes = set()
            for row in cur.fetchall():
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
        # Get users
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, shop_name FROM users WHERE shop_name IS NOT NULL")
            for row in cur.fetchall():
                user_mapping[row['shop_name']] = str(row['id'])

        # Get templates
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT t.id, t.name, t.user_id, u.shop_name
                FROM etsy_product_templates t
                JOIN users u ON t.user_id = u.id
                WHERE u.shop_name IS NOT NULL
            """)
            for row in cur.fetchall():
                key = f"{row['shop_name']}|{row['name']}"
                template_mapping[key] = {
                    'template_id': str(row['id']),
                    'user_id': str(row['user_id'])
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


def insert_design(conn, design_data):
    """Insert a single design into the database"""
    try:
        # Check if multi-tenant is enabled
        multi_tenant = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

        with conn.cursor() as cur:
            if multi_tenant:
                # Get user's org_id
                cur.execute("SELECT org_id FROM users WHERE id = %s", (design_data['user_id'],))
                org_row = cur.fetchone()
                org_id = org_row[0] if org_row else None

                cur.execute("""
                    INSERT INTO design_images
                    (id, user_id, org_id, filename, file_path, phash, ahash, dhash, whash,
                     is_active, is_digital, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    design_data['id'], design_data['user_id'], org_id,
                    design_data['filename'], design_data['file_path'],
                    design_data['phash'], design_data['ahash'],
                    design_data['dhash'], design_data['whash'],
                    design_data['is_active'], design_data['is_digital'],
                    design_data['created_at'], design_data['updated_at']
                ))
            else:
                cur.execute("""
                    INSERT INTO design_images
                    (id, user_id, filename, file_path, phash, ahash, dhash, whash,
                     is_active, is_digital, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    design_data['id'], design_data['user_id'],
                    design_data['filename'], design_data['file_path'],
                    design_data['phash'], design_data['ahash'],
                    design_data['dhash'], design_data['whash'],
                    design_data['is_active'], design_data['is_digital'],
                    design_data['created_at'], design_data['updated_at']
                ))

        return True
    except Exception as e:
        logger.error(f"Error inserting design: {e}")
        return False


def main():
    """Main migration function"""
    logger.info("🚀 Starting simple design migration")

    # Get environment variables
    local_root_path = os.getenv('LOCAL_ROOT_PATH')
    database_url = os.getenv('DATABASE_URL')

    if not local_root_path:
        logger.error("LOCAL_ROOT_PATH environment variable not set")
        sys.exit(1)

    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    logger.info(f"LOCAL_ROOT_PATH: {local_root_path}")

    # Connect to database
    try:
        conn = psycopg2.connect(database_url)
        logger.info("✅ Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Get existing data
        logger.info("📊 Loading existing data from database...")
        existing_hashes = get_existing_hashes(conn)
        user_mapping, template_mapping = get_user_template_mapping(conn)

        logger.info(f"Found {len(existing_hashes)} existing design hashes")
        logger.info(f"Found {len(user_mapping)} users and {len(template_mapping)} templates")

        # Find design files
        logger.info("🔍 Scanning for design files...")
        design_files = find_design_files(local_root_path)

        if not design_files:
            logger.info("No design files found")
            return

        # Process files
        logger.info(f"🔄 Processing {len(design_files)} design files...")

        created_count = 0
        skipped_count = 0
        error_count = 0

        for i, file_info in enumerate(design_files):
            if i % 10 == 0:
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
            if not hashes:
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

            # Insert into database
            if insert_design(conn, design_data):
                created_count += 1
                # Add hashes to existing set to prevent duplicates in this batch
                for hash_value in hashes.values():
                    if hash_value:
                        existing_hashes.add(hash_value)
            else:
                error_count += 1

        # Commit all changes
        conn.commit()

        # Final summary
        logger.info("=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files found: {len(design_files)}")
        logger.info(f"Designs created: {created_count}")
        logger.info(f"Designs skipped (duplicates/missing templates): {skipped_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("✅ Migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()