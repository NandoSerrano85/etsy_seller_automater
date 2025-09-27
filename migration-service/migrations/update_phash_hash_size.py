"""
Update existing phashes to use consistent 16x16 hash size and generate missing hash types

This migration:
1. Updates existing phashes that were created with 8x8 hash size (16 chars) to 16x16 hash size (64 chars)
2. Generates missing ahash, dhash, and whash values for enhanced duplicate detection
3. Ensures all designs have complete hash coverage for the new multi-hash duplicate detection system
"""

import logging
from sqlalchemy import text
from PIL import Image
import imagehash
import os

def generate_all_hashes(image_path, hash_size=16):
    """Generate all hash types for an image"""
    try:
        with Image.open(image_path) as img:
            return {
                'phash': str(imagehash.phash(img, hash_size=hash_size)),
                'ahash': str(imagehash.average_hash(img, hash_size=hash_size)),
                'dhash': str(imagehash.dhash(img, hash_size=hash_size)),
                'whash': str(imagehash.whash(img, hash_size=hash_size))
            }
    except Exception as e:
        logging.error(f"Error generating hashes for {image_path}: {e}")
        return None


def upgrade(connection):
    """Update existing phashes to use 16x16 hash size and generate missing hash types."""
    try:
        logging.info("Starting comprehensive hash update migration...")

        # Step 1: Get designs with 8x8 phashes (16 character hashes) that need updating
        logging.info("Step 1: Updating 8x8 phashes to 16x16...")
        result = connection.execute(text("""
            SELECT id, file_path, phash
            FROM design_images
            WHERE phash IS NOT NULL
            AND LENGTH(phash) = 16
            AND is_active = true
        """))

        designs_with_old_phash = result.fetchall()
        logging.info(f"Found {len(designs_with_old_phash)} designs with 8x8 phashes to update")

        # Step 2: Get designs missing any of the new hash types
        logging.info("Step 2: Finding designs missing hash types...")
        result = connection.execute(text("""
            SELECT id, file_path, phash, ahash, dhash, whash
            FROM design_images
            WHERE is_active = true
            AND file_path IS NOT NULL
            AND (ahash IS NULL OR dhash IS NULL OR whash IS NULL OR LENGTH(phash) = 16)
        """))

        designs_missing_hashes = result.fetchall()
        logging.info(f"Found {len(designs_missing_hashes)} designs missing hash types")

        if not designs_missing_hashes:
            logging.info("All designs already have complete hash coverage")
            return

        updated_count = 0
        error_count = 0
        batch_size = 50

        # Process designs in batches
        for i in range(0, len(designs_missing_hashes), batch_size):
            batch = designs_missing_hashes[i:i + batch_size]
            logging.info(f"Processing batch {i//batch_size + 1}/{(len(designs_missing_hashes) + batch_size - 1)//batch_size}")

            for design in batch:
                design_id, file_path, old_phash, old_ahash, old_dhash, old_whash = design

                try:
                    # Check if file exists
                    if not file_path or not os.path.exists(file_path):
                        logging.warning(f"File not found for design {design_id}: {file_path}")
                        error_count += 1
                        continue

                    # Generate all hashes
                    hashes = generate_all_hashes(file_path, hash_size=16)
                    if not hashes:
                        error_count += 1
                        continue

                    # Determine what needs updating
                    updates = {}
                    update_parts = []

                    # Always update phash if it's 8x8 (16 chars)
                    if old_phash and len(old_phash) == 16:
                        updates['phash'] = hashes['phash']
                        update_parts.append("phash = :phash")
                    elif not old_phash:
                        updates['phash'] = hashes['phash']
                        update_parts.append("phash = :phash")

                    # Update missing hash types
                    if not old_ahash:
                        updates['ahash'] = hashes['ahash']
                        update_parts.append("ahash = :ahash")

                    if not old_dhash:
                        updates['dhash'] = hashes['dhash']
                        update_parts.append("dhash = :dhash")

                    if not old_whash:
                        updates['whash'] = hashes['whash']
                        update_parts.append("whash = :whash")

                    # Skip if nothing to update
                    if not update_parts:
                        continue

                    # Build and execute update query
                    updates['design_id'] = design_id
                    query = f"""
                        UPDATE design_images
                        SET {', '.join(update_parts)}
                        WHERE id = :design_id
                    """

                    connection.execute(text(query), updates)
                    updated_count += 1

                    # Log progress for significant updates
                    if old_phash and len(old_phash) == 16:
                        logging.info(f"Updated design {design_id}: phash {old_phash} -> {hashes['phash'][:8]}...")
                    else:
                        logging.debug(f"Updated missing hashes for design {design_id}")

                except Exception as e:
                    logging.error(f"Error updating hashes for design {design_id}: {e}")
                    error_count += 1
                    continue

        # Step 3: Summary
        logging.info("=" * 60)
        logging.info("HASH UPDATE MIGRATION SUMMARY")
        logging.info("=" * 60)
        logging.info(f"Designs processed: {len(designs_missing_hashes)}")
        logging.info(f"Successfully updated: {updated_count}")
        logging.info(f"Errors: {error_count}")

        # Step 4: Verify results
        logging.info("Step 4: Verifying migration results...")
        result = connection.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(phash) as with_phash,
                COUNT(ahash) as with_ahash,
                COUNT(dhash) as with_dhash,
                COUNT(whash) as with_whash,
                SUM(CASE WHEN LENGTH(phash) = 16 THEN 1 ELSE 0 END) as old_phash_count
            FROM design_images
            WHERE is_active = true
        """))

        stats = result.fetchone()
        total, with_phash, with_ahash, with_dhash, with_whash, old_phash_count = stats

        logging.info(f"Post-migration stats:")
        logging.info(f"  Total active designs: {total}")
        logging.info(f"  With phash: {with_phash} ({100*with_phash/total:.1f}%)")
        logging.info(f"  With ahash: {with_ahash} ({100*with_ahash/total:.1f}%)")
        logging.info(f"  With dhash: {with_dhash} ({100*with_dhash/total:.1f}%)")
        logging.info(f"  With whash: {with_whash} ({100*with_whash/total:.1f}%)")
        logging.info(f"  Remaining 8x8 phashes: {old_phash_count}")

        if old_phash_count > 0:
            logging.warning(f"Still have {old_phash_count} designs with 8x8 phashes (files may not exist)")

        logging.info("✅ Hash update migration completed successfully!")

    except Exception as e:
        logging.error(f"Error during comprehensive hash update migration: {e}")
        raise e

def downgrade(connection):
    """Downgrade not supported - would lose hash data and accuracy."""
    logging.warning("Downgrade for comprehensive hash update not supported")
    logging.warning("Cannot safely remove ahash, dhash, whash columns or convert 16x16 phashes back to 8x8")
    logging.warning("This would result in loss of duplicate detection accuracy and data integrity")

    # Optional: Clear the new hash columns if really needed (not recommended)
    # connection.execute(text("""
    #     UPDATE design_images
    #     SET ahash = NULL, dhash = NULL, whash = NULL
    #     WHERE ahash IS NOT NULL OR dhash IS NOT NULL OR whash IS NOT NULL
    # """))
    # logging.info("Cleared ahash, dhash, whash columns")

    raise NotImplementedError("Downgrade not implemented to prevent data loss")