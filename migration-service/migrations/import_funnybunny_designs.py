"""
Import FunnyBunnyTransfers designs from NAS to design_images table

This migration scans /share/Graphics/FunnyBunnyTransfers/UVDTF 16oz/
and imports all PNG files into the design_images table for the user.

Environment Variables Required:
- DATABASE_URL: PostgreSQL connection string
- QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD: NAS credentials
- FUNNYBUNNY_USER_EMAIL: Email of the user to import designs for (optional, defaults to first user)
"""

import logging
import os
import sys
import time
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import NAS storage utility
current_dir = os.path.dirname(os.path.abspath(__file__))
possible_server_dirs = [
    os.path.join(current_dir, '..', '..', 'server'),
    '/app/server',
    os.path.join(current_dir, '..', 'server')
]

for server_dir in possible_server_dirs:
    if os.path.exists(server_dir):
        sys.path.insert(0, server_dir)
        break

# Global nas_storage will be initialized in upgrade function
nas_storage = None

def calculate_all_hashes_from_content(image_content: bytes, hash_size: int = 16) -> dict:
    """Calculate all perceptual hashes for image content."""
    try:
        import imagehash
        from PIL import Image

        with Image.open(BytesIO(image_content)) as img:
            phash = imagehash.phash(img, hash_size=hash_size)
            ahash = imagehash.average_hash(img, hash_size=hash_size)
            dhash = imagehash.dhash(img, hash_size=hash_size)
            whash = imagehash.whash(img, hash_size=hash_size)

            return {
                'phash': str(phash),
                'ahash': str(ahash),
                'dhash': str(dhash),
                'whash': str(whash)
            }
    except Exception as e:
        raise Exception(f"Error calculating hashes: {e}")


def get_user_id(connection) -> Optional[str]:
    """Get user ID for FunnyBunnyTransfers."""
    from sqlalchemy import text

    # Try to get user by email from environment variable
    user_email = os.getenv('FUNNYBUNNY_USER_EMAIL')

    if user_email:
        result = connection.execute(
            text("SELECT id FROM users WHERE email = :email LIMIT 1"),
            {"email": user_email}
        )
        row = result.fetchone()
        if row:
            logger.info(f"Found user by email: {user_email}")
            return str(row[0])

    # Fallback: Get first active user
    result = connection.execute(
        text("SELECT id, email FROM users WHERE is_active = true ORDER BY created_at ASC LIMIT 1")
    )
    row = result.fetchone()
    if row:
        logger.info(f"Using first active user: {row[1]}")
        return str(row[0])

    logger.error("No users found in database")
    return None


def get_template_id(connection, template_name: str) -> Optional[str]:
    """Get template ID for the given template name."""
    from sqlalchemy import text

    result = connection.execute(
        text("SELECT id FROM etsy_product_templates WHERE name = :name LIMIT 1"),
        {"name": template_name}
    )
    row = result.fetchone()
    if row:
        return str(row[0])

    logger.warning(f"Template '{template_name}' not found in database")
    return None


def design_exists(connection, user_id: str, filename: str) -> bool:
    """Check if design already exists."""
    from sqlalchemy import text

    result = connection.execute(
        text("SELECT COUNT(*) FROM design_images WHERE user_id = :user_id AND filename = :filename"),
        {"user_id": user_id, "filename": filename}
    )
    count = result.fetchone()[0]
    return count > 0


def import_funnybunny_designs(connection, user_id: str, template_id: Optional[str]):
    """Import all designs from FunnyBunnyTransfers/UVDTF 16oz."""
    from sqlalchemy import text

    shop_name = "FunnyBunnyTransfers"
    template_name = "UVDTF 16oz"
    nas_path = f"{template_name}/"  # Relative path in NAS

    logger.info(f"Scanning NAS: /share/Graphics/{shop_name}/{template_name}/")

    # List all files in the directory
    try:
        with nas_storage.get_sftp_connection() as sftp:
            base_path = f"/share/Graphics/{shop_name}"
            full_path = f"{base_path}/{template_name}"

            logger.info(f"Listing files in: {full_path}")
            files = sftp.listdir(full_path)

            # Filter for PNG files only
            png_files = [f for f in files if f.lower().endswith('.png')]
            logger.info(f"Found {len(png_files)} PNG files")

    except Exception as e:
        logger.error(f"Failed to list NAS directory: {e}")
        return 0, 0

    if not png_files:
        logger.info("No PNG files found")
        return 0, 0

    # Check multi-tenant mode
    multi_tenant = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'
    org_id = None

    if multi_tenant:
        result = connection.execute(
            text("SELECT org_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        if row:
            org_id = row[0]

    # Process each file
    processed = 0
    skipped = 0
    errors = 0

    for filename in png_files:
        try:
            # Check if already exists
            if design_exists(connection, user_id, filename):
                logger.info(f"⏭️  Skipping existing: {filename}")
                skipped += 1
                continue

            # Download file content
            logger.info(f"📥 Downloading: {filename}")
            file_content = nas_storage.download_file_to_memory(
                shop_name,
                f"{template_name}/{filename}"
            )

            if not file_content:
                logger.error(f"Failed to download: {filename}")
                errors += 1
                continue

            # Calculate hashes
            logger.info(f"🔍 Calculating hashes for: {filename}")
            hashes = calculate_all_hashes_from_content(file_content)

            # Create design record
            design_id = str(uuid.uuid4())
            file_path = f"{template_name}/{filename}"
            now = datetime.now(timezone.utc)

            # Insert into database
            if multi_tenant and org_id:
                insert_query = text("""
                    INSERT INTO design_images
                    (id, user_id, org_id, filename, file_path, phash, ahash, dhash, whash, is_active, created_at, updated_at)
                    VALUES
                    (:id, :user_id, :org_id, :filename, :file_path, :phash, :ahash, :dhash, :whash, :is_active, :created_at, :updated_at)
                """)
                connection.execute(insert_query, {
                    "id": design_id,
                    "user_id": user_id,
                    "org_id": org_id,
                    "filename": filename,
                    "file_path": file_path,
                    "phash": hashes['phash'],
                    "ahash": hashes['ahash'],
                    "dhash": hashes['dhash'],
                    "whash": hashes['whash'],
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                })
            else:
                insert_query = text("""
                    INSERT INTO design_images
                    (id, user_id, filename, file_path, phash, ahash, dhash, whash, is_active, created_at, updated_at)
                    VALUES
                    (:id, :user_id, :filename, :file_path, :phash, :ahash, :dhash, :whash, :is_active, :created_at, :updated_at)
                """)
                connection.execute(insert_query, {
                    "id": design_id,
                    "user_id": user_id,
                    "filename": filename,
                    "file_path": file_path,
                    "phash": hashes['phash'],
                    "ahash": hashes['ahash'],
                    "dhash": hashes['dhash'],
                    "whash": hashes['whash'],
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                })

            # Create template association if template_id exists
            if template_id:
                association_id = str(uuid.uuid4())
                assoc_query = text("""
                    INSERT INTO design_product_template_association
                    (id, design_image_id, product_template_id)
                    VALUES
                    (:id, :design_image_id, :product_template_id)
                    ON CONFLICT DO NOTHING
                """)
                connection.execute(assoc_query, {
                    "id": association_id,
                    "design_image_id": design_id,
                    "product_template_id": template_id
                })

            connection.commit()
            logger.info(f"✅ Imported: {filename}")
            processed += 1

        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {e}")
            errors += 1
            try:
                connection.rollback()
            except:
                pass

    return processed, skipped, errors


def upgrade(connection):
    """Main migration function."""
    global nas_storage

    try:
        from server.src.utils.nas_storage import nas_storage as imported_nas_storage
        nas_storage = imported_nas_storage

        if not nas_storage.enabled:
            logger.info("NAS storage is not enabled. Skipping FunnyBunnyTransfers import.")
            return

        logger.info("=" * 60)
        logger.info("Starting FunnyBunnyTransfers design import migration")
        logger.info("=" * 60)

        # Test NAS connectivity
        try:
            with nas_storage.get_sftp_connection() as sftp:
                sftp.getcwd()
            logger.info("✅ NAS connectivity confirmed")
        except Exception as e:
            logger.error(f"❌ NAS connectivity failed: {e}")
            return

        # Get user ID
        user_id = get_user_id(connection)
        if not user_id:
            logger.error("Cannot proceed without user ID")
            return

        # Get template ID
        template_id = get_template_id(connection, "UVDTF 16oz")

        # Import designs
        start_time = time.time()
        processed, skipped, errors = import_funnybunny_designs(connection, user_id, template_id)
        elapsed = time.time() - start_time

        logger.info("=" * 60)
        logger.info("Migration completed!")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Skipped: {skipped}")
        logger.info(f"  Errors: {errors}")
        logger.info(f"  Time: {elapsed:.1f}s")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()


def downgrade(connection):
    """Rollback migration - remove imported designs."""
    from sqlalchemy import text

    logger.info("Rolling back FunnyBunnyTransfers design import...")

    # Get user ID
    user_id = get_user_id(connection)
    if not user_id:
        logger.error("Cannot rollback without user ID")
        return

    # Delete designs where file_path starts with "UVDTF 16oz/"
    result = connection.execute(
        text("""
            DELETE FROM design_images
            WHERE user_id = :user_id
            AND file_path LIKE 'UVDTF 16oz/%'
        """),
        {"user_id": user_id}
    )

    deleted_count = result.rowcount
    connection.commit()

    logger.info(f"Deleted {deleted_count} designs")
