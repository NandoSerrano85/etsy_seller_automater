#!/usr/bin/env python3
"""
Run shipping-related migrations for the handling fee feature

This script runs the necessary migrations to add handling fee support
to the ecommerce storefront.
"""

import os
import sys
from pathlib import Path

# Add migration-service to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

def run_migration():
    """Run the handling fee migration"""
    print("=" * 70)
    print("SHIPPING HANDLING FEE MIGRATION")
    print("=" * 70)
    print()

    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print()
        print("Please set DATABASE_URL to your PostgreSQL connection string:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        print()
        return False

    print(f"✅ DATABASE_URL found: {database_url[:30]}...")
    print()

    try:
        # Import after path setup
        from sqlalchemy import create_engine, text

        # Create engine
        print("🔄 Connecting to database...")
        engine = create_engine(database_url)

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("✅ Database connection successful")
        print()

        # Run the migration
        print("🔄 Running handling_fee migration...")
        print()

        # Import migration
        from migrations.add_handling_fee_to_storefront_settings import upgrade, downgrade

        with engine.connect() as conn:
            trans = conn.begin()
            try:
                upgrade(conn)
                trans.commit()
                print()
                print("=" * 70)
                print("✅ MIGRATION COMPLETED SUCCESSFULLY")
                print("=" * 70)
                print()
                print("Next steps:")
                print("1. Go to your admin panel: CraftFlow Commerce Storefront Settings")
                print("2. Set your desired handling fee (e.g., 2.50)")
                print("3. Click Save")
                print("4. Test checkout to see handling fee applied to shipping rates")
                print()
                return True

            except Exception as e:
                trans.rollback()
                print()
                print("=" * 70)
                print("❌ MIGRATION FAILED")
                print("=" * 70)
                print()
                print(f"Error: {e}")
                print()
                import traceback
                traceback.print_exc()
                return False

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ CONNECTION FAILED")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("Please check:")
        print("1. DATABASE_URL is correct")
        print("2. Database is running and accessible")
        print("3. You have proper permissions")
        print()
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """Verify the migration was successful"""
    print()
    print("=" * 70)
    print("VERIFYING MIGRATION")
    print("=" * 70)
    print()

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'ecommerce_storefront_settings'
                AND column_name = 'handling_fee'
            """))

            row = result.fetchone()

            if row:
                print("✅ handling_fee column exists")
                print(f"   - Column name: {row[0]}")
                print(f"   - Data type: {row[1]}")
                print(f"   - Default value: {row[2]}")
                print()

                # Check if there are any storefront settings
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM ecommerce_storefront_settings
                """))
                count = result.fetchone()[0]

                print(f"📊 Found {count} storefront settings record(s)")

                if count > 0:
                    # Show handling fee values
                    result = conn.execute(text("""
                        SELECT id, user_id, store_name, handling_fee
                        FROM ecommerce_storefront_settings
                        LIMIT 5
                    """))

                    print()
                    print("Current handling_fee values:")
                    print("-" * 70)
                    for row in result:
                        print(f"  ID: {row[0]}, User: {row[1]}")
                        print(f"  Store: {row[2] or '(not set)'}")
                        print(f"  Handling Fee: ${row[3] or '0.00'}")
                        print()

                return True
            else:
                print("❌ handling_fee column does not exist")
                print()
                print("The migration may not have run successfully.")
                print("Try running this script again.")
                return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "HANDLING FEE MIGRATION TOOL" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Run migration
    success = run_migration()

    if success:
        # Verify migration
        verify_migration()
        print()
        print("=" * 70)
        print("🎉 ALL DONE!")
        print("=" * 70)
        sys.exit(0)
    else:
        print()
        print("=" * 70)
        print("❌ MIGRATION INCOMPLETE")
        print("=" * 70)
        print()
        print("Please fix the errors above and try again.")
        sys.exit(1)
