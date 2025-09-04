# Deployment Setup Guide

## Overview
This project uses a dual deployment strategy:
- **Frontend**: Deployed to Netlify automatically on push to main branch
- **Backend**: Deployed to QNAP NAS via Docker using GitHub Actions

## 1. Frontend Deployment (Netlify)

### Setup Steps:
1. **Connect Repository to Netlify**:
   - Go to https://app.netlify.com/
   - Click "Add new site" → "Import an existing project"
   - Connect your GitHub repository

2. **Configure Build Settings**:
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/build`
   - These are already configured in `netlify.toml`

3. **Environment Variables**:
   Set the following in Netlify Dashboard → Site Settings → Environment Variables:
   ```
   REACT_APP_API_BASE_URL=https://your-qnap-domain.com:8080
   ```

### Features Included:
- Automatic deploys on push to main branch
- React Router support with redirects
- Security headers (CSP, XSS protection, etc.)
- Static asset caching (1 year for /static/*, 5 minutes for index.html)

## 2. Backend Deployment (QNAP via Docker)

### Prerequisites:
1. **QNAP NAS Setup**:
   - SSH access enabled
   - Docker installed via Container Station
   - Ports configured (default: 8080 for backend)

2. **Docker Hub Account**:
   - Create account at https://hub.docker.com/
   - Create repository (e.g., `yourusername/printer-automater`)

### GitHub Secrets Configuration

Add these secrets in GitHub → Repository → Settings → Secrets and Variables → Actions:

#### Docker Configuration:
```
DOCKER_USERNAME=your_docker_hub_username
DOCKER_PASSWORD=your_docker_hub_password
```

#### QNAP Connection:
```
QNAP_HOST=your-nas.myqnapcloud.com
QNAP_USERNAME=your_ssh_username
QNAP_PASSWORD=your_ssh_password
QNAP_SSH_PORT=22
BACKEND_PORT=8080
```

#### Application Environment Variables:
```
CLIENT_ID=your_etsy_client_id
CLIENT_SECRET=your_etsy_client_secret
SHOP_ID=your_etsy_shop_id
CLIENT_VERIFIER=your_client_verifier
CODE_CHALLENGE=your_code_challenge
STATE_ID=your_state_id
ETSY_OAUTH_TOKEN=your_etsy_oauth_token
ETSY_OAUTH_TOKEN_EXPIRY=token_expiry_timestamp
ETSY_REFRESH_TOKEN=your_etsy_refresh_token
SHOP_NAME=your_shop_name
SHOP_URL=https://www.etsy.com/shop/your_shop_name
DATABASE_URL=postgresql://username:password@host:5432/database_name
JWT_SECRET_KEY=your_super_secret_jwt_key
JWT_ALGORITHM=HS256
USER_LOGIN_ACCESS_TOKEN_EXPIRE_MINUTES=300
DISABLE_REGISTRATION=true
REMOTE_ROOT_PATH=/share/Graphics/YourTransfers
REMOTE_ROOT_HOST=YourNAS.myqnapcloud.com
REMOTE_HOST_USERNAME=your_nas_username
REMOTE_HOST_PASSWORD=your_nas_password
LOCAL_ROOT_PATH=/app/temp/
```

### QNAP Preparation:

1. **Create Volume Directories**:
   ```bash
   sudo mkdir -p /share/CACHEDEV1_DATA/Container/printer-automater-uploads
   sudo mkdir -p /share/CACHEDEV1_DATA/Container/printer-automater-temp
   sudo chmod 755 /share/CACHEDEV1_DATA/Container/printer-automater-*
   ```

2. **Enable Docker and SSH**:
   - Install Container Station from QNAP App Center
   - Enable SSH: Control Panel → Network & File Services → SSH → Enable SSH service

3. **Configure Firewall** (if enabled):
   - Allow port for backend (default: 8080)
   - Allow SSH port (default: 22)

## 3. Deployment Process

### Automatic Deployment:
The deployment triggers automatically when you push changes to the main branch that affect:
- `server/**` (backend changes)
- `frontend/**` (frontend changes via Netlify)
- `requirements.txt`
- `Dockerfile`
- GitHub workflow files

### Manual Deployment:
- **Frontend**: Push to main branch or trigger manual deploy in Netlify dashboard
- **Backend**: Use GitHub Actions tab → "Deploy Backend to QNAP" → "Run workflow"

### Deployment Flow:
1. **Build Phase**:
   - Creates multi-architecture Docker image (amd64/arm64)
   - Pushes to Docker Hub with latest and commit SHA tags
   - Uses build cache for faster subsequent builds

2. **Deploy Phase**:
   - SSH into QNAP NAS
   - Stops existing container gracefully
   - Pulls latest Docker image
   - Starts new container with all environment variables
   - Mounts persistent volumes for uploads and temp files

3. **Health Check**:
   - Waits for container to start (10 seconds)
   - Verifies container is running
   - Tests health endpoint
   - Reports deployment status

4. **Cleanup**:
   - Removes old Docker images (keeps latest 3)
   - Cleans up dangling images

## 4. Monitoring and Troubleshooting

### Health Check Endpoints:
- **Frontend**: https://your-netlify-domain.netlify.app/
- **Backend**: https://your-qnap-domain.com:8080/health

### Logs:
- **Netlify**: Site Dashboard → Functions → View logs
- **QNAP Docker**: 
  ```bash
  sudo docker logs printer-automater-backend
  sudo docker logs -f printer-automater-backend  # Follow logs
  ```

### Common Issues:

1. **Build Failures**:
   - Check GitHub Actions tab for detailed error logs
   - Verify all secrets are properly set
   - Ensure Docker Hub credentials are correct

2. **QNAP Connection Issues**:
   - Verify SSH access works manually
   - Check QNAP firewall settings
   - Confirm SSH port and credentials

3. **Container Issues**:
   - Check container logs: `sudo docker logs printer-automater-backend`
   - Verify environment variables are set correctly
   - Ensure required volumes exist and have proper permissions

4. **Database Connection**:
   - Verify DATABASE_URL is accessible from QNAP
   - Check PostgreSQL is running and accepting connections
   - Confirm database exists and user has proper permissions

## 5. Rollback Procedure

### Frontend (Netlify):
1. Go to Site Dashboard → Deploys
2. Find previous successful deploy
3. Click "..." → "Publish deploy"

### Backend (QNAP):
1. SSH into QNAP
2. Stop current container:
   ```bash
   sudo docker stop printer-automater-backend
   sudo docker rm printer-automater-backend
   ```
3. Run previous image version:
   ```bash
   sudo docker run -d --name printer-automater-backend [previous-image-tag] [same-environment-variables]
   ```

## 6. Scaling and Optimization

### Performance Considerations:
- Docker images use multi-stage builds and layer caching
- Static assets cached appropriately
- Health checks ensure container stability
- Automatic cleanup prevents disk space issues

### Future Enhancements:
- Consider using docker-compose for easier management
- Implement backup strategy for uploads/data
- Add monitoring and alerting
- Consider load balancing for high availability

## 7. Security Notes

- All sensitive data stored as GitHub Secrets
- Container runs as non-root user
- Security headers implemented in Netlify
- HTTPS enforced for all communications
- Database connections should use SSL
- **User registration disabled in production** (`DISABLE_REGISTRATION=true`)
- Registration endpoint returns HTTP 403 when disabled
- For development, set `DISABLE_REGISTRATION=false` in local `.env`
- Regular updates of base Docker images recommended

### Production Security Features:
- Registration blocked at API level (returns 403 Forbidden)
- Existing users can still login normally
- Rate limiting still applies to all auth endpoints
- Environment-based configuration allows dev/prod differences