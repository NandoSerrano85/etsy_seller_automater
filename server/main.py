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
from server.src.database.core import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from server.src.api import register_routes
from server.src.logging import config_logging, LogLevels
from server.src import message
from threading import Timer
from dotenv import load_dotenv

import uvicorn, webbrowser

SERVER_CONFIG = {
    'default_host': '127.0.0.1',
    'default_port': 3003,
    'default_debug': False,
}

config_logging(LogLevels.info)


# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://comforting-cocada-88dd8c.netlify.app",
        "https://printer-automater.netlify.app", 
        "https://*.railway.app",  # Allow all Railway frontend URLs
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

register_routes(app)
message.register_error_handlers(app)
Base.metadata.create_all(bind=engine)

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

