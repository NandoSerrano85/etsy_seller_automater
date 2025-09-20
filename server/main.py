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
from contextlib import asynccontextmanager
import asyncio

# Enable multi-tenant features early, before entity imports
os.environ['ENABLE_MULTI_TENANT'] = 'true'

from server.src.database.core import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from server.src.api import register_routes
from server.src.app_logging import config_logging, LogLevels
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

print("🔄 Starting CraftFlow application...")
print(f"🌍 Environment: {os.getenv('DOCKER_ENV', 'development')}")
print(f"🚀 Railway Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'not-set')}")
print(f"🗄️  Database URL: {os.getenv('DATABASE_URL', 'not-set')[:50]}...")
print(f"🔧 Multi-tenant: {os.getenv('ENABLE_MULTI_TENANT', 'false')}")


# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Global variable to hold the token refresh task
token_refresh_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    global token_refresh_task

    # Startup
    print("🔄 Starting application services...")

    # Initialize cache service
    try:
        from server.src.services.cache_service import cache_service
        # Cache service initializes automatically
        print("🚀 Cache service initialized")
    except Exception as e:
        print(f"⚠️  Warning: Failed to initialize cache service: {e}")

    # Only start token refresh service in production
    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        try:
            from server.src.services.token_refresh_service import start_token_refresh_service
            print("🔄 Starting automatic token refresh service...")

            # Start the token refresh service as a background task
            token_refresh_task = asyncio.create_task(start_token_refresh_service())
            print("✅ Token refresh service started")

        except Exception as e:
            print(f"⚠️  Warning: Failed to start token refresh service: {e}")
    else:
        print("ℹ️  Skipping token refresh service in development mode")

    print("✅ Application services started")

    yield  # App runs here

    # Shutdown
    print("🛑 Shutting down application services...")

    if token_refresh_task:
        try:
            from server.src.services.token_refresh_service import stop_token_refresh_service
            stop_token_refresh_service()
            token_refresh_task.cancel()
            print("✅ Token refresh service stopped")
        except Exception as e:
            print(f"⚠️  Warning: Error stopping token refresh service: {e}")

    print("✅ Application shutdown complete")

print("📋 Creating FastAPI application...")
app = FastAPI(lifespan=lifespan)
print("✅ FastAPI application created")

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

print("📋 Registering routes...")
register_routes(app)
print("✅ Routes registered")

print("📋 Registering error handlers...")
message.register_error_handlers(app)
print("✅ Error handlers registered")

# Skip all database operations in production to ensure fast startup
if os.getenv('RAILWAY_ENVIRONMENT') != 'production':
    # Create database tables with error handling (enums handled by migration service)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Database table creation failed: {e}")
        # Continue running - tables might already exist
else:
    print("ℹ️  Skipping all database operations in production for fast startup")

# All migrations are now handled by the separate Railway migration service
print("ℹ️  All migrations are handled by the separate Railway migration service")
print("ℹ️  Main API starts immediately for fast health checks")

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

    print(f"🚀 Starting CraftFlow server on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌍 Environment: {os.getenv('DOCKER_ENV', 'development')}")

    # Disable automatic browser opening to prevent unwanted redirects
    # if not os.getenv('DOCKER_ENV') and not debug:
    #     Timer(2, open_browser).start()

    print("✅ Application startup completed successfully")
    print("🟢 Server is ready to accept connections")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == '__main__':
    run_server()

