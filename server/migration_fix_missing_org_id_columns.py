"""
Migration to add missing org_id columns to tables that need multi-tenant support
This migration adds org_id columns to tables that are missing them when MULTI_TENANT is enabled
"""
import os
import sys
import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the server directory to the Python path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.core import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception as e:
        logger.error(f"Error checking if column {column_name} exists in {table_name}: {e}")
        return False

def add_org_id_column(table_name):
    """Add org_id column to a table if it doesn't exist"""
    if check_column_exists(table_name, 'org_id'):
        logger.info(f"✅ Column org_id already exists in {table_name}")
        return True

    try:
        with engine.connect() as connection:
            # Add the org_id column
            add_column_sql = f"""
            ALTER TABLE {table_name}
            ADD COLUMN org_id UUID
            REFERENCES organizations(id) ON DELETE CASCADE;
            """
            connection.execute(text(add_column_sql))
            connection.commit()
            logger.info(f"✅ Added org_id column to {table_name}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"❌ Error adding org_id column to {table_name}: {e}")
        return False

def migrate_existing_users_to_organizations():
    """Create organizations for existing users and update user records"""
    try:
        with engine.connect() as connection:
            # Check if we have users without org_id
            result = connection.execute(text("""
                SELECT COUNT(*) as count FROM users WHERE org_id IS NULL
            """))
            users_without_org = result.fetchone()[0]

            if users_without_org == 0:
                logger.info("✅ All users already have organizations assigned")
                return True

            logger.info(f"🔄 Found {users_without_org} users without organizations. Creating organizations...")

            # Create organizations for users that don't have them
            migration_sql = """
            WITH new_orgs AS (
                INSERT INTO organizations (id, name, description, settings, created_at, updated_at)
                SELECT
                    gen_random_uuid(),
                    COALESCE(u.shop_name, u.email || '''s Organization'),
                    'Auto-generated organization for existing user',
                    '{}',
                    NOW(),
                    NOW()
                FROM users u
                WHERE u.org_id IS NULL
                RETURNING id, name
            ),
            user_org_mapping AS (
                SELECT
                    u.id as user_id,
                    (SELECT no.id FROM new_orgs no LIMIT 1 OFFSET (ROW_NUMBER() OVER () - 1)) as org_id
                FROM users u
                WHERE u.org_id IS NULL
            )
            UPDATE users
            SET org_id = uom.org_id
            FROM user_org_mapping uom
            WHERE users.id = uom.user_id;
            """

            connection.execute(text(migration_sql))
            connection.commit()
            logger.info("✅ Created organizations for existing users")
            return True

    except SQLAlchemyError as e:
        logger.error(f"❌ Error migrating users to organizations: {e}")
        return False

def update_existing_records_with_org_id():
    """Update existing records in multi-tenant tables with org_id from their user"""
    tables_with_user_id = [
        'design_images',
        'mockups',
        'etsy_product_templates'
    ]

    for table_name in tables_with_user_id:
        try:
            # Check if table exists
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                logger.info(f"⚠️  Table {table_name} does not exist, skipping")
                continue

            # Check if table has both user_id and org_id columns
            if not check_column_exists(table_name, 'user_id'):
                logger.info(f"⚠️  Table {table_name} does not have user_id column, skipping")
                continue

            if not check_column_exists(table_name, 'org_id'):
                logger.info(f"⚠️  Table {table_name} does not have org_id column, skipping")
                continue

            with engine.connect() as connection:
                # Update records to have org_id from their user
                update_sql = f"""
                UPDATE {table_name}
                SET org_id = users.org_id
                FROM users
                WHERE {table_name}.user_id = users.id
                AND {table_name}.org_id IS NULL;
                """

                result = connection.execute(text(update_sql))
                connection.commit()

                rows_updated = result.rowcount
                logger.info(f"✅ Updated {rows_updated} records in {table_name} with org_id")

        except SQLAlchemyError as e:
            logger.error(f"❌ Error updating {table_name} with org_id: {e}")

def main():
    """Main migration function"""
    logger.info("🔄 Starting migration to fix missing org_id columns...")

    # Check if multi-tenant is enabled
    multi_tenant_enabled = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'
    if not multi_tenant_enabled:
        logger.info("ℹ️  Multi-tenant is not enabled, skipping migration")
        return

    # Tables that need org_id columns for multi-tenant support
    tables_needing_org_id = [
        'design_images',
        'mockups',
        'etsy_product_templates'
    ]

    success = True

    # Add org_id columns to tables that need them
    for table_name in tables_needing_org_id:
        if not add_org_id_column(table_name):
            success = False

    # Migrate existing users to have organizations
    if not migrate_existing_users_to_organizations():
        success = False

    # Update existing records with org_id
    update_existing_records_with_org_id()

    if success:
        logger.info("✅ Migration completed successfully!")
    else:
        logger.error("❌ Migration completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()