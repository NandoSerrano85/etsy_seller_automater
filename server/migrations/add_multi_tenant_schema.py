"""
Add multi-tenant architecture schema

This migration adds the complete multi-tenant schema including:
- Organizations table
- User-organization relationships (org_id in users)
- Shops table  
- Files table for NAS integration
- Print jobs table
- Events table for audit logging
- Printers table
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add multi-tenant schema tables and relationships."""
    try:
        # Create organizations table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR NOT NULL,
                description TEXT,
                settings JSONB DEFAULT '{"is_active": true}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Created organizations table")

        # Add org_id to users table (nullable for backward compatibility)
        connection.execute(text("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
        """))
        logging.info("Added org_id to users table")

        # Create organization_members table for many-to-many relationship
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS organization_members (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role VARCHAR NOT NULL DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(organization_id, user_id)
            );
        """))
        logging.info("Created organization_members table")

        # Create shops table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS shops (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                platform VARCHAR NOT NULL,
                platform_shop_id VARCHAR,
                shop_config JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Created shops table")

        # Create files table for NAS integration
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS files (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                filename VARCHAR NOT NULL,
                original_filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR NOT NULL,
                file_hash VARCHAR NOT NULL,
                storage_backend VARCHAR NOT NULL DEFAULT 'nas',
                file_metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Created files table")

        # Create print_jobs table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS print_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                created_by_user_id UUID NOT NULL REFERENCES users(id),
                printer_id UUID REFERENCES printers(id),
                shop_id UUID REFERENCES shops(id),
                job_name VARCHAR NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                file_ids UUID[],
                print_config JSONB DEFAULT '{}',
                progress_percentage INTEGER DEFAULT 0,
                estimated_completion TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Created print_jobs table")

        # Create events table for audit logging
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id),
                event_type VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                entity_id UUID,
                event_data JSONB DEFAULT '{}',
                ip_address VARCHAR,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Created events table")

        # Create printers table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS printers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id),
                name VARCHAR NOT NULL,
                printer_type VARCHAR NOT NULL,
                max_width_inches FLOAT NOT NULL,
                max_height_inches FLOAT NOT NULL,
                dpi INTEGER NOT NULL DEFAULT 300,
                supported_template_ids UUID[],
                is_active BOOLEAN DEFAULT true,
                is_default BOOLEAN DEFAULT false,
                notes TEXT,
                printer_config JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logging.info("Created printers table")

        # Add indexes for performance
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_organization_members_org_id ON organization_members(organization_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON organization_members(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_shops_org_id ON shops(organization_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_files_org_id ON files(organization_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_print_jobs_org_id ON print_jobs(organization_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_print_jobs_status ON print_jobs(status);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_events_org_id ON events(organization_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_printers_org_id ON printers(organization_id);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_printers_user_id ON printers(user_id);"))
        logging.info("Created performance indexes")

        # Update existing canvas_configs table to add DPI and spacing fields if they don't exist
        connection.execute(text("""
            ALTER TABLE canvas_configs 
            ADD COLUMN IF NOT EXISTS dpi INTEGER DEFAULT 300,
            ADD COLUMN IF NOT EXISTS spacing_width_inches FLOAT DEFAULT 0.125,
            ADD COLUMN IF NOT EXISTS spacing_height_inches FLOAT DEFAULT 0.125;
        """))
        logging.info("Updated canvas_configs table with DPI and spacing fields")

        logging.info("Successfully completed multi-tenant schema migration")
        
    except Exception as e:
        logging.error(f"Error in multi-tenant schema migration: {e}")
        raise

def downgrade(connection):
    """Remove multi-tenant schema (use with caution - will drop data)."""
    try:
        # Drop tables in reverse dependency order
        connection.execute(text("DROP TABLE IF EXISTS events CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS print_jobs CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS printers CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS files CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS shops CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS organization_members CASCADE;"))
        
        # Remove org_id from users
        connection.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS org_id;"))
        
        # Drop organizations table last
        connection.execute(text("DROP TABLE IF EXISTS organizations CASCADE;"))
        
        # Remove DPI and spacing fields from canvas_configs
        connection.execute(text("""
            ALTER TABLE canvas_configs 
            DROP COLUMN IF EXISTS dpi,
            DROP COLUMN IF EXISTS spacing_width_inches,
            DROP COLUMN IF EXISTS spacing_height_inches;
        """))
        
        logging.info("Successfully removed multi-tenant schema")
        
    except Exception as e:
        logging.error(f"Error removing multi-tenant schema: {e}")
        raise

if __name__ == "__main__":
    # This can be run directly for testing
    from server.src.database.core import engine
    with engine.connect() as conn:
        with conn.begin():
            upgrade(conn)
            logging.info("Multi-tenant migration completed successfully!")