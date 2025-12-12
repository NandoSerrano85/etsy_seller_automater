"""
Import designs from NAS and populate design_images table with phash values

This migration scans the NAS storage at /share/Graphics/<shop_name>/<template_name>
for all users and templates, imports the images to the design_images table,
and generates phash values for duplicate detection.
"""

import logging
from sqlalchemy import text
from pathlib import Path
import imagehash
from PIL import Image
from io import BytesIO
import uuid
from datetime import datetime, timezone

# Import NAS storage utility - handle different deployment paths
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
possible_server_dirs = [
    os.path.join(current_dir, '..', '..', 'server'),  # Local: migration-service/migrations/../../../server
    '/app/server',                                     # Railway: /app/server
    os.path.join(current_dir, '..', 'server')        # Alternative: migrations/../server
]

for server_dir in possible_server_dirs:
    if os.path.exists(server_dir):
        sys.path.insert(0, server_dir)
        break

from server.src.utils.nas_storage import nas_storage

def calculate_phash_from_content(image_content: bytes, hash_size: int = 16) -> str:
    """
    Calculate perceptual hash for image content.

    Args:
        image_content: Image content as bytes
        hash_size: Hash size for the perceptual hash

    Returns:
        String representation of the hash
    """
    try:
        with Image.open(BytesIO(image_content)) as img:
            phash = imagehash.phash(img, hash_size=hash_size)
            return str(phash)
    except Exception as e:
        logging.error(f"Error calculating phash: {e}")
        raise

def get_all_users_and_shops(connection):
    """Get all users with their Etsy shop names from etsy_stores table."""
    # Query etsy_stores table for Etsy shop names (not users.shop_name which may be Shopify)
    result = connection.execute(text("""
        SELECT user_id, shop_name FROM etsy_stores WHERE is_active = true
    """))
    return result.fetchall()

def get_all_templates(connection):
    """Get all product templates."""
    result = connection.execute(text("""
        SELECT id, name, user_id FROM etsy_product_templates
    """))
    return result.fetchall()

def design_exists(connection, user_id: str, filename: str) -> bool:
    """Check if a design already exists for this user with this filename."""
    result = connection.execute(text("""
        SELECT COUNT(*) as count FROM design_images
        WHERE user_id = :user_id AND filename = :filename
    """), {"user_id": user_id, "filename": filename})
    count = result.fetchone()[0]
    return count > 0

def upgrade(connection):
    """Import designs from NAS and populate design_images table."""

    try:
        if not nas_storage.enabled:
            logging.info("NAS storage is not enabled. Skipping design import migration.")
            return

        logging.info("Starting NAS design import migration...")

        # Test NAS connectivity before proceeding
        try:
            # Quick connectivity test
            with nas_storage.get_sftp_connection() as sftp:
                sftp.getcwd()  # Simple test
            logging.info("NAS connectivity confirmed")
        except Exception as e:
            logging.warning(f"NAS connectivity test failed: {e}")
            logging.info("Skipping NAS import migration due to connectivity issues")
            return

    except Exception as e:
        logging.warning(f"Error during NAS migration setup: {e}")
        return

    try:
        # Get all users and templates
        users = get_all_users_and_shops(connection)
        templates = get_all_templates(connection)

        # Create a mapping of user_id to shop_name
        user_shop_mapping = {str(user[0]): user[1] for user in users}

        # Group templates by user
        user_templates = {}
        for template in templates:
            template_id, template_name, user_id = template
            user_id_str = str(user_id)
            if user_id_str not in user_templates:
                user_templates[user_id_str] = []
            user_templates[user_id_str].append((template_id, template_name))

        total_imported = 0
        total_skipped = 0
        total_errors = 0

        # Process each user
        for user_id_str, shop_name in user_shop_mapping.items():
            if user_id_str not in user_templates:
                logging.info(f"No templates found for user {user_id_str} ({shop_name}), skipping")
                continue

            logging.info(f"Processing user {user_id_str} ({shop_name})")

            # Process each template for this user
            for template_id, template_name in user_templates[user_id_str]:
                try:
                    logging.info(f"  Processing template: {template_name}")

                    # List files in NAS directory for this shop/template
                    template_path = f"{template_name}"
                    files = nas_storage.list_files(shop_name, template_path)

                    if not files:
                        logging.info(f"    No files found in {shop_name}/{template_name}")
                        continue

                    logging.info(f"    Found {len(files)} files")

                    # Process each file
                    for file_info in files:
                        filename = file_info['filename']
                        file_size = file_info['size']

                        # Skip if not an image file
                        file_ext = Path(filename).suffix.lower()
                        if file_ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                            logging.debug(f"      Skipping non-image file: {filename}")
                            continue

                        # Check if design already exists
                        if design_exists(connection, user_id_str, filename):
                            logging.debug(f"      Skipping existing design: {filename}")
                            total_skipped += 1
                            continue

                        try:
                            # Download file content from NAS
                            file_content = nas_storage.download_file_to_memory(
                                shop_name,
                                f"{template_name}/{filename}"
                            )

                            if not file_content:
                                logging.error(f"      Failed to download {filename}")
                                total_errors += 1
                                continue

                            # Calculate phash
                            phash = calculate_phash_from_content(file_content)

                            # Build file path (NAS path)
                            file_path = f"{nas_storage.base_path}/{shop_name}/{template_name}/{filename}"

                            # Insert into design_images table
                            design_id = str(uuid.uuid4())
                            insert_query = text("""
                                INSERT INTO design_images
                                (id, user_id, filename, file_path, phash, is_active, created_at, updated_at)
                                VALUES
                                (:id, :user_id, :filename, :file_path, :phash, :is_active, :created_at, :updated_at)
                            """)

                            now = datetime.now(timezone.utc)
                            connection.execute(insert_query, {
                                "id": design_id,
                                "user_id": user_id_str,
                                "filename": filename,
                                "file_path": file_path,
                                "phash": phash,
                                "is_active": True,
                                "created_at": now,
                                "updated_at": now
                            })

                            # Associate with the template
                            association_query = text("""
                                INSERT INTO design_template_association
                                (design_image_id, product_template_id)
                                VALUES (:design_id, :template_id)
                                ON CONFLICT DO NOTHING
                            """)

                            connection.execute(association_query, {
                                "design_id": design_id,
                                "template_id": str(template_id)
                            })

                            logging.info(f"      Imported: {filename} (phash: {phash[:8]}...)")
                            total_imported += 1

                        except Exception as e:
                            logging.error(f"      Error processing {filename}: {e}")
                            total_errors += 1
                            continue

                except Exception as e:
                    logging.error(f"  Error processing template {template_name}: {e}")
                    total_errors += 1
                    continue

        # Commit all changes
        connection.commit()

        logging.info(f"NAS design import completed:")
        logging.info(f"  - Imported: {total_imported} designs")
        logging.info(f"  - Skipped: {total_skipped} existing designs")
        logging.info(f"  - Errors: {total_errors} failed imports")

    except Exception as e:
        logging.error(f"Error during NAS design import migration: {e}")
        connection.rollback()
        raise e

def downgrade(connection):
    """Remove imported designs (optional - could be dangerous)."""
    logging.warning("Downgrade for NAS design import not implemented for safety reasons.")
    logging.warning("To remove imported designs, manually delete from design_images table where needed.")