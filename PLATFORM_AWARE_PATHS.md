# Platform-Aware Paths (Etsy/Shopify)

## Problem

The system was using Etsy shop names (`etsy_stores.shop_name`) for **ALL** designs, including Shopify designs. This caused incorrect paths for Shopify designs.

**Example Issue:**

- Shopify design uploaded → System used Etsy shop name → Wrong path → File not found

## Solution

Made **all paths platform-aware** by querying the correct table based on the design's platform:

- **Etsy designs** → Use `etsy_stores.shop_name`
- **Shopify designs** → Use `shopify_stores.shop_name`

---

## Key Changes

### 1. server/src/routes/designs/service.py

**Added platform-aware helper function:**

```python
def get_platform_shop_name(db: Session, user_id: UUID, platform: str = 'etsy') -> str:
    """
    Get the shop name for a user based on platform.
    Queries etsy_stores for Etsy or shopify_stores for Shopify.
    """
    platform = platform.lower()

    if platform == 'etsy':
        store = db.query(EtsyStore).filter(
            EtsyStore.user_id == user_id,
            EtsyStore.is_active == True
        ).order_by(EtsyStore.created_at.desc()).first()

        if store and store.shop_name:
            return store.shop_name

    elif platform == 'shopify':
        store = db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.is_active == True
        ).order_by(ShopifyStore.created_at.desc()).first()

        if store and store.shop_name:
            return store.shop_name

    # Fallback
    return f"user_{str(user_id)[:8]}"
```

**Added convenience wrappers:**

```python
def get_etsy_shop_name(db: Session, user_id: UUID) -> str:
    return get_platform_shop_name(db, user_id, platform='etsy')

def get_shopify_shop_name(db: Session, user_id: UUID) -> str:
    return get_platform_shop_name(db, user_id, platform='shopify')
```

**Updated all design upload paths:**

```python
# Line 591: Get shop name based on design platform
platform_shop_name = get_platform_shop_name(db, user_id, platform=design_data.platform)

# Lines 720, 951: Use platform-specific shop name for NAS uploads
success = nas_storage.upload_file_content(
    file_content=image_bytes,
    shop_name=platform_shop_name,  # ← Platform-aware
    relative_path=relative_path
)

# Line 1108: Build file path with correct shop name
platform_shop_name = get_platform_shop_name(db, user_id, platform=design_data.platform)
nas_file_path = f"/share/Graphics/{platform_shop_name}/{nas_relative_path}"
```

---

### 2. server/src/services/image_upload_workflow.py

**Updated `_get_user_shop_name()` to accept platform parameter:**

```python
def _get_user_shop_name(self, platform: Optional[str] = None) -> str:
    """
    Get the shop name for the current user based on platform.

    Args:
        platform: 'etsy' or 'shopify'. If None, tries Etsy first, then Shopify.
    """
    # Try Etsy first (most common)
    if not platform or platform == 'etsy':
        result = self.db_session.execute(text("""
            SELECT shop_name FROM etsy_stores
            WHERE user_id = :user_id AND is_active = true
            ORDER BY created_at DESC LIMIT 1
        """), {"user_id": self.user_id})

        row = result.fetchone()
        if row and row[0]:
            return row[0]

    # Try Shopify if Etsy not found or platform is 'shopify'
    if not platform or platform == 'shopify':
        result = self.db_session.execute(text("""
            SELECT shop_name FROM shopify_stores
            WHERE user_id = :user_id AND is_active = true
            ORDER BY created_at DESC LIMIT 1
        """), {"user_id": self.user_id})

        row = result.fetchone()
        if row and row[0]:
            return row[0]

    # Fallback
    return f"user_{self.user_id[:8]}"
```

**Auto-detection:**

- If `platform` parameter not provided, tries Etsy first, then Shopify
- Returns the first active store found
- Falls back to `user_{user_id[:8]}` if neither found

---

### 3. Migration Scripts

All migration scripts updated to be platform-aware:

#### import_nas_designs_batched.py

**Queries both store tables:**

```python
# Get Etsy stores
etsy_users_result = connection.execute(text("""
    SELECT user_id, shop_name, 'etsy' as platform FROM etsy_stores
    WHERE is_active = true
"""))

# Get Shopify stores
shopify_users_result = connection.execute(text("""
    SELECT user_id, shop_name, 'shopify' as platform FROM shopify_stores
    WHERE is_active = true
"""))

# Create mapping: user_id -> (shop_name, platform)
user_shop_mapping = {}
for user_id, shop_name, platform in etsy_users:
    user_shop_mapping[str(user_id)] = (shop_name, 'etsy')
for user_id, shop_name, platform in shopify_users:
    user_shop_mapping[str(user_id)] = (shop_name, 'shopify')
```

**Gets templates from both platforms:**

```python
# Etsy templates
etsy_templates = connection.execute(text("""
    SELECT id, name, user_id FROM etsy_product_templates
"""))

# Shopify templates
shopify_templates = connection.execute(text("""
    SELECT id, name, user_id FROM shopify_product_templates
"""))
```

**Matches templates to platform:**

```python
for template_id, template_name, template_platform in user_templates[user_id_str]:
    # Skip templates that don't match this user's platform
    if template_platform != platform:
        continue

    # Process files for this template...
```

#### import_nas_designs.py

**Similar platform-aware updates:**

```python
def get_all_users_and_shops(connection):
    """Get all users with their shop names from both stores."""
    etsy_result = connection.execute(text("""
        SELECT user_id, shop_name, 'etsy' as platform FROM etsy_stores WHERE is_active = true
    """))

    shopify_result = connection.execute(text("""
        SELECT user_id, shop_name, 'shopify' as platform FROM shopify_stores WHERE is_active = true
    """))

    return etsy_result.fetchall() + shopify_result.fetchall()
```

**Filters by platform:**

```python
for user_id_str, (shop_name, platform) in user_shop_mapping.items():
    # This migration is for Etsy templates only
    if platform != 'etsy':
        continue

    # Process Etsy templates...
```

#### import_local_designs.py

**Handles both platforms:**

```python
# Get users from both stores
etsy_result = conn.execute(text("""
    SELECT user_id, shop_name, 'etsy' as platform FROM etsy_stores WHERE is_active = true
"""))
shopify_result = conn.execute(text("""
    SELECT user_id, shop_name, 'shopify' as platform FROM shopify_stores WHERE is_active = true
"""))

# Map: shop_name -> (user_id, platform)
user_mapping = {}
for row in etsy_result.fetchall():
    user_mapping[row[1]] = (str(row[0]), 'etsy')
for row in shopify_result.fetchall():
    user_mapping[row[1]] = (str(row[0]), 'shopify')

# Get templates from both platforms with platform info
template_mapping = {
    'template_id': str(template_id),
    'user_id': str(user_id),
    'platform': platform  # ← Platform tracking
}
```

---

## Path Formats

### Etsy Designs

```
/share/Graphics/{etsy_shop_name}/{template_name}/{filename}
```

**Example:**

```
/share/Graphics/NookTransfers/UVDTF 16oz/UV 906 UVDTF_16oz_906.png
```

### Shopify Designs

```
/share/Graphics/{shopify_shop_name}/{template_name}/{filename}
```

**Example:**

```
/share/Graphics/MyShopifyStore/ProductTemplate/design_001.png
```

---

## Benefits

### ✅ Correct Paths for Both Platforms

- Etsy designs use Etsy shop name
- Shopify designs use Shopify shop name
- No more cross-platform path errors

### ✅ Automatic Platform Detection

- `image_upload_workflow.py` auto-detects which store exists
- Tries Etsy first (most common), then Shopify
- Seamless fallback behavior

### ✅ Migration Support

- Migration scripts handle both platforms
- Can import designs for both Etsy and Shopify stores
- Platform validation ensures correct matching

### ✅ Backward Compatible

- Gallery function still uses `get_etsy_shop_name()` (Etsy-specific)
- Fallback to `user_{user_id[:8]}` if no store found
- Existing Etsy-only deployments continue to work

---

## Logging

New log messages show which platform and shop name is being used:

**Etsy:**

```
Using Etsy shop name from etsy_stores: NookTransfers
```

**Shopify:**

```
Using Shopify shop name from shopify_stores: MyShopifyStore
```

**Fallback:**

```
Using fallback shop name for platform 'etsy': user_e4049cc2
```

---

## Database Tables

### etsy_stores

```sql
CREATE TABLE etsy_stores (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    shop_name VARCHAR(255),  -- Etsy shop display name
    etsy_shop_id VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    ...
);
```

### shopify_stores

```sql
CREATE TABLE shopify_stores (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    shop_name VARCHAR(255),  -- Shopify shop display name
    shop_domain VARCHAR(255),
    shopify_shop_id VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    ...
);
```

---

## Testing

After deployment, verify:

1. **Etsy uploads** → Check logs for "Using Etsy shop name"
2. **Shopify uploads** → Check logs for "Using Shopify shop name"
3. **NAS paths** → Should use correct shop name for each platform
4. **Mockup generation** → Should find files at correct paths

---

## Deployment

**Status:** ✅ Deployed to production

**Commit:** `90164f6` - "Make all paths platform-aware (Etsy/Shopify)"

**Branch:** `production`

---

## Summary

**Before:** All designs used Etsy shop name → Shopify designs had wrong paths ❌

**After:** Designs use platform-specific shop names → Correct paths for both Etsy and Shopify ✅

This ensures:

- Etsy designs stored at `/share/Graphics/{etsy_shop_name}/...`
- Shopify designs stored at `/share/Graphics/{shopify_shop_name}/...`
- Migration scripts respect platform boundaries
- No cross-platform path conflicts

All paths are now **truly platform-aware**!
