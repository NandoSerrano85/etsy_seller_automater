# CraftFlow Multi-Tenant Reverse Proxy Configuration

This directory contains reverse proxy configurations for the CraftFlow multi-tenant storefront system.

## Overview

The proxy handles:

- Wildcard subdomains: `*.craftflow.store` -> Storefront
- Admin panel: `admin.craftflow.store` -> Admin Frontend
- API: `api.craftflow.store` -> Backend
- Custom domains: Any verified domain -> Storefront

## Options

### Option 1: Caddy (Recommended)

Caddy provides automatic HTTPS with Let's Encrypt and simpler configuration.

```bash
# Start with Caddy profile
docker-compose --profile caddy up -d
```

**Features:**

- Automatic HTTPS via Let's Encrypt
- Automatic certificate renewal
- Simple Caddyfile configuration
- On-demand TLS for custom domains
- HTTP/2 by default

### Option 2: Nginx + Certbot

Nginx provides more control but requires manual certificate management.

```bash
# Initialize certificates first
./init-letsencrypt.sh

# Start with Nginx profile
docker-compose --profile nginx up -d
```

**Features:**

- Fine-grained control
- Battle-tested configuration
- Separate cert management via Certbot
- More complex setup

## Configuration

### Environment Variables

Set these in your `.env` file:

```env
# Domain configuration
DOMAIN=craftflow.store
ADMIN_SUBDOMAIN=admin
API_SUBDOMAIN=api

# Let's Encrypt
LETSENCRYPT_EMAIL=admin@craftflow.store
LETSENCRYPT_STAGING=false  # Set to true for testing

# Service hosts (if not using Docker network)
STOREFRONT_HOST=storefront:3001
BACKEND_HOST=backend:3003
ADMIN_HOST=admin-frontend:3000
```

### Custom Domains

For custom domains to work, you need:

1. **DNS Configuration**: Customer adds CNAME pointing to `stores.craftflow.store`
2. **Domain Verification**: Customer adds TXT record for verification
3. **SSL Certificate**: Automatically provisioned after verification

#### Caddy On-Demand TLS

Caddy can automatically provision SSL for verified custom domains:

```caddyfile
{
    on_demand_tls {
        ask http://backend:3003/api/internal/verify-domain
        interval 2m
        burst 5
    }
}
```

#### Nginx Custom Domains

For Nginx, you need to:

1. Run certbot for each new custom domain
2. Update Nginx config to include the new domain
3. Reload Nginx

## Production Deployment

### Prerequisites

1. DNS configured:
   - `*.craftflow.store` -> Your server IP
   - `admin.craftflow.store` -> Your server IP
   - `api.craftflow.store` -> Your server IP

2. Ports 80 and 443 open

3. Docker network created:
   ```bash
   docker network create craftflow-network
   ```

### Deploy Steps

1. Clone the repository and navigate to proxy directory:

   ```bash
   cd deployment/proxy
   ```

2. Configure environment variables:

   ```bash
   cp .env.example .env
   vim .env
   ```

3. Start the proxy:

   ```bash
   # Using Caddy (recommended)
   docker-compose --profile caddy up -d

   # Or using Nginx
   ./init-letsencrypt.sh
   docker-compose --profile nginx up -d
   ```

4. Verify the setup:
   ```bash
   curl -I https://admin.craftflow.store
   curl -I https://api.craftflow.store/health
   curl -I https://demo.craftflow.store
   ```

## Troubleshooting

### Certificate Issues

**Caddy:**

```bash
# Check Caddy logs
docker logs craftflow-proxy

# Force certificate renewal
docker exec craftflow-proxy caddy reload
```

**Nginx/Certbot:**

```bash
# Check certificate status
docker exec craftflow-certbot certbot certificates

# Force renewal
docker exec craftflow-certbot certbot renew --force-renewal
```

### Connectivity Issues

```bash
# Test upstream connectivity
docker exec craftflow-proxy curl -I http://storefront:3001
docker exec craftflow-proxy curl -I http://backend:3003
docker exec craftflow-proxy curl -I http://admin-frontend:3000
```

### DNS Propagation

```bash
# Check DNS propagation
dig +short mystore.craftflow.store
nslookup mystore.craftflow.store

# Check from multiple DNS servers
dig @8.8.8.8 mystore.craftflow.store
dig @1.1.1.1 mystore.craftflow.store
```

## Security Notes

1. **Rate Limiting**: Consider adding rate limiting for API endpoints
2. **WAF**: Consider adding a Web Application Firewall
3. **DDoS Protection**: Use Cloudflare or similar service for production
4. **Headers**: Security headers are included in both configurations

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Internet / CDN                 │
                    └───────────────────┬─────────────────────┘
                                        │
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │         Reverse Proxy (Caddy/Nginx)      │
                    │         - SSL Termination                │
                    │         - Domain Routing                 │
                    │         - Load Balancing                 │
                    └───────────────────┬─────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
            ▼                           ▼                           ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │   Storefront   │          │    Backend     │          │ Admin Frontend │
    │   (Next.js)    │          │   (FastAPI)    │          │    (React)     │
    │   Port 3001    │          │   Port 3003    │          │   Port 3000    │
    └───────────────┘          └───────────────┘          └───────────────┘
            │                           │
            │                           │
            ▼                           ▼
    ┌───────────────┐          ┌───────────────┐
    │   Public API   │          │   Database     │
    │  /api/store/*  │          │  (PostgreSQL)  │
    └───────────────┘          └───────────────┘
```
