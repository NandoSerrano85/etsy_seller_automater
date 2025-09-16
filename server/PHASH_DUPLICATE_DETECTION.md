# Perceptual Hash-Based Duplicate Detection System

## Overview

The duplicate detection system has been completely refactored to use database-stored perceptual hashes (phashes) instead of reading files from disk. This provides much faster duplicate detection and better scalability.

## Changes Made

### 1. Database Migration

**File:** `server/migrations/add_phash_to_designs.py`

- Adds `phash` column (VARCHAR(64)) to `design_images` table
- Creates index for fast lookups: `idx_design_images_phash`
- Includes both upgrade and downgrade functions

### 2. Entity Update

**File:** `server/src/entities/designs.py`

- Added `phash = Column(String(64), nullable=True)` field to DesignImages model

### 3. One-Time Migration Script

**File:** `server/scripts/generate_design_phashes.py`

- Generates phashes for all existing designs in the QNAP NAS
- Searches in `/share/Graphics/<shop_name>/<template_name>/` pattern
- Processes designs in batches for memory efficiency
- Handles various file path formats and missing files gracefully
- Provides detailed logging and progress tracking

### 4. Enhanced Duplicate Detection Functions

**File:** `server/src/routes/mockups/service.py`

- Added `calculate_phash()` function for generating perceptual hashes
- Added `check_duplicates_in_database()` function for database-based duplicate checking
- Updated duplicate detection logic to use database queries instead of file system scans

### 5. Design Creation Service Update

**File:** `server/src/routes/designs/service.py`

- Added phash calculation during design creation
- New designs automatically get phashes stored in database

## How It Works

### New Design Upload Process:

1. **File Upload**: User uploads image files
2. **Phash Calculation**: System calculates perceptual hash for each image
3. **Database Check**: Queries existing designs for similar phashes using Hamming distance
4. **Duplicate Filter**: Removes duplicates based on configurable threshold (default: 5)
5. **Storage**: Stores phash with design record for future comparisons

### Existing Design Migration:

1. **Run Migration**: Execute database migration to add phash column
2. **Run Script**: Execute `generate_design_phashes.py` to populate existing records
3. **Verify**: All designs now have phashes for fast duplicate detection

## Key Benefits

### Performance Improvements:

- **Fast Lookups**: Database queries instead of file system scans
- **Scalable**: Works efficiently with thousands of designs
- **Memory Efficient**: No need to load large hash databases into memory

### Accuracy Improvements:

- **Consistent Hashing**: Uses same algorithm (imagehash.phash) across all operations
- **Configurable Threshold**: Hamming distance threshold (default: 5) for duplicate detection
- **Better Error Handling**: Graceful handling of missing or corrupted files

### Maintenance Benefits:

- **No File Dependencies**: Doesn't require access to original files for comparison
- **Centralized Storage**: All hash data stored in database
- **Easy Debugging**: Clear logging and error reporting

## Installation & Usage

### 1. Run Database Migration:

```bash
# Apply the migration (exact command depends on your migration system)
python -c "
from server.migrations.add_phash_to_designs import upgrade
from sqlalchemy import create_engine
from server.src.database.core import get_database_url

engine = create_engine(get_database_url())
with engine.connect() as conn:
    upgrade(conn)
    conn.commit()
"
```

### 2. Generate Phashes for Existing Designs:

```bash
cd /path/to/server
python scripts/generate_design_phashes.py
```

### 3. Verify Installation:

```sql
-- Check that phash column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'design_images' AND column_name = 'phash';

-- Check that phashes were generated
SELECT COUNT(*) as total_designs,
       COUNT(phash) as designs_with_phash,
       COUNT(*) - COUNT(phash) as designs_without_phash
FROM design_images
WHERE is_active = true;
```

## Configuration

### Duplicate Detection Threshold:

The Hamming distance threshold can be adjusted in the duplicate checking functions:

- **Threshold 0**: Exact matches only
- **Threshold 5**: Default - catches very similar images
- **Threshold 10**: More lenient - catches loosely similar images

### File Path Patterns:

The migration script searches for files in:

- Primary: `/share/Graphics/<shop_name>/<template_name>/`
- Fallback: Direct file_path from database
- Alternative: User-specific directories

## Error Handling

### Missing Files:

- Script logs warnings for missing files but continues processing
- Database records are preserved even if files are missing
- Future uploads will still work correctly

### Invalid Phashes:

- Invalid stored phashes are logged and skipped
- System gracefully handles corrupted hash data
- New phashes can be regenerated if needed

## Monitoring & Maintenance

### Performance Monitoring:

```sql
-- Check duplicate detection performance
EXPLAIN ANALYZE
SELECT * FROM design_images
WHERE phash IS NOT NULL
  AND user_id = 'some-user-id'
  AND is_active = true;
```

### Maintenance Tasks:

```sql
-- Find designs without phashes
SELECT id, filename, file_path
FROM design_images
WHERE phash IS NULL
  AND is_active = true;

-- Regenerate missing phashes (run migration script)
```

## Backward Compatibility

The old file-based duplicate detection functions remain in the codebase but are no longer used. This ensures:

- No breaking changes for existing code
- Easy rollback if issues arise
- Gradual migration path

## Future Enhancements

1. **Batch Phash Updates**: API endpoint to regenerate phashes for specific designs
2. **Advanced Similarity**: Integration with more sophisticated image similarity algorithms
3. **Performance Optimization**: Further database query optimization for very large datasets
4. **Duplicate Management**: UI for reviewing and managing detected duplicates
