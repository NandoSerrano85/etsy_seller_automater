#!/usr/bin/env python3
"""
Script to diagnose and fix subscription/user mismatches.

Usage:
    python scripts/fix_subscriptions.py diagnose
    python scripts/fix_subscriptions.py fix --email user@example.com --tier pro
    python scripts/fix_subscriptions.py sync-all
"""

import os
import sys
import argparse
from uuid import UUID

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def diagnose():
    """Show all users and their subscription status."""
    print("\n" + "=" * 80)
    print("SUBSCRIPTION DIAGNOSIS REPORT")
    print("=" * 80)

    with Session() as session:
        # Get all users with their subscriptions
        result = session.execute(text("""
            SELECT
                u.id AS user_id,
                u.email,
                u.subscription_plan AS user_table_plan,
                s.id AS subscription_id,
                s.user_id AS subscription_user_id,
                s.tier AS subscription_tier,
                s.status AS subscription_status
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            ORDER BY u.email
        """))

        rows = result.fetchall()

        print(f"\n{'EMAIL':<40} {'USER_PLAN':<12} {'SUB_TIER':<12} {'STATUS':<15}")
        print("-" * 80)

        issues = []
        for row in rows:
            user_id, email, user_plan, sub_id, sub_user_id, sub_tier, sub_status = row

            if sub_id is None:
                status = "❌ NO SUB RECORD"
                issues.append(('no_subscription', email, user_id, user_plan))
            elif user_plan != sub_tier:
                status = "⚠️  TIER MISMATCH"
                issues.append(('mismatch', email, user_id, user_plan, sub_tier))
            else:
                status = "✅ OK"

            print(f"{email:<40} {user_plan or 'N/A':<12} {sub_tier or 'N/A':<12} {status:<15}")

        # Check for orphaned subscriptions
        orphaned = session.execute(text("""
            SELECT s.id, s.user_id, s.tier
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE u.id IS NULL
        """)).fetchall()

        if orphaned:
            print("\n⚠️  ORPHANED SUBSCRIPTIONS (no matching user):")
            for sub_id, user_id, tier in orphaned:
                print(f"   Subscription {sub_id} -> user_id {user_id} (tier: {tier})")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total users: {len(rows)}")
        print(f"Users without subscription records: {len([i for i in issues if i[0] == 'no_subscription'])}")
        print(f"Users with tier mismatch: {len([i for i in issues if i[0] == 'mismatch'])}")
        print(f"Orphaned subscriptions: {len(orphaned)}")

        if issues:
            print("\nTo fix issues, run one of:")
            print("  python scripts/fix_subscriptions.py fix --email <email> --tier <tier>")
            print("  python scripts/fix_subscriptions.py sync-all")


def fix_user(email: str, tier: str):
    """Create or update subscription for a specific user."""
    valid_tiers = ['free', 'starter', 'pro', 'full']
    if tier not in valid_tiers:
        print(f"ERROR: Invalid tier '{tier}'. Must be one of: {valid_tiers}")
        sys.exit(1)

    with Session() as session:
        # Get user
        result = session.execute(
            text("SELECT id, email, subscription_plan FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()

        if not user:
            print(f"ERROR: User with email '{email}' not found")
            sys.exit(1)

        user_id, user_email, current_plan = user
        print(f"\nUser found: {user_email} (ID: {user_id})")
        print(f"Current plan in users table: {current_plan}")

        # Check if subscription exists
        sub_result = session.execute(
            text("SELECT id, tier, status FROM subscriptions WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        subscription = sub_result.fetchone()

        if subscription:
            sub_id, sub_tier, sub_status = subscription
            print(f"Existing subscription: tier={sub_tier}, status={sub_status}")

            # Update existing subscription
            session.execute(
                text("""
                    UPDATE subscriptions
                    SET tier = :tier, status = 'active', updated_at = NOW()
                    WHERE user_id = :user_id
                """),
                {"tier": tier, "user_id": user_id}
            )
            print(f"✅ Updated subscription tier to '{tier}'")
        else:
            print("No subscription record found")

            # Create new subscription
            session.execute(
                text("""
                    INSERT INTO subscriptions (id, user_id, tier, status, created_at, updated_at)
                    VALUES (gen_random_uuid(), :user_id, :tier, 'active', NOW(), NOW())
                """),
                {"user_id": user_id, "tier": tier}
            )
            print(f"✅ Created new subscription with tier '{tier}'")

        # Also update user's subscription_plan to keep in sync
        session.execute(
            text("UPDATE users SET subscription_plan = :tier, updated_at = NOW() WHERE id = :user_id"),
            {"tier": tier, "user_id": user_id}
        )
        print(f"✅ Updated user's subscription_plan to '{tier}'")

        session.commit()
        print("\n✅ Changes committed successfully!")


def sync_all():
    """Create subscription records for all users who don't have one."""
    with Session() as session:
        # Find users without subscriptions
        result = session.execute(text("""
            SELECT u.id, u.email, u.subscription_plan
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            WHERE s.id IS NULL
        """))

        users_without_subs = result.fetchall()

        if not users_without_subs:
            print("✅ All users already have subscription records!")
            return

        print(f"\nFound {len(users_without_subs)} users without subscription records:")
        for user_id, email, plan in users_without_subs:
            tier = plan if plan in ['free', 'starter', 'pro', 'full'] else 'free'
            print(f"  - {email}: will create with tier '{tier}'")

        confirm = input("\nCreate subscription records for these users? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return

        for user_id, email, plan in users_without_subs:
            tier = plan if plan in ['free', 'starter', 'pro', 'full'] else 'free'
            session.execute(
                text("""
                    INSERT INTO subscriptions (id, user_id, tier, status, created_at, updated_at)
                    VALUES (gen_random_uuid(), :user_id, :tier, 'active', NOW(), NOW())
                """),
                {"user_id": user_id, "tier": tier}
            )
            print(f"✅ Created subscription for {email} with tier '{tier}'")

        session.commit()
        print(f"\n✅ Created {len(users_without_subs)} subscription records!")


def main():
    parser = argparse.ArgumentParser(description='Fix subscription/user mismatches')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Diagnose command
    subparsers.add_parser('diagnose', help='Show all users and their subscription status')

    # Fix command
    fix_parser = subparsers.add_parser('fix', help='Fix subscription for a specific user')
    fix_parser.add_argument('--email', required=True, help='User email')
    fix_parser.add_argument('--tier', required=True, choices=['free', 'starter', 'pro', 'full'],
                           help='Subscription tier')

    # Sync-all command
    subparsers.add_parser('sync-all', help='Create subscription records for all users without one')

    args = parser.parse_args()

    if args.command == 'diagnose':
        diagnose()
    elif args.command == 'fix':
        fix_user(args.email, args.tier)
    elif args.command == 'sync-all':
        sync_all()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
