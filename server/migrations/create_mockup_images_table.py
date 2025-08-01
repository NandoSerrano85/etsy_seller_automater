#!/usr/bin/env python3
"""
Migration script to create the mockup_images table.
This table will store mockup images with user_id association and mask information.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

def create_mockup_images_table():
    """Create the mockup_images table in the database."""
    
    # Get database connection details
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/etsydb')
    
    # Parse the database URL
    if database_url.startswith('postgresql://'):
        # Remove postgresql:// prefix
        connection_string = database_url.replace('postgresql://', '')
        
        # Parse username, password, host, port, database
        if '@' in connection_string:
            auth_part, rest = connection_string.split('@', 1)
            username, password = auth_part.split(':', 1)
            
            if ':' in rest:
                host_part, db_part = rest.split(':', 1)
                host = host_part
                if '/' in db_part:
                    port, database = db_part.split('/', 1)
                else:
                    port = '5432'
                    database = db_part
            else:
                host = rest.split('/')[0]
                port = '5432'
                database = rest.split('/')[1]
        else:
            raise ValueError("Invalid database URL format")
    else:
        raise ValueError("Unsupported database URL format")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()
        
        # Create the mockup_images table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS mockup_images (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            template_name VARCHAR NOT NULL,
            filename VARCHAR NOT NULL,
            file_path VARCHAR NOT NULL,
            mask_data JSONB,
            points_data JSONB,
            image_type VARCHAR,
            design_id VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, filename)
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create indexes for faster lookups
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_mockup_images_user_id ON mockup_images(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_mockup_images_template_name ON mockup_images(template_name);",
            "CREATE INDEX IF NOT EXISTS idx_mockup_images_user_template ON mockup_images(user_id, template_name);"
        ]
        
        for index_sql in create_indexes_sql:
            cursor.execute(index_sql)
        
        # Commit the changes
        conn.commit()
        
        print("✓ Successfully created mockup_images table")
        print("✓ Created indexes for faster lookups")
        
        # Verify the table was created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'mockup_images'
        """)
        
        if cursor.fetchone():
            print("✓ Table verification successful")
        else:
            print("✗ Table verification failed")
            return False
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return False

if __name__ == "__main__":
    success = create_mockup_images_table()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 