"""
Fix cart items missing IDs

This migration ensures all cart items have unique IDs.
Older cart items might be missing the 'id' field which causes
404 errors when trying to remove them.
"""

from sqlalchemy import text
import uuid
import json


def upgrade(connection):
    """Add IDs to cart items that are missing them"""

    print("🔄 Checking for cart items without IDs...")

    # Check if shopping_carts table exists
    check_table_sql = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'shopping_carts'
        )
    """)

    result = connection.execute(check_table_sql)
    table_exists = result.fetchone()[0]

    if not table_exists:
        print("⚠️  shopping_carts table does not exist, skipping migration")
        return

    # Get all carts
    get_carts_sql = text("""
        SELECT id, items
        FROM shopping_carts
        WHERE items IS NOT NULL
        AND jsonb_array_length(items) > 0
    """)

    result = connection.execute(get_carts_sql)
    carts = result.fetchall()

    if not carts:
        print("✅ No carts found or all carts are empty")
        return

    print(f"📊 Found {len(carts)} cart(s) to check")

    updated_count = 0
    items_fixed = 0

    for cart_id, items_json in carts:
        items = items_json if isinstance(items_json, list) else json.loads(items_json)

        needs_update = False
        fixed_items = []

        for item in items:
            if 'id' not in item or not item.get('id'):
                # Generate a new UUID for this cart item
                item['id'] = str(uuid.uuid4())
                needs_update = True
                items_fixed += 1
                print(f"  ✅ Added ID to item: {item.get('product_name', 'Unknown')} in cart {cart_id}")

            fixed_items.append(item)

        if needs_update:
            # Update the cart with fixed items
            update_sql = text("""
                UPDATE shopping_carts
                SET items = :items,
                    updated_at = NOW()
                WHERE id = :cart_id
            """)

            connection.execute(
                update_sql,
                {"items": json.dumps(fixed_items), "cart_id": cart_id}
            )
            updated_count += 1

    if updated_count > 0:
        print()
        print(f"✅ Updated {updated_count} cart(s)")
        print(f"✅ Fixed {items_fixed} cart item(s) missing IDs")
    else:
        print("✅ All cart items already have IDs")


def downgrade(connection):
    """No downgrade needed - IDs are beneficial"""
    print("⏭️  No downgrade needed for cart item IDs")
