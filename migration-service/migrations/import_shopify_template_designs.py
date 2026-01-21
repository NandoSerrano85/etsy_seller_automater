"""
Import Shopify template designs from NAS to design_images table

This migration scans all Shopify template directories in NAS and imports
design files, associating them with the appropriate templates.

Templates included:
- UVDTF 16oz, UVDTF 12oz, UVDTF 20oz
- UVDTF Decal
- MK
- UVDTF Bookmark
- UVDTF Ornament
- DTF
- Kindel Decal
- UVDTF Mirror
- UVDTF Milk Carton

Environment Variables Required:
- DATABASE_URL: PostgreSQL connection string
- QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD: NAS credentials
- SHOPIFY_SHOP_NAME: Name of Shopify shop folder in NAS (e.g., "FunnyBunnyTransfers")
- SHOPIFY_USER_EMAIL: Email of user to import for (optional, uses first user if not set)
"""

import logging
import os
import sys
import time
from typing import List, Dict, Optional, Tuple
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

# Templates to process
SHOPIFY_TEMPLATES = [
    "UVDTF 16oz",
    "UVDTF 12oz",
    "UVDTF 20oz",
    "UVDTF Decal",
    "MK",
    "UVDTF Bookmark",
    "UVDTF Ornament",
    "DTF",
    "Kindel Decal",
    "UVDTF Mirror",
    "UVDTF Milk Carton"
]


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
    """Get user ID for Shopify designs."""
    from sqlalchemy import text

    # Try to get user by email from environment variable
    user_email = os.getenv('SHOPIFY_USER_EMAIL')

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


def get_or_create_template_id(connection, template_name: str, user_id: str) -> Optional[str]:
    """Get or create template ID for the given template name."""
    from sqlalchemy import text

    # Check if template exists
    result = connection.execute(
        text("SELECT id FROM etsy_product_templates WHERE name = :name AND user_id = :user_id LIMIT 1"),
        {"name": template_name, "user_id": user_id}
    )
    row = result.fetchone()
    if row:
        logger.info(f"Template '{template_name}' exists with ID: {row[0]}")
        return str(row[0])

    # Create template if it doesn't exist
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Check if multi-tenant is enabled
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

    if multi_tenant and org_id:
        insert_query = text("""
            INSERT INTO etsy_product_templates
            (id, user_id, org_id, name, created_at, updated_at)
            VALUES
            (:id, :user_id, :org_id, :name, :created_at, :updated_at)
        """)
        connection.execute(insert_query, {
            "id": template_id,
            "user_id": user_id,
            "org_id": org_id,
            "name": template_name,
            "created_at": now,
            "updated_at": now
        })
    else:
        insert_query = text("""
            INSERT INTO etsy_product_templates
            (id, user_id, name, created_at, updated_at)
            VALUES
            (:id, :user_id, :name, :created_at, :updated_at)
        """)
        connection.execute(insert_query, {
            "id": template_id,
            "user_id": user_id,
            "name": template_name,
            "created_at": now,
            "updated_at": now
        })

    connection.commit()
    logger.info(f"✅ Created template '{template_name}' with ID: {template_id}")
    return template_id


def design_exists(connection, user_id: str, filename: str) -> bool:
    """Check if design already exists."""
    from sqlalchemy import text

    result = connection.execute(
        text("SELECT COUNT(*) FROM design_images WHERE user_id = :user_id AND filename = :filename"),
        {"user_id": user_id, "filename": filename}
    )
    count = result.fetchone()[0]
    return count > 0


def import_template_designs(connection, user_id: str, shop_name: str, template_name: str, template_id: str) -> Tuple[int, int, int]:
    """Import designs for a specific template."""
    from sqlalchemy import text

    logger.info(f"📂 Processing template: {template_name}")
    logger.info(f"   NAS path: /share/Graphics/{shop_name}/{template_name}/")

    # List files in the template directory
    try:
        with nas_storage.get_sftp_connection() as sftp:
            full_path = f"/share/Graphics/{shop_name}/{template_name}"

            # Check if directory exists
            try:
                sftp.stat(full_path)
            except:
                logger.warning(f"   Directory does not exist: {full_path}")
                return 0, 0, 0

            files = sftp.listdir(full_path)
            png_files = [f for f in files if f.lower().endswith('.png')]
            logger.info(f"   Found {len(png_files)} PNG files")

    except Exception as e:
        logger.error(f"   Failed to list directory: {e}")
        return 0, 0, 0

    if not png_files:
        return 0, 0, 0

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
                logger.debug(f"   ⏭️  Skipping existing: {filename}")
                skipped += 1
                continue

            # Download file content
            logger.debug(f"   📥 Downloading: {filename}")
            file_content = nas_storage.download_file_to_memory(
                shop_name,
                f"{template_name}/{filename}"
            )

            if not file_content:
                logger.error(f"   Failed to download: {filename}")
                errors += 1
                continue

            # Calculate hashes
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

            # Create template association
            assoc_query = text("""
                INSERT INTO design_template_association
                (design_image_id, product_template_id)
                VALUES
                (:design_image_id, :product_template_id)
                ON CONFLICT DO NOTHING
            """)
            connection.execute(assoc_query, {
                "design_image_id": design_id,
                "product_template_id": template_id
            })

            connection.commit()
            processed += 1
            if processed % 10 == 0:
                logger.info(f"   Progress: {processed}/{len(png_files)}")

        except Exception as e:
            logger.error(f"   ❌ Error processing {filename}: {e}")
            errors += 1
            try:
                connection.rollback()
            except:
                pass

    logger.info(f"   ✅ Template complete: {processed} imported, {skipped} skipped, {errors} errors")
    return processed, skipped, errors


def upgrade(connection):
    """Main migration function."""
    global nas_storage

    try:
        from server.src.utils.nas_storage import nas_storage as imported_nas_storage
        nas_storage = imported_nas_storage

        if not nas_storage.enabled:
            logger.info("NAS storage is not enabled. Skipping Shopify template import.")
            return

        logger.info("=" * 70)
        logger.info("Starting Shopify template design import migration")
        logger.info("=" * 70)

        # Test NAS connectivity
        try:
            with nas_storage.get_sftp_connection() as sftp:
                sftp.getcwd()
            logger.info("✅ NAS connectivity confirmed")
        except Exception as e:
            logger.error(f"❌ NAS connectivity failed: {e}")
            return

        # Get Shopify shop name from environment
        shop_name = os.getenv('SHOPIFY_SHOP_NAME', 'FunnyBunnyTransfers')
        logger.info(f"Using Shopify shop name: {shop_name}")

        # Get user ID
        user_id = get_user_id(connection)
        if not user_id:
            logger.error("Cannot proceed without user ID")
            return

        # Process each template
        start_time = time.time()
        total_processed = 0
        total_skipped = 0
        total_errors = 0

        for template_name in SHOPIFY_TEMPLATES:
            # Get or create template
            template_id = get_or_create_template_id(connection, template_name, user_id)
            if not template_id:
                logger.error(f"Failed to get/create template: {template_name}")
                continue

            # Import designs for this template
            processed, skipped, errors = import_template_designs(
                connection, user_id, shop_name, template_name, template_id
            )

            total_processed += processed
            total_skipped += skipped
            total_errors += errors

        elapsed = time.time() - start_time

        logger.info("=" * 70)
        logger.info("Migration completed!")
        logger.info(f"  Templates processed: {len(SHOPIFY_TEMPLATES)}")
        logger.info(f"  Designs imported: {total_processed}")
        logger.info(f"  Designs skipped: {total_skipped}")
        logger.info(f"  Errors: {total_errors}")
        logger.info(f"  Time: {elapsed:.1f}s")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()


def downgrade(connection):
    """Rollback migration - remove imported designs."""
    from sqlalchemy import text

    logger.info("Rolling back Shopify template design import...")

    # Get user ID
    user_id = get_user_id(connection)
    if not user_id:
        logger.error("Cannot rollback without user ID")
        return

    # Delete designs for each template
    for template_name in SHOPIFY_TEMPLATES:
        result = connection.execute(
            text("""
                DELETE FROM design_images
                WHERE user_id = :user_id
                AND file_path LIKE :file_path_pattern
            """),
            {"user_id": user_id, "file_path_pattern": f"{template_name}/%"}
        )
        deleted = result.rowcount
        if deleted > 0:
            logger.info(f"Deleted {deleted} designs from {template_name}")

    connection.commit()
    logger.info("Rollback complete")
