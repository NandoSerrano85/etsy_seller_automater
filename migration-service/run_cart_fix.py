#!/usr/bin/env python3
"""
Quick script to run cart item ID fix migration
"""
import os
import sys
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent / 'server'))

# Load .env file
from dotenv import load_dotenv
env_path = current_dir.parent / '.env'
load_dotenv(env_path)

def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('❌ DATABASE_URL not set')
        return False

    print(f'Using DATABASE_URL: {db_url[:50]}...')

    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)

    # Test connection
    print('🔄 Testing database connection...')
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False

    # Import and run migration
    from migrations.fix_cart_item_ids import upgrade

    print('🔄 Running cart item ID fix migration...')
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                upgrade(conn)
                trans.commit()
                print()
                print('✅ Migration completed successfully!')
                return True
            except Exception as e:
                trans.rollback()
                print(f'❌ Migration failed: {e}')
                import traceback
                traceback.print_exc()
                return False
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
