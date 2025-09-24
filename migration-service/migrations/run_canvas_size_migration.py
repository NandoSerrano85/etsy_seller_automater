#!/usr/bin/env python3
"""
Canvas size configuration migration

This migration handles canvas and size configuration updates.
Converted to standard migration service format.
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade(connection):
    """Canvas size configuration migration"""
    logger.info("🔄 Starting canvas size migration...")

    try:
        # Check if canvas_configs table exists
        result = connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'canvas_configs'
            )
        """))

        if not result.scalar():
            logger.info("✅ canvas_configs table doesn't exist - likely handled by other migrations")
            return

        # Add any canvas size specific updates here if needed
        # For now, just log completion since the table structure is handled by other migrations
        logger.info("✅ Canvas size migration completed successfully")

    except Exception as e:
        logger.error(f"❌ Canvas size migration failed: {e}")
        raise

def downgrade(connection):
    """Reverse canvas size migration (optional)"""
    logger.info("🔄 Reversing canvas size migration...")
    # Add rollback logic if needed
    logger.info("✅ Canvas size migration rollback completed") 