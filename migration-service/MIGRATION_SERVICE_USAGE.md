# Migration Service Usage Guide

The migration service now includes local design migration alongside existing NAS and schema migrations.

## Migration Modes

### 1. **All Migrations** (default)

Runs all available migrations in order:

```bash
MIGRATION_MODE=all python run-migrations.py
```

### 2. **Startup Only**

Runs only database schema migrations:

```bash
MIGRATION_MODE=startup python run-migrations.py
```

### 3. **Local Design Migration Only**

Migrates designs from LOCAL_ROOT_PATH to database:

```bash
MIGRATION_MODE=local-only python run-migrations.py
```

### 4. **NAS Migration Only**

Migrates designs from NAS to database:

```bash
MIGRATION_MODE=nas-only python run-migrations.py
```

## Local Design Migration

### Environment Variables

**Required:**

- `DATABASE_URL` - PostgreSQL connection string
- `LOCAL_ROOT_PATH` - Path to directory containing shop folders

**Optional:**

- `LOCAL_MIGRATION_DRY_RUN=true` - Preview changes without making them
- `LOCAL_MIGRATION_SHOP=ShopName` - Migrate only specific shop
- `LOCAL_MIGRATION_TEMPLATE=TemplateName` - Migrate only specific template

### Examples

#### Basic Local Migration

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export LOCAL_ROOT_PATH="/path/to/your/designs"
export MIGRATION_MODE="local-only"

python run-migrations.py
```

#### Dry Run (Preview Only)

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export LOCAL_ROOT_PATH="/path/to/your/designs"
export LOCAL_MIGRATION_DRY_RUN="true"
export MIGRATION_MODE="local-only"

python run-migrations.py
```

#### Migrate Specific Shop

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export LOCAL_ROOT_PATH="/path/to/your/designs"
export LOCAL_MIGRATION_SHOP="MyShopName"
export MIGRATION_MODE="local-only"

python run-migrations.py
```

#### Migrate Specific Template

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export LOCAL_ROOT_PATH="/path/to/your/designs"
export LOCAL_MIGRATION_TEMPLATE="UVDTF 16oz"
export MIGRATION_MODE="local-only"

python run-migrations.py
```

### Expected Directory Structure

```
LOCAL_ROOT_PATH/
├── shop1/
│   ├── template1/
│   │   ├── design1.png
│   │   └── design2.png
│   ├── template2/
│   │   └── design3.png
│   └── Digital/
│       └── template3/
│           └── digital_design1.png
└── shop2/
    └── template4/
        └── design5.png
```

### Migration Process

1. **Discovery**: Scans LOCAL_ROOT_PATH for shop/template directories and image files
2. **Validation**: Matches shop names to users and template names to database entries
3. **Processing**: Crops transparent areas, resizes images, generates 4 perceptual hashes
4. **Duplicate Detection**: Compares hashes against existing database entries
5. **Insertion**: Adds unique designs to design_images table in batches

### Dependencies

The migration requires these Python packages:

```bash
pip install opencv-python pillow imagehash numpy sqlalchemy
```

## Railway Deployment

### With Local Migration

```bash
# Railway environment variables
DATABASE_URL=postgresql://...
LOCAL_ROOT_PATH=/app/designs
MIGRATION_MODE=all

# Optional: Configure local migration
LOCAL_MIGRATION_DRY_RUN=false
```

### Local Migration in Docker

```dockerfile
# Copy design files to container
COPY designs/ /app/designs/

# Set environment variables
ENV LOCAL_ROOT_PATH=/app/designs
ENV MIGRATION_MODE=all
```

## Integration with Existing Workflow

After local migration completes:

1. **Designs Available**: All migrated designs appear in the design gallery
2. **Duplicate Detection**: New uploads are checked against migrated designs
3. **Mockup Generation**: Migrated designs can be used for mockup creation
4. **Hash-Based Matching**: Enhanced duplicate detection using 4 hash algorithms

## Output Example

```
🚀 Starting migration service...
📋 Migration mode: local-only
✅ Database connection established
🔄 Running local design import migration...
LOCAL_ROOT_PATH: /path/to/designs
Dry run mode: false
📊 Loading existing data from database...
Found 150 existing design hashes
Found 5 users and 12 templates
🔍 Scanning for design files...
Scanning shop: MyShop1
Scanning shop: MyShop2
Found 247 design files total
🔄 Processing 247 design files...
Progress: 50/247 files processed
Progress: 100/247 files processed
Progress: 150/247 files processed
Progress: 200/247 files processed
============================================================
LOCAL DESIGN MIGRATION SUMMARY
============================================================
Total files found: 247
Designs created: 89
Designs skipped (duplicates/missing templates): 158
Errors: 0
✅ Local design migration completed successfully!
🎉 Migration service completed successfully!
```

## Error Handling

The migration service handles errors gracefully:

- **Missing Dependencies**: Warns and skips if opencv/pillow/imagehash not available
- **Missing LOCAL_ROOT_PATH**: Skips local migration if not configured
- **Missing Shop/Template**: Logs warnings but continues with other files
- **Duplicate Images**: Skips duplicates based on hash comparison
- **Processing Errors**: Logs errors but continues with remaining files
- **Database Errors**: Uses transactions to ensure data consistency

## Safety Features

- ✅ **Atomic Transactions**: All changes committed together or rolled back
- ✅ **Duplicate Detection**: Prevents duplicate entries using multiple hash algorithms
- ✅ **Batch Processing**: Processes designs in batches of 50 for performance
- ✅ **Dry Run Mode**: Preview changes without making them
- ✅ **Error Recovery**: Continues processing if individual files fail
- ✅ **Optional Execution**: Skips gracefully if LOCAL_ROOT_PATH not configured

## Monitoring

Monitor migration progress through logs:

- Progress updates every 50 files
- Detailed error logging
- Final summary with statistics
- Individual file processing status

The local design migration integrates seamlessly with your existing migration service and provides a robust way to import existing design files into your database.
