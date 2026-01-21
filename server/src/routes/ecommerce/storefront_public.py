"""
Public Storefront API endpoints.

These endpoints are accessed by the storefront frontend to load configurations
based on domain name. They do not require authentication and are optimized for
public access with caching.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

from server.src.database.core import get_db
from server.src.entities.ecommerce.storefront_settings import StorefrontSettings
from server.src.entities.ecommerce.product import Product


router = APIRouter(
    prefix='/api/store',
    tags=['Public Storefront']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class PublicStorefrontConfig(BaseModel):
    """Public storefront configuration for frontend"""
    store_name: str
    store_description: Optional[str]
    logo_url: Optional[str]
    favicon_url: Optional[str]

    # Theme
    primary_color: str
    secondary_color: str
    accent_color: str
    text_color: str
    background_color: str
    font_family: str

    # Settings
    currency: str
    timezone: str

    # Contact
    contact_email: Optional[str]
    support_phone: Optional[str]

    # Social
    social_links: Dict

    # SEO
    meta_title: Optional[str]
    meta_description: Optional[str]
    google_analytics_id: Optional[str]
    facebook_pixel_id: Optional[str]

    # Status
    is_published: bool
    maintenance_mode: bool

    # Identifiers
    user_id: str
    subdomain: Optional[str]
    custom_domain: Optional[str]


class PublicProductImage(BaseModel):
    """Product image for public API"""
    url: str
    alt: Optional[str]
    position: int


class PublicProductVariant(BaseModel):
    """Product variant for public API"""
    id: str
    name: str
    sku: Optional[str]
    price: float
    compare_at_price: Optional[float]
    inventory_quantity: Optional[int]
    is_available: bool


class PublicProduct(BaseModel):
    """Product for public storefront"""
    id: str
    title: str
    slug: str
    description: Optional[str]
    price: float
    compare_at_price: Optional[float]
    featured_image: Optional[str]
    images: List[PublicProductImage]
    category: Optional[str]
    product_type: str
    is_available: bool
    has_variants: bool
    variants: List[PublicProductVariant]


class PublicProductDetail(PublicProduct):
    """Detailed product view with full information"""
    meta_title: Optional[str]
    meta_description: Optional[str]


class PaginatedProducts(BaseModel):
    """Paginated product list"""
    items: List[PublicProduct]
    total: int
    page: int
    page_size: int
    pages: int


class PublicCategory(BaseModel):
    """Product category for public API"""
    id: str
    name: str
    slug: str
    description: Optional[str]
    image_url: Optional[str]
    product_count: int


# ============================================================================
# Helper Functions
# ============================================================================

def get_storefront_by_domain(db: Session, domain: str) -> Optional[StorefrontSettings]:
    """
    Look up storefront by domain (custom domain or subdomain).

    Args:
        db: Database session
        domain: The domain to look up (e.g., "shop.example.com" or "myshop.craftflow.store")

    Returns:
        StorefrontSettings if found, None otherwise
    """
    # Clean the domain
    domain = domain.lower().strip()

    # First try custom domain
    storefront = db.query(StorefrontSettings).filter(
        StorefrontSettings.custom_domain == domain,
        StorefrontSettings.domain_verified == True,
        StorefrontSettings.is_active == True
    ).first()

    if storefront:
        return storefront

    # Try subdomain (extract from craftflow.store subdomain)
    if '.craftflow.store' in domain:
        subdomain = domain.replace('.craftflow.store', '')
        storefront = db.query(StorefrontSettings).filter(
            StorefrontSettings.subdomain == subdomain,
            StorefrontSettings.is_active == True
        ).first()
        return storefront

    # Direct subdomain lookup
    storefront = db.query(StorefrontSettings).filter(
        StorefrontSettings.subdomain == domain,
        StorefrontSettings.is_active == True
    ).first()

    return storefront


def format_product_for_public(product: Product) -> PublicProduct:
    """Format a product for public API response"""
    images = []
    if product.images:
        for i, img in enumerate(product.images if isinstance(product.images, list) else []):
            if isinstance(img, dict):
                images.append(PublicProductImage(
                    url=img.get('url', ''),
                    alt=img.get('alt', product.title),
                    position=img.get('position', i)
                ))
            elif isinstance(img, str):
                images.append(PublicProductImage(url=img, alt=product.title, position=i))

    variants = []
    if product.has_variants and product.variants:
        for var in product.variants:
            variants.append(PublicProductVariant(
                id=str(var.id),
                name=var.name or '',
                sku=var.sku,
                price=float(var.price) if var.price else float(product.price),
                compare_at_price=float(var.compare_at_price) if var.compare_at_price else None,
                inventory_quantity=var.inventory_quantity,
                is_available=var.inventory_quantity > 0 if var.inventory_quantity else True
            ))

    return PublicProduct(
        id=str(product.id),
        title=product.title,
        slug=product.slug or str(product.id),
        description=product.description,
        price=float(product.price) if product.price else 0.0,
        compare_at_price=float(product.compare_at_price) if product.compare_at_price else None,
        featured_image=product.featured_image,
        images=images,
        category=product.category,
        product_type=product.product_type or 'physical',
        is_available=product.status == 'active' and (not product.track_inventory or product.inventory_quantity > 0),
        has_variants=product.has_variants or False,
        variants=variants
    )


# ============================================================================
# Public Routes
# ============================================================================

@router.get('/{domain}/config', response_model=PublicStorefrontConfig)
async def get_store_config(
    domain: str,
    db: Session = Depends(get_db)
):
    """
    Get store configuration by domain.

    This endpoint is used by the storefront frontend to load branding,
    theme, and configuration settings based on the domain.

    Args:
        domain: The domain (custom domain or subdomain)

    Returns:
        Store configuration including branding, theme, and settings
    """
    storefront = get_storefront_by_domain(db, domain)

    if not storefront:
        raise HTTPException(status_code=404, detail="Store not found")

    # Check if store is published (allow preview mode)
    if not storefront.is_published:
        raise HTTPException(status_code=404, detail="Store not found")

    return PublicStorefrontConfig(
        store_name=storefront.store_name or "Store",
        store_description=storefront.store_description,
        logo_url=storefront.logo_url,
        favicon_url=storefront.favicon_url,
        primary_color=storefront.primary_color or "#10b981",
        secondary_color=storefront.secondary_color or "#059669",
        accent_color=storefront.accent_color or "#34d399",
        text_color=storefront.text_color or "#111827",
        background_color=storefront.background_color or "#ffffff",
        font_family=storefront.font_family or "Inter",
        currency=storefront.currency or "USD",
        timezone=storefront.timezone or "America/New_York",
        contact_email=storefront.contact_email,
        support_phone=storefront.support_phone,
        social_links=storefront.social_links or {},
        meta_title=storefront.meta_title,
        meta_description=storefront.meta_description,
        google_analytics_id=storefront.google_analytics_id,
        facebook_pixel_id=storefront.facebook_pixel_id,
        is_published=storefront.is_published or False,
        maintenance_mode=storefront.maintenance_mode or False,
        user_id=str(storefront.user_id),
        subdomain=storefront.subdomain,
        custom_domain=storefront.custom_domain
    )


@router.get('/{domain}/products', response_model=PaginatedProducts)
async def get_store_products(
    domain: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search products"),
    sort: Optional[str] = Query("created_at", description="Sort field"),
    order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get products for a store by domain.

    Supports filtering by category, search, sorting, and pagination.
    Only returns active products from published stores.

    Args:
        domain: The domain (custom domain or subdomain)
        category: Optional category filter
        search: Optional search query
        sort: Sort field (created_at, price, title)
        order: Sort order (asc/desc)
        page: Page number (1-indexed)
        page_size: Items per page (max 100)

    Returns:
        Paginated list of products
    """
    storefront = get_storefront_by_domain(db, domain)

    if not storefront:
        raise HTTPException(status_code=404, detail="Store not found")

    if not storefront.is_published:
        raise HTTPException(status_code=404, detail="Store not found")

    # Build query
    query = db.query(Product).filter(
        Product.user_id == storefront.user_id,
        Product.status == 'active'
    )

    # Category filter
    if category:
        query = query.filter(Product.category == category)

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.title.ilike(search_term)) |
            (Product.description.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Sorting
    sort_column = getattr(Product, sort, Product.created_at)
    if order.lower() == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedProducts(
        items=[format_product_for_public(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get('/{domain}/products/{slug}', response_model=PublicProductDetail)
async def get_store_product(
    domain: str,
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get a single product by slug or ID.

    Args:
        domain: The domain (custom domain or subdomain)
        slug: Product slug or ID

    Returns:
        Product details
    """
    storefront = get_storefront_by_domain(db, domain)

    if not storefront:
        raise HTTPException(status_code=404, detail="Store not found")

    if not storefront.is_published:
        raise HTTPException(status_code=404, detail="Store not found")

    # Try to find by slug first, then by ID
    product = db.query(Product).filter(
        Product.user_id == storefront.user_id,
        Product.status == 'active',
        (Product.slug == slug) | (Product.id == slug)
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    base = format_product_for_public(product)

    return PublicProductDetail(
        **base.dict(),
        meta_title=product.meta_title,
        meta_description=product.meta_description
    )


@router.get('/{domain}/categories', response_model=List[PublicCategory])
async def get_store_categories(
    domain: str,
    db: Session = Depends(get_db)
):
    """
    Get product categories for a store.

    Returns categories that have at least one active product.

    Args:
        domain: The domain (custom domain or subdomain)

    Returns:
        List of categories with product counts
    """
    storefront = get_storefront_by_domain(db, domain)

    if not storefront:
        raise HTTPException(status_code=404, detail="Store not found")

    if not storefront.is_published:
        raise HTTPException(status_code=404, detail="Store not found")

    # Get unique categories from products with counts
    from sqlalchemy import func

    categories_query = db.query(
        Product.category,
        func.count(Product.id).label('product_count')
    ).filter(
        Product.user_id == storefront.user_id,
        Product.status == 'active',
        Product.category.isnot(None),
        Product.category != ''
    ).group_by(Product.category).all()

    categories = []
    for cat_name, count in categories_query:
        categories.append(PublicCategory(
            id=cat_name.lower().replace(' ', '-'),
            name=cat_name,
            slug=cat_name.lower().replace(' ', '-'),
            description=None,
            image_url=None,
            product_count=count
        ))

    return categories


@router.get('/{domain}/featured', response_model=List[PublicProduct])
async def get_featured_products(
    domain: str,
    limit: int = Query(8, ge=1, le=20, description="Number of products"),
    db: Session = Depends(get_db)
):
    """
    Get featured products for a store.

    Returns the most recently added active products.

    Args:
        domain: The domain (custom domain or subdomain)
        limit: Maximum number of products to return

    Returns:
        List of featured products
    """
    storefront = get_storefront_by_domain(db, domain)

    if not storefront:
        raise HTTPException(status_code=404, detail="Store not found")

    if not storefront.is_published:
        raise HTTPException(status_code=404, detail="Store not found")

    products = db.query(Product).filter(
        Product.user_id == storefront.user_id,
        Product.status == 'active'
    ).order_by(Product.created_at.desc()).limit(limit).all()

    return [format_product_for_public(p) for p in products]


# ============================================================================
# Preview Route (allows viewing unpublished stores)
# ============================================================================

@router.get('/preview/{domain}/config', response_model=PublicStorefrontConfig)
async def get_store_config_preview(
    domain: str,
    preview_token: Optional[str] = Query(None, description="Preview token"),
    db: Session = Depends(get_db)
):
    """
    Get store configuration for preview mode.

    Allows viewing unpublished stores with a preview token or for authenticated owners.

    Args:
        domain: The domain (custom domain or subdomain)
        preview_token: Optional preview token for authentication

    Returns:
        Store configuration including branding, theme, and settings
    """
    storefront = get_storefront_by_domain(db, domain)

    if not storefront:
        raise HTTPException(status_code=404, detail="Store not found")

    # For preview, we allow unpublished stores
    # In production, you'd want to verify the preview token

    return PublicStorefrontConfig(
        store_name=storefront.store_name or "Store",
        store_description=storefront.store_description,
        logo_url=storefront.logo_url,
        favicon_url=storefront.favicon_url,
        primary_color=storefront.primary_color or "#10b981",
        secondary_color=storefront.secondary_color or "#059669",
        accent_color=storefront.accent_color or "#34d399",
        text_color=storefront.text_color or "#111827",
        background_color=storefront.background_color or "#ffffff",
        font_family=storefront.font_family or "Inter",
        currency=storefront.currency or "USD",
        timezone=storefront.timezone or "America/New_York",
        contact_email=storefront.contact_email,
        support_phone=storefront.support_phone,
        social_links=storefront.social_links or {},
        meta_title=storefront.meta_title,
        meta_description=storefront.meta_description,
        google_analytics_id=storefront.google_analytics_id,
        facebook_pixel_id=storefront.facebook_pixel_id,
        is_published=storefront.is_published or False,
        maintenance_mode=storefront.maintenance_mode or False,
        user_id=str(storefront.user_id),
        subdomain=storefront.subdomain,
        custom_domain=storefront.custom_domain
    )
