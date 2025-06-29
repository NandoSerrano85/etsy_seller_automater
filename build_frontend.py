#!/usr/bin/env python3
"""
Script to build the React frontend and prepare it for serving by the FastAPI backend.
"""

import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Building React Frontend...")
    
    # Check if Node.js is installed
    if not run_command("node --version"):
        print("❌ Node.js is not installed. Please install Node.js first.")
        return False
    
    # Check if npm is installed
    if not run_command("npm --version"):
        print("❌ npm is not installed. Please install npm first.")
        return False
    
    # Navigate to frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    if not os.path.exists(frontend_dir):
        print("❌ Frontend directory not found.")
        return False
    
    # Install dependencies
    print("📦 Installing dependencies...")
    if not run_command("npm install", cwd=frontend_dir):
        print("❌ Failed to install dependencies.")
        return False
    
    # Build the React app
    print("🔨 Building React app...")
    if not run_command("npm run build", cwd=frontend_dir):
        print("❌ Failed to build React app.")
        return False
    
    print("✅ Frontend built successfully!")
    print("🎉 You can now run the server with: python server/main.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 