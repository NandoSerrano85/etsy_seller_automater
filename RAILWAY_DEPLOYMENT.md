# Railway Production Deployment - QNAP NAS Integration

## Overview

This configuration enables Railway production deployment to access QNAP NAS files via HTTP/HTTPS for mockup generation, since Railway doesn't support SMB/CIFS mounting.

## Required Railway Environment Variables

Set these in your Railway backend service:

### QNAP NAS Configuration

```bash
QNAP_HOST=your-qnap-external-ip-or-domain.com
QNAP_USERNAME=your-qnap-username
QNAP_PASSWORD=your-qnap-password
QNAP_PORT=443                    # HTTPS port (or 80 for HTTP)
QNAP_USE_HTTPS=true             # Use HTTPS (recommended)
```

### Shopify Configuration

```bash
SHOPIFY_API_KEY=your_shopify_app_key
SHOPIFY_API_SECRET=your_shopify_app_secret
SHOPIFY_REDIRECT_URI=https://your-backend.railway.app/api/shopify/callback
SHOPIFY_SCOPES=read_products,write_products,read_orders
FRONTEND_URL=https://your-frontend.railway.app
```

### Database & Application

```bash
DATABASE_URL=your_railway_postgres_url
DOCKER_ENV=true                 # Enables Railway production mode
```

## QNAP NAS Setup

### 1. Enable Web File Manager

- Log into QNAP admin panel
- Go to Control Panel > Network Services > Web Server
- Enable Web Server with HTTPS
- Note the port (usually 443 for HTTPS)

### 2. Configure External Access

- Set up port forwarding on your router: External Port → QNAP IP:443
- Or use QNAP's myQNAPcloud service for external access
- Ensure the QNAP is accessible from Railway's IP range

### 3. File Permissions

- Ensure your QNAP user has read access to /Graphics/NookTransfers/Mockups/BaseMockups/
- Test access via web browser: https://your-qnap-host/

## How It Works

### Local Development

- Uses direct file system access (cv2.imread on /share/Graphics/...)
- Works with your local QNAP mount

### Railway Production

- Detects DOCKER_ENV or RAILWAY_ENVIRONMENT_NAME
- Uses HTTP client to download files from QNAP NAS
- Loads images into memory for mockup processing
- Authenticates with QNAP web interface

## Testing Deployment

1. Deploy to Railway with environment variables set
2. Check logs for QNAP authentication success:
   ```
   INFO: QNAP client initialized for host: your-qnap-host
   INFO: QNAP authentication successful
   ```
3. Test mockup generation - should see:
   ```
   INFO: Railway production: Loading via QNAP HTTP client: /share/Graphics/...
   INFO: Successfully loaded via QNAP HTTP client: /share/Graphics/...
   ```

## Security Notes

- Use HTTPS (QNAP_USE_HTTPS=true) for secure transmission
- Store QNAP credentials as Railway environment secrets
- Consider IP whitelisting on QNAP if possible
