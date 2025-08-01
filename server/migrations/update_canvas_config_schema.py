"""
Migration to update canvas_configs table schema.
Remove user_id column and add product_template_id column.
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/etsydb')
engine = create_engine(DATABASE_URL)

def run_migration():
    """Run the migration to update the canvas_configs table schema."""
    try:
        print("Updating canvas_configs table schema...")
        
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                # Check if the table exists
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'canvas_configs'
                    );
                """))
                
                if not result.scalar():
                    print("canvas_configs table does not exist. Creating it with new schema...")
                    # Create the table with the new schema
                    connection.execute(text("""
                        CREATE TABLE canvas_configs (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            product_template_id UUID NOT NULL REFERENCES etsy_product_templates(id),
                            name VARCHAR NOT NULL,
                            width_inches FLOAT NOT NULL,
                            height_inches FLOAT NOT NULL,
                            description TEXT,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_stretch BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE
                        );
                    """))
                else:
                    print("canvas_configs table exists. Updating schema...")
                    
                    # Check if user_id column exists
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'canvas_configs' 
                            AND column_name = 'user_id'
                        );
                    """))
                    
                    if result.scalar():
                        print("Removing user_id column...")
                        # Drop the foreign key constraint first
                        connection.execute(text("""
                            ALTER TABLE canvas_configs 
                            DROP CONSTRAINT IF EXISTS canvas_configs_user_id_fkey;
                        """))
                        
                        # Remove the user_id column
                        connection.execute(text("""
                            ALTER TABLE canvas_configs 
                            DROP COLUMN IF EXISTS user_id;
                        """))
                        
                        # Remove the unique constraint that included user_id
                        connection.execute(text("""
                            ALTER TABLE canvas_configs 
                            DROP CONSTRAINT IF EXISTS _user_canvas_template_uc;
                        """))
                    
                    # Check if product_template_id column exists
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'canvas_configs' 
                            AND column_name = 'product_template_id'
                        );
                    """))
                    
                    if not result.scalar():
                        print("Adding product_template_id column...")
                        connection.execute(text("""
                            ALTER TABLE canvas_configs 
                            ADD COLUMN product_template_id UUID REFERENCES etsy_product_templates(id);
                        """))
                    
                    # Check if name column exists (was template_name)
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'canvas_configs' 
                            AND column_name = 'name'
                        );
                    """))
                    
                    if not result.scalar():
                        print("Renaming template_name to name...")
                        connection.execute(text("""
                            ALTER TABLE canvas_configs 
                            RENAME COLUMN template_name TO name;
                        """))
                    
                    # Check if is_stretch column exists
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'canvas_configs' 
                            AND column_name = 'is_stretch'
                        );
                    """))
                    
                    if not result.scalar():
                        print("Adding is_stretch column...")
                        connection.execute(text("""
                            ALTER TABLE canvas_configs 
                            ADD COLUMN is_stretch BOOLEAN DEFAULT TRUE;
                        """))
                    
                    # Update the id column to UUID if it's not already
                    result = connection.execute(text("""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'canvas_configs' 
                        AND column_name = 'id';
                    """))
                    
                    if result.scalar() != 'uuid':
                        print("Converting id column to UUID...")
                        # This is a complex operation that might require data migration
                        # For now, we'll just note it
                        print("Warning: ID column type conversion may require data migration")
                
                print("Migration completed successfully!")
                
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration() 