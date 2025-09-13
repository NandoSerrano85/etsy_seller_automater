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

# Create database tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Warning: Database table creation failed: {e}")
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

                # Run multi-tenant migration
                run_multi_tenant_migration(conn)
                    
    except Exception as e:
        print(f"⚠️  Warning: Migration failed: {e}")
        # Continue running - the column might exist or the migration might not be critical

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
            
            # Create required enums first
            print("📋 Creating required enums...")
            try:
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
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE file_status_enum AS ENUM (
                            'uploading', 'ready', 'processing', 'failed', 'archived'
                        );
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                print("✅ Created enum types")
            except Exception as enum_error:
                print(f"⚠️  Warning: Enum creation failed: {enum_error}")
            
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
            
            print("✅ Basic multi-tenant tables created successfully")
            print("ℹ️  Other multi-tenant tables will be created by SQLAlchemy as needed")
            
            print("✅ Multi-tenant schema migration completed successfully")
            
            # Enable multi-tenant features after successful migration
            enable_multi_tenant_features()
            
        else:
            print("✅ Multi-tenant schema already exists")
            # Check if multi-tenant features should be enabled
            enable_multi_tenant_features()
            
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
    
    print(f"Starting Etsy OAuth server on http://{host}:{port}")
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

