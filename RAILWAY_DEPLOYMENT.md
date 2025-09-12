# Railway Deployment Guide

This guide explains how to deploy the Etsy Seller Automater with the new multi-tenant architecture on Railway.

## Architecture Overview

The application now supports a microservices architecture with the following components:

### Services

1. **API Service** - Main FastAPI backend (`server/main.py`)
2. **Background Workers** - Process async tasks (`server/worker/main.py`)
3. **Print Job Workers** - Handle print processing
4. **Task Scheduler** - Periodic task execution
5. **PostgreSQL** - Primary database
6. **Redis** - Task queues and caching

### External Dependencies

- **QNAP NAS** - File storage via SFTP
- **Etsy API** - Marketplace integration

## Deployment Steps

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init
```

### 2. Add Required Services

Add these services to your Railway project:

#### PostgreSQL Plugin

```bash
railway add postgresql
```

#### Redis Plugin

```bash
railway add redis
```

### 3. Configure Environment Variables

Set these variables in your Railway project:

#### Application Secrets

```
JWT_SECRET=your-jwt-secret-key
ETSY_API_KEY=your-etsy-api-key
ETSY_CLIENT_SECRET=your-etsy-client-secret
```

#### QNAP NAS Configuration

```
QNAP_NAS_HOST=your.qnap.host.com
QNAP_NAS_USERNAME=your-username
QNAP_NAS_PASSWORD=your-password
QNAP_NAS_BASE_PATH=/share/Graphics
```

#### Frontend URL

```
FRONTEND_URL=https://your-frontend-domain.railway.app
```

### 4. Deploy Main API Service

The current Railway configuration will deploy the main API service:

```bash
railway up
```

### 5. Add Additional Worker Services

To add background workers, create additional Railway services:

#### Background Worker Service

- Create new service in Railway dashboard
- Use same GitHub repo
- Set build command: `docker build -f Dockerfile.railway-worker .`
- Set start command: `python server/worker/main.py`
- Add environment variable: `WORKER_TYPE=general`

#### Print Job Worker Service

- Create new service in Railway dashboard
- Use same GitHub repo
- Set build command: `docker build -f Dockerfile.railway-worker .`
- Set start command: `python server/worker/print_processor.py`
- Add environment variable: `WORKER_TYPE=print_jobs`

#### Scheduler Service

- Create new service in Railway dashboard
- Use same GitHub repo
- Set build command: `docker build -f Dockerfile.railway-worker .`
- Set start command: `python server/worker/scheduler.py`
- Add environment variable: `WORKER_TYPE=scheduler`

### 6. Database Migration

After deployment, run database migrations:

```bash
# Connect to your Railway project
railway shell

# Run the migration scripts
python -c "
import sys
sys.path.insert(0, '.')
exec(open('migration_add_railway_entities.py').read())
"

# Run printer and canvas config migration
python migration_add_printers_and_canvas_updates.py
```

Or use Alembic if configured:

```bash
railway run alembic upgrade head
```

## New API Endpoints

The multi-tenant architecture provides these new endpoints:

### Organizations

- `POST /api/organizations/` - Create organization
- `GET /api/organizations/` - List organizations
- `GET /api/organizations/{id}` - Get organization
- `PUT /api/organizations/{id}` - Update organization
- `DELETE /api/organizations/{id}` - Delete organization
- `GET /api/organizations/{id}/features` - Get feature flags
- `PUT /api/organizations/{id}/features` - Update feature flags
- `GET /api/organizations/{id}/stats` - Get statistics

### Shops

- `POST /api/organizations/{org_id}/shops/` - Connect shop
- `GET /api/organizations/{org_id}/shops/` - List shops
- `GET /api/organizations/{org_id}/shops/{id}` - Get shop
- `PUT /api/organizations/{org_id}/shops/{id}` - Update shop
- `DELETE /api/organizations/{org_id}/shops/{id}` - Disconnect shop
- `POST /api/organizations/{org_id}/shops/{id}/sync` - Trigger sync

### Files (NAS Storage)

- `POST /api/organizations/{org_id}/files/upload` - Upload file
- `GET /api/organizations/{org_id}/files/search` - Search files
- `GET /api/organizations/{org_id}/files/{id}` - Get file info
- `PUT /api/organizations/{org_id}/files/{id}` - Update file
- `DELETE /api/organizations/{org_id}/files/{id}` - Delete file
- `GET /api/organizations/{org_id}/files/{id}/download` - Download file
- `GET /api/organizations/{org_id}/files/stats/storage` - Storage stats

### Print Jobs

- `POST /api/organizations/{org_id}/print-jobs/` - Create job
- `GET /api/organizations/{org_id}/print-jobs/search` - Search jobs
- `GET /api/organizations/{org_id}/print-jobs/{id}` - Get job
- `POST /api/organizations/{org_id}/print-jobs/{id}/retry` - Retry job
- `POST /api/organizations/{org_id}/print-jobs/{id}/cancel` - Cancel job
- `GET /api/organizations/{org_id}/print-jobs/stats/summary` - Job stats
- `GET /api/organizations/{org_id}/print-jobs/queue/info` - Queue info

### Events/Audit

- `POST /api/organizations/{org_id}/events/` - Create event
- `GET /api/organizations/{org_id}/events/search` - Search events
- `GET /api/organizations/{org_id}/events/{id}` - Get event
- `GET /api/organizations/{org_id}/events/audit/{type}/{id}` - Audit trail
- `GET /api/organizations/{org_id}/events/activity/user/{id}` - User activity
- `GET /api/organizations/{org_id}/events/activity/errors` - System errors
- `GET /api/organizations/{org_id}/events/stats/summary` - Event stats
- `GET /api/organizations/{org_id}/events/export/audit-trail` - Export audit

### Printers

- `POST /api/printers/` - Create printer
- `GET /api/printers/` - List user printers
- `GET /api/printers/{id}` - Get printer details
- `PUT /api/printers/{id}` - Update printer
- `DELETE /api/printers/{id}` - Delete printer
- `POST /api/printers/{id}/check-capability` - Check print capability
- `GET /api/printers/compatible/find` - Find compatible printers
- `GET /api/printers/default/get` - Get default printer
- `POST /api/printers/{id}/set-default` - Set default printer
- `GET /api/printers/stats/summary` - Printer statistics
- `GET /api/printers/suggestions/config` - Configuration suggestions

## File Storage Architecture

The application now uses a hybrid storage approach:

### Development Mode

- Files stored locally (`LOCAL_ROOT_PATH` set)
- Backed up to QNAP NAS via SFTP

### Production Mode (Railway)

- Files stored directly on QNAP NAS
- No local storage required
- Path format: `/share/Graphics/{shop_name}/{file_type}/{filename}`

## Multi-Tenancy

The application now supports multiple organizations:

### Organization Structure

- Each organization has a `shop_name` that maps to NAS directory
- Organizations can have multiple users and shops
- Feature flags control functionality per organization
- All data is isolated by `org_id`

### User Assignment

- Users belong to one organization
- User access is controlled by organization membership
- Role-based access control within organizations

## Background Jobs

The system supports various background job types:

### Job Types

- `gang_sheets` - Generate gang sheet layouts
- `mockups` - Create product mockups
- `designs` - Process design files
- `orders` - Handle order processing
- `print_files` - Generate print-ready files

### Queue Management

- Jobs queued in Redis
- Multiple workers process jobs
- Retry logic for failed jobs
- Status tracking and progress monitoring

## Monitoring & Health Checks

### Health Endpoints

- `GET /health` - Comprehensive health check
- `GET /ping` - Simple ping response

### Monitoring Features

- System resource monitoring
- Database connection health
- Service status tracking
- Error rate monitoring

## Security Considerations

### Environment Variables

- All secrets encrypted in Railway
- Database URLs auto-generated
- NAS credentials secured
- JWT secrets properly managed

### Access Control

- Organization-based data isolation
- User authentication required
- Role-based permissions
- Audit logging for all actions

## Troubleshooting

### Common Issues

1. **NAS Connection Failures**
   - Check QNAP*NAS*\* environment variables
   - Verify network connectivity to NAS
   - Ensure SFTP access is enabled on QNAP

2. **Database Migration Errors**
   - Run migration script manually
   - Check DATABASE_URL configuration
   - Verify PostgreSQL plugin is active

3. **Worker Connection Issues**
   - Verify REDIS_URL is set
   - Check worker service status
   - Review worker logs for errors

4. **File Upload Problems**
   - Verify NAS storage configuration
   - Check file permissions on NAS
   - Review storage statistics

### Logs and Debugging

```bash
# View service logs
railway logs

# Connect to service shell
railway shell

# Check environment variables
railway variables
```

## Scaling Considerations

### Horizontal Scaling

- API service can be scaled up/down
- Worker services can run multiple replicas
- Database connections managed via connection pooling

### Resource Limits

- Monitor CPU/memory usage
- Scale workers based on queue length
- Optimize file storage usage

### Cost Optimization

- Use appropriate service sizing
- Monitor resource utilization
- Implement auto-scaling policies if needed
