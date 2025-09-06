# 🚀 Production Deployment Guide for QNAP NAS

This guide will help you deploy the Printer Automater backend to your QNAP NAS at `printmadenas.myqnapcloud.com`.

## 📋 Prerequisites

### Local Machine Requirements
- Docker installed and running
- SSH client
- rsync (optional, for faster file transfers)

### QNAP NAS Requirements
- Container Station installed and enabled
- SSH access enabled
- Docker and Docker Compose available
- Sufficient storage space (recommended: 20GB+)

## 🔧 Initial QNAP Setup

### 1. Enable SSH on QNAP
1. Log into QTS web interface
2. Go to **Control Panel** → **Telnet / SSH**
3. Enable **Allow SSH connection**
4. Set SSH port (default: 22)
5. Apply settings

### 2. Set up SSH Key Authentication (Recommended)
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to QNAP
ssh-copy-id -p 22 admin@printmadenas.myqnapcloud.com
```

### 3. Run Initial QNAP Setup
Copy the setup script to your QNAP and run it:
```bash
# Copy setup script to QNAP
scp qnap-setup.sh admin@printmadenas.myqnapcloud.com:/share/

# SSH into QNAP and run setup
ssh admin@printmadenas.myqnapcloud.com
cd /share
chmod +x qnap-setup.sh
./qnap-setup.sh
```

## 🛠️ Configuration

### 1. Create Production Environment File
```bash
# Copy the template
cp .env.prod.template .env.prod

# Edit with your production values
nano .env.prod
```

**Important Settings to Configure:**
```env
# Database - Use strong passwords!
DB_USER=printer_automater_user
DB_PASSWORD=your_very_secure_password_here
DB_NAME=printer_automater_prod

# Backend
BACKEND_PORT=8080
FRONTEND_URL=https://printer-automater.netlify.app

# Etsy API (Get from https://www.etsy.com/developers/)
ETSY_CLIENT_ID=your_etsy_client_id
ETSY_CLIENT_SECRET=your_etsy_client_secret
ETSY_REDIRECT_URI=http://printmadenas.myqnapcloud.com:8080/auth/etsy/callback

# JWT - Generate a secure secret (64+ characters)
JWT_SECRET=your_very_long_secure_jwt_secret_min_64_chars_recommended

# Security
DISABLE_REGISTRATION=true
```

### 2. Configure Environment Variables (Optional)
```bash
# Set deployment-specific environment variables
export QNAP_USER=admin
export QNAP_SSH_PORT=22
export DOCKER_REGISTRY=localhost:5000
```

## 🚀 Deployment Options

### Option 1: Full Deployment (Recommended)
```bash
# Deploy with backup
./deploy-production.sh --backup

# Or simple deployment
./deploy-production.sh
```

### Option 2: Build and Deploy Separately
```bash
# Build images locally
./deploy-production.sh --build-only

# Deploy to QNAP (uses pre-built images)
./deploy-production.sh --deploy-only
```

### Option 3: Manual Deployment Steps

#### Step 1: Build Docker Images
```bash
docker build -f Dockerfile.backend -t printer-automater-backend:latest .
```

#### Step 2: Copy Files to QNAP
```bash
# Copy docker-compose file
scp docker-compose.prod.yml admin@printmadenas.myqnapcloud.com:/share/printer-automater/

# Copy environment file
scp .env.prod admin@printmadenas.myqnapcloud.com:/share/printer-automater/
```

#### Step 3: Deploy on QNAP
```bash
# SSH into QNAP
ssh admin@printmadenas.myqnapcloud.com

# Navigate to project directory
cd /share/printer-automater

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## 🔍 Monitoring and Management

### Check Service Status
```bash
ssh admin@printmadenas.myqnapcloud.com
cd /share/printer-automater
./printer-automater-service.sh status
```

### View Logs
```bash
# Real-time logs
./printer-automater-service.sh logs

# Or specific service logs
docker-compose -f docker-compose.prod.yml logs backend -f
```

### Service Management
```bash
# Start services
./printer-automater-service.sh start

# Stop services
./printer-automater-service.sh stop

# Restart services
./printer-automater-service.sh restart
```

## 🔒 Security Considerations

### 1. Firewall Configuration
- Open port 8080 for the backend API
- Consider using a reverse proxy (nginx) for SSL termination
- Restrict access to database port 5432

### 2. SSL/HTTPS Setup (Optional)
```bash
# Generate SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /share/printer-automater/ssl/server.key \
  -out /share/printer-automater/ssl/server.crt

# Update environment variables
USE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/server.crt
SSL_KEY_PATH=/etc/ssl/private/server.key
```

### 3. Database Security
- Use strong passwords
- Regularly backup database
- Consider encrypting backups

## 💾 Backup and Recovery

### Automatic Backups
```bash
# Add to crontab for daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * /share/printer-automater/backup.sh
```

### Manual Backup
```bash
ssh admin@printmadenas.myqnapcloud.com
/share/printer-automater/backup.sh
```

### Restore from Backup
```bash
# List available backups
ls /share/printer-automater/backups/

# Restore database
docker exec -i printer-automater-backend-prod psql -U postgres printer_automater_db < backup_20241205_020000/database.sql

# Restore files
cd /share/printer-automater
tar -xzf backups/backup_20241205_020000/uploads.tar.gz
tar -xzf backups/backup_20241205_020000/images.tar.gz
```

## 🌐 Access Your Application

After successful deployment, your application will be available at:
- **Backend API**: http://printmadenas.myqnapcloud.com:8080
- **Frontend**: https://printer-automater.netlify.app (connects to your backend)

### Health Check
```bash
curl http://printmadenas.myqnapcloud.com:8080/health
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Compose Not Found
```bash
# Install docker-compose on QNAP
# Through Container Station UI or manually
```

#### 2. Permission Denied Errors
```bash
# Fix permissions
chmod 777 /share/printer-automater/{uploads,temp,images}
```

#### 3. Database Connection Issues
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Check database connection
docker exec -it printer-automater-backend-prod psql -U postgres -h db
```

#### 4. Port Already in Use
```bash
# Check what's using the port
netstat -tlnp | grep 8080

# Change BACKEND_PORT in .env.prod if needed
```

#### 5. Memory Issues
```bash
# Check memory usage
free -h

# Check docker stats
docker stats

# Reduce worker processes if needed
WORKER_PROCESSES=1
```

### Log Locations
- **Application logs**: `/share/printer-automater/logs/`
- **Docker logs**: `docker-compose logs`
- **System logs**: `/var/log/`

## 📞 Support

If you encounter issues:
1. Check the logs: `./printer-automater-service.sh logs`
2. Verify configuration: Review `.env.prod` settings
3. Check system resources: Memory, disk space, CPU
4. Review firewall settings
5. Consult QNAP documentation for Container Station

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Redeploy
./deploy-production.sh --backup
```

### Regular Maintenance
- Monitor disk space usage
- Review and rotate logs
- Update Docker images periodically
- Test backups regularly
- Monitor SSL certificate expiration (if using HTTPS)

---

**🎉 Congratulations!** Your Printer Automater backend should now be running on your QNAP NAS!