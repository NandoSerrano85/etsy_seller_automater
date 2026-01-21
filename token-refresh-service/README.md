# Token Refresh Service

Automated service for refreshing authentication tokens for integrated platforms (Etsy, Shopify).

## Overview

This service runs continuously in the background and:

- Refreshes Etsy OAuth tokens before they expire
- Validates Shopify access tokens
- Updates tokens in the database automatically
- Runs every 3 minutes by default (configurable)

## Features

### Etsy Token Refresh

- Monitors token expiration times
- Automatically refreshes tokens 10 minutes before expiry
- Updates both access and refresh tokens in database
- Handles refresh failures gracefully

### Shopify Token Validation

- Validates Shopify tokens are still active
- Marks stores as inactive if tokens are invalid
- Shopify tokens don't expire but can be revoked

## Configuration

### Environment Variables

Create a `.env` file with:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Etsy OAuth
ETSY_CLIENT_ID=your_etsy_client_id
ETSY_CLIENT_SECRET=your_etsy_client_secret

# Shopify OAuth
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret

# Service Configuration
REFRESH_INTERVAL_MINUTES=3
LOG_LEVEL=INFO
```

## Running the Service

### Using Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f token-refresh

# Stop the service
docker-compose down
```

### Using Docker

```bash
# Build the image
docker build -t token-refresh-service .

# Run the container
docker run -d \
  --name token-refresh \
  --env-file .env \
  token-refresh-service

# View logs
docker logs -f token-refresh
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
cd src
python main.py
```

## How It Works

1. **Startup**: Service initializes and connects to the database
2. **Initial Refresh**: Runs token refresh immediately on startup
3. **Scheduled Refresh**: Continues running every 3 minutes (configurable)
4. **Etsy Processing**:
   - Queries all Etsy users with tokens expiring within 10 minutes
   - Refreshes each token via Etsy OAuth API
   - Updates database with new tokens and expiration times
5. **Shopify Processing**:
   - Queries all active Shopify stores
   - Validates each token with a simple API call
   - Marks stores as inactive if validation fails
6. **Logging**: Detailed logs of all operations and results

## Monitoring

The service provides comprehensive logging:

- `INFO`: Regular operations and successful refreshes
- `WARNING`: Token validation failures, expiring tokens
- `ERROR`: Refresh failures, API errors, database issues

### Log Output Example

```
🚀 Token Refresh Service starting...
⏱️  Refresh interval: 3 minutes
✅ Etsy refresher initialized
✅ Shopify refresher initialized

================================================================================
🔄 Starting refresh cycle at 2025-10-08T10:00:00
================================================================================

🔵 Processing Etsy tokens...
Found 5 Etsy users with expiring/expired tokens
✅ Refreshed token for Etsy user: 123456789
✅ Refreshed token for Etsy user: 987654321

🟢 Processing Shopify tokens...
Found 3 active Shopify stores to validate
✅ Token valid for store: my-shop.myshopify.com

================================================================================
📊 REFRESH CYCLE SUMMARY
================================================================================
Etsy:    2/2 refreshed, 0 failed
Shopify: 3/3 validated, 0 failed
================================================================================
✅ Refresh cycle completed at 2025-10-08T10:00:15
================================================================================
```

## Database Schema

The service interacts with these tables:

### etsy_users

- `user_id`: User UUID (primary key)
- `access_token`: Current OAuth access token
- `refresh_token`: OAuth refresh token
- `token_expires_at`: Token expiration timestamp
- `updated_at`: Last update timestamp

### shopify_stores

- `id`: Store UUID (primary key)
- `shop_domain`: Shopify shop domain
- `access_token`: Shopify access token
- `is_active`: Whether the store is active
- `updated_at`: Last update timestamp

## Error Handling

- **Network Errors**: Retries on next cycle, doesn't mark tokens as invalid
- **Token Refresh Failures**: Logged as errors, token remains unchanged
- **Database Errors**: Rolled back, logged, service continues
- **Unexpected Errors**: Logged with stack trace, service waits 60s before retrying

## Deployment

### Production Deployment

1. Set environment variables in your hosting platform
2. Build and deploy the Docker container
3. Ensure database connectivity
4. Monitor logs for successful operation

### Railway Deployment

```bash
# Install Railway CLI
npm install -g railway

# Login and link project
railway login
railway link

# Deploy
railway up
```

## Maintenance

- **Logs**: Check logs regularly for failures
- **Database**: Ensure database connection is stable
- **Tokens**: Monitor token refresh success rates
- **Updates**: Pull latest code and rebuild container

## Troubleshooting

### Service won't start

- Check DATABASE_URL is correct
- Verify OAuth credentials are set
- Check database is accessible

### Tokens not refreshing

- Check token expiration times in database
- Verify OAuth credentials are valid
- Check API rate limits

### High failure rate

- Check network connectivity
- Verify OAuth app permissions
- Check database write permissions

## License

MIT
