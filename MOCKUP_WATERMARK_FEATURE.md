# Mockup Generation with Watermark Feature

## Overview

This document describes the watermark functionality for mockup generation and the migration tool to regenerate all Etsy mockups with proper watermarks.

## Features Implemented

### 1. Watermark Support in Mockup Generation

- **Watermark Upload**: Users can now upload a watermark file when generating mockups
- **Automatic Application**: Watermarks are automatically applied to all generated mockups with 45% opacity
- **Centered Placement**: Watermarks are centered on the mockup image at 60% of image width
- **Database Storage**: Watermark paths are stored in `mockup_images` table for reference

### 2. Migration for Regenerating Etsy Mockups

A new migration has been created to regenerate all Etsy design mockups with proper watermarks.

**Migration File**: `migration-service/migrations/regenerate_etsy_mockups_with_watermark.py`

**How to Trigger**:
Set the following environment variable in Railway:

```bash
REGENERATE_ETSY_MOCKUPS=true
```

**Optional Configuration**:

```bash
WATERMARK_PATH=/share/Graphics/FunnyBunny/Mockups/BaseMockups/Watermarks/Rectangle Watermark.png
```

**Dependencies**:

The migration requires the following dependencies to be installed in the migration service:

- `opencv-python-headless==4.8.1.78` - For image processing and watermark application
- `numpy==1.24.3` - For numerical operations on images

These are included in `migration-service/migration-requirements.txt`.

**What It Does**:

1. Checks for required dependencies (cv2, numpy) and gracefully skips if not available
2. Finds all Etsy mockups in the database (where `template_source = 'etsy'` or NULL)
3. For each mockup:
   - Retrieves associated designs
   - Loads the proper template configuration
   - Regenerates all mockup images with the watermark applied
   - Updates the `mockup_images` table with watermark paths
4. Provides detailed logging of success/failure for each mockup

**Usage**:

```bash
# In Railway dashboard or railway.json:
REGENERATE_ETSY_MOCKUPS=true

# Deploy to trigger the migration
# After completion, remove or set to false:
REGENERATE_ETSY_MOCKUPS=false
```

## Frontend Changes

### CraftFlow Product Creator (`/craftflow/products/create`)

**New Fields**:

- **Template Section**: Now collapsible with Show/Hide toggle
- **Design Files Upload**: Multi-file upload for designs
- **Watermark File Upload**: Single file upload for watermark (required)
  - Accepts: PNG, JPEG, JPG
  - Description: "Upload a transparent PNG watermark that will be applied to all generated mockups"

**User Flow**:

1. Click "Add Product with Template" button
2. Template section auto-expands
3. Select a CraftFlow Commerce template
4. Upload design file(s)
5. Upload watermark file (required)
6. Click "Generate Mockups with Watermark"
7. Mockups are generated with watermark and added to product images

**Validation**:

- Template must be selected
- At least one design file must be uploaded
- Watermark file must be uploaded
- Button is disabled until all requirements are met

## Backend Implementation

### Mockup Utility (`server/src/utils/mockups_util.py`)

**Key Functions**:

- `add_watermark()`: Applies watermark to mockup image
  - Scales watermark to 60% of image width
  - Centers watermark on image
  - Applies at 45% opacity
  - Supports alpha channel blending

- `create_mockup_images()`: Creates mockups from design files
  - Accepts optional `watermark_path` parameter
  - Defaults to: `{root_path}Mockups/BaseMockups/Watermarks/Rectangle Watermark.png`
  - Applies watermark to all generated mockups

- `create_mockups_for_etsy()`: Batch creates mockups for Etsy designs
  - Uses watermark from mockup_images or default
  - Supports parallel processing for large batches
  - Saves to NAS in production or local filesystem in development

### Mockup Service (`server/src/routes/mockups/service.py`)

**`upload_mockup_files()`**:

- Accepts `watermark_file` parameter
- Saves watermark to NAS or local storage
- Stores watermark path in `mockup_images` table
- Format: `/share/Graphics/{shop_name}/Mockups/BaseMockups/Watermarks/{filename}`

## Database Schema

### `mockup_images` Table

```sql
ALTER TABLE mockup_images
ADD COLUMN watermark_path VARCHAR;
```

The `watermark_path` column stores the full path to the watermark file used for that mockup image.

## Environment Variables

### Required for Production

- `RAILWAY_ENVIRONMENT_NAME`: Indicates Railway production environment
- `QNAP_HOST`: QNAP NAS host
- `QNAP_USERNAME`: QNAP NAS username
- `QNAP_PASSWORD`: QNAP NAS password

### Optional for Migration

- `REGENERATE_ETSY_MOCKUPS`: Set to `true` to trigger regeneration (default: `false`)
- `WATERMARK_PATH`: Custom watermark path (default: `/share/Graphics/FunnyBunny/Mockups/BaseMockups/Watermarks/Rectangle Watermark.png`)

## Testing

### Local Testing

1. Set up local environment with design files
2. Create a mockup with template
3. Upload design files and watermark
4. Verify generated mockups have watermark applied

### Production Testing

1. Deploy with `REGENERATE_ETSY_MOCKUPS=true`
2. Monitor migration logs
3. Verify mockups are regenerated with watermarks
4. Check NAS storage for updated mockup files
5. Set `REGENERATE_ETSY_MOCKUPS=false` after completion

## Migration Logs

The migration provides detailed logging:

- `⏭️  Skipping` - Migration not triggered (env var not set)
- `🔄 Starting` - Migration has started
- `Found X mockups` - Number of mockups to process
- `✅ Successfully regenerated` - Individual mockup success
- `❌ Failed to regenerate` - Individual mockup failure
- `✅ Completed` - Final summary with counts

## Error Handling

The migration is designed to be resilient:

- Continues processing even if individual mockups fail
- Logs detailed error messages and stack traces
- Rolls back database changes on error
- Provides summary of successful vs failed mockups
- Idempotent - can be run multiple times safely

## Performance

- **Sequential Processing**: Used for ≤10 designs (simpler, easier to debug)
- **Parallel Processing**: Used for >10 designs (8 workers max)
- **NAS Upload**: Retries built into NAS storage service
- **Memory Efficient**: Processes one mockup at a time in sequential mode

## Maintenance

### To Update Default Watermark

1. Upload new watermark to NAS: `/share/Graphics/{shop_name}/Mockups/BaseMockups/Watermarks/`
2. Update `WATERMARK_PATH` environment variable
3. Run migration to regenerate with new watermark

### To Regenerate Specific Mockups

Modify the migration query to filter by specific criteria:

```python
mockups_query = db.query(Mockups).filter(
    Mockups.id == specific_id
).all()
```

## Future Enhancements

Potential improvements:

- [ ] Watermark position configuration (top-left, bottom-right, etc.)
- [ ] Watermark opacity configuration
- [ ] Multiple watermark support
- [ ] Watermark library/gallery
- [ ] Batch regeneration UI
- [ ] Progress tracking for large regenerations
- [ ] Email notification when regeneration completes
