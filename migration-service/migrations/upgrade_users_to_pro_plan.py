"""
Upgrade all users to Pro plan for CraftFlow Commerce access (OPTIONAL).

This migration upgrades all existing users to the 'pro' subscription plan
to ensure they have access to CraftFlow Commerce features.

DISABLED BY DEFAULT - Set AUTO_UPGRADE_USERS_TO_PRO=true to enable

Alternative: Use the admin API endpoint to manually upgrade specific users
"""

import os
from sqlalchemy import text


def upgrade(connection):
    """Upgrade all users to Pro plan (optional, controlled by env var)"""

    # Check if auto-upgrade is enabled
    auto_upgrade = os.getenv('AUTO_UPGRADE_USERS_TO_PRO', 'false').lower() == 'true'

    if not auto_upgrade:
        print("⏭️  AUTO_UPGRADE_USERS_TO_PRO not enabled, skipping automatic upgrade")
        print("   To enable: Set AUTO_UPGRADE_USERS_TO_PRO=true")
        print("   Or use admin API to manually upgrade specific users")
        return

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
        AND subscription_plan != 'enterprise'
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
