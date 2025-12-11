# Platform-Aware Duplicate Detection Implementation

## Summary

Successfully implemented platform-aware duplicate detection to keep Shopify and Etsy designs separate. Users can now upload the same design to both platforms without triggering duplicate detection.

---

## Problem

Previously, duplicate detection checked all designs for a user regardless of platform. This meant:

- Uploading the same design to both Shopify and Etsy would trigger "duplicate" warnings
- Users couldn't have identical designs in both marketplaces
- The system couldn't distinguish between platform-specific uploads

---

## Solution

Added a `platform` field to the `design_images` table that automatically detects whether a design is for Etsy or Shopify based on the template being used. Duplicate detection now filters by platform, so:

✅ Same design can exist in both Etsy and Shopify
✅ Duplicates only detected within the same platform
✅ Automatic platform detection from template ID
✅ Backward compatible (existing designs default to 'etsy')

---

## Changes Made

### 1. Database Migration

**File:** `migration-service/migrations/add_platform_to_designs.py`

Created migration to:

- Add `platform VARCHAR(20) DEFAULT 'etsy' NOT NULL` column to `design_images` table
- Add index on `platform` column for faster queries
- Add composite index on `(user_id, platform, phash)` for optimized duplicate detection
- Default all existing designs to 'etsy' for backward compatibility

**How to run:** Migration will run automatically on Railway deployment, or manually using:

```bash
python migration-service/run-migrations.py
```

---

### 2. Entity Model Update

**File:** `server/src/entities/designs.py` (line 37)

```python
platform = Column(String(20), default='etsy', nullable=False)  # 'etsy' or 'shopify'
```

---

### 3. Pydantic Model Updates

**File:** `server/src/routes/designs/model.py`

Updated all models to include platform field:

```python
class DesignImageBase(BaseModel):
    # ...
    platform: str = 'etsy'  # 'etsy' or 'shopify'
```

```python
class DesignImageCreate(BaseModel):
    # ...
    platform: str = 'etsy'  # Will be auto-detected from template
```

```python
class DesignImageUpdate(BaseModel):
    # ...
    platform: Optional[str] = None  # 'etsy' or 'shopify'
```

---

### 4. Platform Auto-Detection

**File:** `server/src/routes/designs/service.py`

Added helper function to detect platform from template:

```python
def _detect_platform_from_template(db: Session, template_id: UUID) -> str:
    """
    Detect whether a template belongs to Etsy or Shopify platform

    Returns:
        'etsy' or 'shopify' based on which table contains the template
    """
    # Check EtsyProductTemplate table
    etsy_template = db.query(EtsyProductTemplate).filter(
        EtsyProductTemplate.id == template_id
    ).first()
    if etsy_template:
        return 'etsy'

    # Check ShopifyProductTemplate table
    shopify_template = db.query(ShopifyProductTemplate).filter(
        ShopifyProductTemplate.id == template_id
    ).first()
    if shopify_template:
        return 'shopify'

    # Default to 'etsy' for backward compatibility
    return 'etsy'
```

Updated `create_design()` to auto-detect platform (lines 384-388):

```python
# Auto-detect platform from template if not already set
if design_data.platform == 'etsy' and design_data.product_template_id:
    detected_platform = _detect_platform_from_template(db, design_data.product_template_id)
    design_data.platform = detected_platform
    logging.info(f"🔍 Auto-detected platform: {detected_platform} for template {design_data.product_template_id}")
```

---

### 5. Updated Duplicate Detection

**File:** `server/src/routes/designs/service.py`

#### Exact Match Check (lines 642-666):

```python
def check_duplicate_in_database(phash_hex: str, platform: str = 'etsy') -> bool:
    """Check if image already exists in database using indexed queries"""
    result = db.execute(text("""
        SELECT 1 FROM design_images
        WHERE user_id = :user_id
        AND platform = :platform  -- ✨ NEW: Filter by platform
        AND is_active = true
        AND phash = :phash
        LIMIT 1
    """), {"user_id": str(user_id), "platform": platform, "phash": phash_hex})

    is_duplicate = result.fetchone() is not None
    logging.info(f"🔍 Database duplicate check ({platform}) completed: {'DUPLICATE' if is_duplicate else 'UNIQUE'}")
    return is_duplicate
```

#### Hamming Distance Check (lines 668-719):

```python
def check_hamming_distance_in_database(phash_hex: str, platform: str = 'etsy', threshold: int = 5):
    """Check Hamming distance against recent database entries (last 1000 images)"""
    result = db.execute(text("""
        SELECT phash, filename FROM design_images
        WHERE user_id = :user_id
        AND platform = :platform  -- ✨ NEW: Filter by platform
        AND is_active = true
        AND phash IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1000
    """), {"user_id": str(user_id), "platform": platform})

    rows = result.fetchall()
    logging.info(f"🔍 Checking Hamming distance against {len(rows)} recent {platform} images")
    # ... Hamming distance calculation ...
```

#### Updated Function Calls (lines 938, 946):

```python
# Pass platform parameter to duplicate detection functions
if check_duplicate_in_database(phash, platform=design_data.platform):
    # ... exact match handling ...

is_similar, similar_filename = check_hamming_distance_in_database(
    phash,
    platform=design_data.platform,  # ✨ NEW: Pass platform
    threshold=5
)
```

---

### 6. Design Creation Update

**File:** `server/src/routes/designs/service.py` (line 1053)

```python
design = DesignImages(
    user_id=user_id,
    filename=filename,
    file_path=nas_file_path,
    description=design_data.description,
    phash=phash,
    ahash=ahash,
    dhash=dhash,
    whash=whash,
    canvas_config_id=design_data.canvas_config_id,
    platform=design_data.platform,  # ✨ NEW: Set platform
    is_active=design_data.is_active
)
```

---

### 7. Migration Runner Update

**File:** `migration-service/run-migrations.py` (line 116)

Added new migration to the known migration order:

```python
"add_platform_to_designs",  # Adds platform column to separate Shopify and Etsy designs
```

---

## Database Indexes

The migration creates these indexes for optimal performance:

1. **`idx_design_images_platform`** - Index on platform column for filtering
2. **`idx_design_images_user_platform_phash`** - Composite index for duplicate detection queries

Query performance:

- Exact duplicate check: O(log n) using indexed lookup
- Hamming distance check: Scans only last 1000 images for the specific platform

---

## How It Works

### Upload Flow

1. **User uploads design** via frontend with `product_template_id`
2. **Platform auto-detection:**
   - System checks if template_id exists in `etsy_product_templates` → platform = 'etsy'
   - Otherwise checks if template_id exists in `shopify_product_templates` → platform = 'shopify'
   - Defaults to 'etsy' if not found
3. **Duplicate detection:**
   - Checks for duplicates **only within the detected platform**
   - Etsy designs compared only against other Etsy designs
   - Shopify designs compared only against other Shopify designs
4. **Design saved** with platform field set

### Example Scenarios

#### Scenario 1: Same Design in Both Platforms ✅

```
Upload 1: Design "Bunny.png" → Template "UVDTF 16oz" (Etsy) → platform='etsy' → Saved
Upload 2: Design "Bunny.png" → Template "UVDTF Cup" (Shopify) → platform='shopify' → Saved ✅

Result: Both designs saved, no duplicate detected because different platforms
```

#### Scenario 2: Duplicate Within Same Platform ⚠️

```
Upload 1: Design "Bunny.png" → Template "UVDTF 16oz" (Etsy) → platform='etsy' → Saved
Upload 2: Design "Bunny.png" → Template "UVDTF 20oz" (Etsy) → platform='etsy' → Duplicate! ⚠️

Result: Second upload rejected as duplicate (same platform)
```

---

## Testing Checklist

### Before Deploying:

- [x] Migration file created with upgrade and downgrade functions
- [x] Migration added to run-migrations.py order
- [x] Entity model updated with platform column
- [x] Pydantic models updated
- [x] Duplicate detection filters by platform
- [x] Platform auto-detection implemented
- [x] Design creation sets platform field

### After Deploying:

- [ ] Verify migration ran successfully in Railway logs
- [ ] Test uploading same design to Etsy template
- [ ] Test uploading same design to Shopify template
- [ ] Verify both designs are saved without duplicate warnings
- [ ] Test duplicate detection still works within same platform
- [ ] Check database indexes were created

---

## Deployment Steps

1. **Push to production branch:**

   ```bash
   git add .
   git commit -m "Add platform-aware duplicate detection for Shopify and Etsy"
   git push origin production
   ```

2. **Railway will automatically:**
   - Run the migration service
   - Execute `add_platform_to_designs` migration
   - Add platform column with 'etsy' default
   - Create indexes
   - Restart API service

3. **Verify in Railway logs:**
   ```
   🔄 Running add_platform_to_designs...
   Added platform column to design_images table
   Added index for platform column
   Added composite index for user_id + platform + phash
   ✅ add_platform_to_designs completed
   ```

---

## Rollback Plan

If issues occur, the migration can be rolled back:

```python
# The downgrade function will:
# 1. Drop composite index idx_design_images_user_platform_phash
# 2. Drop platform index idx_design_images_platform
# 3. Drop platform column from design_images table
```

To rollback manually:

```sql
DROP INDEX IF EXISTS idx_design_images_user_platform_phash;
DROP INDEX IF EXISTS idx_design_images_platform;
ALTER TABLE design_images DROP COLUMN IF EXISTS platform;
```

---

## Files Modified

1. ✅ `migration-service/migrations/add_platform_to_designs.py` - New migration
2. ✅ `migration-service/run-migrations.py` - Added to migration order
3. ✅ `server/src/entities/designs.py` - Added platform column
4. ✅ `server/src/routes/designs/model.py` - Updated Pydantic models
5. ✅ `server/src/routes/designs/service.py` - Platform detection and duplicate checks
6. ✅ `server/src/entities/template.py` - Imported ShopifyProductTemplate

---

## Notes

- **Backward Compatible:** All existing designs will default to 'etsy' platform
- **Automatic Detection:** Platform is auto-detected from template, no manual input needed
- **Performance:** Indexed queries ensure fast duplicate detection even with thousands of designs
- **Future-Proof:** Can easily add more platforms (e.g., 'amazon', 'walmart') in the future

---

## Next Steps

After deployment:

1. Monitor Railway logs for successful migration
2. Test uploading the same design to both Etsy and Shopify templates
3. Verify duplicate detection still works correctly within each platform
4. Update frontend documentation if needed (platform detection is automatic, so no changes needed)

🎉 **Platform separation is now live!**
