# Design Migration Scripts

This directory contains scripts to migrate existing design files from `LOCAL_ROOT_PATH` to the `design_images` database table.

## Overview

The migration scripts will:

1. **Scan** existing design files in `LOCAL_ROOT_PATH/<shop_name>/<template_name>/`
2. **Process** each image (crop transparent areas, resize for standardization)
3. **Generate** perceptual hashes (phash, ahash, dhash, whash) for duplicate detection
4. **Check** for duplicates against existing database entries
5. **Insert** unique designs into the `design_images` table

## Directory Structure Expected

```
LOCAL_ROOT_PATH/
├── shop1/
│   ├── template1/
│   │   ├── design1.png
│   │   ├── design2.jpg
│   │   └── design3.png
│   ├── template2/
│   │   └── design4.png
│   └── Digital/
│       └── template3/
│           ├── digital_design1.png
│           └── digital_design2.png
└── shop2/
    ├── template4/
    │   └── design5.png
    └── Mockups/           # Ignored
        └── ...
```

## Scripts Available

### 1. `simple_design_migration.py` (Recommended)

**Simple standalone script with minimal dependencies.**

#### Features:

- ✅ No complex project imports required
- ✅ Direct database connection via `psycopg2`
- ✅ Built-in image processing (crop, resize, hash)
- ✅ Duplicate detection
- ✅ Progress logging
- ✅ Error handling and rollback

#### Usage:

```bash
# Install dependencies
pip install -r migration_requirements.txt

# Set environment variables
export LOCAL_ROOT_PATH="/path/to/your/designs"
export DATABASE_URL="postgresql://user:password@host:port/database"

# Run migration
python simple_design_migration.py
```

### 2. `migrate_existing_designs.py` (Advanced)

**Full-featured script with project integration.**

#### Features:

- ✅ Uses existing project utilities (crop_transparent, resize_image_by_inches)
- ✅ Dry-run mode for testing
- ✅ Shop/template filtering
- ✅ Detailed statistics
- ✅ Multi-tenant support

#### Usage:

```bash
# Preview what would be migrated (dry-run)
python migrate_existing_designs.py --dry-run

# Migrate all designs
python migrate_existing_designs.py

# Migrate specific shop only
python migrate_existing_designs.py --shop-name "MyShopName"

# Migrate specific template only
python migrate_existing_designs.py --template-name "UVDTF 16oz"

# Verbose logging
python migrate_existing_designs.py --verbose
```

## Environment Variables Required

```bash
# Required for both scripts
LOCAL_ROOT_PATH="/path/to/your/design/root"     # Path to directory containing shop folders
DATABASE_URL="postgresql://user:pass@host/db"   # PostgreSQL connection string

# Optional
ENABLE_MULTI_TENANT="true"                      # Enable multi-tenant mode (default: false)
```

## Database Requirements

The scripts expect the following database structure:

### Tables Required:

- `users` - with `shop_name` field
- `etsy_product_templates` - with `name` and `user_id` fields
- `design_images` - target table for migrations

### design_images Table Columns:

```sql
- id (UUID, primary key)
- user_id (UUID, foreign key to users)
- org_id (UUID, optional for multi-tenant)
- filename (string)
- file_path (string)
- phash (string, 64 chars)
- ahash (string, 64 chars)
- dhash (string, 64 chars)
- whash (string, 64 chars)
- is_active (boolean)
- is_digital (boolean)
- created_at (timestamp)
- updated_at (timestamp)
```

## Migration Process Flow

1. **Discovery Phase**
   - Scan `LOCAL_ROOT_PATH` for shop directories
   - Find template subdirectories (including `Digital/`)
   - Identify image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`)

2. **Validation Phase**
   - Match shop names to users in database
   - Match template names to `etsy_product_templates`
   - Skip files where user/template doesn't exist

3. **Processing Phase**
   - Load each image with OpenCV
   - Crop transparent areas
   - Resize for standardization (3000x3000 max, maintaining aspect ratio)
   - Generate 4 perceptual hashes

4. **Duplicate Detection**
   - Compare all generated hashes against existing database entries
   - Skip if any hash matches (indicates duplicate)

5. **Database Insertion**
   - Insert unique designs into `design_images` table
   - Handle multi-tenant `org_id` if enabled
   - Commit all changes atomically

## Expected Output

```
2024-01-15 10:30:00 - INFO - 🚀 Starting simple design migration
2024-01-15 10:30:00 - INFO - LOCAL_ROOT_PATH: /path/to/designs
2024-01-15 10:30:01 - INFO - ✅ Connected to database
2024-01-15 10:30:01 - INFO - 📊 Loading existing data from database...
2024-01-15 10:30:01 - INFO - Found 150 existing design hashes
2024-01-15 10:30:01 - INFO - Found 5 users and 12 templates
2024-01-15 10:30:02 - INFO - 🔍 Scanning for design files...
2024-01-15 10:30:02 - INFO - Scanning shop: MyShop1
2024-01-15 10:30:03 - INFO - Scanning shop: MyShop2
2024-01-15 10:30:03 - INFO - Found 247 design files total
2024-01-15 10:30:04 - INFO - 🔄 Processing 247 design files...
2024-01-15 10:30:10 - INFO - Progress: 50/247 files processed
2024-01-15 10:30:20 - INFO - Progress: 100/247 files processed
...
2024-01-15 10:35:30 - INFO - ============================================================
2024-01-15 10:35:30 - INFO - MIGRATION SUMMARY
2024-01-15 10:35:30 - INFO - ============================================================
2024-01-15 10:35:30 - INFO - Total files found: 247
2024-01-15 10:35:30 - INFO - Designs created: 89
2024-01-15 10:35:30 - INFO - Designs skipped (duplicates/missing templates): 158
2024-01-15 10:35:30 - INFO - Errors: 0
2024-01-15 10:35:30 - INFO - ✅ Migration completed successfully!
```

## Troubleshooting

### Common Issues:

1. **"No user found for shop"**
   - Check that `users.shop_name` matches directory names exactly
   - Verify shop directories exist in `LOCAL_ROOT_PATH`

2. **"No template found"**
   - Ensure `etsy_product_templates.name` matches subdirectory names
   - Create missing templates in database first

3. **"Could not load image"**
   - Check file permissions
   - Verify image files are not corrupted
   - Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF

4. **Database connection errors**
   - Verify `DATABASE_URL` is correct
   - Check database server is running
   - Ensure user has INSERT permissions on `design_images` table

5. **Import errors (migrate_existing_designs.py)**
   - Run from server directory: `cd server && python migrate_existing_designs.py`
   - Ensure all project dependencies are installed

### Performance Tips:

- Run during off-peak hours for large migrations
- Use `--dry-run` first to estimate time and check for issues
- Monitor database performance during migration
- Consider processing in batches for very large datasets

## Safety Features

- ✅ **Atomic transactions** - All changes committed together or rolled back
- ✅ **Duplicate detection** - Prevents duplicate entries
- ✅ **Error handling** - Continues processing if individual files fail
- ✅ **Dry-run mode** - Preview changes without making them
- ✅ **Detailed logging** - Track progress and debug issues

## After Migration

Once migration is complete:

1. **Verify data** - Check `design_images` table for expected entries
2. **Test workflow** - Upload new designs to ensure duplicate detection works
3. **Update frontend** - Designs should now appear in design gallery
4. **Generate mockups** - Existing designs can now be used for mockup generation

The migrated designs will be fully integrated with your image processing workflow and available for mockup generation via the `/mockups/upload-mockup` endpoint.
