# Path Consistency - Final Resolution

## Problem Summary

**Initial Issue:** Only 14 out of 17 designs uploaded successfully to Etsy (3 failed)

**Root Cause:** Mixed path formats in the system caused confusion about whether to use:

- `shop_name` from database (e.g., "NookTransfers")
- User ID-based paths (e.g., "user_e4049cc2")

**Actual Issue:** Platform separation needed (Etsy vs Shopify), NOT path format changes

---

## Solution

### ✅ What Was Already Working

The **platform separation** was already implemented:

- Added `platform` column to `design_images` table
- Duplicate detection filters by platform: `WHERE platform = :platform`
- Etsy designs only compare against other Etsy designs
- Shopify designs only compare against other Shopify designs

This was the **correct fix** - Etsy and Shopify designs stay separated.

### ❌ What Was Incorrect

Changing to user ID-based paths (`user_{user_id[:8]}`) was **unnecessary** because:

- The old `shop_name` approach was working fine
- NAS folders already use shop names (e.g., "NookTransfers")
- More human-readable and matches existing structure
- Platform separation handles Etsy/Shopify isolation

---

## Final Path Format

**All systems now consistently use:**

```
/share/Graphics/{shop_name}/{template_name}/{filename}
```

Where `shop_name` comes from the `users` table in the database.

**Example:**

```
/share/Graphics/NookTransfers/UVDTF 16oz/UV 906 UVDTF_16oz_906.png
```

---

## Files Using Correct Path Format

### Server Code

1. **server/src/services/image_upload_workflow.py**
   - Gets `shop_name` from database query
   - Falls back to `user_{user_id[:8]}` only if shop_name not found
   - Logs warning if fallback is used

2. **server/src/routes/designs/service.py**
   - Uses `user.shop_name` from database throughout
   - Constructs paths: `f"/share/Graphics/{user.shop_name}/{template}"`

### Migration Scripts

1. **migration-service/migrations/import_nas_designs.py**
   - Queries `shop_name` from users table
   - Uses shop_name for all path construction

2. **migration-service/migrations/import_nas_designs_batched.py**
   - Queries `shop_name` from users table
   - Builds paths: `f"{nas_storage.base_path}/{shop_name}/{template}/{file}"`

3. **migration-service/migrations/import_local_designs.py**
   - Gets shop_name from database join
   - Constructs NAS paths using shop_name

---

## Platform Separation Implementation

**Location:** `server/src/routes/designs/service.py:706-730`

```python
def check_hamming_distance_in_database(phash_hex: str, platform: str = 'etsy', threshold: int = None):
    """Check Hamming distance against recent database entries"""

    # Query filters by platform - CRITICAL FOR SEPARATION
    result = db.execute(text("""
        SELECT phash, filename FROM design_images
        WHERE user_id = :user_id
        AND platform = :platform  # ← Keeps Etsy and Shopify separate
        AND is_active = true
        AND phash IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1000
    """), {"user_id": str(user_id), "platform": platform})
```

**Called with:** `check_hamming_distance_in_database(phash, platform=design_data.platform)`

This ensures:

- Etsy uploads only check against Etsy designs
- Shopify uploads only check against Shopify designs

---

## Summary of Changes (Commit: 40bb844)

### Reverted Migration Scripts

- ❌ **Removed:** User ID-based paths (`user_{user_id[:8]}`)
- ✅ **Restored:** Shop name from database

### Added Logging

- Logs warning if shop_name lookup fails and fallback is used
- Helps debug any future path issues

### No Changes to designs/service.py

- Already correctly using `user.shop_name`
- No modifications needed

---

## Testing Next Upload

When you upload 17 designs next:

1. ✅ All paths will use your shop name (e.g., "NookTransfers")
2. ✅ Platform filter ensures no Shopify conflicts
3. ✅ Duplicate detection threshold is 15 (not 5)
4. ✅ All files stored consistently on NAS

**Expected result:** All 17 designs upload successfully with no duplicate warnings (assuming they're truly unique).

---

## Why This is the Correct Approach

1. **Uses existing infrastructure** - NAS folders already organized by shop_name
2. **Human-readable** - Easy to find files manually on NAS
3. **Platform separation** - Already working via platform column filter
4. **Consistent with history** - Matches your previous working setup
5. **Fallback safety** - Can use user_id if shop_name missing

---

## Environment Variables

Still in effect from earlier fix:

```bash
DUPLICATE_HAMMING_THRESHOLD=15
```

This prevents false positive duplicates when comparing against 11,000+ existing designs.

---

## Deployment

**Status:** ✅ Deployed to production

**Commit:** `40bb844` - "Revert to shop_name-based paths consistently"

**Branch:** `production`

---

## Key Takeaway

The **platform column** was the real fix needed. Changing path formats was solving the wrong problem. Your original shop_name-based approach was correct all along.
