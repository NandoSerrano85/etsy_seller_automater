"""
Add individual mask properties to mockup_mask_data table

This migration adds is_cropped_list and alignment_list columns to support
individual mask properties for each mask in a mockup, rather than applying
the same properties to all masks.

New columns:
- is_cropped_list: JSON array of boolean values, one for each mask
- alignment_list: JSON array of alignment strings, one for each mask
"""

import logging
from sqlalchemy import text

def upgrade(connection):
    """Add is_cropped_list and alignment_list columns to mockup_mask_data table."""

    try:
        logging.info("Adding individual mask properties columns to mockup_mask_data table...")

        # Check if columns already exist
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mockup_mask_data'
            AND column_name IN ('is_cropped_list', 'alignment_list')
        """))
        existing_columns = [row[0] for row in result.fetchall()]

        # Add is_cropped_list column if it doesn't exist
        if 'is_cropped_list' not in existing_columns:
            connection.execute(text("""
                ALTER TABLE mockup_mask_data
                ADD COLUMN is_cropped_list JSON
            """))
            logging.info("✅ Added is_cropped_list column")
        else:
            logging.info("ℹ️  is_cropped_list column already exists")

        # Add alignment_list column if it doesn't exist
        if 'alignment_list' not in existing_columns:
            connection.execute(text("""
                ALTER TABLE mockup_mask_data
                ADD COLUMN alignment_list JSON
            """))
            logging.info("✅ Added alignment_list column")
        else:
            logging.info("ℹ️  alignment_list column already exists")

        # Note: Transaction is managed by migration runner, don't commit here

        # Verify the columns were added
        result = connection.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'mockup_mask_data'
            AND column_name IN ('is_cropped_list', 'alignment_list')
            ORDER BY column_name
        """))

        columns = result.fetchall()
        if columns:
            logging.info("📋 New columns added successfully:")
            for column_name, data_type, is_nullable in columns:
                logging.info(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        else:
            logging.warning("⚠️  Could not verify column creation")

        # Optional: Migrate existing data by converting single values to arrays
        # Check if there are existing records with is_cropped/alignment values
        result = connection.execute(text("""
            SELECT COUNT(*)
            FROM mockup_mask_data
            WHERE is_cropped IS NOT NULL OR alignment IS NOT NULL
        """))
        existing_records = result.fetchone()[0]

        if existing_records > 0:
            logging.info(f"🔄 Found {existing_records} existing records with mask properties")
            logging.info("💡 Consider running a data migration to populate new list columns")
            logging.info("   Example: UPDATE mockup_mask_data SET is_cropped_list = '[true]', alignment_list = '[\"center\"]'")

        logging.info("✅ Individual mask properties migration completed successfully")

    except Exception as e:
        logging.error(f"❌ Error adding individual mask properties columns: {e}")
        connection.rollback()
        raise

def downgrade(connection):
    """Remove is_cropped_list and alignment_list columns from mockup_mask_data table."""

    try:
        logging.info("Removing individual mask properties columns from mockup_mask_data table...")

        # Drop is_cropped_list column if it exists
        try:
            connection.execute(text("""
                ALTER TABLE mockup_mask_data
                DROP COLUMN IF EXISTS is_cropped_list
            """))
            logging.info("✅ Removed is_cropped_list column")
        except Exception as e:
            logging.warning(f"⚠️  Could not remove is_cropped_list column: {e}")

        # Drop alignment_list column if it exists
        try:
            connection.execute(text("""
                ALTER TABLE mockup_mask_data
                DROP COLUMN IF EXISTS alignment_list
            """))
            logging.info("✅ Removed alignment_list column")
        except Exception as e:
            logging.warning(f"⚠️  Could not remove alignment_list column: {e}")

        # Note: Transaction is managed by migration runner, don't commit here

        logging.info("✅ Individual mask properties downgrade completed")

    except Exception as e:
        logging.error(f"❌ Error removing individual mask properties columns: {e}")
        # Note: Transaction is managed by migration runner, don't rollback here
        raise