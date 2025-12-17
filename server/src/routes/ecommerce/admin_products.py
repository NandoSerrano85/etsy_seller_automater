"""Admin Product API endpoints for CraftFlow Commerce management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from server.src.database.core import get_db
from server.src.entities.ecommerce.product import Product, ProductType, PrintMethod, ProductCategory
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.routes.auth.plan_access import require_pro_plan
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/admin/products',
    tags=['Ecommerce Admin - Products']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class ProductResponse(BaseModel):
    """Product response model for admin."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    product_type: str
    print_method: str
    category: str
    price: float
    compare_at_price: Optional[float] = None
    cost: Optional[float] = None
    track_inventory: bool
    inventory_quantity: int
    allow_backorder: bool
    digital_file_url: Optional[str] = None
    images: Optional[List[str]] = []
    featured_image: Optional[str] = None
    is_active: bool
    is_featured: bool
    design_id: Optional[str] = None
    template_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductCreateRequest(BaseModel):
    """Product creation/update request."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    product_type: str
    print_method: str
    category: str
    price: float = Field(..., gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, ge=0)
    track_inventory: bool = False
    inventory_quantity: int = Field(0, ge=0)
    allow_backorder: bool = False
    digital_file_url: Optional[str] = None
    images: Optional[List[str]] = []
    featured_image: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    design_id: Optional[str] = None
    template_name: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get('/', response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    print_method: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Get paginated list of products for admin management.

    Requires: Pro plan or higher
    """
    # Filter by current user's products only (data isolation)
    query = db.query(Product).filter(Product.user_id == current_user.id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.slug.ilike(search_term)
            )
        )

    if print_method:
        query = query.filter(Product.print_method == print_method)

    if category:
        query = query.filter(Product.category == category)

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    # Get total count
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()

    # Convert to response
    items = []
    for product in products:
        items.append(ProductResponse(
            id=str(product.id),
            name=product.name,
            slug=product.slug,
            description=product.description,
            short_description=product.short_description,
            product_type=product.product_type,
            print_method=product.print_method,
            category=product.category,
            price=product.price,
            compare_at_price=product.compare_at_price,
            cost=product.cost,
            track_inventory=product.track_inventory,
            inventory_quantity=product.inventory_quantity,
            allow_backorder=product.allow_backorder,
            digital_file_url=product.digital_file_url,
            images=product.images or [],
            featured_image=product.featured_image,
            is_active=product.is_active,
            is_featured=product.is_featured,
            design_id=str(product.design_id) if product.design_id else None,
            template_name=product.template_name,
            created_at=product.created_at.isoformat() if product.created_at else None,
            updated_at=product.updated_at.isoformat() if product.updated_at else None
        ))

    total_pages = (total + page_size - 1) // page_size

    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get('/{product_id}', response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Get single product by ID.

    Requires: Pro plan or higher
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    # Filter by user_id for data isolation
    product = db.query(Product).filter(
        Product.id == product_uuid,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        product_type=product.product_type,
        print_method=product.print_method,
        category=product.category,
        price=product.price,
        compare_at_price=product.compare_at_price,
        cost=product.cost,
        track_inventory=product.track_inventory,
        inventory_quantity=product.inventory_quantity,
        allow_backorder=product.allow_backorder,
        digital_file_url=product.digital_file_url,
        images=product.images or [],
        featured_image=product.featured_image,
        is_active=product.is_active,
        is_featured=product.is_featured,
        design_id=str(product.design_id) if product.design_id else None,
        template_name=product.template_name,
        created_at=product.created_at.isoformat() if product.created_at else None,
        updated_at=product.updated_at.isoformat() if product.updated_at else None
    )


@router.post('/', response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Create a new product.

    Requires: Pro plan or higher
    """
    # Check if slug already exists for this user
    existing = db.query(Product).filter(
        Product.slug == product_data.slug,
        Product.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product with this slug already exists")

    # Validate enum values
    if product_data.product_type not in [e.value for e in ProductType]:
        raise HTTPException(status_code=400, detail=f"Invalid product_type: {product_data.product_type}")

    if product_data.print_method not in [e.value for e in PrintMethod]:
        raise HTTPException(status_code=400, detail=f"Invalid print_method: {product_data.print_method}")

    if product_data.category not in [e.value for e in ProductCategory]:
        raise HTTPException(status_code=400, detail=f"Invalid category: {product_data.category}")

    # Create product with user_id for isolation
    product = Product(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=product_data.name,
        slug=product_data.slug,
        description=product_data.description,
        short_description=product_data.short_description,
        product_type=product_data.product_type,
        print_method=product_data.print_method,
        category=product_data.category,
        price=product_data.price,
        compare_at_price=product_data.compare_at_price,
        cost=product_data.cost,
        track_inventory=product_data.track_inventory,
        inventory_quantity=product_data.inventory_quantity,
        allow_backorder=product_data.allow_backorder,
        digital_file_url=product_data.digital_file_url,
        images=product_data.images,
        featured_image=product_data.featured_image,
        is_active=product_data.is_active,
        is_featured=product_data.is_featured,
        design_id=uuid.UUID(product_data.design_id) if product_data.design_id else None,
        template_name=product_data.template_name
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return ProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        product_type=product.product_type,
        print_method=product.print_method,
        category=product.category,
        price=product.price,
        compare_at_price=product.compare_at_price,
        cost=product.cost,
        track_inventory=product.track_inventory,
        inventory_quantity=product.inventory_quantity,
        allow_backorder=product.allow_backorder,
        digital_file_url=product.digital_file_url,
        images=product.images or [],
        featured_image=product.featured_image,
        is_active=product.is_active,
        is_featured=product.is_featured,
        design_id=str(product.design_id) if product.design_id else None,
        template_name=product.template_name,
        created_at=product.created_at.isoformat() if product.created_at else None,
        updated_at=product.updated_at.isoformat() if product.updated_at else None
    )


@router.put('/{product_id}', response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Update an existing product.

    Requires: Pro plan or higher
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    # Filter by user_id for data isolation
    product = db.query(Product).filter(
        Product.id == product_uuid,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if new slug conflicts with another product
    if product_data.slug != product.slug:
        existing = db.query(Product).filter(
            Product.slug == product_data.slug,
            Product.user_id == current_user.id,
            Product.id != product_uuid
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this slug already exists")

    # Update product fields
    product.name = product_data.name
    product.slug = product_data.slug
    product.description = product_data.description
    product.short_description = product_data.short_description
    product.product_type = product_data.product_type
    product.print_method = product_data.print_method
    product.category = product_data.category
    product.price = product_data.price
    product.compare_at_price = product_data.compare_at_price
    product.cost = product_data.cost
    product.track_inventory = product_data.track_inventory
    product.inventory_quantity = product_data.inventory_quantity
    product.allow_backorder = product_data.allow_backorder
    product.digital_file_url = product_data.digital_file_url
    product.images = product_data.images
    product.featured_image = product_data.featured_image
    product.is_active = product_data.is_active
    product.is_featured = product_data.is_featured
    product.template_name = product_data.template_name

    if product_data.design_id:
        product.design_id = uuid.UUID(product_data.design_id)
    else:
        product.design_id = None

    db.commit()
    db.refresh(product)

    return ProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        product_type=product.product_type,
        print_method=product.print_method,
        category=product.category,
        price=product.price,
        compare_at_price=product.compare_at_price,
        cost=product.cost,
        track_inventory=product.track_inventory,
        inventory_quantity=product.inventory_quantity,
        allow_backorder=product.allow_backorder,
        digital_file_url=product.digital_file_url,
        images=product.images or [],
        featured_image=product.featured_image,
        is_active=product.is_active,
        is_featured=product.is_featured,
        design_id=str(product.design_id) if product.design_id else None,
        template_name=product.template_name,
        created_at=product.created_at.isoformat() if product.created_at else None,
        updated_at=product.updated_at.isoformat() if product.updated_at else None
    )


@router.delete('/{product_id}', status_code=204)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Delete a product permanently.

    Requires: Pro plan or higher
    """
    try:
        product_uuid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    # Filter by user_id for data isolation
    product = db.query(Product).filter(
        Product.id == product_uuid,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    return None
