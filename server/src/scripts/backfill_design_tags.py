#!/usr/bin/env python3
"""
Batch process existing designs to generate AI tags

Usage:
    python -m server.src.scripts.backfill_design_tags --user-id UUID --limit 100
    python -m server.src.scripts.backfill_design_tags --all --batch-size 10
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from sqlalchemy import text

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.src.database.core import get_db
from server.src.entities.designs import DesignImages
from server.src.services.ai_tagging_service import ai_tagging_service
from server.src.utils.nas_storage import nas_storage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def backfill_tags(user_id=None, limit=None, batch_size=10, dry_run=False):
    """
    Generate tags for existing designs without tags

    Args:
        user_id: Optional - process only this user's designs
        limit: Optional - max number to process
        batch_size: Process N images before pausing (rate limiting)
        dry_run: If True, don't actually save tags
    """
    db = next(get_db())

    try:
        # Build query for designs without tags
        query = db.query(DesignImages).filter(
            DesignImages.is_active == True
        ).filter(
            (DesignImages.tags == None) | (DesignImages.tags == [])
        )

        if user_id:
            query = query.filter(DesignImages.user_id == user_id)

        if limit:
            query = query.limit(limit)

        designs = query.all()
        logging.info(f"Found {len(designs)} designs to process")

        if dry_run:
            logging.info("DRY RUN MODE - no changes will be saved")

        success_count = 0
        error_count = 0

        for i, design in enumerate(designs):
            try:
                logging.info(f"[{i+1}/{len(designs)}] Processing: {design.filename}")

                # Download image from NAS
                # Parse file_path: "/share/Graphics/{shop}/{template}/{file}"
                parts = design.file_path.split('/')
                if len(parts) < 5:
                    logging.error(f"Invalid file_path format: {design.file_path}")
                    error_count += 1
                    continue

                shop_name = parts[3]
                relative_path = '/'.join(parts[4:])

                image_bytes = nas_storage.download_file_to_memory(shop_name, relative_path)
                if not image_bytes:
                    logging.error(f"Failed to download: {design.file_path}")
                    error_count += 1
                    continue

                # Generate tags
                result = ai_tagging_service.generate_tags(image_bytes, design.filename)

                if not dry_run:
                    # Update design
                    design.tags = result['tags']
                    design.tags_metadata = result.get('metadata')
                    db.commit()

                success_count += 1
                logging.info(f"✓ Generated {len(result['tags'])} tags: {result['tags'][:5]}...")

                # Rate limiting: pause after each batch
                if (i + 1) % batch_size == 0:
                    import time
                    logging.info(f"Batch complete. Pausing 2s for rate limiting...")
                    time.sleep(2)

            except Exception as e:
                logging.error(f"Failed to process {design.filename}: {e}")
                error_count += 1
                if not dry_run:
                    db.rollback()

        logging.info(f"\nBackfill complete!")
        logging.info(f"  Success: {success_count}")
        logging.info(f"  Errors: {error_count}")
        logging.info(f"  Total: {len(designs)}")

    finally:
        db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Backfill AI tags for existing designs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all designs for a specific user
  python -m server.src.scripts.backfill_design_tags --user-id abc-123-def

  # Process first 50 designs (dry run)
  python -m server.src.scripts.backfill_design_tags --limit 50 --dry-run

  # Process all designs with custom batch size
  python -m server.src.scripts.backfill_design_tags --all --batch-size 5
        """
    )
    parser.add_argument('--user-id', help='Process only this user ID (UUID)')
    parser.add_argument('--limit', type=int, help='Max number of designs to process')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Batch size for rate limiting (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without saving')
    parser.add_argument('--all', action='store_true',
                       help='Process all users (requires confirmation)')

    args = parser.parse_args()

    if args.all and not args.user_id:
        confirm = input("Process ALL users' designs? This may take a while and incur API costs. (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    backfill_tags(
        user_id=args.user_id,
        limit=args.limit,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
