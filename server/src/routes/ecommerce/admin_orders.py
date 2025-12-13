"""Admin Order API endpoints for CraftFlow Commerce management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from server.src.database.core import get_db
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/orders',
    tags=['Ecommerce Admin - Orders']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class OrderItemResponse(BaseModel):
    """Order item response model."""
    id: str
    product_id: Optional[str] = None
    product_name: str
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    price: float
    quantity: int
    total: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response model for admin."""
    id: str
    order_number: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    guest_email: Optional[str] = None
    subtotal: float
    tax: float
    shipping: float
    discount: float
    total: float
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    fulfillment_status: Optional[str] = None
    tracking_number: Optional[str] = None
    status: str
    items: Optional[List[OrderItemResponse]] = []
    shipping_address: Optional[dict] = None
    billing_address: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Paginated order list response."""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrderUpdateRequest(BaseModel):
    """Order update request."""
    status: Optional[str] = None
    payment_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    internal_note: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get('/', response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of orders for admin management.
    """
    query = db.query(Order)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Order.order_number.ilike(search_term),
                Order.guest_email.ilike(search_term)
            )
        )

    if status:
        query = query.filter(Order.status == status)

    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    # Get total count
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()

    # Convert to response
    items = []
    for order in orders:
        # Get customer name from shipping address or customer
        customer_name = None
        if order.shipping_address and isinstance(order.shipping_address, dict):
            first_name = order.shipping_address.get('first_name', '')
            last_name = order.shipping_address.get('last_name', '')
            customer_name = f"{first_name} {last_name}".strip()

        # Get order items
        order_items = []
        items_query = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items_query:
            order_items.append(OrderItemResponse(
                id=str(item.id),
                product_id=str(item.product_id) if item.product_id else None,
                product_name=item.product_name or '',
                variant_name=item.variant_name,
                sku=item.sku,
                price=item.price,
                quantity=item.quantity,
                total=item.total
            ))

        items.append(OrderResponse(
            id=str(order.id),
            order_number=order.order_number,
            customer_id=str(order.customer_id) if order.customer_id else None,
            customer_name=customer_name,
            customer_email=order.guest_email,
            guest_email=order.guest_email,
            subtotal=order.subtotal,
            tax=order.tax or 0,
            shipping=order.shipping or 0,
            discount=order.discount or 0,
            total=order.total,
            payment_status=order.payment_status,
            payment_method=order.payment_method,
            fulfillment_status=order.fulfillment_status,
            tracking_number=order.tracking_number,
            status=order.status,
            items=order_items,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            created_at=order.created_at.isoformat() if order.created_at else None,
            updated_at=order.updated_at.isoformat() if order.updated_at else None
        ))

    total_pages = (total + page_size - 1) // page_size

    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get('/{order_id}', response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single order by ID."""
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    order = db.query(Order).filter(Order.id == order_uuid).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get customer name from shipping address
    customer_name = None
    if order.shipping_address and isinstance(order.shipping_address, dict):
        first_name = order.shipping_address.get('first_name', '')
        last_name = order.shipping_address.get('last_name', '')
        customer_name = f"{first_name} {last_name}".strip()

    # Get order items
    order_items = []
    items_query = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items_query:
        order_items.append(OrderItemResponse(
            id=str(item.id),
            product_id=str(item.product_id) if item.product_id else None,
            product_name=item.product_name or '',
            variant_name=item.variant_name,
            sku=item.sku,
            price=item.price,
            quantity=item.quantity,
            total=item.total
        ))

    return OrderResponse(
        id=str(order.id),
        order_number=order.order_number,
        customer_id=str(order.customer_id) if order.customer_id else None,
        customer_name=customer_name,
        customer_email=order.guest_email,
        guest_email=order.guest_email,
        subtotal=order.subtotal,
        tax=order.tax or 0,
        shipping=order.shipping or 0,
        discount=order.discount or 0,
        total=order.total,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        fulfillment_status=order.fulfillment_status,
        tracking_number=order.tracking_number,
        status=order.status,
        items=order_items,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        created_at=order.created_at.isoformat() if order.created_at else None,
        updated_at=order.updated_at.isoformat() if order.updated_at else None
    )


@router.put('/{order_id}', response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_data: OrderUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update order status and tracking information."""
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    order = db.query(Order).filter(Order.id == order_uuid).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update fields
    if order_data.status is not None:
        order.status = order_data.status

    if order_data.payment_status is not None:
        order.payment_status = order_data.payment_status

    if order_data.fulfillment_status is not None:
        order.fulfillment_status = order_data.fulfillment_status
        if order_data.fulfillment_status == 'shipped':
            order.shipped_at = datetime.utcnow()

    if order_data.tracking_number is not None:
        order.tracking_number = order_data.tracking_number

    if order_data.tracking_url is not None:
        order.tracking_url = order_data.tracking_url

    if order_data.internal_note is not None:
        order.internal_note = order_data.internal_note

    db.commit()
    db.refresh(order)

    # Get customer name and items for response
    customer_name = None
    if order.shipping_address and isinstance(order.shipping_address, dict):
        first_name = order.shipping_address.get('first_name', '')
        last_name = order.shipping_address.get('last_name', '')
        customer_name = f"{first_name} {last_name}".strip()

    order_items = []
    items_query = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items_query:
        order_items.append(OrderItemResponse(
            id=str(item.id),
            product_id=str(item.product_id) if item.product_id else None,
            product_name=item.product_name or '',
            variant_name=item.variant_name,
            sku=item.sku,
            price=item.price,
            quantity=item.quantity,
            total=item.total
        ))

    return OrderResponse(
        id=str(order.id),
        order_number=order.order_number,
        customer_id=str(order.customer_id) if order.customer_id else None,
        customer_name=customer_name,
        customer_email=order.guest_email,
        guest_email=order.guest_email,
        subtotal=order.subtotal,
        tax=order.tax or 0,
        shipping=order.shipping or 0,
        discount=order.discount or 0,
        total=order.total,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        fulfillment_status=order.fulfillment_status,
        tracking_number=order.tracking_number,
        status=order.status,
        items=order_items,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        created_at=order.created_at.isoformat() if order.created_at else None,
        updated_at=order.updated_at.isoformat() if order.updated_at else None
    )
