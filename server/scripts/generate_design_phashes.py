#!/usr/bin/env python3
"""
Complete phash system setup script for existing design images.

This script:
1. Runs database migration to add phash column and index
2. Reads all design_images records from the database
3. For each design that doesn't have a phash, generates one from the file
4. Updates the database with the computed phash

Usage:
    python scripts/generate_design_phashes.py

This script can be run safely multiple times - it will skip migration if already applied
and only process designs that don't already have phashes.
"""

import os
import sys
import logging
from pathlib import Path
from PIL import Image
import imagehash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the server src directory to the path so we can import modules
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root / "src"))

from database.core import get_database_url
from entities.designs import DesignImages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_phash(file_path: str, hash_size: int = 16) -> str:
    """
    Calculate perceptual hash for an image file.

    Args:
        file_path: Path to the image file
        hash_size: Hash size (default 16 for 16x16 = 256-bit hash)

    Returns:
        String representation of the hash, or None if error
    """
    try:
        # Handle both NAS paths and local paths
        if file_path.startswith('/share/Graphics/'):
            # This is a NAS path - use as is
            full_path = file_path
        else:
            # This might be a relative path - we'll try to find it
            full_path = file_path

        with Image.open(full_path) as img:
            phash = imagehash.phash(img, hash_size=hash_size)
            return str(phash)
    except Exception as e:
        logger.warning(f"Failed to calculate phash for {file_path}: {e}")
        return None

def find_design_file(design_record, base_nas_path="/share/Graphics"):
    """
    Try to find the actual file for a design record.

    Args:
        design_record: DesignImages database record
        base_nas_path: Base path for NAS storage

    Returns:
        Full path to the file, or None if not found
    """
    possible_paths = []

    # Try the stored file_path directly
    if design_record.file_path:
        possible_paths.append(design_record.file_path)

    # Try constructing path from base NAS path + filename
    if design_record.filename:
        possible_paths.append(os.path.join(base_nas_path, design_record.filename))

    # Try looking in user-specific directories
    # Pattern: /share/Graphics/<shop_name>/<template_name>/filename
    if hasattr(design_record, 'user') and design_record.user:
        user_dirs = [
            os.path.join(base_nas_path, f"user_{design_record.user_id}"),
            os.path.join(base_nas_path, "default")
        ]

        for user_dir in user_dirs:
            if os.path.exists(user_dir):
                # Look for template directories
                for template_dir in os.listdir(user_dir):
                    template_path = os.path.join(user_dir, template_dir)
                    if os.path.isdir(template_path):
                        file_path = os.path.join(template_path, design_record.filename)
                        possible_paths.append(file_path)

    # Check each possible path
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path

    return None

def generate_phashes_batch(session, batch_size=100):
    """
    Generate phashes for designs in batches.

    Args:
        session: Database session
        batch_size: Number of records to process at once
    """
    # Count total designs without phash
    total_count = session.query(DesignImages).filter(
        DesignImages.phash.is_(None),
        DesignImages.is_active == True
    ).count()

    logger.info(f"Found {total_count} design images without phash")

    if total_count == 0:
        logger.info("All designs already have phashes!")
        return

    processed = 0
    updated = 0
    errors = 0

    # Process in batches
    offset = 0
    while offset < total_count:
        batch = session.query(DesignImages).filter(
            DesignImages.phash.is_(None),
            DesignImages.is_active == True
        ).offset(offset).limit(batch_size).all()

        if not batch:
            break

        logger.info(f"Processing batch {offset//batch_size + 1}: records {offset+1}-{min(offset+batch_size, total_count)} of {total_count}")

        for design in batch:
            processed += 1

            # Find the actual file
            file_path = find_design_file(design)

            if not file_path:
                logger.warning(f"Could not find file for design {design.id} (filename: {design.filename})")
                errors += 1
                continue

            # Calculate phash
            phash = calculate_phash(file_path)

            if phash:
                # Update database
                design.phash = phash
                updated += 1

                if updated % 10 == 0:
                    logger.info(f"Progress: {updated} designs updated, {errors} errors")
            else:
                errors += 1

        # Commit this batch
        try:
            session.commit()
            logger.info(f"Committed batch {offset//batch_size + 1}")
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            session.rollback()

        offset += batch_size

    logger.info(f"Migration complete! Processed: {processed}, Updated: {updated}, Errors: {errors}")

def run_database_migration(engine):
    """Run the database migration to add phash column."""
    logger.info("Running database migration to add phash column...")

    try:
        with engine.connect() as conn:
            # Check if phash column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'design_images' AND column_name = 'phash'
            """))

            if result.fetchone():
                logger.info("phash column already exists, skipping migration")
                return True

            # Add the phash column
            logger.info("Adding phash column to design_images table...")
            conn.execute(text("""
                ALTER TABLE design_images ADD COLUMN phash VARCHAR(64);
            """))

            # Add index for faster lookups
            logger.info("Creating index on phash column...")
            conn.execute(text("""
                CREATE INDEX idx_design_images_phash ON design_images(phash) WHERE phash IS NOT NULL;
            """))

            # Commit the transaction
            conn.commit()
            logger.info("Database migration completed successfully!")
            return True

    except Exception as e:
        logger.error(f"Error running database migration: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("Starting phash system setup for existing designs...")

    # Get database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    # Run database migration first
    if not run_database_migration(engine):
        logger.error("Database migration failed! Cannot continue with phash generation.")
        return

    # Process designs
    session = SessionLocal()
    try:
        generate_phashes_batch(session)
    finally:
        session.close()

    logger.info("Phash system setup complete!")

if __name__ == "__main__":
    main()