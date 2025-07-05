#!/usr/bin/env python3
"""
Database migration to add template_title column to etsy_templates table.
Run this script to update your database schema.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the server directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/etsydb')

def run_migration():
    """Add template_title column to etsy_templates table."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Check if the column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'etsy_templates' 
                AND column_name = 'template_title'
            """))
            
            if result.fetchone():
                print("✅ template_title column already exists")
                return
            
            # Add the template_title column
            conn.execute(text("""
                ALTER TABLE etsy_templates 
                ADD COLUMN template_title VARCHAR
            """))
            
            conn.commit()
            print("✅ Successfully added template_title column to etsy_templates table")
            
        except Exception as e:
            print(f"❌ Error adding template_title column: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Running database migration to add template_title column...")
    run_migration()
    print("✅ Migration completed successfully!") 