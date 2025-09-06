# QNAP Container Station Setup Guide

This guide will help you set up your printer-automater application on QNAP Container Station using Docker registry auto-pull (no SSH required).

## Prerequisites

1. **QNAP Container Station installed** and running
2. **GitHub repository** with the application code
3. **GitHub Container Registry access** configured

## Step 1: Prepare QNAP Directories

Create the required directories on your QNAP:

```bash
# SSH into your QNAP (one-time setup only)
mkdir -p /share/printer-automater/{images,uploads,temp,logs}
chmod 755 /share/printer-automater
```

Or create these directories through QNAP File Manager:
- `/share/printer-automater/images`
- `/share/printer-automater/uploads` 
- `/share/printer-automater/temp`
- `/share/printer-automater/logs`

## Step 2: Upload Configuration Files

1. Copy these files to `/share/printer-automater/` on your QNAP:
   - `docker-compose.prod.yml`
   - `.env.prod`

You can use QNAP File Manager or SCP:
```bash
scp docker-compose.prod.yml .env.prod admin@printmadenas.myqnapcloud.com:/share/printer-automater/
```

## Step 3: Container Station Setup

### Method A: Using Container Station UI

1. **Open Container Station** on your QNAP
2. **Go to "Create" → "Create Application"**
3. **Choose "Docker Compose"**
4. **Upload or paste** the content of `docker-compose.prod.yml`
5. **Set environment variables** from `.env.prod`
6. **Click "Create"**

### Method B: Using Container Station Command Line (Advanced)

1. **Open Container Station SSH/Terminal**
2. **Navigate to your project directory:**
   ```bash
   cd /share/printer-automater
   ```
3. **Start the application:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Step 4: Configure Auto-Updates

### Option A: Watchtower (Recommended)

Add this to your docker-compose.prod.yml:

```yaml
services:
  # ... your existing services ...
  
  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_POLL_INTERVAL=300  # Check every 5 minutes
      - WATCHTOWER_CLEANUP=true       # Remove old images
      - WATCHTOWER_INCLUDE_STOPPED=true
    restart: unless-stopped
```

### Option B: Scheduled Updates via QNAP

1. **Go to Control Panel → Task Scheduler**
2. **Create a new task:**
   - **Name:** Update Printer Automater
   - **Schedule:** Daily at 2 AM (or your preference)
   - **Command:**
     ```bash
     cd /share/printer-automater && docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d
     ```

## Step 5: GitHub Container Registry Authentication

If your repository is private, you need to authenticate:

1. **Create a Personal Access Token** on GitHub:
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Create token with `read:packages` permission

2. **Login to registry on QNAP:**
   ```bash
   docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_TOKEN
   ```

## Step 6: Verify Deployment

1. **Check container status:**
   ```bash
   docker ps
   ```

2. **Check logs:**
   ```bash
   docker logs printer-automater-backend-prod
   ```

3. **Test the application:**
   - Visit: `http://printmadenas.myqnapcloud.com:8080/health`
   - Should return server health information

## Deployment Process

### Automatic Deployment
1. **Push code to GitHub main branch**
2. **GitHub Actions builds and pushes image** to registry
3. **Watchtower detects new image** and updates container automatically
4. **Application is updated** with zero downtime

### Manual Deployment
```bash
# SSH into QNAP or use Container Station terminal
cd /share/printer-automater
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring and Maintenance

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs backend

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Update Application
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart with new images
docker-compose -f docker-compose.prod.yml up -d

# Remove old images
docker image prune -f
```

### Backup Database
```bash
# Create backup
docker exec printer-automater-backend-prod-db-1 pg_dump -U printer_automater_user printer_automater_prod > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20241201.sql | docker exec -i printer-automater-backend-prod-db-1 psql -U printer_automater_user printer_automater_prod
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs printer-automater-backend-prod

# Check resource usage
docker stats

# Verify environment variables
docker exec printer-automater-backend-prod env
```

### Database Issues
```bash
# Connect to database
docker exec -it printer-automater-backend-prod-db-1 psql -U printer_automater_user printer_automater_prod

# Check database status
docker exec printer-automater-backend-prod-db-1 pg_isready -U printer_automater_user
```

### Network Issues
```bash
# Check container network
docker network ls
docker network inspect printer-automater_printer-automater-network
```

## Security Notes

1. **Change default passwords** in `.env.prod`
2. **Use strong JWT secrets**
3. **Keep GitHub tokens secure**
4. **Regular security updates** via Watchtower
5. **Monitor logs** for suspicious activity

## Benefits of This Approach

✅ **No SSH required** - eliminates authentication issues  
✅ **Automatic updates** - containers update when you push code  
✅ **Better security** - uses registry authentication  
✅ **Easier rollbacks** - can pin to specific image versions  
✅ **Scalable** - works with multiple environments  
✅ **Standard practice** - follows Docker/Kubernetes patterns