# Railway + QNAP NAS Deployment Guide

This guide shows how to deploy your CraftFlow application to Railway using your QNAP NAS as storage instead of AWS S3.

## 🏗️ Architecture Overview

```
Railway Cloud Infrastructure:
├── API Service (FastAPI) - Handles web requests
├── Worker Service - Background image processing
├── PostgreSQL Database - Metadata & app data
├── Redis Cache - Job queues & sessions
└── QNAP NAS (Your Hardware) - File storage via SFTP
```

## 🚀 Deployment Steps

### 1. Railway Project Setup

1. **Create Railway Project**

   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login to Railway
   railway login

   # Create new project
   railway new
   # Name: craftflow-prod
   ```

2. **Add Database Services**

   ```bash
   # Add PostgreSQL
   railway add postgresql

   # Add Redis
   railway add redis
   ```

### 2. Deploy API Service

1. **Create API Service**
   - In Railway Dashboard: Click "New Service" > "GitHub Repo"
   - Connect your repository
   - Service name: `api`
   - Set root directory to: `/` (root of repo)

2. **Configure API Service**

   ```yaml
   # Service Settings
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn server.main:app --host 0.0.0.0 --port $PORT --workers 1
   Port: 8000
   ```

3. **Environment Variables for API**

   ```env
   # Database (Auto-provided by Railway)
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...

   # QNAP NAS Storage
   QNAP_HOST=your-nas-ip-or-hostname
   QNAP_USERNAME=your-nas-username
   QNAP_PASSWORD=your-nas-password
   QNAP_PORT=22
   NAS_BASE_PATH=/share/Graphics

   # Authentication
   JWT_SECRET_KEY=your-super-secure-secret-key
   JWT_ALGORITHM=HS256
   USER_LOGIN_ACCESS_TOKEN_EXPIRE_MINUTES=300

   # Etsy API
   CLIENT_ID=your-etsy-client-id
   CLIENT_SECRET=your-etsy-client-secret

   # App Settings
   DISABLE_REGISTRATION=false
   RAILWAY_ENV=production
   ```

### 3. Deploy Worker Service (Optional)

1. **Create Worker Service**
   - Click "New Service" > "GitHub Repo"
   - Same repository
   - Service name: `worker`
   - Use `Dockerfile.worker`

2. **Configure Worker Service**

   ```yaml
   # Service Settings
   Build Command: pip install -r requirements.txt
   Start Command: python -m server.worker.main
   Port: None (internal service)
   ```

3. **Environment Variables for Worker**
   ```env
   # Same as API service
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   QNAP_HOST=your-nas-ip-or-hostname
   QNAP_USERNAME=your-nas-username
   QNAP_PASSWORD=your-nas-password
   QNAP_PORT=22
   WORKER_CONCURRENCY=2
   ```

### 4. Database Migration

1. **Run Initial Migration**

   ```bash
   # Connect to your deployed API service
   railway shell

   # Inside the Railway shell, run:
   python -c "
   from server.src.database.core import engine
   from server.src.entities import *
   from sqlalchemy import text

   # Run the schema creation
   with open('database_schema_nas.sql', 'r') as f:
       schema = f.read()

   with engine.connect() as conn:
       conn.execute(text(schema))
       conn.commit()
   "
   ```

## 🔧 QNAP NAS Configuration

### 1. Enable SSH on QNAP

1. Log into QNAP web interface
2. Go to **Control Panel > Network & File Services > SSH**
3. Check **"Allow SSH connection"**
4. Set port to `22` (or note your custom port)
5. Click **Apply**

### 2. Create Directory Structure

SSH into your QNAP and create the base directory:

```bash
ssh your-nas-username@your-nas-ip
mkdir -p /share/Graphics
chmod 755 /share/Graphics
```

### 3. Test NAS Connection

```bash
# From your local machine, test SFTP connection
sftp your-nas-username@your-nas-ip
> cd /share/Graphics
> mkdir test_shop
> rmdir test_shop
> quit
```

## 📁 File Storage Structure

Your QNAP NAS will store files in this structure:

```
/share/Graphics/
└── {shop_name}/
    ├── {template_name}/
    │   └── design_files.png
    ├── Mockups/
    │   └── BaseMockups/
    │       ├── {template_name}/
    │       │   └── mockup_files.png
    │       └── Watermarks/
    │           └── watermark_files.png
    ├── Printfiles/
    │   └── gang_sheets.pdf
    └── Exports/
        └── export_files.zip
```

## 🚦 Health Checks

Add health check endpoints to monitor your services:

```python
# In server/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "nas_connection": nas_storage.enabled
    }
```

## 📊 Monitoring

### Railway Metrics

- Monitor CPU/Memory usage in Railway Dashboard
- Set up alerts for service downtime
- Monitor deployment logs

### Application Metrics

```python
# Add to your FastAPI app
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

## 🔐 Security Considerations

1. **NAS Access**
   - Use strong passwords for NAS accounts
   - Consider creating dedicated user for the application
   - Enable 2FA on QNAP admin account

2. **Network Security**
   - Configure QNAP firewall to allow only Railway IPs
   - Use VPN if accessing from external networks
   - Regular security updates on QNAP

3. **Data Backup**
   - Configure QNAP automatic backups
   - Test restore procedures regularly
   - Consider offsite backup for critical data

## 🎯 Environment-Specific Settings

### Production

```env
RAILWAY_ENV=production
LOG_LEVEL=WARNING
WORKER_CONCURRENCY=4
```

### Staging

```env
RAILWAY_ENV=staging
LOG_LEVEL=INFO
WORKER_CONCURRENCY=2
```

### Development

```env
RAILWAY_ENV=development
LOG_LEVEL=DEBUG
WORKER_CONCURRENCY=1
LOCAL_ROOT_PATH=/tmp/dev-files  # Falls back to local storage
```

## 🚀 Scaling

### Horizontal Scaling

- Scale Worker service based on Redis queue length
- API service can be scaled based on request volume

### Vertical Scaling

- Increase RAM for image processing workloads
- Monitor CPU usage during peak times

## 🔄 Deployment Pipeline

1. **Development** → Push to `dev` branch
2. **Staging** → Push to `staging` branch
3. **Production** → Push to `main` branch

Each environment has its own Railway project with isolated databases.

## 🐛 Troubleshooting

### Common Issues

1. **"NAS storage disabled"**
   - Check QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD environment variables
   - Verify SSH access to QNAP
   - Check paramiko installation in requirements.txt

2. **"File upload failed"**
   - Verify /share/Graphics directory exists and is writable
   - Check network connectivity between Railway and QNAP
   - Monitor QNAP storage space

3. **"Database connection failed"**
   - Verify DATABASE_URL is correctly set
   - Check Railway PostgreSQL service status
   - Review database migration logs

### Debug Commands

```bash
# Check NAS connectivity
railway shell
python -c "
from server.src.utils.nas_storage import nas_storage
print('NAS enabled:', nas_storage.enabled)
if nas_storage.enabled:
    print('Testing connection...')
    result = nas_storage.file_exists('test', 'nonexistent.txt')
    print('Connection test result:', result)
"

# Check database connectivity
python -c "
from server.src.database.core import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connected:', result.fetchone())
"
```

## 📞 Support

- Railway Documentation: https://docs.railway.app
- QNAP Support: https://www.qnap.com/en/support
- Project Issues: Create issues in your repository

---

This architecture gives you the benefits of Railway's managed infrastructure while keeping your file storage on your own QNAP NAS hardware, avoiding cloud storage costs and keeping data under your control.
