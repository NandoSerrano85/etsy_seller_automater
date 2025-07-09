#!/usr/bin/env python3
"""
Script to run the canvas and size configuration migration.
"""
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from server.migrations.create_canvas_size_tables import run_migration

if __name__ == "__main__":
    print("Running canvas and size configuration migration...")
    run_migration()
    print("Migration completed!") 