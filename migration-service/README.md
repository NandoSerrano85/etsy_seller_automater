# Migration Service

The Migration Service is the centralized database migration system for CraftFlow/PrintPilot. It handles all database schema changes, data migrations, and system updates in a safe, reliable, and auditable manner.

## Purpose

This service runs independently from the main API to:

- ✅ **Prevent health check failures** - Main API starts immediately
- ✅ **Run heavy operations** - NAS imports, data migrations, etc.
- ✅ **Isolate failures** - Migration issues don't affect API availability
- ✅ **Enable on-demand execution** - Run migrations when needed

## Setup in Railway

### 1. Create New Service

1. In Railway dashboard, click "New Service"
2. Choose "Deploy from GitHub repo"
3. Select your repository
4. Choose "migration-service" as the service name

### 2. Environment Variables

Set these in the migration service:

```bash
# Database (same as main API)
DATABASE_URL=postgresql://user:pass@host:port/db

# NAS Configuration
QNAP_HOST=your.nas.ip.address
QNAP_USERNAME=your_nas_username
QNAP_PASSWORD=your_nas_password
QNAP_PORT=22
NAS_BASE_PATH=/share/Graphics

# Migration Control
MIGRATION_MODE=all  # Options: 'all', 'startup', 'nas-only'

# NAS Processing Options
NAS_USE_BATCHED=true  # Use optimized batch processing (default: true)
```

### 3. Service Configuration

- **Service Type**: Background Worker (not web service)
- **Build**: Uses `migration-service/Dockerfile`
- **Restart Policy**: On Failure (max 3 retries)

## Migration Modes

### `MIGRATION_MODE=all` (default)

Runs all migrations:

1. Startup migrations (lightweight schema changes)
2. NAS design import (heavy data import)
3. Complex migrations (heavy data transformations)

### `MIGRATION_MODE=startup`

Runs only lightweight startup migrations:

- Schema updates
- Index creation
- Enum additions

### `MIGRATION_MODE=nas-only`

Runs only NAS design import:

- Scans `/share/Graphics/<shop_name>/<template_name>/`
- Imports images to `design_images` table
- Generates phashes for duplicate detection

## NAS Processing Options

### Batched Processing (Default)

When `NAS_USE_BATCHED=true` (default):

- **500MB Batches**: Files are grouped into ~500MB chunks
- **Parallel Processing**: Multiple batches processed simultaneously
- **Memory Efficient**: Avoids loading all files at once
- **Progress Tracking**: Detailed logging of batch progress
- **Error Isolation**: Batch failures don't affect other batches
- **Optimal Performance**: Uses multiprocessing for CPU-bound tasks

### Sequential Processing

When `NAS_USE_BATCHED=false`:

- **One-by-one**: Files processed sequentially
- **Lower Memory**: Minimal memory usage
- **Simple Debugging**: Easier to trace individual file issues
- **Slower**: No parallel processing benefits

## Usage

### Automatic Execution

The service runs automatically when deployed or restarted.

### Manual Execution

Restart the service in Railway dashboard to re-run migrations.

### Monitoring

Check service logs in Railway dashboard for:

- Migration progress
- Error messages
- Completion status

## Benefits

1. **Fast API Startup** - Main API health checks pass immediately
2. **Isolated Execution** - Migration failures don't crash API
3. **Resource Control** - Different CPU/memory allocation
4. **Easy Debugging** - Separate logs for migration operations
5. **On-Demand** - Run migrations when needed without API downtime

## 📋 Table of Contents

- [Purpose](#purpose)
- [Setup in Railway](#setup-in-railway)
- [Migration Modes](#migration-modes)
- [Adding New Migrations](#adding-new-migrations)
- [Migration Examples](#migration-examples)
- [File Structure](#file-structure)
- [Architecture Details](#architecture-details)
- [Troubleshooting](#troubleshooting)

## 📁 File Structure

```
migration-service/
├── README.md                    # This comprehensive documentation
├── run-migrations.py            # Main migration runner (centralized logic)
├── migration-requirements.txt   # Python dependencies
├── Dockerfile                  # Container configuration
├── railway.json               # Railway deployment config
└── migrations/                # All migration files (centralized)
    ├── add_multi_tenant_schema.py
    ├── add_etsy_shop_id.py
    ├── add_phash_to_designs.py
    ├── update_phash_hash_size.py
    ├── separate_platform_connections.py
    ├── remove_shopify_unique_constraint.py
    ├── import_nas_designs.py
    ├── import_nas_designs_batched.py
    ├── migration_add_railway_entities.py
    ├── migration_add_printers_and_canvas_updates.py
    └── run_canvas_size_migration.py
```

## ➕ Adding New Migrations

### Step 1: Create Migration File

Create a new Python file in `migration-service/migrations/`:

```bash
# Standard naming convention
touch migration-service/migrations/add_user_preferences.py
```

### Step 2: Implement Migration Structure

```python
#!/usr/bin/env python3
"""
Migration: Add user preferences table

This migration adds a new user_preferences table to store
user-specific settings and preferences.
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade(connection):
    """Add user preferences table"""
    logger.info("🔄 Adding user_preferences table...")

    try:
        # Check if table already exists
        result = connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'user_preferences'
            )
        """))

        if result.scalar():
            logger.info("✅ user_preferences table already exists, skipping")
            return

        # Create the table
        connection.execute(text("""
            CREATE TABLE user_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                preference_key VARCHAR(100) NOT NULL,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Add indexes for performance
        connection.execute(text("""
            CREATE INDEX idx_user_preferences_user_id
            ON user_preferences(user_id)
        """))

        connection.execute(text("""
            CREATE UNIQUE INDEX idx_user_preferences_user_key
            ON user_preferences(user_id, preference_key)
        """))

        logger.info("✅ user_preferences table created successfully")

    except Exception as e:
        logger.error(f"❌ Failed to create user_preferences table: {e}")
        raise

def downgrade(connection):
    """Remove user preferences table (optional)"""
    logger.info("🔄 Removing user_preferences table...")
    try:
        connection.execute(text("DROP TABLE IF EXISTS user_preferences CASCADE"))
        logger.info("✅ user_preferences table removed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to remove user_preferences table: {e}")
        raise
```

### Step 3: Update Migration Order (if needed)

If your migration has dependencies, add it to the migration order in `run-migrations.py`:

```python
# In discover_migrations() function
migration_order = [
    # Core schema migrations (must run first)
    "add_multi_tenant_schema",
    "migration_add_railway_entities",

    # Add your migration in the appropriate order
    "add_user_preferences",  # <-- Add here

    # Platform-specific migrations
    "add_etsy_shop_id",
    # ... rest of migrations
]
```

### Step 4: Test the Migration

```bash
# Test locally first
python run-migrations.py

# Check for any errors in the logs
# Verify database changes manually if needed
```

## 📝 Migration Examples

### Simple Schema Migration

```python
def upgrade(connection):
    """Add email_verified column to users table"""
    logger.info("🔄 Adding email_verified column...")

    # Check if column already exists
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email_verified'
    """))

    if result.scalar() > 0:
        logger.info("✅ email_verified column already exists")
        return

    # Add the column
    connection.execute(text("""
        ALTER TABLE users
        ADD COLUMN email_verified BOOLEAN DEFAULT FALSE
    """))

    logger.info("✅ email_verified column added successfully")
```

### Data Migration with Batching

```python
def upgrade(connection):
    """Update user display names from legacy format"""
    logger.info("🔄 Updating user display names...")

    batch_size = 1000
    offset = 0
    total_updated = 0

    while True:
        # Get batch of users to update
        result = connection.execute(text("""
            SELECT id, first_name, last_name
            FROM users
            WHERE display_name IS NULL
            ORDER BY id
            LIMIT :batch_size OFFSET :offset
        """), {"batch_size": batch_size, "offset": offset})

        users = result.fetchall()
        if not users:
            break

        # Update each user in the batch
        for user in users:
            display_name = f"{user.first_name} {user.last_name}".strip()
            connection.execute(text("""
                UPDATE users
                SET display_name = :display_name
                WHERE id = :user_id
            """), {"display_name": display_name, "user_id": user.id})

        total_updated += len(users)
        offset += batch_size
        logger.info(f"  📊 Updated {total_updated} user display names...")

    logger.info(f"✅ Updated {total_updated} user display names successfully")
```

## 🏗️ Architecture Details

### Core Components

#### 1. Migration Runner (`run-migrations.py`)

The main executable that orchestrates all migration operations:

```python
# Core functions:
- setup_database()           # Database connection setup
- discover_migrations()      # Auto-discovery from migrations/ directory
- run_startup_migrations()   # Schema changes
- run_nas_migration()        # NAS design import operations
- run_complex_migrations()   # Heavy data transformations
```

#### 2. Migration Discovery System

- **Auto-Discovery**: Automatically finds all `.py` files in `migrations/` directory
- **Dependency Ordering**: Maintains correct execution order for dependent migrations
- **Error Handling**: Graceful handling of missing or broken migration files
- **Progress Tracking**: Comprehensive logging for all operations

#### 3. Transaction Management

- **Safe Execution**: Each migration runs in its own transaction
- **Rollback Capability**: Failed migrations are automatically rolled back
- **Error Isolation**: One failed migration doesn't affect others
- **Progress Persistence**: Successful migrations are tracked

### Migration Types

1. **Startup Migrations** (Lightweight, < 30 seconds)
   - Schema changes, constraints, indexes
   - Run on every service start
   - Must be idempotent (safe to run multiple times)

2. **NAS Migrations** (Heavy, minutes to hours)
   - Large data imports from Network Attached Storage
   - Batched processing for memory efficiency
   - Progress tracking and resume capability

3. **Complex Migrations** (Variable duration)
   - Data transformations and optimizations
   - System-wide updates
   - Run only when specifically needed

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```
❌ Database connection failed: could not connect to server
```

**Solution**: Check `DATABASE_URL` and database availability

#### 2. Migration Import Errors

```
❌ Could not load migration_name: No module named 'module'
```

**Solution**: Verify migration file exists in `migrations/` directory and has correct format

#### 3. Transaction Rollback

```
❌ Migration failed: (some error)
```

**Solution**: Check migration logs, fix issues, and re-run. Failed migrations are automatically rolled back.

#### 4. NAS Connection Issues

```
⚠️ NAS credentials not configured, skipping NAS migration
```

**Solution**: Set `QNAP_HOST`, `QNAP_USERNAME`, and `QNAP_PASSWORD` environment variables

### Debugging Tips

1. **Enable Debug Logging**: Add detailed logging to your migrations
2. **Test Locally First**: Always test migrations locally before deploying
3. **Use Transactions**: All migrations automatically run in transactions
4. **Check Dependencies**: Ensure migration order respects dependencies
5. **Verify Database State**: Use database tools to verify changes

### Recovery Procedures

If a migration fails:

1. **Check the logs** for specific error messages
2. **Fix the migration code** based on the error
3. **Re-run the migration** - failed migrations are automatically rolled back
4. **For data migrations**: Consider adding resume capability for large operations

---

_This migration service ensures safe, reliable, and auditable database changes for the CraftFlow/PrintPilot application. All migrations are now centralized in the `migration-service/migrations/` directory for better organization and maintainability._
