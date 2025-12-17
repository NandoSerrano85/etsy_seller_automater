#!/usr/bin/env python3
"""
Standalone migration runner for Railway deployment

This service runs independently from the main API and handles:
- Database schema migrations
- Local design imports from LOCAL_ROOT_PATH with phash generation
- NAS design imports with phash generation
- Data transformations and cleanup

Environment Variables Required:
- DATABASE_URL: PostgreSQL connection string

Optional:
- LOCAL_ROOT_PATH: Local design directory path for local-only migration
- LOCAL_MIGRATION_DRY_RUN: Set to 'true' for dry run mode
- LOCAL_MIGRATION_SHOP: Migrate only specific shop
- LOCAL_MIGRATION_TEMPLATE: Migrate only specific template
- QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD: NAS access
- MIGRATION_MODE: 'all', 'startup', 'local-only', 'nas-only' (default: 'all')
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

# Add server to Python path for Railway deployments
sys.path.insert(0, '/app/server')
# Add local server path for development
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'server'))

def setup_database():
    """Setup database connection"""
    try:
        # Try to import from server first (Railway deployment)
        try:
            from server.src.database.core import engine
        except ImportError:
            # Fallback: create engine directly from DATABASE_URL
            from sqlalchemy import create_engine
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable is required")
            engine = create_engine(database_url)

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
    """Automatically discover all migration files from migration-service/migrations/"""
    import glob
    import importlib.util

    # Get migrations from our own migrations directory
    current_dir = os.path.dirname(__file__)

    # Try different possible locations for migrations directory
    possible_migrations_dirs = [
        os.path.join(current_dir, 'migrations'),  # Local development: migration-service/migrations/
        '/app/migrations',                         # Railway: /app/migrations/ (from Dockerfile)
        '/app/migration-service/migrations'       # Alternative Railway path
    ]

    migrations_dir = None
    for dir_path in possible_migrations_dirs:
        if os.path.exists(dir_path):
            migrations_dir = dir_path
            logger.info(f"📁 Using migrations directory: {migrations_dir}")
            break

    if migrations_dir is None:
        logger.warning(f"⚠️  Migrations directory not found in any of: {possible_migrations_dirs}")
        return []

    migration_files = glob.glob(os.path.join(migrations_dir, '*.py'))
    migration_modules = []

    # Define dependency order for known migrations
    migration_order = [
        # Core schema migrations (must run first)
        "add_multi_tenant_schema",        # Must run first for multi-tenant support
        "migration_add_railway_entities", # Railway entities

        # Platform-specific migrations
        "add_etsy_shop_id",               # Adds Etsy shop ID fields
        "separate_platform_connections",   # Separates platform connections
        "remove_shopify_unique_constraint", # Removes Shopify constraints
        "add_production_partner_ids",  # Adds production_partner_ids column
        "add_readiness_state_id",         # Adds readiness_state_id column
        "add_shopify_product_templates",  # Adds Shopify product templates table
        "add_org_id_to_shopify_templates", # Adds org_id column to shopify templates if missing
        "add_variant_configs_to_shopify_templates", # Adds variant_configs JSON column for nested variants
        "add_craftflow_commerce_templates", # Adds CraftFlow Commerce templates table and mockups support

        # Design-related migrations
        "add_phash_to_designs",           # Adds phash column to designs
        "add_additional_hash_columns",    # Adds ahash, dhash, whash columns
        "update_phash_hash_size",         # Updates phash column size and generates all hashes
        "add_platform_to_designs",        # Adds platform column to separate Shopify and Etsy designs
        "import_local_designs",           # Import local designs with all hash calculations
        "run_canvas_size_migration",      # Canvas size updates
        "migration_add_printers_and_canvas_updates", # Printer and canvas updates

        # Ecommerce migrations
        "create_ecommerce_tables",        # Creates all ecommerce tables for storefront
        "fix_storefront_settings_user_id_type",  # Fixes user_id column type from INTEGER to UUID
        "add_updated_at_to_product_reviews",  # Adds missing updated_at column to product reviews

        # Data migrations (triggered by env vars)
        "regenerate_etsy_mockups_with_watermark",  # Regenerates Etsy mockups with watermarks (REGENERATE_ETSY_MOCKUPS=true)
    ]

    # Exclude certain files
    excluded_files = [
        "__init__.py",
        "__pycache__",
        "import_nas_designs.py",         # Replaced by batched version
        "import_nas_designs_batched.py", # Handled separately as NAS migration
        "clear_design_images.py",        # Manual cleanup script with user input
        "import_funnybunny_designs.py",  # Manual import script
        "import_shopify_template_designs.py"  # Manual import script
    ]

    # Add migrations directory to Python path for imports
    if migrations_dir not in sys.path:
        sys.path.insert(0, migrations_dir)

    # First, add known migrations in order
    for migration_name in migration_order:
        migration_file = os.path.join(migrations_dir, f"{migration_name}.py")
        if os.path.exists(migration_file):
            migration_modules.append(migration_name)
        else:
            logger.debug(f"🔍 Known migration not found: {migration_name}")

    # Then discover any new migrations not in the known list
    for file_path in migration_files:
        filename = os.path.basename(file_path)
        if filename in excluded_files:
            continue

        migration_name = filename.replace('.py', '')

        # Add if not already in the list
        if migration_name not in migration_modules:
            migration_modules.append(migration_name)
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
            import importlib.util
            migration_file_path = os.path.join(os.path.dirname(__file__), 'migrations', f"{migration_name}.py")
            spec = importlib.util.spec_from_file_location(migration_name, migration_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

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

def run_local_design_migration(engine):
    """Run local design import migration"""
    logger.info("🔄 Running local design import migration...")

    try:
        # Check LOCAL_ROOT_PATH configuration
        local_root_path = os.getenv('LOCAL_ROOT_PATH')
        if not local_root_path:
            logger.info("ℹ️  LOCAL_ROOT_PATH not configured, skipping local design migration")
            return True  # Return True since this is optional

        if not os.path.exists(local_root_path):
            logger.warning(f"⚠️  LOCAL_ROOT_PATH does not exist: {local_root_path}, skipping local design migration")
            return True  # Return True since this is optional

        # Use the same directory discovery logic as discover_migrations()
        current_dir = os.path.dirname(__file__)
        possible_migrations_dirs = [
            os.path.join(current_dir, 'migrations'),
            '/app/migrations',
            '/app/migration-service/migrations'
        ]

        migration_dir = None
        for dir_path in possible_migrations_dirs:
            if os.path.exists(dir_path):
                migration_dir = dir_path
                break

        if migration_dir is None:
            logger.error("❌ Could not find migrations directory for local design migration")
            return False

        import importlib.util
        migration_file = os.path.join(migration_dir, 'import_local_designs.py')

        if not os.path.exists(migration_file):
            logger.warning("⚠️  Local design migration file not found, skipping")
            return True  # Return True since this is optional

        spec = importlib.util.spec_from_file_location('import_local_designs', migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Local design migration handles its own transactions
        try:
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    module.upgrade(conn)
                    trans.commit()
                    logger.info("✅ Local design migration completed successfully")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"❌ Local design migration failed: {e}")
                    return False
        except Exception as e:
            logger.error(f"❌ Local design migration failed: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ Could not run local design migration: {e}")
        return False


def run_nas_migration(engine):
    """Run NAS design import migration"""
    logger.info("🔄 Running optimized NAS design import migration...")

    try:
        # Check NAS configuration
        if not all([os.getenv('QNAP_HOST'), os.getenv('QNAP_USERNAME'), os.getenv('QNAP_PASSWORD')]):
            logger.info("ℹ️  NAS credentials not configured, skipping NAS migration")
            return True  # Return True since this is optional

        # Check if we should use batched processing
        use_batched = os.getenv('NAS_USE_BATCHED', 'true').lower() == 'true'

        import importlib.util

        # Use the same directory discovery logic as discover_migrations()
        current_dir = os.path.dirname(__file__)
        possible_migrations_dirs = [
            os.path.join(current_dir, 'migrations'),
            '/app/migrations',
            '/app/migration-service/migrations'
        ]

        migration_dir = None
        for dir_path in possible_migrations_dirs:
            if os.path.exists(dir_path):
                migration_dir = dir_path
                break

        if migration_dir is None:
            logger.error("❌ Could not find migrations directory for NAS migration")
            return False

        if use_batched:
            logger.info("📦 Using batched parallel processing for NAS migration")
            migration_file = os.path.join(migration_dir, 'import_nas_designs_batched.py')
            spec = importlib.util.spec_from_file_location('import_nas_designs_batched', migration_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Batched migration handles its own transactions and connections
            try:
                with engine.connect() as conn:
                    module.upgrade(conn)
                logger.info("✅ NAS migration completed successfully")
                return True
            except Exception as e:
                logger.error(f"❌ NAS migration failed: {e}")
                return False
        else:
            logger.info("📄 Using sequential processing for NAS migration")
            migration_file = os.path.join(migration_dir, 'import_nas_designs.py')
            spec = importlib.util.spec_from_file_location('import_nas_designs', migration_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Sequential migration uses single transaction
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    module.upgrade(conn)
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

            import importlib.util
            migration_file_path = os.path.join(os.path.dirname(__file__), 'migrations', f"{migration_name}.py")
            spec = importlib.util.spec_from_file_location(migration_name, migration_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

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

        if migration_mode in ['all', 'local-only']:
            local_success = run_local_design_migration(engine)
            if migration_mode == 'local-only':
                success = local_success

        if migration_mode in ['all', 'nas-only']:
            nas_success = run_nas_migration(engine)
            if migration_mode == 'nas-only':
                success = nas_success

        if migration_mode == 'all':
            complex_success = run_complex_migrations(engine)
            # For 'all' mode, we want both startup and complex to succeed
            # Local and NAS are optional (depends on configuration)

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