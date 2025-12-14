"""Product API endpoints for ecommerce storefront."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, noload
from sqlalchemy import or_, and_
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from server.src.database.core import get_db
from server.src.entities.ecommerce.product import (
    Product,
    ProductVariant,
    ProductType,
    PrintMethod,
    ProductCategory
)


router = APIRouter(
    prefix='/api/storefront/products',
    tags=['Storefront - Products']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class ProductVariantResponse(BaseModel):
    """Product variant response model."""
    id: str
    name: str
    sku: Optional[str] = None
    price: Optional[float] = None
    inventory_quantity: int = 0
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response model."""
    id: str
    name: str
    slug: str
    short_description: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    featured_image: Optional[str] = None
    print_method: str
    category: str
    product_type: str
    is_featured: bool = False
    inventory_quantity: int = 0
    track_inventory: bool = False

    class Config:
        from_attributes = True


class ProductDetailResponse(BaseModel):
    """Product detail response model."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    images: Optional[List[str]] = []
    featured_image: Optional[str] = None
    print_method: str
    category: str
    product_type: str
    has_variants: bool = False
    variants: List[ProductVariantResponse] = []
    inventory_quantity: int = 0
    track_inventory: bool = False
    allow_backorder: bool = False
    digital_file_url: Optional[str] = None
    download_limit: int = 3
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_featured: bool = False
    template_name: Optional[str] = None
    long_description: Optional[str] = None  # Alias for description for storefront compatibility
    image_url: Optional[str] = None  # Alias for featured_image for storefront compatibility
    image_gallery: Optional[List[str]] = []  # Alias for images for storefront compatibility
    sku: Optional[str] = None  # Added for storefront display

    class Config:
        from_attributes = True

    def model_post_init(self, __context) -> None:
        """Set aliases after initialization."""
        # Set long_description as alias for description
        if self.description and not self.long_description:
            object.__setattr__(self, 'long_description', self.description)
        # Set image_url as alias for featured_image
        if self.featured_image and not self.image_url:
            object.__setattr__(self, 'image_url', self.featured_image)
        # Set image_gallery as alias for images
        if self.images and not self.image_gallery:
            object.__setattr__(self, 'image_gallery', self.images)


class ProductCreateRequest(BaseModel):
    """Product creation request model."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    product_type: str = Field(..., description="physical or digital")
    print_method: str = Field(..., description="uvdtf, dtf, sublimation, vinyl, other, digital")
    category: str = Field(..., description="cup_wraps, single_square, single_rectangle, other_custom")
    price: float = Field(..., gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, ge=0)
    track_inventory: bool = False
    inventory_quantity: int = Field(0, ge=0)
    allow_backorder: bool = False
    digital_file_url: Optional[str] = None
    download_limit: int = Field(3, gt=0)
    images: Optional[List[str]] = []
    featured_image: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    design_id: Optional[str] = None
    template_name: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

class ProductListPaginatedResponse(BaseModel):
    """Paginated product list response for storefront."""
    items: List[ProductListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get('/', response_model=ProductListPaginatedResponse)
async def list_products(
    print_method: Optional[str] = Query(None, description="Filter by print method"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    featured: Optional[bool] = Query(None, description="Filter featured products"),
    search: Optional[str] = Query(None, min_length=2, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, le=100, ge=1, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of products for storefront.

    Filters:
    - print_method: uvdtf, dtf, sublimation, vinyl, other, digital
    - category: cup_wraps, single_square, single_rectangle, other_custom
    - featured: true/false
    - search: search term for name/description

    Returns paginated list of products with basic info.
    """
    query = db.query(Product).filter(Product.is_active == True).options(noload(Product.reviews))

    # Filter by print method (HOW it's made)
    if print_method:
        query = query.filter(Product.print_method == print_method)

    # Filter by category/product type (WHAT it is)
    if category:
        query = query.filter(Product.category == category)

    # Filter by featured status
    if featured is not None:
        query = query.filter(Product.is_featured == featured)

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.short_description.ilike(search_term)
            )
        )

    # Get total count before pagination
    total = query.count()

    # Order by featured first, then by created date
    query = query.order_by(
        Product.is_featured.desc(),
        Product.created_at.desc()
    )

    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size

    # Paginate
    products = query.offset(offset).limit(page_size).all()

    # Convert to response models
    items = [
        ProductListResponse.model_validate(product)
        for product in products
    ]

    return ProductListPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get('/print-method/{method}', response_model=List[ProductListResponse])
async def get_products_by_print_method(
    method: str = Path(..., description="Print method: uvdtf, dtf, sublimation, vinyl, other"),
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get products by print method (HOW they're made).

    Valid methods: uvdtf, dtf, sublimation, vinyl, other, digital
    """
    products = db.query(Product).filter(
        Product.print_method == method,
        Product.is_active == True
    ).order_by(
        Product.is_featured.desc(),
        Product.created_at.desc()
    ).offset(offset).limit(limit).all()

    return products


@router.get('/category/{category_name}', response_model=List[ProductListResponse])
async def get_products_by_category(
    category_name: str = Path(..., description="Category: cup_wraps, single_square, single_rectangle, other_custom"),
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get products by category/product type (WHAT they are).

    Valid categories: cup_wraps, single_square, single_rectangle, other_custom
    """
    products = db.query(Product).filter(
        Product.category == category_name,
        Product.is_active == True
    ).order_by(
        Product.is_featured.desc(),
        Product.created_at.desc()
    ).offset(offset).limit(limit).all()

    return products


@router.get('/search', response_model=List[ProductListResponse])
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100, ge=1),
    db: Session = Depends(get_db)
):
    """
    Search products by name or description.

    Returns up to `limit` products matching the search query.
    """
    search_term = f"%{q}%"

    products = db.query(Product).filter(
        Product.is_active == True,
        or_(
            Product.name.ilike(search_term),
            Product.description.ilike(search_term),
            Product.short_description.ilike(search_term)
        )
    ).order_by(
        Product.is_featured.desc(),
        Product.created_at.desc()
    ).limit(limit).all()

    return products


@router.get('/{slug}', response_model=ProductDetailResponse)
async def get_product_by_slug(
    slug: str = Path(..., description="Product slug"),
    db: Session = Depends(get_db)
):
    """
    Get single product by slug.

    Returns full product details including variants.
    """
    product = db.query(Product).filter(
        Product.slug == slug,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.get('/id/{product_id}', response_model=ProductDetailResponse)
async def get_product_by_id(
    product_id: str = Path(..., description="Product UUID"),
    db: Session = Depends(get_db)
):
    """
    Get single product by ID.

    Returns full product details including variants.
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(
        Product.id == product_uuid,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# ============================================================================
# Admin Endpoints (Create, Update, Delete)
# ============================================================================

@router.post('/', response_model=ProductDetailResponse, status_code=201)
async def create_product(
    product_data: ProductCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new product.

    Requires admin authentication (to be implemented).
    """
    # Check if slug already exists
    existing = db.query(Product).filter(Product.slug == product_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product with this slug already exists")

    # Validate enum values
    if product_data.product_type not in [e.value for e in ProductType]:
        raise HTTPException(status_code=400, detail=f"Invalid product_type: {product_data.product_type}")

    if product_data.print_method not in [e.value for e in PrintMethod]:
        raise HTTPException(status_code=400, detail=f"Invalid print_method: {product_data.print_method}")

    if product_data.category not in [e.value for e in ProductCategory]:
        raise HTTPException(status_code=400, detail=f"Invalid category: {product_data.category}")

    # Create product
    product = Product(
        id=uuid.uuid4(),
        **product_data.dict(exclude={'design_id'}),
        design_id=uuid.UUID(product_data.design_id) if product_data.design_id else None
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.put('/{product_id}', response_model=ProductDetailResponse)
async def update_product(
    product_id: str,
    product_data: ProductCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing product.

    Requires admin authentication (to be implemented).
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == product_uuid).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if new slug conflicts with another product
    if product_data.slug != product.slug:
        existing = db.query(Product).filter(
            Product.slug == product_data.slug,
            Product.id != product_uuid
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this slug already exists")

    # Update product fields
    for field, value in product_data.dict(exclude={'design_id'}).items():
        setattr(product, field, value)

    if product_data.design_id:
        product.design_id = uuid.UUID(product_data.design_id)

    db.commit()
    db.refresh(product)

    return product


@router.delete('/{product_id}', status_code=204)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a product (soft delete by setting is_active=False).

    Requires admin authentication (to be implemented).
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == product_uuid).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Soft delete
    product.is_active = False
    db.commit()

    return None
