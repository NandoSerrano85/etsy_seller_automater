#!/usr/bin/env python3
"""
Migration script to import existing design files from LOCAL_ROOT_PATH into design_images table.

This script will:
1. Scan LOCAL_ROOT_PATH/<shop_name>/<template_name>/ directories
2. Process existing design files (crop, resize, generate hashes)
3. Insert them into the design_images table with proper metadata
4. Handle duplicates and provide detailed logging

Usage:
    python migrate_existing_designs.py [--dry-run] [--shop-name SHOP_NAME] [--template-name TEMPLATE_NAME]

Options:
    --dry-run: Preview what would be migrated without making changes
    --shop-name: Only migrate designs for specific shop (optional)
    --template-name: Only migrate designs for specific template (optional)
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Set
import uuid

# Add server src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
server_src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, server_src_dir)

try:
    import cv2
    import numpy as np
    from PIL import Image
    import imagehash
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker, Session
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install: pip install opencv-python pillow imagehash sqlalchemy psycopg2")
    sys.exit(1)

# Import project modules
from database.core import get_db, engine
from entities.user import User
from entities.template import EtsyProductTemplate
from entities.designs import DesignImages
from utils.cropping import crop_transparent
from utils.resizing import resize_image_by_inches
from routes.designs.service import calculate_multiple_hashes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('design_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DesignMigrationStats:
    """Track migration statistics"""
    def __init__(self):
        self.total_files_found = 0
        self.total_users_processed = 0
        self.total_templates_processed = 0
        self.designs_created = 0
        self.designs_skipped_duplicate = 0
        self.designs_skipped_error = 0
        self.errors = []

    def log_summary(self):
        logger.info("=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files found: {self.total_files_found}")
        logger.info(f"Users processed: {self.total_users_processed}")
        logger.info(f"Templates processed: {self.total_templates_processed}")
        logger.info(f"Designs created: {self.designs_created}")
        logger.info(f"Designs skipped (duplicates): {self.designs_skipped_duplicate}")
        logger.info(f"Designs skipped (errors): {self.designs_skipped_error}")
        logger.info(f"Total errors: {len(self.errors)}")

        if self.errors:
            logger.info("\nERRORS:")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.error(f"  • {error}")
            if len(self.errors) > 10:
                logger.info(f"  ... and {len(self.errors) - 10} more errors")


class DesignMigrator:
    """Main migration class"""

    def __init__(self, db_session: Session, dry_run: bool = False):
        self.db = db_session
        self.dry_run = dry_run
        self.stats = DesignMigrationStats()
        self.local_root_path = os.getenv('LOCAL_ROOT_PATH', '')

        if not self.local_root_path:
            raise ValueError("LOCAL_ROOT_PATH environment variable not set")

        if not os.path.exists(self.local_root_path):
            raise ValueError(f"LOCAL_ROOT_PATH does not exist: {self.local_root_path}")

        logger.info(f"Initialized migrator - LOCAL_ROOT_PATH: {self.local_root_path}")
        logger.info(f"Dry run mode: {self.dry_run}")

    def get_existing_design_hashes(self, user_id: str) -> Set[str]:
        """Get all existing design hashes for a user to avoid duplicates"""
        try:
            result = self.db.execute(text("""
                SELECT DISTINCT phash, ahash, dhash, whash
                FROM design_images
                WHERE user_id = :user_id
                AND is_active = true
                AND (phash IS NOT NULL OR ahash IS NOT NULL OR dhash IS NOT NULL OR whash IS NOT NULL)
            """), {"user_id": user_id})

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
            logger.error(f"Failed to get existing hashes for user {user_id}: {e}")
            return set()

    def is_duplicate(self, hashes: Dict[str, str], existing_hashes: Set[str]) -> bool:
        """Check if any of the image hashes already exist"""
        for hash_type, hash_value in hashes.items():
            if hash_value and hash_value in existing_hashes:
                return True
        return False

    def process_image_file(self, file_path: str, template_name: str, user_id: str,
                          template_id: str, canvas_id: Optional[str] = None) -> Optional[Dict]:
        """Process a single image file and return design data"""
        try:
            logger.debug(f"Processing: {file_path}")

            # Step 1: Load and validate image
            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError(f"Could not load image: {file_path}")

            # Step 2: Crop transparent areas
            cropped_image = crop_transparent(image=img)
            if cropped_image is None:
                logger.warning(f"Failed to crop {file_path}, using original")
                cropped_image = img

            # Step 3: Resize the cropped image
            try:
                resized_image = resize_image_by_inches(
                    image=cropped_image,
                    image_type=template_name,
                    db=self.db,
                    canvas_id=canvas_id,
                    product_template_id=template_id,
                    target_dpi=400
                )
            except Exception as e:
                logger.warning(f"Failed to resize {file_path}: {e}, using cropped image")
                resized_image = cropped_image

            # Step 4: Convert to PIL for hash generation
            if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                # BGRA to RGBA
                pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGRA2RGBA))
            elif len(resized_image.shape) == 3 and resized_image.shape[2] == 3:
                # BGR to RGB
                pil_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))
            else:
                # Grayscale
                pil_image = Image.fromarray(resized_image)

            # Step 5: Generate multiple hashes
            hashes = {
                'phash': str(imagehash.phash(pil_image, hash_size=16)),
                'ahash': str(imagehash.average_hash(pil_image, hash_size=16)),
                'dhash': str(imagehash.dhash(pil_image, hash_size=16)),
                'whash': str(imagehash.whash(pil_image, hash_size=16))
            }

            # Step 6: Prepare design data
            filename = os.path.basename(file_path)
            design_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'filename': filename,
                'file_path': file_path,
                'phash': hashes['phash'],
                'ahash': hashes['ahash'],
                'dhash': hashes['dhash'],
                'whash': hashes['whash'],
                'canvas_config_id': canvas_id,
                'is_active': True,
                'is_digital': 'Digital' in file_path,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }

            return design_data

        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return None

    def find_design_files(self, shop_path: str) -> List[Dict]:
        """Find all design files in shop directory"""
        design_files = []
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}

        try:
            # Look for both regular and digital templates
            template_dirs = []

            # Regular templates
            if os.path.exists(shop_path):
                for item in os.listdir(shop_path):
                    item_path = os.path.join(shop_path, item)
                    if os.path.isdir(item_path) and item != 'Digital' and item != 'Mockups':
                        template_dirs.append((item_path, item, False))  # (path, name, is_digital)

            # Digital templates
            digital_path = os.path.join(shop_path, 'Digital')
            if os.path.exists(digital_path):
                for item in os.listdir(digital_path):
                    item_path = os.path.join(digital_path, item)
                    if os.path.isdir(item_path):
                        template_dirs.append((item_path, item, True))  # (path, name, is_digital)

            # Scan each template directory for image files
            for template_path, template_name, is_digital in template_dirs:
                if os.path.exists(template_path):
                    for file in os.listdir(template_path):
                        file_path = os.path.join(template_path, file)
                        if os.path.isfile(file_path):
                            file_ext = os.path.splitext(file)[1].lower()
                            if file_ext in image_extensions:
                                design_files.append({
                                    'file_path': file_path,
                                    'template_name': template_name,
                                    'is_digital': is_digital,
                                    'filename': file
                                })

        except Exception as e:
            error_msg = f"Error scanning {shop_path}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)

        return design_files

    def migrate_shop_designs(self, shop_name: str, target_template: Optional[str] = None) -> bool:
        """Migrate all designs for a specific shop"""
        try:
            logger.info(f"Processing shop: {shop_name}")

            # Get user by shop name
            user = self.db.query(User).filter(User.shop_name == shop_name).first()
            if not user:
                logger.warning(f"No user found for shop: {shop_name}")
                return False

            user_id = str(user.id)
            logger.info(f"Found user: {user_id} for shop: {shop_name}")

            # Get existing hashes to avoid duplicates
            existing_hashes = self.get_existing_design_hashes(user_id)
            logger.info(f"Found {len(existing_hashes)} existing design hashes for user")

            # Find design files
            shop_path = os.path.join(self.local_root_path, shop_name)
            if not os.path.exists(shop_path):
                logger.warning(f"Shop directory does not exist: {shop_path}")
                return False

            design_files = self.find_design_files(shop_path)
            logger.info(f"Found {len(design_files)} design files in {shop_path}")
            self.stats.total_files_found += len(design_files)

            if target_template:
                design_files = [f for f in design_files if f['template_name'] == target_template]
                logger.info(f"Filtered to {len(design_files)} files for template: {target_template}")

            # Get user's templates
            templates = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user.id
            ).all()

            template_map = {template.name: template for template in templates}
            logger.info(f"Found {len(template_map)} templates for user")

            # Process each design file
            designs_to_create = []
            processed_templates = set()

            for file_info in design_files:
                template_name = file_info['template_name']
                processed_templates.add(template_name)

                # Find matching template
                template = template_map.get(template_name)
                if not template:
                    logger.warning(f"No template found for: {template_name}, skipping file: {file_info['filename']}")
                    continue

                # Process the image file
                design_data = self.process_image_file(
                    file_path=file_info['file_path'],
                    template_name=template_name,
                    user_id=user_id,
                    template_id=str(template.id)
                )

                if not design_data:
                    self.stats.designs_skipped_error += 1
                    continue

                # Check for duplicates
                hashes = {
                    'phash': design_data['phash'],
                    'ahash': design_data['ahash'],
                    'dhash': design_data['dhash'],
                    'whash': design_data['whash']
                }

                if self.is_duplicate(hashes, existing_hashes):
                    logger.debug(f"Skipping duplicate: {file_info['filename']}")
                    self.stats.designs_skipped_duplicate += 1
                    continue

                # Add to creation list
                designs_to_create.append(design_data)
                existing_hashes.update(h for h in hashes.values() if h)

            # Create designs in database
            if designs_to_create and not self.dry_run:
                logger.info(f"Creating {len(designs_to_create)} new designs in database")

                try:
                    # Check if multi-tenant is enabled
                    multi_tenant = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

                    if multi_tenant:
                        # Get user's org_id
                        org_result = self.db.execute(text("""
                            SELECT org_id FROM users WHERE id = :user_id
                        """), {"user_id": user_id})
                        org_row = org_result.fetchone()
                        org_id = org_row[0] if org_row else None

                        for design_data in designs_to_create:
                            self.db.execute(text("""
                                INSERT INTO design_images
                                (id, user_id, org_id, filename, file_path, phash, ahash, dhash, whash,
                                 canvas_config_id, is_active, is_digital, created_at, updated_at)
                                VALUES (:id, :user_id, :org_id, :filename, :file_path, :phash, :ahash,
                                        :dhash, :whash, :canvas_config_id, :is_active, :is_digital,
                                        :created_at, :updated_at)
                            """), {**design_data, 'org_id': org_id})
                    else:
                        for design_data in designs_to_create:
                            self.db.execute(text("""
                                INSERT INTO design_images
                                (id, user_id, filename, file_path, phash, ahash, dhash, whash,
                                 canvas_config_id, is_active, is_digital, created_at, updated_at)
                                VALUES (:id, :user_id, :filename, :file_path, :phash, :ahash,
                                        :dhash, :whash, :canvas_config_id, :is_active, :is_digital,
                                        :created_at, :updated_at)
                            """), design_data)

                    self.db.commit()
                    self.stats.designs_created += len(designs_to_create)
                    logger.info(f"✅ Successfully created {len(designs_to_create)} designs")

                except Exception as e:
                    self.db.rollback()
                    error_msg = f"Failed to create designs in database: {e}"
                    logger.error(error_msg)
                    self.stats.errors.append(error_msg)
                    return False

            elif self.dry_run:
                logger.info(f"[DRY RUN] Would create {len(designs_to_create)} new designs")

            self.stats.total_users_processed += 1
            self.stats.total_templates_processed += len(processed_templates)

            logger.info(f"✅ Completed shop: {shop_name}")
            return True

        except Exception as e:
            error_msg = f"Error migrating shop {shop_name}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return False

    def migrate_all_shops(self, target_shop: Optional[str] = None, target_template: Optional[str] = None):
        """Migrate designs for all shops or a specific shop"""
        try:
            if target_shop:
                # Migrate specific shop
                if os.path.exists(os.path.join(self.local_root_path, target_shop)):
                    self.migrate_shop_designs(target_shop, target_template)
                else:
                    logger.error(f"Shop directory not found: {target_shop}")
            else:
                # Migrate all shops
                if not os.path.exists(self.local_root_path):
                    logger.error(f"LOCAL_ROOT_PATH does not exist: {self.local_root_path}")
                    return

                shop_dirs = [d for d in os.listdir(self.local_root_path)
                           if os.path.isdir(os.path.join(self.local_root_path, d))]

                logger.info(f"Found {len(shop_dirs)} shop directories to process")

                for shop_name in shop_dirs:
                    self.migrate_shop_designs(shop_name, target_template)

        except Exception as e:
            error_msg = f"Error in migrate_all_shops: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Migrate existing design files to database')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be migrated without making changes')
    parser.add_argument('--shop-name', type=str,
                       help='Only migrate designs for specific shop')
    parser.add_argument('--template-name', type=str,
                       help='Only migrate designs for specific template')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("🚀 Starting design migration")
    logger.info(f"Arguments: {vars(args)}")

    try:
        # Create database session
        db_session = next(get_db())

        # Initialize migrator
        migrator = DesignMigrator(db_session, dry_run=args.dry_run)

        # Run migration
        migrator.migrate_all_shops(
            target_shop=args.shop_name,
            target_template=args.template_name
        )

        # Log final stats
        migrator.stats.log_summary()

        if args.dry_run:
            logger.info("🔍 DRY RUN COMPLETED - No changes were made")
        else:
            logger.info("✅ MIGRATION COMPLETED")

    except KeyboardInterrupt:
        logger.info("❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'db_session' in locals():
            db_session.close()


if __name__ == '__main__':
    main()