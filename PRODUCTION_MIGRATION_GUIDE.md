# Production Migration Guide - Multi-Tenant Architecture

## Overview

This guide contains the steps needed to migrate the production database to support the new multi-tenant Railway architecture with organizations, printers, and enhanced features.

## ⚠️ Important Notes

- **Backup your database before running any migrations**
- These migrations are designed to be backward compatible
- The application can run without these migrations, but multi-tenant features will not be available
- Run migrations during a maintenance window if possible

## Migration Steps

### Step 1: Connect to Production Database

```bash
# Connect to your production PostgreSQL database
# Replace with your actual connection details
psql -h your-db-host -U your-db-user -d your-database-name
```

### Step 2: Run Core Multi-Tenant Schema Migration

Execute the following SQL commands in order:

```sql
-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{"is_active": true}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add org_id to users table (nullable for backward compatibility)
ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

-- Create organization_members table for many-to-many relationship
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);

-- Create shops table
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

-- Create files table for NAS integration
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

-- Create print_jobs table
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

-- Create events table for audit logging
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

-- Create printers table
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

-- Add performance indexes
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_org_id ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_shops_org_id ON shops(organization_id);
CREATE INDEX IF NOT EXISTS idx_files_org_id ON files(organization_id);
CREATE INDEX IF NOT EXISTS idx_print_jobs_org_id ON print_jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_print_jobs_status ON print_jobs(status);
CREATE INDEX IF NOT EXISTS idx_events_org_id ON events(organization_id);
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_printers_org_id ON printers(organization_id);
CREATE INDEX IF NOT EXISTS idx_printers_user_id ON printers(user_id);

-- Update existing canvas_configs table to add DPI and spacing fields
ALTER TABLE canvas_configs
ADD COLUMN IF NOT EXISTS dpi INTEGER DEFAULT 300,
ADD COLUMN IF NOT EXISTS spacing_width_inches FLOAT DEFAULT 0.125,
ADD COLUMN IF NOT EXISTS spacing_height_inches FLOAT DEFAULT 0.125;
```

### Step 3: Data Migration (Optional)

If you want to migrate existing users to organizations:

```sql
-- Create a default organization for existing users
INSERT INTO organizations (name, description, settings)
VALUES ('Default Organization', 'Migrated from single-tenant setup', '{"is_active": true}')
ON CONFLICT DO NOTHING;

-- Get the organization ID
-- Update existing users to belong to the default organization
UPDATE users
SET org_id = (SELECT id FROM organizations WHERE name = 'Default Organization' LIMIT 1)
WHERE org_id IS NULL;

-- Add users to organization_members table
INSERT INTO organization_members (organization_id, user_id, role)
SELECT
    (SELECT id FROM organizations WHERE name = 'Default Organization' LIMIT 1),
    id,
    'admin'
FROM users
WHERE id NOT IN (SELECT user_id FROM organization_members);
```

### Step 4: Update Application Code

After running the migration successfully:

1. **Uncomment the multi-tenant fields in `server/src/entities/user.py`:**

```python
# Change this:
# TODO: Uncomment after running multi-tenant migration
# org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)

# To this:
org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)
```

2. **Uncomment the relationships:**

```python
# Uncomment these lines:
organization = relationship('Organization', back_populates='users')
files = relationship('File', back_populates='created_by_user')
print_jobs = relationship('PrintJob', back_populates='created_by_user')
events = relationship('Event', back_populates='user')
printers = relationship('Printer', back_populates='user', cascade='all, delete-orphan')
```

3. **Update the API routes in `server/src/api.py`:**

```python
# Uncomment these imports and routes:
from server.src.routes.organizations.routes import router as organization_router
from server.src.routes.shops.routes import router as shop_router
from server.src.routes.files.routes import router as file_router
from server.src.routes.print_jobs.routes import router as print_job_router
from server.src.routes.events.routes import router as event_router
from server.src.routes.printers.routes import router as printer_router

# And add these to register_routes():
app.include_router(organization_router, prefix="/api")
app.include_router(shop_router, prefix="/api")
app.include_router(file_router, prefix="/api")
app.include_router(print_job_router, prefix="/api")
app.include_router(event_router, prefix="/api")
app.include_router(printer_router, prefix="/api")
```

### Step 5: Restart Application

After making the code changes, restart your application:

```bash
# If using Docker Compose
docker-compose restart backend

# Or rebuild if needed
docker-compose up --build -d backend
```

## Verification

After migration, verify the setup:

1. **Check tables were created:**

```sql
\dt
-- Should show: organizations, organization_members, shops, files, print_jobs, events, printers
```

2. **Test basic functionality:**

- Login should work (existing authentication)
- Access `/api/organizations` (should return empty list initially)
- Access `/admin` (admin dashboard)

3. **Create test organization:**

- Use the frontend to create an organization
- Verify organization appears in admin dashboard

## Rollback (if needed)

If you need to rollback the migration:

```sql
-- Remove added columns
ALTER TABLE users DROP COLUMN IF EXISTS org_id;
ALTER TABLE canvas_configs DROP COLUMN IF EXISTS dpi, DROP COLUMN IF EXISTS spacing_width_inches, DROP COLUMN IF EXISTS spacing_height_inches;

-- Drop tables in dependency order
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS print_jobs CASCADE;
DROP TABLE IF EXISTS printers CASCADE;
DROP TABLE IF EXISTS files CASCADE;
DROP TABLE IF EXISTS shops CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
```

## Support

If you encounter issues:

1. Check application logs: `docker-compose logs backend`
2. Check database connectivity
3. Verify all SQL commands executed successfully
4. Ensure the application code changes were made correctly

## Next Steps

After successful migration:

1. **Organization Setup**: Create organizations for your users
2. **Printer Configuration**: Add printers through `/printers` interface
3. **Admin Access**: Use `/admin` for system management
4. **Multi-tenant Features**: All new features will be organization-scoped

The migration provides a solid foundation for multi-tenant Railway deployment while maintaining backward compatibility with existing single-tenant functionality.
