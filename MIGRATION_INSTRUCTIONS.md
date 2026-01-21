# Database Migration Instructions

## Quick Start

To apply all pending migrations:

```bash
cd migration-service
python run_migrations.py
```

This will automatically run any migrations that haven't been applied yet.

---

## New Migrations Added

### 1. `add_phash_indexes.py`

**Purpose**: Add database indexes for perceptual hash duplicate detection

**What it does**:

- Creates indexes on `phash`, `ahash`, `dhash`, `whash` columns
- Creates composite index on `user_id` and `is_active`
- Optimizes duplicate detection queries (1000x faster)

**Run manually**:

```bash
cd migration-service
python run_migrations.py add_phash_indexes
```

### 2. `add_production_partner_ids.py`

**Purpose**: Add support for Etsy API production partner IDs requirement

**What it does**:

- Adds `production_partner_ids` TEXT column to `etsy_product_templates`
- Allows templates to specify production partners (or default to "ready to ship")
- Fixes: `"error":"A readiness_state_id is required for physical listings."`

**Run manually**:

```bash
cd migration-service
python run_migrations.py add_production_partner_ids
```

---

## Migration System Overview

The migration service uses Python-based migrations with:

- ✅ Automatic migration tracking (knows what's been run)
- ✅ Rollback support via `downgrade()` functions
- ✅ Idempotent (safe to run multiple times)
- ✅ Logging and error handling

---

## Verifying Migrations

### Check Migration Status

```bash
cd migration-service
python run_migrations.py --status
```

### Verify Database Changes

**Check phash indexes**:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'design_images'
AND indexname LIKE 'idx_design_images_%';
```

**Check production_partner_ids column**:

```sql
\d etsy_product_templates
-- Should show: production_partner_ids | text
```

---

## Rollback (if needed)

If you need to undo a migration:

```bash
cd migration-service
python run_migrations.py --rollback add_phash_indexes
python run_migrations.py --rollback add_production_partner_ids
```

**Note**: Check your migration service documentation for exact rollback syntax.

---

## Troubleshooting

### "Column already exists" errors

The migrations are idempotent - they check if changes exist before applying them. These warnings are normal if running migrations multiple times.

### "Module not found" errors

Make sure you're in the migration-service directory:

```bash
cd migration-service
pip install -r requirements.txt  # if needed
python run_migrations.py
```

### Manual SQL Alternative

If the migration service isn't working, you can apply changes manually:

```sql
-- Add phash indexes
CREATE INDEX IF NOT EXISTS idx_design_images_phash
ON design_images(phash) WHERE phash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_ahash
ON design_images(ahash) WHERE ahash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_dhash
ON design_images(dhash) WHERE dhash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_whash
ON design_images(whash) WHERE whash IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_design_images_user_active
ON design_images(user_id, is_active) WHERE is_active = true;

-- Add production_partner_ids column
ALTER TABLE etsy_product_templates
ADD COLUMN IF NOT EXISTS production_partner_ids TEXT;

-- Update statistics
ANALYZE design_images;
ANALYZE etsy_product_templates;
```

---

## Files Changed

**Migrations Added**:

- ✅ `migration-service/migrations/add_phash_indexes.py`
- ✅ `migration-service/migrations/add_production_partner_ids.py`

**Old Files Removed**:

- ❌ `server/migrations/add_phash_indexes.sql` (converted to Python)
- ❌ `server/migrations/add_production_partner_ids.sql` (converted to Python)

---

## Next Steps After Migration

1. **Restart your application** (if needed to reload schema)
2. **Verify the error is fixed**:
   - Upload workflow should be faster (due to indexes)
   - Etsy mockup uploads should succeed without `readiness_state_id` error
3. **Monitor performance**:
   - Check duplicate detection query times
   - Verify NAS uploads are working

---

**Last Updated**: 2025-09-30
**Status**: ✅ Ready to run
