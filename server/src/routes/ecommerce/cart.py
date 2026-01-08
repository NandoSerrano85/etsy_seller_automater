"""Shopping cart API endpoints for ecommerce storefront."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid

from server.src.database.core import get_db
from server.src.entities.ecommerce.cart import ShoppingCart
from server.src.entities.ecommerce.product import Product, ProductVariant


router = APIRouter(
    prefix='/api/storefront/cart',
    tags=['Storefront - Shopping Cart']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class CartItemRequest(BaseModel):
    """Request model for adding item to cart."""
    product_id: str = Field(..., description="Product UUID")
    variant_id: Optional[str] = Field(None, description="Variant UUID if product has variants")
    quantity: int = Field(1, ge=1, le=100, description="Quantity to add")


class CartItemResponse(BaseModel):
    """Response model for cart item."""
    id: str  # Unique item ID in cart
    product_id: str
    product_name: str
    product_slug: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    price: float
    quantity: int
    subtotal: float
    image: Optional[str] = None


class CartResponse(BaseModel):
    """Response model for shopping cart."""
    id: str
    items: List[CartItemResponse] = []
    subtotal: float = 0
    item_count: int = 0
    created_at: datetime
    updated_at: datetime


class UpdateCartItemRequest(BaseModel):
    """Request model for updating cart item quantity."""
    quantity: int = Field(..., ge=0, le=100, description="New quantity (0 to remove)")


# ============================================================================
# Helper Functions
# ============================================================================

def get_or_create_cart(db: Session, session_id: Optional[str] = None, customer_id: Optional[str] = None) -> ShoppingCart:
    """
    Get existing cart or create a new one.

    Args:
        db: Database session
        session_id: Session ID for guest carts
        customer_id: Customer ID for authenticated users

    Returns:
        ShoppingCart instance
    """
    # Try to find existing active cart
    if customer_id:
        cart = db.query(ShoppingCart).filter(
            ShoppingCart.customer_id == uuid.UUID(customer_id),
            ShoppingCart.is_active == True
        ).first()
    elif session_id:
        cart = db.query(ShoppingCart).filter(
            ShoppingCart.session_id == session_id,
            ShoppingCart.is_active == True
        ).first()
    else:
        # Create new session ID if neither provided
        session_id = str(uuid.uuid4())
        cart = None

    # Create new cart if none exists
    if not cart:
        cart = ShoppingCart(
            id=uuid.uuid4(),
            session_id=session_id,
            customer_id=uuid.UUID(customer_id) if customer_id else None,
            items=[],
            subtotal=0,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


def calculate_cart_totals(cart: ShoppingCart) -> float:
    """
    Calculate cart subtotal from items.

    Args:
        cart: ShoppingCart instance

    Returns:
        Subtotal amount
    """
    if not cart.items:
        return 0.0

    subtotal = sum(item.get('subtotal', 0) for item in cart.items)
    return round(subtotal, 2)


def format_cart_response(cart: ShoppingCart) -> CartResponse:
    """
    Format cart for API response.

    Args:
        cart: ShoppingCart instance

    Returns:
        CartResponse
    """
    items = []
    for item in (cart.items or []):
        items.append(CartItemResponse(
            id=item.get('id'),
            product_id=item.get('product_id'),
            product_name=item.get('product_name'),
            product_slug=item.get('product_slug', ''),
            variant_id=item.get('variant_id'),
            variant_name=item.get('variant_name'),
            price=item.get('price'),
            quantity=item.get('quantity'),
            subtotal=item.get('subtotal'),
            image=item.get('image')
        ))

    return CartResponse(
        id=str(cart.id),
        items=items,
        subtotal=cart.subtotal,
        item_count=len(items),
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get('/', response_model=CartResponse)
async def get_cart(
    x_session_id: Optional[str] = Header(None),
    customer_id: Optional[str] = None,  # TODO: Get from auth token
    db: Session = Depends(get_db)
):
    """
    Get current shopping cart.

    Uses X-Session-ID header for guest carts or customer_id for authenticated users.
    """
    cart = get_or_create_cart(db, session_id=x_session_id, customer_id=customer_id)
    return format_cart_response(cart)


@router.post('/add', response_model=CartResponse)
async def add_to_cart(
    item: CartItemRequest,
    x_session_id: Optional[str] = Header(None),
    customer_id: Optional[str] = None,  # TODO: Get from auth token
    db: Session = Depends(get_db)
):
    """
    Add item to shopping cart.

    If item already exists, increases quantity.
    Creates new cart if none exists.
    """
    # Get or create cart
    cart = get_or_create_cart(db, session_id=x_session_id, customer_id=customer_id)

    # Validate product exists and is active
    try:
        product_uuid = uuid.UUID(item.product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(
        Product.id == product_uuid,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    # Get variant if specified
    variant = None
    variant_name = None
    price = product.price

    if item.variant_id:
        try:
            variant_uuid = uuid.UUID(item.variant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid variant ID format")

        variant = db.query(ProductVariant).filter(
            ProductVariant.id == variant_uuid,
            ProductVariant.product_id == product_uuid,
            ProductVariant.is_active == True
        ).first()

        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found or inactive")

        variant_name = variant.name
        # Use variant price if set, otherwise use product price
        price = variant.price if variant.price else product.price

    # Check if item already exists in cart
    cart_items = cart.items or []
    existing_item = None

    for cart_item in cart_items:
        if (cart_item.get('product_id') == item.product_id and
            cart_item.get('variant_id') == item.variant_id):
            existing_item = cart_item
            break

    if existing_item:
        # Update quantity of existing item
        existing_item['quantity'] += item.quantity
        existing_item['subtotal'] = round(existing_item['quantity'] * existing_item['price'], 2)
    else:
        # Add new item to cart
        new_item = {
            'id': str(uuid.uuid4()),
            'product_id': item.product_id,
            'product_name': product.name,
            'product_slug': product.slug,
            'variant_id': item.variant_id,
            'variant_name': variant_name,
            'price': price,
            'quantity': item.quantity,
            'subtotal': round(price * item.quantity, 2),
            'image': product.featured_image
        }
        cart_items.append(new_item)

    # Update cart
    cart.items = cart_items
    cart.subtotal = calculate_cart_totals(cart)
    cart.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cart)

    return format_cart_response(cart)


@router.put('/update/{item_id}', response_model=CartResponse)
async def update_cart_item(
    item_id: str,
    update: UpdateCartItemRequest,
    x_session_id: Optional[str] = Header(None),
    customer_id: Optional[str] = None,  # TODO: Get from auth token
    db: Session = Depends(get_db)
):
    """
    Update cart item quantity.

    Set quantity to 0 to remove item from cart.
    """
    # Get cart
    cart = get_or_create_cart(db, session_id=x_session_id, customer_id=customer_id)

    # Find item in cart
    cart_items = cart.items or []
    item_found = False

    for i, cart_item in enumerate(cart_items):
        if cart_item.get('id') == item_id:
            item_found = True

            if update.quantity == 0:
                # Remove item
                cart_items.pop(i)
            else:
                # Update quantity
                cart_items[i]['quantity'] = update.quantity
                cart_items[i]['subtotal'] = round(cart_items[i]['price'] * update.quantity, 2)

            break

    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    # Update cart
    cart.items = cart_items
    cart.subtotal = calculate_cart_totals(cart)
    cart.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cart)

    return format_cart_response(cart)


@router.delete('/remove/{item_id}', response_model=CartResponse)
async def remove_from_cart(
    item_id: str,
    x_session_id: Optional[str] = Header(None),
    customer_id: Optional[str] = None,  # TODO: Get from auth token
    db: Session = Depends(get_db)
):
    """
    Remove item from shopping cart.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Get cart
    cart = get_or_create_cart(db, session_id=x_session_id, customer_id=customer_id)

    # Log cart state for debugging
    logger.info(f"Attempting to remove item {item_id} from cart {cart.id}")
    logger.info(f"Cart has {len(cart.items or [])} items")

    # Find and remove item
    cart_items = cart.items or []
    item_found = False

    # Log all cart item IDs for debugging
    cart_item_ids = [item.get('id') for item in cart_items]
    logger.info(f"Cart item IDs: {cart_item_ids}")

    for i, cart_item in enumerate(cart_items):
        if cart_item.get('id') == item_id:
            removed_item = cart_items.pop(i)
            logger.info(f"Removed item: {removed_item.get('product_name')} (id: {item_id})")
            item_found = True
            break

    if not item_found:
        logger.warning(f"Item {item_id} not found in cart. Available IDs: {cart_item_ids}")
        raise HTTPException(
            status_code=404,
            detail=f"Item not found in cart. Item ID: {item_id}"
        )

    # Update cart
    cart.items = cart_items
    cart.subtotal = calculate_cart_totals(cart)
    cart.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cart)

    logger.info(f"Successfully removed item. Cart now has {len(cart_items)} items")
    return format_cart_response(cart)


@router.delete('/clear', response_model=CartResponse)
async def clear_cart(
    x_session_id: Optional[str] = Header(None),
    customer_id: Optional[str] = None,  # TODO: Get from auth token
    db: Session = Depends(get_db)
):
    """
    Clear all items from shopping cart.
    """
    # Get cart
    cart = get_or_create_cart(db, session_id=x_session_id, customer_id=customer_id)

    # Clear items
    cart.items = []
    cart.subtotal = 0
    cart.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cart)

    return format_cart_response(cart)
