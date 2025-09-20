#!/usr/bin/env python3
"""
Standalone migration runner for Railway deployment

This service runs independently from the main API and handles:
- Database schema migrations
- NAS design imports with phash generation
- Data transformations and cleanup

Environment Variables Required:
- DATABASE_URL: PostgreSQL connection string
- QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD: NAS access
- MIGRATION_MODE: 'all', 'startup', 'nas-only' (default: 'all')
"""

import os
import sys
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add server to Python path
sys.path.insert(0, '/app/server')

def setup_database():
    """Setup database connection"""
    try:
        from server.src.database.core import engine
        from sqlalchemy import text

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("✅ Database connection established")
        return engine
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

def discover_migrations():
    """Automatically discover all migration files"""
    import os
    import glob

    # Get all Python files in migrations directory (except __init__.py and imports)
    migrations_dir = '/app/server/migrations'
    if not os.path.exists(migrations_dir):
        migrations_dir = 'server/migrations'  # Fallback for local development

    migration_files = glob.glob(os.path.join(migrations_dir, '*.py'))
    migration_modules = []

    # Define dependency order for known migrations
    migration_order = [
        "add_multi_tenant_schema",        # Must run first for multi-tenant support
        "add_etsy_shop_id",               # Adds Etsy shop ID fields
        "add_phash_to_designs",           # Adds phash column to designs
        "remove_shopify_unique_constraint", # Removes Shopify constraints
        "update_phash_hash_size",         # Updates phash column size
        "separate_platform_connections"   # Separates platform connections
    ]

    # Exclude certain files
    excluded_files = [
        "__init__.py",
        "__pycache__",
        "import_nas_designs.py",         # Replaced by batched version
        "import_nas_designs_batched.py"  # Handled separately as NAS migration
    ]

    # First, add known migrations in order
    for migration_name in migration_order:
        module_name = f"server.migrations.{migration_name}"
        migration_modules.append(module_name)

    # Then discover any new migrations not in the known list
    for file_path in migration_files:
        filename = os.path.basename(file_path)
        if filename in excluded_files:
            continue

        migration_name = filename.replace('.py', '')
        module_name = f"server.migrations.{migration_name}"

        # Add if not already in the list
        if module_name not in migration_modules:
            migration_modules.append(module_name)
            logger.info(f"🔍 Discovered new migration: {migration_name}")

    return migration_modules

def run_startup_migrations(engine):
    """Run lightweight startup migrations"""
    logger.info("🔄 Running startup migrations...")

    # Auto-discover all migrations
    migrations = discover_migrations()
    logger.info(f"📋 Found {len(migrations)} migrations to run")

    success_count = 0

    for migration_name in migrations:
        try:
            logger.info(f"  🔄 Running {migration_name}...")

            # Import and run migration
            module = __import__(migration_name, fromlist=['upgrade'])

            with engine.connect() as conn:
                # Start transaction
                trans = conn.begin()
                try:
                    module.upgrade(conn)
                    trans.commit()
                    logger.info(f"  ✅ {migration_name} completed")
                    success_count += 1
                except Exception as e:
                    trans.rollback()
                    logger.error(f"  ❌ {migration_name} failed: {e}")

        except Exception as e:
            logger.error(f"  ❌ Could not load {migration_name}: {e}")

    logger.info(f"✅ Startup migrations completed: {success_count}/{len(migrations)} successful")

    # Log which migrations were run
    if success_count < len(migrations):
        logger.warning(f"⚠️  Some migrations may have failed or were skipped")
    return success_count

def run_nas_migration(engine):
    """Run NAS design import migration"""
    logger.info("🔄 Running optimized NAS design import migration...")

    try:
        # Check NAS configuration
        if not all([os.getenv('QNAP_HOST'), os.getenv('QNAP_USERNAME'), os.getenv('QNAP_PASSWORD')]):
            logger.warning("⚠️  NAS credentials not configured, skipping NAS migration")
            return False

        # Check if we should use batched processing
        use_batched = os.getenv('NAS_USE_BATCHED', 'true').lower() == 'true'

        if use_batched:
            logger.info("📦 Using batched parallel processing for NAS migration")
            from server.migrations.import_nas_designs_batched import upgrade

            # Batched migration handles its own transactions and connections
            try:
                with engine.connect() as conn:
                    upgrade(conn)
                logger.info("✅ NAS migration completed successfully")
                return True
            except Exception as e:
                logger.error(f"❌ NAS migration failed: {e}")
                return False
        else:
            logger.info("📄 Using sequential processing for NAS migration")
            from server.migrations.import_nas_designs import upgrade

            # Sequential migration uses single transaction
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    upgrade(conn)
                    trans.commit()
                    logger.info("✅ NAS migration completed successfully")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"❌ NAS migration failed: {e}")
                    return False

    except Exception as e:
        logger.error(f"❌ Could not run NAS migration: {e}")
        return False

def run_complex_migrations(engine):
    """Run complex/heavy migrations"""
    logger.info("🔄 Running complex migrations...")

    # Add complex migrations here as needed
    complex_migrations = [
        # "server.migrations.heavy_data_migration",
        # "server.migrations.index_creation",
    ]

    if not complex_migrations:
        logger.info("ℹ️  No complex migrations defined")
        return True

    success_count = 0

    for migration_name in complex_migrations:
        try:
            logger.info(f"  🔄 Running {migration_name}...")

            module = __import__(migration_name, fromlist=['upgrade'])

            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    module.upgrade(conn)
                    trans.commit()
                    logger.info(f"  ✅ {migration_name} completed")
                    success_count += 1
                except Exception as e:
                    trans.rollback()
                    logger.error(f"  ❌ {migration_name} failed: {e}")

        except Exception as e:
            logger.error(f"  ❌ Could not load {migration_name}: {e}")

    logger.info(f"✅ Complex migrations completed: {success_count}/{len(complex_migrations)} successful")
    return success_count == len(complex_migrations)

def main():
    """Main migration runner"""
    logger.info("🚀 Starting migration service...")

    # Get migration mode
    migration_mode = os.getenv('MIGRATION_MODE', 'all').lower()
    logger.info(f"📋 Migration mode: {migration_mode}")

    try:
        # Setup database
        engine = setup_database()

        success = True

        # Run migrations based on mode
        if migration_mode in ['all', 'startup']:
            startup_success = run_startup_migrations(engine)
            if migration_mode == 'startup':
                success = startup_success > 0

        if migration_mode in ['all', 'nas-only']:
            nas_success = run_nas_migration(engine)
            if migration_mode == 'nas-only':
                success = nas_success

        if migration_mode == 'all':
            complex_success = run_complex_migrations(engine)
            # For 'all' mode, we want both startup and complex to succeed
            # NAS is optional (depends on configuration)

        if success:
            logger.info("🎉 Migration service completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Migration service completed with errors")
            sys.exit(1)

    except Exception as e:
        logger.error(f"💥 Migration service failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()