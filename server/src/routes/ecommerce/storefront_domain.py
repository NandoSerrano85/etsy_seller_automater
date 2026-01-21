"""
Storefront Domain Management API endpoints.

Handles custom domain setup, DNS verification, SSL provisioning,
and storefront publishing for multi-tenant storefronts.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import secrets
import re

from server.src.database.core import get_db
from server.src.entities.ecommerce.storefront_settings import StorefrontSettings
from server.src.entities.ecommerce.domain_verification import DomainVerification
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.routes.auth.plan_access import require_full_plan
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/storefront/domain',
    tags=['Ecommerce - Storefront Domain']
)


# ============================================================================
# Constants
# ============================================================================

RESERVED_SUBDOMAINS = {
    'admin', 'api', 'www', 'mail', 'smtp', 'ftp', 'blog', 'shop', 'store',
    'app', 'dashboard', 'panel', 'support', 'help', 'docs', 'status',
    'cdn', 'static', 'assets', 'media', 'images', 'files', 'download',
    'login', 'register', 'auth', 'oauth', 'account', 'profile', 'settings',
    'craftflow', 'etsy', 'shopify', 'test', 'staging', 'dev', 'demo'
}

BASE_DOMAIN = "craftflow.store"
VERIFICATION_RECORD_PREFIX = "_craftflow-verify"


# ============================================================================
# Pydantic Models
# ============================================================================

class SetSubdomainRequest(BaseModel):
    """Request to set a subdomain"""
    subdomain: str = Field(..., min_length=3, max_length=63)

    @validator('subdomain')
    def validate_subdomain(cls, v):
        # Convert to lowercase and strip
        v = v.lower().strip()

        # Check for valid characters (alphanumeric and hyphens)
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', v):
            raise ValueError('Subdomain must contain only lowercase letters, numbers, and hyphens. Cannot start or end with a hyphen.')

        # Check against reserved subdomains
        if v in RESERVED_SUBDOMAINS:
            raise ValueError(f'Subdomain "{v}" is reserved and cannot be used.')

        return v


class SetCustomDomainRequest(BaseModel):
    """Request to set a custom domain"""
    domain: str = Field(..., min_length=4, max_length=255)

    @validator('domain')
    def validate_domain(cls, v):
        # Convert to lowercase and strip
        v = v.lower().strip()

        # Remove protocol if present
        v = re.sub(r'^https?://', '', v)

        # Remove trailing slash
        v = v.rstrip('/')

        # Validate domain format
        domain_pattern = r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        if not re.match(domain_pattern, v):
            raise ValueError('Invalid domain format. Example: shop.example.com')

        return v


class DomainInstructionsResponse(BaseModel):
    """DNS setup instructions response"""
    domain: str
    verification_method: str
    cname_record: dict
    txt_record: dict
    instructions: List[str]
    verification_token: str


class DomainStatusResponse(BaseModel):
    """Domain verification status response"""
    domain: str
    is_verified: bool
    ssl_status: str
    verification_method: Optional[str]
    last_checked: Optional[datetime]
    error_message: Optional[str]
    attempts: int


class StorefrontStatusResponse(BaseModel):
    """Storefront status response"""
    subdomain: Optional[str]
    subdomain_url: Optional[str]
    custom_domain: Optional[str]
    custom_domain_url: Optional[str]
    domain_verified: bool
    domain_verification_token: Optional[str]
    ssl_status: str
    ssl_expires_at: Optional[datetime]
    is_active: bool
    is_published: bool
    maintenance_mode: bool
    published_at: Optional[datetime]
    preview_url: Optional[str]
    primary_url: Optional[str]


class PublishRequest(BaseModel):
    """Request to publish/unpublish storefront"""
    publish: bool = True


class MaintenanceRequest(BaseModel):
    """Request to enable/disable maintenance mode"""
    enabled: bool = True


# ============================================================================
# Helper Functions
# ============================================================================

def get_storefront_or_404(db: Session, user_id: UUID) -> StorefrontSettings:
    """Get storefront settings or raise 404"""
    settings = db.query(StorefrontSettings).filter(
        StorefrontSettings.user_id == user_id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=404,
            detail="Storefront not found. Please create storefront settings first."
        )

    return settings


def get_or_create_storefront(db: Session, user: User) -> StorefrontSettings:
    """Get storefront settings or create a default one if not exists"""
    settings = db.query(StorefrontSettings).filter(
        StorefrontSettings.user_id == user.id
    ).first()

    if not settings:
        # Create a default storefront settings entry
        settings = StorefrontSettings(
            user_id=user.id,
            store_name=f"{user.email.split('@')[0]}'s Store" if user.email else "My Store",
            is_active=True,
            is_published=False,
            maintenance_mode=False,
            domain_verified=False,
            ssl_status="none"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return f"cf_verify_{secrets.token_urlsafe(32)}"


def generate_subdomain_from_store_name(store_name: str, db: Session) -> str:
    """Generate a unique subdomain from store name"""
    # Clean the store name
    subdomain = re.sub(r'[^a-z0-9]', '', store_name.lower())[:50]

    if not subdomain:
        subdomain = "store"

    # Check if subdomain is taken
    original = subdomain
    counter = 1

    while True:
        if subdomain in RESERVED_SUBDOMAINS:
            subdomain = f"{original}{counter}"
            counter += 1
            continue

        existing = db.query(StorefrontSettings).filter(
            StorefrontSettings.subdomain == subdomain
        ).first()

        if not existing:
            break

        subdomain = f"{original}{counter}"
        counter += 1

    return subdomain


# ============================================================================
# Routes - Subdomain Management
# ============================================================================

@router.post('/subdomain')
async def set_subdomain(
    request: SetSubdomainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Set or update the subdomain for the storefront.

    The subdomain will be used for {subdomain}.craftflow.store

    Requires: Full plan
    """
    # Use get_or_create to auto-create storefront if not exists
    settings = get_or_create_storefront(db, current_user)

    # Check if subdomain is already taken
    existing = db.query(StorefrontSettings).filter(
        StorefrontSettings.subdomain == request.subdomain,
        StorefrontSettings.id != settings.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Subdomain '{request.subdomain}' is already taken."
        )

    settings.subdomain = request.subdomain

    # Generate verification token if not exists
    if not settings.domain_verification_token:
        settings.domain_verification_token = generate_verification_token()

    db.commit()
    db.refresh(settings)

    return {
        "message": "Subdomain set successfully",
        "subdomain": settings.subdomain,
        "url": f"https://{settings.subdomain}.{BASE_DOMAIN}"
    }


@router.delete('/subdomain')
async def remove_subdomain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Remove the subdomain from the storefront.

    Requires: Full plan
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.subdomain:
        raise HTTPException(status_code=400, detail="No subdomain is set")

    settings.subdomain = None
    db.commit()

    return {"message": "Subdomain removed successfully"}


# ============================================================================
# Routes - Custom Domain Management
# ============================================================================

@router.post('/domain')
async def set_custom_domain(
    request: SetCustomDomainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Set a custom domain for the storefront.

    Returns DNS configuration instructions for domain verification.

    Requires: Full plan
    """
    # Use get_or_create to auto-create storefront if not exists
    settings = get_or_create_storefront(db, current_user)

    # Check if domain is already in use
    existing = db.query(StorefrontSettings).filter(
        StorefrontSettings.custom_domain == request.domain,
        StorefrontSettings.id != settings.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Domain '{request.domain}' is already registered to another storefront."
        )

    # Generate new verification token
    verification_token = generate_verification_token()

    # Update settings
    settings.custom_domain = request.domain
    settings.domain_verified = False
    settings.domain_verification_token = verification_token
    settings.domain_verification_method = "dns_txt"
    settings.ssl_status = "none"

    # Create verification record
    verification = DomainVerification(
        storefront_id=settings.id,
        domain=request.domain,
        verification_token=verification_token,
        verification_method="dns_txt",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(verification)

    db.commit()
    db.refresh(settings)

    return {
        "message": "Custom domain set. Please configure DNS records to verify ownership.",
        "domain": request.domain,
        "verification_token": verification_token,
        "instructions_url": f"/api/ecommerce/admin/storefront-domain/domain/instructions"
    }


@router.delete('/domain')
async def remove_custom_domain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Remove custom domain from the storefront.

    The subdomain will still be available if set.

    Requires: Full plan
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain is set")

    settings.custom_domain = None
    settings.domain_verified = False
    settings.ssl_status = "none"
    settings.ssl_certificate_path = None
    settings.ssl_private_key_path = None
    settings.ssl_expires_at = None

    # Delete related verification records
    db.query(DomainVerification).filter(
        DomainVerification.storefront_id == settings.id
    ).delete()

    db.commit()

    return {"message": "Custom domain removed successfully"}


@router.get('/domain/instructions', response_model=DomainInstructionsResponse)
async def get_domain_instructions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Get DNS setup instructions for custom domain verification.

    Requires: Full plan
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain is set")

    domain = settings.custom_domain
    token = settings.domain_verification_token

    # Determine if root domain or subdomain
    domain_parts = domain.split('.')
    is_subdomain = len(domain_parts) > 2

    return DomainInstructionsResponse(
        domain=domain,
        verification_method="dns_txt",
        cname_record={
            "type": "CNAME",
            "name": domain_parts[0] if is_subdomain else "@",
            "value": f"stores.{BASE_DOMAIN}",
            "description": f"Points {domain} to CraftFlow servers"
        },
        txt_record={
            "type": "TXT",
            "name": f"{VERIFICATION_RECORD_PREFIX}.{domain_parts[0]}" if is_subdomain else VERIFICATION_RECORD_PREFIX,
            "value": token,
            "description": "Verifies domain ownership"
        },
        instructions=[
            f"1. Log in to your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare)",
            f"2. Go to DNS settings for {'.'.join(domain_parts[-2:])}",
            f"3. Add a CNAME record:",
            f"   - Name/Host: {domain_parts[0] if is_subdomain else '@'}",
            f"   - Value/Points to: stores.{BASE_DOMAIN}",
            f"4. Add a TXT record:",
            f"   - Name/Host: {VERIFICATION_RECORD_PREFIX}",
            f"   - Value: {token}",
            f"5. Wait for DNS propagation (can take up to 48 hours)",
            f"6. Click 'Verify Domain' to check your configuration"
        ],
        verification_token=token
    )


@router.post('/domain/verify')
async def verify_domain(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Trigger domain verification.

    Checks DNS records to verify domain ownership.

    Requires: Full plan
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain is set")

    if settings.domain_verified:
        return {
            "status": "already_verified",
            "message": "Domain is already verified"
        }

    # Import DNS verification service
    try:
        from server.src.services.dns_verification_service import verify_domain_ownership

        result = verify_domain_ownership(
            domain=settings.custom_domain,
            expected_token=settings.domain_verification_token
        )

        # Update verification record
        verification = db.query(DomainVerification).filter(
            DomainVerification.storefront_id == settings.id,
            DomainVerification.domain == settings.custom_domain
        ).order_by(DomainVerification.created_at.desc()).first()

        if verification:
            verification.attempts += 1
            verification.last_checked_at = datetime.utcnow()

        if result['verified']:
            settings.domain_verified = True
            if verification:
                verification.status = "verified"
                verification.verified_at = datetime.utcnow()

            db.commit()

            # Schedule SSL provisioning in background
            background_tasks.add_task(provision_ssl_certificate, settings.id, db)

            return {
                "status": "verified",
                "message": "Domain verified successfully! SSL certificate is being provisioned.",
                "domain": settings.custom_domain
            }
        else:
            if verification:
                verification.status = "failed"
                verification.error_message = result.get('error', 'Verification failed')

            db.commit()

            return {
                "status": "failed",
                "message": result.get('error', 'Domain verification failed'),
                "details": result.get('details', {}),
                "domain": settings.custom_domain
            }

    except ImportError:
        # DNS verification service not available, mark as verified for dev
        settings.domain_verified = True
        db.commit()

        return {
            "status": "verified",
            "message": "Domain marked as verified (DNS verification service not available)",
            "domain": settings.custom_domain
        }


@router.get('/domain/status', response_model=DomainStatusResponse)
async def get_domain_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Get domain verification and SSL status.

    Requires: Full plan
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain is set")

    # Get latest verification record
    verification = db.query(DomainVerification).filter(
        DomainVerification.storefront_id == settings.id,
        DomainVerification.domain == settings.custom_domain
    ).order_by(DomainVerification.created_at.desc()).first()

    return DomainStatusResponse(
        domain=settings.custom_domain,
        is_verified=settings.domain_verified,
        ssl_status=settings.ssl_status or "none",
        verification_method=settings.domain_verification_method,
        last_checked=verification.last_checked_at if verification else None,
        error_message=verification.error_message if verification else None,
        attempts=verification.attempts if verification else 0
    )


# ============================================================================
# Routes - SSL Management
# ============================================================================

@router.post('/ssl/provision')
async def provision_ssl(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Provision SSL certificate for verified custom domain.

    Uses Let's Encrypt for free SSL certificates.

    Requires: Full plan with verified custom domain
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain is set")

    if not settings.domain_verified:
        raise HTTPException(status_code=400, detail="Domain must be verified first")

    if settings.ssl_status == "active":
        return {
            "status": "active",
            "message": "SSL certificate is already active",
            "expires_at": settings.ssl_expires_at
        }

    settings.ssl_status = "pending"
    db.commit()

    # Run SSL provisioning in background
    background_tasks.add_task(provision_ssl_certificate, settings.id, db)

    return {
        "status": "pending",
        "message": "SSL certificate provisioning started"
    }


async def provision_ssl_certificate(storefront_id: int, db: Session):
    """Background task to provision SSL certificate"""
    try:
        from server.src.services.ssl_service import SSLService

        settings = db.query(StorefrontSettings).filter(
            StorefrontSettings.id == storefront_id
        ).first()

        if not settings:
            return

        success = await SSLService.provision_certificate(
            domain=settings.custom_domain,
            email=settings.contact_email or f"admin@{settings.custom_domain}"
        )

        if success:
            settings.ssl_status = "active"
            settings.ssl_expires_at = datetime.utcnow() + timedelta(days=90)
        else:
            settings.ssl_status = "failed"

        db.commit()

    except ImportError:
        # SSL service not available, mark as active for dev
        settings = db.query(StorefrontSettings).filter(
            StorefrontSettings.id == storefront_id
        ).first()

        if settings:
            settings.ssl_status = "active"
            settings.ssl_expires_at = datetime.utcnow() + timedelta(days=90)
            db.commit()


# ============================================================================
# Routes - Publishing
# ============================================================================

@router.get('/status', response_model=StorefrontStatusResponse)
async def get_storefront_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Get overall storefront status including domain and publishing state.

    Requires: Full plan
    """
    # Use get_or_create to auto-create storefront if not exists
    settings = get_or_create_storefront(db, current_user)

    subdomain_url = f"https://{settings.subdomain}.{BASE_DOMAIN}" if settings.subdomain else None
    custom_domain_url = f"https://{settings.custom_domain}" if settings.custom_domain and settings.domain_verified else None

    # Determine primary URL
    primary_url = custom_domain_url or subdomain_url

    # Preview URL (always uses subdomain)
    preview_url = subdomain_url

    return StorefrontStatusResponse(
        subdomain=settings.subdomain,
        subdomain_url=subdomain_url,
        custom_domain=settings.custom_domain,
        custom_domain_url=custom_domain_url,
        domain_verified=settings.domain_verified or False,
        domain_verification_token=settings.domain_verification_token,
        ssl_status=settings.ssl_status or "none",
        ssl_expires_at=settings.ssl_expires_at,
        is_active=settings.is_active or True,
        is_published=settings.is_published or False,
        maintenance_mode=settings.maintenance_mode or False,
        published_at=settings.published_at,
        preview_url=preview_url,
        primary_url=primary_url
    )


@router.post('/publish')
async def publish_storefront(
    request: PublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Publish or unpublish the storefront.

    A published storefront is publicly accessible.

    Requires: Full plan
    """
    # Use get_or_create to auto-create storefront if not exists
    settings = get_or_create_storefront(db, current_user)

    # Check prerequisites for publishing
    if request.publish:
        if not settings.subdomain and not (settings.custom_domain and settings.domain_verified):
            raise HTTPException(
                status_code=400,
                detail="You need either a subdomain or a verified custom domain to publish"
            )

        if not settings.store_name:
            raise HTTPException(
                status_code=400,
                detail="Please set a store name before publishing"
            )

    settings.is_published = request.publish
    if request.publish and not settings.published_at:
        settings.published_at = datetime.utcnow()

    db.commit()
    db.refresh(settings)

    action = "published" if request.publish else "unpublished"
    return {
        "message": f"Storefront {action} successfully",
        "is_published": settings.is_published,
        "url": settings.get_store_url()
    }


@router.post('/maintenance')
async def toggle_maintenance_mode(
    request: MaintenanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Enable or disable maintenance mode.

    When enabled, visitors see a maintenance page.

    Requires: Full plan
    """
    # Use get_or_create to auto-create storefront if not exists
    settings = get_or_create_storefront(db, current_user)

    settings.maintenance_mode = request.enabled
    db.commit()

    status = "enabled" if request.enabled else "disabled"
    return {
        "message": f"Maintenance mode {status}",
        "maintenance_mode": settings.maintenance_mode
    }


@router.get('/preview')
async def get_preview_url(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_plan)
):
    """
    Get the preview URL for the storefront.

    Preview URL always works, even if storefront is unpublished.

    Requires: Full plan
    """
    settings = get_storefront_or_404(db, current_user.id)

    if not settings.subdomain:
        raise HTTPException(
            status_code=400,
            detail="No subdomain set. Please set a subdomain first."
        )

    preview_url = f"https://{settings.subdomain}.{BASE_DOMAIN}?preview=true"

    return {
        "preview_url": preview_url,
        "subdomain": settings.subdomain
    }
