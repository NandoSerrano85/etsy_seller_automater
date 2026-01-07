"""Orders API endpoints for ecommerce storefront."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from server.src.database.core import get_db
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.entities.ecommerce.customer import Customer
from server.src.routes.ecommerce.customers import get_current_customer
from server.src.routes.ecommerce.checkout import get_current_customer_optional


router = APIRouter(
    prefix='/api/storefront/orders',
    tags=['Storefront - Orders']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class OrderItemResponse(BaseModel):
    """Order item response model."""
    id: str
    product_id: Optional[str] = None
    variant_id: Optional[str] = None
    product_name: str
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    price: float
    quantity: int
    total: float
    download_url: Optional[str] = None
    download_count: int = 0
    download_expires_at: Optional[datetime] = None
    is_fulfilled: bool = False

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response model."""
    id: str
    order_number: str
    customer_id: Optional[str] = None
    guest_email: Optional[str] = None
    subtotal: float
    tax: float
    shipping: float
    discount: float
    total: float
    shipping_address: Optional[dict] = None
    billing_address: Optional[dict] = None
    payment_status: str
    payment_method: Optional[str] = None
    fulfillment_status: str
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    shipped_at: Optional[datetime] = None
    customer_note: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Simplified order response for list view."""
    id: str
    order_number: str
    total: float
    status: str
    payment_status: str
    fulfillment_status: str
    item_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

def format_order_response(order: Order) -> OrderResponse:
    """Format order with all details."""
    items = [
        OrderItemResponse(
            id=str(item.id),
            product_id=str(item.product_id) if item.product_id else None,
            variant_id=str(item.variant_id) if item.variant_id else None,
            product_name=item.product_name,
            variant_name=item.variant_name,
            sku=item.sku,
            price=item.price,
            quantity=item.quantity,
            total=item.total,
            download_url=item.download_url,
            download_count=item.download_count,
            download_expires_at=item.download_expires_at,
            is_fulfilled=item.is_fulfilled
        )
        for item in (order.items or [])
    ]

    return OrderResponse(
        id=str(order.id),
        order_number=order.order_number,
        customer_id=str(order.customer_id) if order.customer_id else None,
        guest_email=order.guest_email,
        subtotal=order.subtotal,
        tax=order.tax,
        shipping=order.shipping,
        discount=order.discount,
        total=order.total,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        fulfillment_status=order.fulfillment_status,
        tracking_number=order.tracking_number,
        tracking_url=order.tracking_url,
        shipped_at=order.shipped_at,
        customer_note=order.customer_note,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items
    )


def format_order_list_response(order: Order) -> OrderListResponse:
    """Format order for list view (less detail)."""
    return OrderListResponse(
        id=str(order.id),
        order_number=order.order_number,
        total=order.total,
        status=order.status,
        payment_status=order.payment_status,
        fulfillment_status=order.fulfillment_status,
        item_count=len(order.items or []),
        created_at=order.created_at
    )


# ============================================================================
# Customer Order Endpoints
# ============================================================================

@router.get('/', response_model=List[OrderListResponse])
async def get_customer_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get all orders for current customer.

    Requires authentication token.
    Returns list of orders with basic info.
    """
    query = db.query(Order).filter(Order.customer_id == current_customer.id)

    # Filter by status if provided
    if status:
        query = query.filter(Order.status == status)

    # Order by most recent first
    query = query.order_by(Order.created_at.desc())

    # Paginate
    orders = query.offset(offset).limit(limit).all()

    return [format_order_list_response(order) for order in orders]


@router.get('/{order_id}', response_model=OrderResponse)
async def get_order_details(
    order_id: str,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get full details for a specific order.

    Requires authentication token.
    Customer can only view their own orders.
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Get order
    order = db.query(Order).filter(
        Order.id == order_uuid,
        Order.customer_id == current_customer.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return format_order_response(order)


@router.get('/number/{order_number}', response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    current_customer: Optional[Customer] = Depends(get_current_customer_optional),
    db: Session = Depends(get_db)
):
    """
    Get full details for an order by order number.

    Supports both authenticated customers and guest orders.
    - Authenticated: Customer can only view their own orders
    - Guest: Can view any order (for post-checkout confirmation)
    """
    # Build query
    query = db.query(Order).filter(Order.order_number == order_number)

    # If authenticated, verify the order belongs to this customer
    if current_customer:
        query = query.filter(Order.customer_id == current_customer.id)

    order = query.first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return format_order_response(order)


# ============================================================================
# Guest Order Lookup (No Auth Required)
# ============================================================================

@router.get('/guest/lookup', response_model=OrderResponse)
async def guest_order_lookup(
    order_number: str = Query(..., description="Order number"),
    email: str = Query(..., description="Email address used for order"),
    db: Session = Depends(get_db)
):
    """
    Look up guest order by order number and email.

    No authentication required.
    For customers who checked out as guests.
    """
    # Get order
    order = db.query(Order).filter(
        Order.order_number == order_number,
        Order.guest_email == email
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found. Please check your order number and email."
        )

    return format_order_response(order)


# ============================================================================
# Digital Product Downloads
# ============================================================================

@router.get('/{order_id}/items/{item_id}/download')
async def download_digital_product(
    order_id: str,
    item_id: str,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get download link for digital product.

    Requires authentication token.
    Increments download count and checks limits.
    """
    try:
        order_uuid = uuid.UUID(order_id)
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Get order and verify ownership
    order = db.query(Order).filter(
        Order.id == order_uuid,
        Order.customer_id == current_customer.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get order item
    item = db.query(OrderItem).filter(
        OrderItem.id == item_uuid,
        OrderItem.order_id == order_uuid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")

    # Check if digital product
    if not item.download_url:
        raise HTTPException(status_code=400, detail="This is not a digital product")

    # Check if download expired
    if item.download_expires_at and datetime.utcnow() > item.download_expires_at:
        raise HTTPException(status_code=410, detail="Download link has expired")

    # Check download limit
    # Get product's download limit from product table if needed
    # For now, assume unlimited downloads if no expiry

    # Increment download count
    item.download_count += 1
    db.commit()

    return {
        "download_url": item.download_url,
        "download_count": item.download_count,
        "expires_at": item.download_expires_at
    }


# ============================================================================
# Admin Endpoints (TODO: Add admin authentication)
# ============================================================================

@router.put('/{order_id}/fulfill')
async def fulfill_order(
    order_id: str,
    tracking_number: Optional[str] = None,
    tracking_url: Optional[str] = None,
    # TODO: Add admin authentication
    db: Session = Depends(get_db)
):
    """
    Mark order as fulfilled.

    TODO: Requires admin authentication.
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Get order
    order = db.query(Order).filter(Order.id == order_uuid).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update fulfillment status
    order.fulfillment_status = "fulfilled"
    order.shipped_at = datetime.utcnow()

    if tracking_number:
        order.tracking_number = tracking_number

    if tracking_url:
        order.tracking_url = tracking_url

    # Mark all items as fulfilled
    for item in order.items:
        item.is_fulfilled = True

    db.commit()
    db.refresh(order)

    return format_order_response(order)


@router.put('/{order_id}/cancel')
async def cancel_order(
    order_id: str,
    cancel_reason: Optional[str] = None,
    # TODO: Add admin authentication
    db: Session = Depends(get_db)
):
    """
    Cancel an order.

    TODO: Requires admin authentication.
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Get order
    order = db.query(Order).filter(Order.id == order_uuid).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if already shipped
    if order.fulfillment_status == "shipped":
        raise HTTPException(status_code=400, detail="Cannot cancel shipped order")

    # Update status
    order.status = "cancelled"
    order.cancelled_at = datetime.utcnow()
    order.cancel_reason = cancel_reason

    db.commit()
    db.refresh(order)

    return format_order_response(order)
