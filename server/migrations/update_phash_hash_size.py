"""
Update existing phashes to use consistent 16x16 hash size

This migration updates existing phashes that were created with 8x8 hash size (16 chars)
to the new 16x16 hash size (64 chars) for consistent duplicate detection.
"""

import logging
from sqlalchemy import text
from PIL import Image
import imagehash
import os

def upgrade(connection):
    """Update existing phashes to use 16x16 hash size."""
    try:
        logging.info("Starting phash hash size update migration...")

        # Get all designs with 8x8 phashes (16 character hashes)
        result = connection.execute(text("""
            SELECT id, file_path, phash
            FROM design_images
            WHERE phash IS NOT NULL
            AND LENGTH(phash) = 16
            AND is_active = true
        """))

        designs_to_update = result.fetchall()

        if not designs_to_update:
            logging.info("No 8x8 phashes found to update")
            return

        logging.info(f"Found {len(designs_to_update)} designs with 8x8 phashes to update")

        updated_count = 0
        error_count = 0

        for design in designs_to_update:
            design_id, file_path, old_phash = design

            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    logging.warning(f"File not found for design {design_id}: {file_path}")
                    continue

                # Calculate new 16x16 phash
                with Image.open(file_path) as img:
                    new_phash = imagehash.phash(img, hash_size=16)
                    new_phash_str = str(new_phash)

                # Update the database record
                connection.execute(text("""
                    UPDATE design_images
                    SET phash = :new_phash
                    WHERE id = :design_id
                """), {
                    "new_phash": new_phash_str,
                    "design_id": design_id
                })

                updated_count += 1
                logging.info(f"Updated phash for design {design_id}: {old_phash} -> {new_phash_str[:8]}...")

            except Exception as e:
                logging.error(f"Error updating phash for design {design_id}: {e}")
                error_count += 1
                continue

        logging.info(f"Phash update completed: {updated_count} updated, {error_count} errors")

    except Exception as e:
        logging.error(f"Error during phash hash size update migration: {e}")
        raise e

def downgrade(connection):
    """Downgrade not supported - would lose phash accuracy."""
    logging.warning("Downgrade for phash hash size update not supported")
    logging.warning("Cannot convert 16x16 phashes back to 8x8 without losing accuracy")