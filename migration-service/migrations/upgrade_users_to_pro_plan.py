"""
Upgrade all users to Pro plan for CraftFlow Commerce access.

This migration upgrades all existing users to the 'pro' subscription plan
to ensure they have access to CraftFlow Commerce features.

This is a one-time migration for existing users. New users can be assigned
different plans through the signup process or admin panel.
"""

from sqlalchemy import text


def upgrade(connection):
    """Upgrade all users to Pro plan"""

    # Check if users table exists
    check_table_sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'users'
        )
    """)

    result = connection.execute(check_table_sql)
    table_exists = result.fetchone()[0]

    if not table_exists:
        print("⚠️  Users table does not exist, skipping migration")
        return

    # Check if subscription_plan column exists
    check_column_sql = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'subscription_plan'
    """)

    result = connection.execute(check_column_sql)
    column_exists = result.fetchone()

    if not column_exists:
        print("⚠️  subscription_plan column does not exist, skipping migration")
        return

    # Count users that will be upgraded
    count_sql = text("""
        SELECT COUNT(*)
        FROM users
        WHERE subscription_plan != 'pro'
    """)

    result = connection.execute(count_sql)
    count = result.fetchone()[0]

    if count == 0:
        print("✅ All users already have Pro plan or higher, skipping")
        return

    # Upgrade all users to Pro plan
    upgrade_sql = text("""
        UPDATE users
        SET subscription_plan = 'pro'
        WHERE subscription_plan != 'pro'
        AND subscription_plan != 'enterprise'
    """)

    connection.execute(upgrade_sql)

    print(f"✅ Upgraded {count} user(s) to Pro plan")
    print("   All users now have access to CraftFlow Commerce features")


def downgrade(connection):
    """Downgrade users back to free plan"""

    # This is optional - you may not want to downgrade users
    # Commenting out the actual downgrade to prevent accidental downgrades

    print("⚠️  Downgrade not implemented to prevent accidental subscription downgrades")
    print("   If you need to change user plans, do so through the admin panel")

    # If you want to enable downgrade, uncomment below:
    # downgrade_sql = text("""
    #     UPDATE users
    #     SET subscription_plan = 'free'
    #     WHERE subscription_plan = 'pro'
    # """)
    # connection.execute(downgrade_sql)
    # print("✅ Downgraded users to free plan")
