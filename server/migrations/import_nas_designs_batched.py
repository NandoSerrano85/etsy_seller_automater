"""
Optimized NAS design import with batch processing and parallel execution

This migration scans the NAS storage at /share/Graphics/<shop_name>/<template_name>
for all users and templates, imports the images to the design_images table in batches
of approximately 500MB, with parallel processing for optimal performance.

Features:
- Batch processing in ~500MB chunks
- Parallel execution using multiprocessing
- Progress tracking and detailed logging
- Memory-efficient processing
- Error isolation per batch
"""

import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from sqlalchemy import text, create_engine
from pathlib import Path
import imagehash
from PIL import Image
from io import BytesIO
import uuid
from datetime import datetime, timezone
import os
import sys
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Import NAS storage utility
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.dirname(current_dir)
sys.path.insert(0, server_dir)

@dataclass
class FileInfo:
    """Information about a file to be processed"""
    user_id: str
    shop_name: str
    template_id: str
    template_name: str
    filename: str
    size: int
    file_path: str

@dataclass
class BatchResult:
    """Result of processing a batch"""
    batch_id: int
    processed: int
    skipped: int
    errors: int
    total_size: int
    processing_time: float
    error_details: List[str]

def calculate_phash_from_content(image_content: bytes, hash_size: int = 16) -> str:
    """Calculate perceptual hash for image content."""
    try:
        with Image.open(BytesIO(image_content)) as img:
            phash = imagehash.phash(img, hash_size=hash_size)
            return str(phash)
    except Exception as e:
        raise Exception(f"Error calculating phash: {e}")

def get_database_connection():
    """Create a new database connection for this process"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")

    engine = create_engine(database_url)
    return engine.connect()

def design_exists(connection, user_id: str, filename: str) -> bool:
    """Check if a design already exists for this user with this filename."""
    result = connection.execute(text("""
        SELECT COUNT(*) as count FROM design_images
        WHERE user_id = :user_id AND filename = :filename
    """), {"user_id": user_id, "filename": filename})
    count = result.fetchone()[0]
    return count > 0

def process_single_file(file_info: FileInfo) -> Tuple[bool, str, Optional[str]]:
    """
    Process a single file and return (success, error_message, phash)
    This function runs in a separate process
    """
    try:
        from server.src.utils.nas_storage import nas_storage

        # Download file content from NAS
        file_content = nas_storage.download_file_to_memory(
            file_info.shop_name,
            f"{file_info.template_name}/{file_info.filename}"
        )

        if not file_content:
            return False, f"Failed to download {file_info.filename}", None

        # Calculate phash
        phash = calculate_phash_from_content(file_content)
        return True, "", phash

    except Exception as e:
        return False, f"Error processing {file_info.filename}: {e}", None

def process_batch(batch_files: List[FileInfo], batch_id: int) -> BatchResult:
    """
    Process a batch of files in parallel within this batch
    This function runs in a separate process
    """
    start_time = time.time()
    processed = 0
    skipped = 0
    errors = 0
    error_details = []
    total_size = sum(f.size for f in batch_files)

    try:
        # Create database connection for this batch
        connection = get_database_connection()

        # Process files with thread pool for I/O operations
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all file processing tasks
            future_to_file = {
                executor.submit(process_single_file, file_info): file_info
                for file_info in batch_files
            }

            # Process results as they complete
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]

                try:
                    # Check if design already exists (in database process)
                    if design_exists(connection, file_info.user_id, file_info.filename):
                        skipped += 1
                        continue

                    # Get processing result
                    success, error_msg, phash = future.result()

                    if not success:
                        errors += 1
                        error_details.append(error_msg)
                        continue

                    # Insert into database
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
                        "user_id": file_info.user_id,
                        "filename": file_info.filename,
                        "file_path": file_info.file_path,
                        "phash": phash,
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now
                    })

                    # Associate with template
                    association_query = text("""
                        INSERT INTO design_template_association
                        (design_image_id, product_template_id)
                        VALUES (:design_id, :template_id)
                        ON CONFLICT DO NOTHING
                    """)

                    connection.execute(association_query, {
                        "design_id": design_id,
                        "template_id": file_info.template_id
                    })

                    processed += 1

                except Exception as e:
                    errors += 1
                    error_details.append(f"Database error for {file_info.filename}: {e}")

        # Commit all changes for this batch
        connection.commit()

    except Exception as e:
        error_details.append(f"Batch {batch_id} failed: {e}")
        errors += len(batch_files)
    finally:
        if 'connection' in locals():
            connection.close()

    processing_time = time.time() - start_time

    return BatchResult(
        batch_id=batch_id,
        processed=processed,
        skipped=skipped,
        errors=errors,
        total_size=total_size,
        processing_time=processing_time,
        error_details=error_details
    )

def create_batches(files: List[FileInfo], target_size_mb: int = 500) -> List[List[FileInfo]]:
    """Group files into batches of approximately target_size_mb"""
    target_size_bytes = target_size_mb * 1024 * 1024
    batches = []
    current_batch = []
    current_size = 0

    # Sort files by size (largest first) for better distribution
    files_sorted = sorted(files, key=lambda f: f.size, reverse=True)

    for file_info in files_sorted:
        # If adding this file would exceed target size and current batch isn't empty
        if current_size + file_info.size > target_size_bytes and current_batch:
            batches.append(current_batch)
            current_batch = [file_info]
            current_size = file_info.size
        else:
            current_batch.append(file_info)
            current_size += file_info.size

    # Add remaining files
    if current_batch:
        batches.append(current_batch)

    return batches

def collect_all_files(connection) -> List[FileInfo]:
    """Collect all files that need to be processed"""
    from server.src.utils.nas_storage import nas_storage

    # Get all users and templates
    users_result = connection.execute(text("""
        SELECT id, shop_name FROM users WHERE shop_name IS NOT NULL
    """))
    users = users_result.fetchall()

    templates_result = connection.execute(text("""
        SELECT id, name, user_id FROM etsy_product_templates
    """))
    templates = templates_result.fetchall()

    # Create mappings
    user_shop_mapping = {str(user[0]): user[1] for user in users}
    user_templates = {}
    for template in templates:
        template_id, template_name, user_id = template
        user_id_str = str(user_id)
        if user_id_str not in user_templates:
            user_templates[user_id_str] = []
        user_templates[user_id_str].append((str(template_id), template_name))

    all_files = []

    # Collect file information
    for user_id_str, shop_name in user_shop_mapping.items():
        if user_id_str not in user_templates:
            logging.info(f"No templates found for user {user_id_str} ({shop_name}), skipping")
            continue

        logging.info(f"Scanning files for user {user_id_str} ({shop_name})")

        for template_id, template_name in user_templates[user_id_str]:
            try:
                # List files in NAS directory
                template_path = f"{template_name}"
                files = nas_storage.list_files(shop_name, template_path)

                if not files:
                    continue

                for file_info in files:
                    filename = file_info['filename']
                    file_size = file_info['size']

                    # Skip non-image files
                    file_ext = Path(filename).suffix.lower()
                    if file_ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
                        continue

                    # Build complete file path
                    file_path = f"{nas_storage.base_path}/{shop_name}/{template_name}/{filename}"

                    all_files.append(FileInfo(
                        user_id=user_id_str,
                        shop_name=shop_name,
                        template_id=template_id,
                        template_name=template_name,
                        filename=filename,
                        size=file_size,
                        file_path=file_path
                    ))

            except Exception as e:
                logging.error(f"Error scanning template {template_name}: {e}")
                continue

    return all_files

def upgrade(connection):
    """Import designs from NAS using batch processing and parallel execution."""

    try:
        from server.src.utils.nas_storage import nas_storage

        if not nas_storage.enabled:
            logging.info("NAS storage is not enabled. Skipping design import migration.")
            return

        logging.info("Starting optimized NAS design import migration...")

        # Test NAS connectivity
        try:
            with nas_storage.get_sftp_connection() as sftp:
                sftp.getcwd()
            logging.info("NAS connectivity confirmed")
        except Exception as e:
            logging.warning(f"NAS connectivity test failed: {e}")
            logging.info("Skipping NAS import migration due to connectivity issues")
            return

        # Collect all files to process
        logging.info("📊 Scanning NAS for files...")
        all_files = collect_all_files(connection)

        if not all_files:
            logging.info("No files found to process")
            return

        total_size_mb = sum(f.size for f in all_files) / (1024 * 1024)
        logging.info(f"📈 Found {len(all_files)} files ({total_size_mb:.1f} MB total)")

        # Create batches
        batches = create_batches(all_files, target_size_mb=500)
        logging.info(f"📦 Created {len(batches)} batches for processing")

        # Log batch information
        for i, batch in enumerate(batches):
            batch_size_mb = sum(f.size for f in batch) / (1024 * 1024)
            logging.info(f"  Batch {i+1}: {len(batch)} files ({batch_size_mb:.1f} MB)")

        # Process batches in parallel
        max_workers = min(mp.cpu_count(), len(batches), 4)  # Limit concurrent batches
        logging.info(f"🚀 Processing batches with {max_workers} parallel workers...")

        total_processed = 0
        total_skipped = 0
        total_errors = 0
        start_time = time.time()

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch processing tasks
            future_to_batch = {
                executor.submit(process_batch, batch, i+1): i+1
                for i, batch in enumerate(batches)
            }

            # Process results as they complete
            for future in as_completed(future_to_batch):
                batch_id = future_to_batch[future]

                try:
                    result = future.result()
                    total_processed += result.processed
                    total_skipped += result.skipped
                    total_errors += result.errors

                    batch_size_mb = result.total_size / (1024 * 1024)
                    logging.info(
                        f"✅ Batch {result.batch_id} completed: "
                        f"{result.processed} processed, {result.skipped} skipped, "
                        f"{result.errors} errors ({batch_size_mb:.1f} MB in {result.processing_time:.1f}s)"
                    )

                    # Log detailed errors if any
                    for error in result.error_details[:5]:  # Limit error spam
                        logging.error(f"   └─ {error}")
                    if len(result.error_details) > 5:
                        logging.error(f"   └─ ... and {len(result.error_details) - 5} more errors")

                except Exception as e:
                    logging.error(f"❌ Batch {batch_id} failed completely: {e}")
                    total_errors += len(batches[batch_id - 1])

        total_time = time.time() - start_time

        logging.info(f"🎉 NAS design import completed in {total_time:.1f}s:")
        logging.info(f"  - Processed: {total_processed} designs")
        logging.info(f"  - Skipped: {total_skipped} existing designs")
        logging.info(f"  - Errors: {total_errors} failed imports")
        logging.info(f"  - Throughput: {total_size_mb/total_time:.1f} MB/s")

    except Exception as e:
        logging.error(f"Error during optimized NAS design import migration: {e}")
        raise e

def downgrade(connection):
    """Remove imported designs (optional - could be dangerous)."""
    logging.warning("Downgrade for NAS design import not implemented for safety reasons.")
    logging.warning("To remove imported designs, manually delete from design_images table where needed.")