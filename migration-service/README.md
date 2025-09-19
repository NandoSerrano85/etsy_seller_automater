# Migration Service

A standalone Railway service for running database migrations and data imports.

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

## File Structure

```
migration-service/
├── Dockerfile              # Migration service container
├── migration-requirements.txt  # Minimal dependencies
├── run-migrations.py       # Main migration runner
├── railway.json           # Railway service config
└── README.md              # This file
```
