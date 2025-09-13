# from threading import Timer
# from dotenv import load_dotenv
# from server.api.router import app
# from server.constants import SERVER_CONFIG
# import uvicorn, webbrowser, os, sys

import os, sys

# Add the project root to the Python path BEFORE any other imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Enable multi-tenant features early, before entity imports
os.environ['ENABLE_MULTI_TENANT'] = 'true'

from server.src.database.core import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from server.src.api import register_routes
from server.src.logging import config_logging, LogLevels
from server.src import message
from threading import Timer
from dotenv import load_dotenv

import uvicorn, webbrowser

SERVER_CONFIG = {
    'default_host': '0.0.0.0',  # Railway requires 0.0.0.0 for external access
    'default_port': 3003,
    'default_debug': False,
}

config_logging(LogLevels.info)


# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

app = FastAPI()

# Get frontend URL from environment variable
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://comforting-cocada-88dd8c.netlify.app",
        "https://printer-automater.netlify.app", 
        "https://printer-automation-frontend-production.up.railway.app",  # Specific Railway frontend URL
        frontend_url,  # Dynamic frontend URL from environment
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.railway\.app",  # Use regex for Railway subdomains
)

# Add explicit OPTIONS handling for debugging
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"message": "OK"}

register_routes(app)
message.register_error_handlers(app)

# Create required enums before table creation
def create_required_enums():
    """Create database enums that are required by SQLAlchemy entities."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            with conn.begin():
                print("📋 Creating required database enums...")
                
                # Create file_type_enum
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE file_type_enum AS ENUM (
                            'original', 'design', 'mockup', 'print_file', 
                            'watermark', 'template', 'export', 'other'
                        );
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Create file_status_enum
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE file_status_enum AS ENUM (
                            'uploading', 'ready', 'processing', 'failed', 'archived'
                        );
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                print("✅ Database enums created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Enum creation failed: {e}")

# Create enums first, then tables
create_required_enums()

# Create database tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Warning: Database table creation failed: {e}")
    # Continue running - tables might already exist

# Run database migrations for new columns
def run_migrations():
    """Run necessary database migrations for new columns."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            with conn.begin():
                print("🔄 Running database migrations...")
                
                # Check if etsy_shop_id column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'etsy_shop_id'
                """))
                
                if not result.fetchone():
                    # Add the etsy_shop_id column
                    conn.execute(text("ALTER TABLE users ADD COLUMN etsy_shop_id VARCHAR"))
                    print("✅ Added etsy_shop_id column to users table")
                else:
                    print("✅ etsy_shop_id column already exists")

                # Check if role column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'role'
                """))
                
                if not result.fetchone():
                    # Add the role column
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'member'"))
                    print("✅ Added role column to users table")
                else:
                    print("✅ role column already exists")

                # Run multi-tenant migration
                run_multi_tenant_migration(conn)
                    
    except Exception as e:
        print(f"⚠️  Warning: Migration failed: {e}")
        # Continue running - the column might exist or the migration might not be critical

def run_org_id_migration(conn):
    """Add missing org_id columns to tables that need multi-tenant support."""
    try:
        from sqlalchemy import text

        print("🔄 Checking for missing org_id columns...")

        # Tables that need org_id columns for multi-tenant support
        tables_needing_org_id = [
            'design_images',
            'mockups',
            'etsy_product_templates'
        ]

        for table_name in tables_needing_org_id:
            # Check if table exists
            table_result = conn.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = '{table_name}' AND table_schema = 'public'
            """))

            if not table_result.fetchone():
                print(f"⚠️  Table {table_name} does not exist, skipping")
                continue

            # Check if org_id column exists
            result = conn.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}' AND column_name = 'org_id'
            """))

            if not result.fetchone():
                # Add the org_id column
                conn.execute(text(f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN org_id UUID REFERENCES organizations(id) ON DELETE CASCADE
                """))
                print(f"✅ Added org_id column to {table_name}")

                # Update existing records with org_id from their user
                if table_name in ['design_images', 'mockups', 'etsy_product_templates']:
                    conn.execute(text(f"""
                        UPDATE {table_name}
                        SET org_id = users.org_id
                        FROM users
                        WHERE {table_name}.user_id = users.id
                        AND {table_name}.org_id IS NULL
                        AND users.org_id IS NOT NULL
                    """))
                    print(f"✅ Updated existing records in {table_name} with org_id")
            else:
                print(f"✅ org_id column already exists in {table_name}")

    except Exception as e:
        print(f"❌ Error adding org_id columns: {e}")

def create_organizations_for_existing_users(conn):
    """Create organizations for existing users that don't have them."""
    try:
        from sqlalchemy import text

        print("🔄 Creating organizations for existing users...")

        # Check if we have users without org_id
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM users WHERE org_id IS NULL
        """))
        users_without_org = result.fetchone()[0]

        if users_without_org == 0:
            print("✅ All users already have organizations assigned")
            return

        print(f"🔄 Found {users_without_org} users without organizations. Creating organizations...")

        # Create organizations for users that don't have them
        conn.execute(text("""
            WITH user_orgs AS (
                SELECT DISTINCT
                    gen_random_uuid() as org_id,
                    u.id as user_id,
                    COALESCE(u.shop_name, u.email || '''s Organization') as org_name,
                    'Auto-generated organization for existing user' as org_description
                FROM users u
                WHERE u.org_id IS NULL
            ),
            new_orgs AS (
                INSERT INTO organizations (id, name, description, settings, created_at, updated_at)
                SELECT
                    uo.org_id,
                    uo.org_name,
                    uo.org_description,
                    '{}',
                    NOW(),
                    NOW()
                FROM user_orgs uo
                RETURNING id, name
            ),
            updated_users AS (
                UPDATE users
                SET org_id = uo.org_id, role = 'owner'
                FROM user_orgs uo
                WHERE users.id = uo.user_id
                RETURNING users.id, users.org_id
            )
            INSERT INTO organization_members (id, organization_id, user_id, role, joined_at)
            SELECT
                gen_random_uuid(),
                uu.org_id,
                uu.id,
                'owner',
                NOW()
            FROM updated_users uu;
        """))

        print("✅ Created organizations for existing users")

    except Exception as e:
        print(f"❌ Error creating organizations for existing users: {e}")

def run_multi_tenant_migration(conn):
    """Run the multi-tenant schema migration."""
    try:
        from sqlalchemy import text
        
        print("🔄 Checking multi-tenant schema...")
        
        # Check if organizations table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'organizations' AND table_schema = 'public'
        """))
        
        if not result.fetchone():
            print("📋 Creating multi-tenant tables...")
            
            # Create organizations table
            conn.execute(text("""
                CREATE TABLE organizations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ Created organizations table")
            
            # Create organization_members table
            conn.execute(text("""
                CREATE TABLE organization_members (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(50) DEFAULT 'member',
                    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(organization_id, user_id)
                )
            """))
            print("✅ Created organization_members table")
            
            # Add org_id column to users table if it doesn't exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'org_id'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN org_id UUID REFERENCES organizations(id) ON DELETE SET NULL
                """))
                print("✅ Added org_id column to users table")
            
            # Add role column to users table if it doesn't exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'role'
            """))
            
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'member'
                """))
                print("✅ Added role column to users table")
            
            print("✅ Basic multi-tenant tables created successfully")
            print("ℹ️  Other multi-tenant tables will be created by SQLAlchemy as needed")
            
            print("✅ Multi-tenant schema migration completed successfully")
            
            # Enable multi-tenant features after successful migration
            enable_multi_tenant_features()
            
        else:
            print("✅ Multi-tenant schema already exists")
            # Check if multi-tenant features should be enabled
            enable_multi_tenant_features()

            # Run the org_id migration for existing tables
            run_org_id_migration(conn)

            # Create organizations for existing users
            create_organizations_for_existing_users(conn)
            
    except Exception as e:
        print(f"❌ Multi-tenant migration failed: {e}")
        # Don't raise the exception to prevent app startup failure
        print("⚠️  App will continue running with existing schema")

def enable_multi_tenant_features():
    """Enable multi-tenant features by setting environment variable."""
    import os
    # Set environment variable to enable multi-tenant features
    os.environ['ENABLE_MULTI_TENANT'] = 'true'
    print("✅ Multi-tenant features enabled")

try:
    run_migrations()
except Exception as e:
    print(f"⚠️  Migration error: {e}")

# Serve static files from the frontend public directory
frontend_public_dir = os.path.join(project_root, "frontend", "public")
if os.path.exists(frontend_public_dir):
    app.mount("/static", StaticFiles(directory=frontend_public_dir), name="static")
    
    # Serve common frontend assets at root level
    @app.get("/manifest.json")
    async def get_manifest():
        from fastapi.responses import FileResponse
        manifest_path = os.path.join(frontend_public_dir, "manifest.json")
        if os.path.exists(manifest_path):
            return FileResponse(manifest_path, media_type="application/json")
        return {"error": "Manifest not found"}
    
    @app.get("/favicon.ico")
    async def get_favicon():
        from fastapi.responses import FileResponse
        favicon_path = os.path.join(frontend_public_dir, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/x-icon")
        return {"error": "Favicon not found"}

# Handle webpack hot reload files - return 404 gracefully
@app.get("/{filename:path}")
async def catch_webpack_files(filename: str):
    from fastapi.responses import JSONResponse
    from fastapi import status
    
    # If this is a webpack hot-reload file, return empty response to avoid console errors
    if (filename.endswith('.hot-update.json') or 
        filename.endswith('.hot-update.js') or
        filename.startswith('__webpack_hmr') or
        filename.endswith('.map')):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Webpack development file not found"}
        )
    
    # For other files, return standard 404
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"File {filename} not found"}
    )

def open_browser():
    """Function to open the browser to the root URL of the FastAPI app."""
    host = os.getenv('HOST', SERVER_CONFIG['default_host'])
    port = int(os.getenv('PORT', SERVER_CONFIG['default_port']))
    webbrowser.open(f"http://{host}:{port}/")

def run_server():
    """Run the FastAPI server with configurable host and port."""
    host = os.getenv('HOST', SERVER_CONFIG['default_host'])
    port = int(os.getenv('PORT', SERVER_CONFIG['default_port']))
    debug = os.getenv('DEBUG', str(SERVER_CONFIG['default_debug'])).lower() == 'true'
    
    print(f"Starting CraftFlow server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Open browser only if not running in Docker and debug is enabled
    if not os.getenv('DOCKER_ENV') and not debug:
        Timer(2, open_browser).start()
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level="info"
    )

if __name__ == '__main__':
    run_server()

