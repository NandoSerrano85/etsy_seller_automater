#!/usr/bin/env python3
"""
Migration script to create the mockup_mask_data table.
This table will store mask data for each user and template combination.
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

def create_mockup_mask_data_table():
    """Create the mockup_mask_data table in the database."""
    
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
        
        # Create the mockup_mask_data table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS mockup_mask_data (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            template_name VARCHAR NOT NULL,
            masks JSONB NOT NULL,
            points JSONB NOT NULL,
            starting_name INTEGER DEFAULT 100,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create index for faster lookups
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_mockup_mask_data_user_template 
        ON mockup_mask_data(user_id, template_name);
        """
        
        cursor.execute(create_index_sql)
        
        # Commit the changes
        conn.commit()
        
        print("✓ Successfully created mockup_mask_data table")
        print("✓ Created index on user_id and template_name")
        
        # Verify the table was created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'mockup_mask_data'
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
    print("Creating mockup_mask_data table...")
    success = create_mockup_mask_data_table()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 