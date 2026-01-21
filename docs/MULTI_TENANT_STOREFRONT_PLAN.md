# Multi-Tenant Storefront Implementation Plan

## Overview

Enable each "Full" subscription user to have their own storefront instance with the ability to use a custom domain (BYOD - Bring Your Own Domain).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Request Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Customer visits: shop.example.com                               │
│         ↓                                                        │
│  [Reverse Proxy] → Lookup domain → Route to storefront app       │
│         ↓                                                        │
│  [Storefront App] → Load user's products, theme, branding        │
│         ↓                                                        │
│  [Serve from] /uploads/product_mockups/{user_id}/                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Domain Options

1. **Subdomain** (default): `{store-name}.craftflow.com`
2. **Custom Domain** (optional): `shop.example.com` or `example.com`

---

## Phase 1: Database Schema

### 1.1 Storefronts Table

```sql
CREATE TABLE storefronts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Domain configuration
    subdomain VARCHAR(63) UNIQUE NOT NULL,        -- "myshop" → myshop.craftflow.com
    custom_domain VARCHAR(255) UNIQUE,            -- "shop.example.com"
    domain_verified BOOLEAN DEFAULT FALSE,
    domain_verification_token VARCHAR(64),
    domain_verification_method VARCHAR(20),       -- "dns_txt" or "dns_cname"

    -- SSL configuration
    ssl_status VARCHAR(20) DEFAULT 'none',        -- none, pending, active, failed, expired
    ssl_certificate_path VARCHAR(500),
    ssl_private_key_path VARCHAR(500),
    ssl_expires_at TIMESTAMP WITH TIME ZONE,
    ssl_auto_renew BOOLEAN DEFAULT TRUE,

    -- Store branding
    store_name VARCHAR(255) NOT NULL,
    store_description TEXT,
    logo_url VARCHAR(500),
    favicon_url VARCHAR(500),

    -- Theme settings
    primary_color VARCHAR(7) DEFAULT '#6B7280',   -- Hex color
    secondary_color VARCHAR(7) DEFAULT '#F3F4F6',
    accent_color VARCHAR(7) DEFAULT '#10B981',
    font_family VARCHAR(100) DEFAULT 'Inter',

    -- Store settings
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    contact_email VARCHAR(255),
    support_phone VARCHAR(20),

    -- Social links
    social_links JSONB DEFAULT '{}',              -- {"instagram": "...", "facebook": "..."}

    -- SEO
    meta_title VARCHAR(70),
    meta_description VARCHAR(160),
    google_analytics_id VARCHAR(20),
    facebook_pixel_id VARCHAR(20),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_published BOOLEAN DEFAULT FALSE,           -- Public visibility
    maintenance_mode BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT unique_user_storefront UNIQUE (user_id)
);

-- Indexes
CREATE INDEX idx_storefronts_subdomain ON storefronts(subdomain);
CREATE INDEX idx_storefronts_custom_domain ON storefronts(custom_domain) WHERE custom_domain IS NOT NULL;
CREATE INDEX idx_storefronts_user_id ON storefronts(user_id);
CREATE INDEX idx_storefronts_is_active ON storefronts(is_active) WHERE is_active = TRUE;
```

### 1.2 Domain Verification Log Table

```sql
CREATE TABLE domain_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    storefront_id UUID NOT NULL REFERENCES storefronts(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    verification_token VARCHAR(64) NOT NULL,
    verification_method VARCHAR(20) NOT NULL,     -- "dns_txt" or "dns_cname"
    status VARCHAR(20) DEFAULT 'pending',         -- pending, verified, failed, expired
    attempts INTEGER DEFAULT 0,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 1.3 SQLAlchemy Entity

```python
# server/src/entities/storefront.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.src.database.core import Base
import uuid

class Storefront(Base):
    __tablename__ = 'storefronts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Domain
    subdomain = Column(String(63), unique=True, nullable=False)
    custom_domain = Column(String(255), unique=True, nullable=True)
    domain_verified = Column(Boolean, default=False)
    domain_verification_token = Column(String(64))
    domain_verification_method = Column(String(20))

    # SSL
    ssl_status = Column(String(20), default='none')
    ssl_certificate_path = Column(String(500))
    ssl_private_key_path = Column(String(500))
    ssl_expires_at = Column(DateTime(timezone=True))
    ssl_auto_renew = Column(Boolean, default=True)

    # Branding
    store_name = Column(String(255), nullable=False)
    store_description = Column(Text)
    logo_url = Column(String(500))
    favicon_url = Column(String(500))

    # Theme
    primary_color = Column(String(7), default='#6B7280')
    secondary_color = Column(String(7), default='#F3F4F6')
    accent_color = Column(String(7), default='#10B981')
    font_family = Column(String(100), default='Inter')

    # Settings
    currency = Column(String(3), default='USD')
    timezone = Column(String(50), default='America/New_York')
    contact_email = Column(String(255))
    support_phone = Column(String(20))

    # Social & SEO
    social_links = Column(JSON, default={})
    meta_title = Column(String(70))
    meta_description = Column(String(160))
    google_analytics_id = Column(String(20))
    facebook_pixel_id = Column(String(20))

    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship('User', back_populates='storefront')
```

---

## Phase 2: Backend API

### 2.1 API Endpoints

| Method   | Endpoint                              | Description                              | Auth      |
| -------- | ------------------------------------- | ---------------------------------------- | --------- |
| `POST`   | `/api/storefront`                     | Create storefront (auto on Full upgrade) | Full plan |
| `GET`    | `/api/storefront`                     | Get current user's storefront            | Full plan |
| `PUT`    | `/api/storefront`                     | Update storefront settings               | Full plan |
| `DELETE` | `/api/storefront`                     | Delete storefront                        | Full plan |
| `POST`   | `/api/storefront/domain`              | Set custom domain                        | Full plan |
| `DELETE` | `/api/storefront/domain`              | Remove custom domain                     | Full plan |
| `GET`    | `/api/storefront/domain/instructions` | Get DNS setup instructions               | Full plan |
| `POST`   | `/api/storefront/domain/verify`       | Trigger domain verification              | Full plan |
| `GET`    | `/api/storefront/domain/status`       | Check verification status                | Full plan |
| `POST`   | `/api/storefront/ssl/provision`       | Provision SSL certificate                | Full plan |
| `POST`   | `/api/storefront/publish`             | Publish storefront                       | Full plan |
| `POST`   | `/api/storefront/unpublish`           | Unpublish storefront                     | Full plan |
| `GET`    | `/api/storefront/preview`             | Get preview URL                          | Full plan |

### 2.2 Public Storefront API (for storefront-frontend)

| Method | Endpoint                              | Description                | Auth   |
| ------ | ------------------------------------- | -------------------------- | ------ |
| `GET`  | `/api/store/{domain}/config`          | Get store config by domain | Public |
| `GET`  | `/api/store/{domain}/products`        | Get store products         | Public |
| `GET`  | `/api/store/{domain}/products/{slug}` | Get single product         | Public |
| `GET`  | `/api/store/{domain}/categories`      | Get store categories       | Public |

### 2.3 Storefront Service

```python
# server/src/routes/storefront/service.py

class StorefrontService:

    @staticmethod
    def create_storefront(db: Session, user_id: UUID, store_name: str) -> Storefront:
        """Create a new storefront for a Full plan user."""
        # Generate unique subdomain from store name
        subdomain = StorefrontService._generate_subdomain(db, store_name)

        storefront = Storefront(
            user_id=user_id,
            store_name=store_name,
            subdomain=subdomain,
            domain_verification_token=secrets.token_urlsafe(32)
        )
        db.add(storefront)
        db.commit()
        return storefront

    @staticmethod
    def set_custom_domain(db: Session, storefront_id: UUID, domain: str) -> dict:
        """Set a custom domain and return verification instructions."""
        # Validate domain format
        # Check domain not already in use
        # Generate verification token
        # Return DNS instructions
        pass

    @staticmethod
    def verify_domain(db: Session, storefront_id: UUID) -> bool:
        """Verify domain ownership via DNS TXT record."""
        # Query DNS for TXT record
        # Check if token matches
        # Update verification status
        pass

    @staticmethod
    def provision_ssl(storefront_id: UUID) -> bool:
        """Provision SSL certificate via Let's Encrypt."""
        # Use certbot or acme.sh
        # Store certificate paths
        # Update nginx/caddy config
        pass

    @staticmethod
    def get_storefront_by_domain(db: Session, domain: str) -> Optional[Storefront]:
        """Lookup storefront by custom domain or subdomain."""
        # Check custom_domain first
        # Then check subdomain
        pass
```

### 2.4 Domain Verification Logic

```python
# DNS TXT Record Verification

import dns.resolver

def verify_domain_txt(domain: str, expected_token: str) -> bool:
    """
    User adds TXT record: _craftflow-verify.example.com -> {token}
    """
    try:
        txt_records = dns.resolver.resolve(f'_craftflow-verify.{domain}', 'TXT')
        for record in txt_records:
            if expected_token in str(record):
                return True
        return False
    except Exception:
        return False

# Alternative: CNAME Verification
def verify_domain_cname(domain: str, expected_target: str) -> bool:
    """
    User adds CNAME: {token}.example.com -> verify.craftflow.com
    """
    try:
        cname_records = dns.resolver.resolve(f'{expected_target}.{domain}', 'CNAME')
        for record in cname_records:
            if 'verify.craftflow.com' in str(record):
                return True
        return False
    except Exception:
        return False
```

---

## Phase 3: Admin Frontend

### 3.1 New Pages/Components

```
admin-frontend/src/
├── pages/
│   └── CraftFlow/
│       └── StorefrontSettings/
│           ├── index.js              # Main settings page
│           ├── GeneralSettings.js    # Name, description, branding
│           ├── DomainSettings.js     # Domain configuration
│           ├── ThemeSettings.js      # Colors, fonts
│           ├── SEOSettings.js        # Meta tags, analytics
│           └── PublishSettings.js    # Publish/unpublish controls
```

### 3.2 Domain Setup Wizard UI Flow

```
Step 1: Enter Custom Domain
┌─────────────────────────────────────────────────────┐
│  Enter your custom domain                           │
│  ┌───────────────────────────────────────────────┐  │
│  │ shop.example.com                              │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [Continue]                                         │
└─────────────────────────────────────────────────────┘

Step 2: DNS Configuration Instructions
┌─────────────────────────────────────────────────────┐
│  Configure your DNS                                 │
│                                                     │
│  Add these DNS records at your domain registrar:   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Type: CNAME                                  │   │
│  │ Name: shop (or @ for root)                   │   │
│  │ Value: stores.craftflow.com                  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Type: TXT                                    │   │
│  │ Name: _craftflow-verify                      │   │
│  │ Value: cf_verify_abc123xyz789...             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  DNS changes can take up to 48 hours to propagate. │
│                                                     │
│  [Verify Domain]                                    │
└─────────────────────────────────────────────────────┘

Step 3: Verification Status
┌─────────────────────────────────────────────────────┐
│  Domain Verification                                │
│                                                     │
│  ✓ CNAME record found                              │
│  ✓ TXT verification record found                   │
│  ⏳ Provisioning SSL certificate...                │
│                                                     │
│  Your domain will be ready in a few minutes.       │
└─────────────────────────────────────────────────────┘
```

### 3.3 Storefront Settings Page Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│  Storefront Settings                           [Preview] [Save] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌─────────────────────────────────────────┐  │
│  │ General      │  │                                         │  │
│  │ Domain    ←  │  │  Custom Domain                          │  │
│  │ Theme        │  │                                         │  │
│  │ SEO          │  │  Current: myshop.craftflow.com          │  │
│  │ Publish      │  │                                         │  │
│  └──────────────┘  │  ┌─────────────────────────────────────┐│  │
│                     │  │ shop.example.com                    ││  │
│                     │  └─────────────────────────────────────┘│  │
│                     │  [Set Custom Domain]                    │  │
│                     │                                         │  │
│                     │  Status: ✓ Verified, SSL Active        │  │
│                     │                                         │  │
│                     └─────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 4: Storefront Frontend (Multi-Tenant)

### 4.1 Request Flow

```javascript
// middleware/tenant.js (Next.js example)

export async function middleware(request) {
  const hostname = request.headers.get("host");

  // Skip for main app domains
  if (hostname === "craftflow.com" || hostname === "admin.craftflow.com") {
    return NextResponse.next();
  }

  // Lookup storefront by domain
  const storefront = await fetch(`${API_URL}/api/store/${hostname}/config`);

  if (!storefront.ok) {
    return NextResponse.redirect("/404");
  }

  // Inject storefront config into request
  const response = NextResponse.next();
  response.headers.set("x-storefront-id", storefront.id);
  response.headers.set("x-storefront-user-id", storefront.user_id);

  return response;
}
```

### 4.2 Dynamic Theming

```javascript
// Load theme from storefront config
const StoreThemeProvider = ({ children, storefront }) => {
  const theme = {
    colors: {
      primary: storefront.primary_color,
      secondary: storefront.secondary_color,
      accent: storefront.accent_color,
    },
    fonts: {
      body: storefront.font_family,
    },
  };

  return (
    <ThemeProvider theme={theme}>
      <Head>
        <title>{storefront.meta_title || storefront.store_name}</title>
        <meta name="description" content={storefront.meta_description} />
        <link rel="icon" href={storefront.favicon_url} />
      </Head>
      {children}
    </ThemeProvider>
  );
};
```

### 4.3 Product Image URLs

```javascript
// Products reference user-specific mockup folder
const productImageUrl = `/uploads/product_mockups/${storefront.user_id}/${image.filename}`;

// Or via API proxy
const productImageUrl = `/api/store/${storefront.subdomain}/images/${image.filename}`;
```

---

## Phase 5: Infrastructure

### 5.1 Reverse Proxy Configuration (Caddy - Recommended)

```caddyfile
# Caddyfile

# Wildcard for subdomains
*.craftflow.com {
    reverse_proxy storefront-frontend:3000

    # Auto HTTPS with Let's Encrypt
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
}

# Custom domains - dynamically configured
# This requires the Caddy API or on-demand TLS

# On-demand TLS for custom domains
:443 {
    tls {
        on_demand
    }

    reverse_proxy storefront-frontend:3000
}
```

### 5.2 Alternative: Nginx + Certbot

```nginx
# Dynamic SSL with Lua (OpenResty)

server {
    listen 443 ssl;
    server_name ~^(?<subdomain>.+)\.craftflow\.com$;

    ssl_certificate /etc/letsencrypt/live/craftflow.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/craftflow.com/privkey.pem;

    location / {
        proxy_pass http://storefront-frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Storefront-Subdomain $subdomain;
    }
}

# Custom domains - requires dynamic certificate loading
server {
    listen 443 ssl;
    server_name ~^(?<domain>.+)$;

    # Dynamic SSL certificate loading via Lua
    ssl_certificate_by_lua_block {
        -- Load certificate based on domain
    }

    location / {
        proxy_pass http://storefront-frontend:3000;
        proxy_set_header Host $host;
    }
}
```

### 5.3 SSL Certificate Automation

```python
# server/src/services/ssl_service.py

import subprocess
from pathlib import Path

class SSLService:
    CERT_PATH = Path("/etc/letsencrypt/live")

    @staticmethod
    async def provision_certificate(domain: str, email: str) -> bool:
        """Provision SSL certificate using certbot."""
        try:
            result = subprocess.run([
                'certbot', 'certonly',
                '--nginx',  # or --standalone
                '-d', domain,
                '--email', email,
                '--agree-tos',
                '--non-interactive',
            ], capture_output=True, text=True)

            return result.returncode == 0
        except Exception as e:
            logger.error(f"SSL provisioning failed: {e}")
            return False

    @staticmethod
    def get_certificate_expiry(domain: str) -> Optional[datetime]:
        """Get certificate expiry date."""
        cert_path = SSLService.CERT_PATH / domain / "fullchain.pem"
        if not cert_path.exists():
            return None

        # Parse certificate and extract expiry
        # ...
```

---

## Phase 6: Auto-Provisioning on Upgrade

### 6.1 Webhook/Event Handler

```python
# When user upgrades to Full plan, auto-create storefront

@router.post("/webhooks/subscription-upgraded")
async def handle_subscription_upgrade(
    event: SubscriptionEvent,
    db: Session = Depends(get_db)
):
    if event.new_tier == "full":
        user = db.query(User).filter(User.id == event.user_id).first()

        # Check if storefront already exists
        existing = db.query(Storefront).filter(
            Storefront.user_id == user.id
        ).first()

        if not existing:
            # Auto-create storefront with default settings
            StorefrontService.create_storefront(
                db=db,
                user_id=user.id,
                store_name=user.shop_name or f"{user.email.split('@')[0]}'s Store"
            )

            # Send welcome email with setup instructions
            EmailService.send_storefront_welcome(user.email)
```

---

## Implementation Order

### Sprint 1: Foundation (1-2 weeks)

- [ ] Create database migration for storefronts table
- [ ] Create Storefront entity and relationships
- [ ] Implement basic CRUD API endpoints
- [ ] Add storefront creation on Full plan upgrade

### Sprint 2: Domain Management (1-2 weeks)

- [ ] Implement subdomain assignment
- [ ] Build custom domain verification (DNS TXT)
- [ ] Create domain setup wizard in admin UI
- [ ] Add verification status checking

### Sprint 3: SSL & Infrastructure (1-2 weeks)

- [ ] Set up Caddy/Nginx with wildcard SSL
- [ ] Implement on-demand SSL for custom domains
- [ ] Configure reverse proxy routing
- [ ] Test domain routing end-to-end

### Sprint 4: Storefront Frontend (1-2 weeks)

- [ ] Add multi-tenant middleware
- [ ] Implement dynamic theme loading
- [ ] Scope product queries by storefront
- [ ] Test with subdomain and custom domain

### Sprint 5: Polish & Launch (1 week)

- [ ] Admin UI for all storefront settings
- [ ] Preview functionality
- [ ] Publish/unpublish controls
- [ ] Documentation for users

---

## Security Considerations

1. **Domain Ownership Verification** - Always verify via DNS before allowing custom domain
2. **SSL Certificate Security** - Store private keys securely, use proper permissions
3. **Rate Limiting** - Limit domain verification attempts
4. **Subdomain Validation** - Prevent reserved words (admin, api, www, etc.)
5. **Data Isolation** - Ensure strict user_id filtering on all queries
6. **CORS Configuration** - Properly configure for custom domains

---

## Cost Considerations

1. **SSL Certificates** - Let's Encrypt is free (rate limits: 50 certs/domain/week)
2. **DNS Lookups** - May need paid DNS service for high volume
3. **CDN** - Consider CloudFlare for custom domain SSL/CDN
4. **Storage** - Product images per user

---

## Future Enhancements

1. **Custom Email Domain** - orders@shop.example.com
2. **White-Label** - Remove all CraftFlow branding
3. **Multiple Storefronts** - Allow users to create multiple stores
4. **Storefront Templates** - Pre-built themes users can choose
5. **Custom CSS/JS** - Advanced customization
6. **API Access** - Let users build custom integrations
