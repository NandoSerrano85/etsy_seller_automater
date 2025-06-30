import uvicorn
import webbrowser
import os
import sys
from threading import Timer
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Import the FastAPI app from routes
from server.api.routes import app

# Import constants
from server.constants import SERVER_CONFIG

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