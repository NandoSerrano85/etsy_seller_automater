#!/usr/bin/env python3
"""
Startup script for the Etsy OAuth server.
Can run in standalone mode or Docker mode.
"""

import os
import sys
import subprocess
import argparse

def run_standalone():
    """Run the server in standalone mode."""
    print("Starting Etsy OAuth server in standalone mode...")
    server_path = os.path.join(os.path.dirname(__file__), 'server', 'main.py')
    subprocess.run([sys.executable, server_path])

def run_docker():
    """Run the server in Docker mode."""
    print("Starting Etsy OAuth server in Docker mode...")
    subprocess.run(['docker-compose', 'up', '--build'])

def run_docker_detached():
    """Run the server in Docker mode (detached)."""
    print("Starting Etsy OAuth server in Docker mode (detached)...")
    subprocess.run(['docker-compose', 'up', '--build', '-d'])

def stop_docker():
    """Stop the Docker container."""
    print("Stopping Etsy OAuth server...")
    subprocess.run(['docker-compose', 'down'])

def main():
    parser = argparse.ArgumentParser(description='Etsy OAuth Server Startup Script')
    parser.add_argument('--mode', choices=['standalone', 'docker', 'docker-detached'], 
                       default='standalone', help='Run mode (default: standalone)')
    parser.add_argument('--stop', action='store_true', help='Stop Docker container')
    
    args = parser.parse_args()
    
    if args.stop:
        stop_docker()
        return
    
    if args.mode == 'standalone':
        run_standalone()
    elif args.mode == 'docker':
        run_docker()
    elif args.mode == 'docker-detached':
        run_docker_detached()

if __name__ == '__main__':
    main() 