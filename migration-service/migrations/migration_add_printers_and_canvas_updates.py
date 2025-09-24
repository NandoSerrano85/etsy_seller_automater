"""
Migration Script: Add Printers and Update CanvasConfig
Adds printer management and enhanced canvas configuration for gangsheet engine

Converted from Alembic to standard SQLAlchemy for migration service
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade(connection):
    """Add printer table and update canvas_config with DPI and spacing"""
    logger.info("🔄 Starting printers and canvas updates migration...")

    # This migration was originally written for Alembic and contains complex table operations
    # The core functionality (printers table, canvas_config updates) is already handled
    # by add_multi_tenant_schema.py which includes these tables
    # Skipping this migration as its functionality is covered by other migrations

    logger.info("✅ Printers and canvas updates migration skipped - functionality covered by other migrations")
    return
    
    # Create printers table
    op.create_table(
        'printers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        
        # Printer information
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('printer_type', sa.String(50), nullable=False, default='inkjet'),
        sa.Column('manufacturer', sa.String(100)),
        sa.Column('model', sa.String(100)),
        sa.Column('description', sa.Text),
        
        # Print area dimensions (in inches)
        sa.Column('max_width_inches', sa.Float, nullable=False),
        sa.Column('max_height_inches', sa.Float, nullable=False),
        
        # Print quality settings
        sa.Column('dpi', sa.Integer, nullable=False, default=300),
        
        # Supported templates
        sa.Column('supported_template_ids', postgresql.ARRAY(postgresql.UUID), server_default=sa.text("ARRAY[]::uuid[]")),
        
        # Printer status
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('is_default', sa.Boolean, default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, index=True),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Add indexes for printer table
    op.create_index('idx_printers_user_org', 'printers', ['user_id', 'org_id'])
    op.create_index('idx_printers_user_default', 'printers', ['user_id', 'is_default'])
    op.create_index('idx_printers_type_active', 'printers', ['printer_type', 'is_active'])
    
    # Update canvas_configs table with new fields
    try:
        # Add DPI field to canvas_config
        op.add_column('canvas_configs', sa.Column('dpi', sa.Integer, nullable=False, server_default='300'))
        
        # Add spacing fields for gang sheet generation
        op.add_column('canvas_configs', sa.Column('spacing_width_inches', sa.Float, nullable=False, server_default='0.125'))
        op.add_column('canvas_configs', sa.Column('spacing_height_inches', sa.Float, nullable=False, server_default='0.125'))
        
        print("✅ Added DPI and spacing fields to canvas_configs table")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not update canvas_configs table: {e}")
        # Continue migration - table might not exist in some environments
    
    # Create constraint to ensure only one default printer per user
    op.create_unique_constraint(
        'uq_user_default_printer', 
        'printers', 
        ['user_id', 'org_id', 'is_default'],
        postgresql_where=sa.text('is_default = true')
    )
    
    print("✅ Added printers table with relationships and constraints")
    print("✅ Updated canvas_configs with DPI and spacing configuration")

def downgrade() -> None:
    """Remove printer table and canvas_config updates"""
    
    # Drop constraints and indexes
    op.drop_constraint('uq_user_default_printer', 'printers')
    op.drop_index('idx_printers_type_active')
    op.drop_index('idx_printers_user_default')
    op.drop_index('idx_printers_user_org')
    
    # Drop printers table
    op.drop_table('printers')
    
    # Remove canvas_config columns
    try:
        op.drop_column('canvas_configs', 'spacing_height_inches')
        op.drop_column('canvas_configs', 'spacing_width_inches')
        op.drop_column('canvas_configs', 'dpi')
        print("✅ Removed canvas_config updates")
    except Exception as e:
        print(f"⚠️  Warning: Could not remove canvas_config columns: {e}")
    
    print("✅ Removed printers table and related constraints")

if __name__ == "__main__":
    # Run the migration directly for testing
    print("Running Printer and CanvasConfig Migration...")
    
    try:
        from sqlalchemy import create_engine
        from server.src.database.core import DATABASE_URL
        
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            with conn.begin():
                # Check if printers table already exists
                result = conn.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'printers' AND table_schema = 'public'
                """)
                
                if result.fetchone():
                    print("✅ Printers table already exists")
                else:
                    # Run upgrade manually
                    print("🔄 Creating printers table...")
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS printers (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                            name VARCHAR(255) NOT NULL,
                            printer_type VARCHAR(50) NOT NULL DEFAULT 'inkjet',
                            manufacturer VARCHAR(100),
                            model VARCHAR(100),
                            description TEXT,
                            max_width_inches FLOAT NOT NULL,
                            max_height_inches FLOAT NOT NULL,
                            dpi INTEGER NOT NULL DEFAULT 300,
                            supported_template_ids UUID[] DEFAULT ARRAY[]::uuid[],
                            is_active BOOLEAN DEFAULT true,
                            is_default BOOLEAN DEFAULT false,
                            created_at TIMESTAMP DEFAULT NOW(),
                            updated_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    
                    # Add indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_printers_user_org ON printers(user_id, org_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_printers_user_default ON printers(user_id, is_default)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_printers_type_active ON printers(printer_type, is_active)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_printers_name ON printers(name)")
                    
                    print("✅ Created printers table with indexes")
                
                # Check and update canvas_configs table
                result = conn.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'canvas_configs' AND column_name = 'dpi'
                """)
                
                if not result.fetchone():
                    print("🔄 Adding DPI and spacing fields to canvas_configs...")
                    try:
                        conn.execute("ALTER TABLE canvas_configs ADD COLUMN IF NOT EXISTS dpi INTEGER NOT NULL DEFAULT 300")
                        conn.execute("ALTER TABLE canvas_configs ADD COLUMN IF NOT EXISTS spacing_width_inches FLOAT NOT NULL DEFAULT 0.125")
                        conn.execute("ALTER TABLE canvas_configs ADD COLUMN IF NOT EXISTS spacing_height_inches FLOAT NOT NULL DEFAULT 0.125")
                        print("✅ Added DPI and spacing fields to canvas_configs")
                    except Exception as e:
                        print(f"⚠️  Could not update canvas_configs: {e}")
                else:
                    print("✅ Canvas configs already has DPI field")
                    
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("You may need to run this migration manually or through Alembic")