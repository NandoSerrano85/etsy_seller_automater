"""Admin Order API endpoints for CraftFlow Commerce management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import os
import io
import requests
import logging

from server.src.database.core import get_db
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.routes.auth.plan_access import require_pro_plan
from server.src.entities.user import User
from server.src.services.shippo_service import ShippoService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/api/ecommerce/admin/orders',
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


class ShippingRateResponse(BaseModel):
    """Shipping rate response."""
    carrier: str
    service: str
    service_level: str
    amount: float
    currency: str
    estimated_days: Optional[int] = None
    duration_terms: str
    rate_id: str
    is_fallback: bool = False


class CreateLabelRequest(BaseModel):
    """Request to create a shipping label."""
    rate_id: str = Field(..., description="Shippo rate ID from get_shipping_rates")
    label_file_type: str = Field("PDF", description="Label format: PDF, PNG, etc.")


class CreateLabelResponse(BaseModel):
    """Shipping label creation response."""
    order_id: str
    order_number: str
    transaction_id: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    label_url: Optional[str] = None
    carrier: Optional[str] = None
    service: Optional[str] = None
    status: str


class BatchLabelRequest(BaseModel):
    """Request to create shipping labels for multiple orders."""
    order_ids: List[str] = Field(..., description="List of order IDs to create labels for")
    carrier: str = Field("USPS", description="Preferred carrier")
    service_level: str = Field("usps_priority", description="Service level")
    label_file_type: str = Field("PDF", description="Label format: PDF, PNG, etc.")


class BatchLabelResponse(BaseModel):
    """Batch label creation response."""
    success_count: int
    failed_count: int
    labels: List[CreateLabelResponse]
    errors: List[dict] = []


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
    current_user: User = Depends(require_pro_plan)
):
    """
    Get paginated list of orders for admin management.

    Requires: Pro plan or higher
    """
    # Filter by current user's orders only (data isolation)
    query = db.query(Order).filter(Order.user_id == current_user.id)

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
    current_user: User = Depends(require_pro_plan)
):
    """
    Get single order by ID.

    Requires: Pro plan or higher
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Filter by user_id for data isolation
    order = db.query(Order).filter(
        Order.id == order_uuid,
        Order.user_id == current_user.id
    ).first()

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
    current_user: User = Depends(require_pro_plan)
):
    """
    Update order status and tracking information.

    Requires: Pro plan or higher
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Filter by user_id for data isolation
    order = db.query(Order).filter(
        Order.id == order_uuid,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Track if tracking info was just added
    tracking_was_added = (
        order_data.tracking_number is not None and
        not order.tracking_number and
        order_data.fulfillment_status == 'shipped'
    )

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

    # Send shipping notification email if tracking was just added
    if tracking_was_added:
        try:
            from server.src.services.email_service import EmailService
            from server.src.entities.ecommerce.email_template import EmailTemplate
            import logging

            # Get active shipping notification template
            email_template = db.query(EmailTemplate).filter(
                EmailTemplate.user_id == current_user.id,
                EmailTemplate.email_type == "shipping_notification",
                EmailTemplate.is_active == True
            ).first()

            if email_template and os.getenv("ENABLE_EMAIL_SERVICE", "false").lower() == "true":
                email_service = EmailService(db=db)

                # Get recipient email
                recipient = None
                if order.guest_email:
                    recipient = order.guest_email
                elif order.customer:
                    from server.src.entities.ecommerce.customer import Customer
                    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                    if customer:
                        recipient = customer.email

                if recipient and order.tracking_number:
                    email_service.send_shipping_notification(
                        user_id=current_user.id,
                        order=order,
                        tracking_number=order.tracking_number,
                        tracking_url=order.tracking_url or "",
                        recipient_email=recipient
                    )
                    logging.info(f"Shipping notification sent to {recipient} for order {order.order_number}")
        except Exception as e:
            # Don't block order update if email fails
            import logging
            logging.error(f"Failed to send shipping notification email: {e}")

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

# ============================================================================
# Shipping Label Endpoints
# ============================================================================

@router.get('/{order_id}/shipping-rates', response_model=List[ShippingRateResponse])
async def get_order_shipping_rates(
    order_id: str,
    length: float = Query(10, ge=0.1, le=100, description="Package length in inches"),
    width: float = Query(8, ge=0.1, le=100, description="Package width in inches"),
    height: float = Query(4, ge=0.1, le=100, description="Package height in inches"),
    weight: float = Query(1, ge=0.1, le=150, description="Package weight in pounds"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Get available shipping rates for an order with custom package dimensions.

    Requires: Pro plan or higher

    Query Parameters:
    - length: Package length in inches (default: 10)
    - width: Package width in inches (default: 8)
    - height: Package height in inches (default: 4)
    - weight: Package weight in pounds (default: 1)
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Get order with user isolation
    order = db.query(Order).filter(
        Order.id == order_uuid,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.shipping_address:
        raise HTTPException(status_code=400, detail="Order has no shipping address")

    # Format address for Shippo
    shipping_addr = order.shipping_address
    to_address = {
        'name': f"{shipping_addr.get('first_name', '')} {shipping_addr.get('last_name', '')}".strip(),
        'street1': shipping_addr.get('address1', ''),
        'street2': shipping_addr.get('address2', ''),
        'city': shipping_addr.get('city', ''),
        'state': shipping_addr.get('state', ''),
        'zip': shipping_addr.get('zip_code', ''),
        'country': 'US',
        'phone': shipping_addr.get('phone', ''),
    }

    # Custom parcel dimensions from request
    parcel = {
        'length': str(length),
        'width': str(width),
        'height': str(height),
        'distance_unit': 'in',
        'weight': str(weight),
        'mass_unit': 'lb'
    }

    # Get rates from Shippo with custom parcel
    shippo = ShippoService()
    rates = shippo.get_shipping_rates(to_address, parcel=parcel)

    return [
        ShippingRateResponse(
            carrier=rate.get('carrier', 'Unknown'),
            service=rate.get('service', 'Standard'),
            service_level=rate.get('service_level', ''),
            amount=rate.get('amount', 0),
            currency=rate.get('currency', 'USD'),
            estimated_days=rate.get('estimated_days'),
            duration_terms=rate.get('duration_terms', ''),
            rate_id=rate.get('rate_id', ''),
            is_fallback=rate.get('is_fallback', False)
        )
        for rate in rates
    ]


@router.post('/{order_id}/create-label', response_model=CreateLabelResponse)
async def create_shipping_label(
    order_id: str,
    label_request: CreateLabelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Create a shipping label for an order.

    Requires: Pro plan or higher
    """
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")

    # Get order with user isolation
    order = db.query(Order).filter(
        Order.id == order_uuid,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if order already has tracking
    if order.tracking_number:
        raise HTTPException(
            status_code=400,
            detail=f"Order already has tracking number: {order.tracking_number}"
        )

    # Check for fallback rate (can't create labels with fallback rates)
    if label_request.rate_id.startswith('fallback_'):
        raise HTTPException(
            status_code=400,
            detail="Cannot create label with fallback rates. Please configure Shippo API key."
        )

    try:
        # Create label via Shippo
        shippo = ShippoService()
        label_result = shippo.create_shipping_label(
            rate_id=label_request.rate_id,
            label_file_type=label_request.label_file_type
        )

        # Update order with tracking info
        order.tracking_number = label_result.get('tracking_number')
        order.tracking_url = label_result.get('tracking_url')
        order.fulfillment_status = 'shipped'
        order.shipped_at = datetime.utcnow()
        order.status = 'shipped'
        db.commit()

        logger.info(f"Created shipping label for order {order.order_number}: {label_result.get('tracking_number')}")

        return CreateLabelResponse(
            order_id=str(order.id),
            order_number=order.order_number,
            transaction_id=label_result.get('transaction_id'),
            tracking_number=label_result.get('tracking_number'),
            tracking_url=label_result.get('tracking_url'),
            label_url=label_result.get('label_url'),
            carrier=label_result.get('carrier'),
            service=label_result.get('service'),
            status='SUCCESS'
        )

    except Exception as e:
        logger.error(f"Failed to create shipping label for order {order.order_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create label: {str(e)}")


@router.post('/batch-labels', response_model=BatchLabelResponse)
async def create_batch_labels(
    batch_request: BatchLabelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Create shipping labels for multiple orders.

    Requires: Pro plan or higher
    """
    shippo = ShippoService()
    if not shippo.enabled:
        raise HTTPException(
            status_code=400,
            detail="Shippo is not configured. Please set SHIPPO_API_KEY."
        )

    labels = []
    errors = []
    success_count = 0
    failed_count = 0

    for order_id in batch_request.order_ids:
        try:
            order_uuid = uuid.UUID(order_id)
        except ValueError:
            errors.append({'order_id': order_id, 'error': 'Invalid order ID format'})
            failed_count += 1
            continue

        # Get order with user isolation
        order = db.query(Order).filter(
            Order.id == order_uuid,
            Order.user_id == current_user.id
        ).first()

        if not order:
            errors.append({'order_id': order_id, 'error': 'Order not found'})
            failed_count += 1
            continue

        if order.tracking_number:
            errors.append({
                'order_id': order_id,
                'order_number': order.order_number,
                'error': f'Already has tracking: {order.tracking_number}'
            })
            failed_count += 1
            continue

        if not order.shipping_address:
            errors.append({
                'order_id': order_id,
                'order_number': order.order_number,
                'error': 'No shipping address'
            })
            failed_count += 1
            continue

        try:
            # Get shipping rates first
            shipping_addr = order.shipping_address
            to_address = {
                'name': f"{shipping_addr.get('first_name', '')} {shipping_addr.get('last_name', '')}".strip(),
                'street1': shipping_addr.get('address1', ''),
                'street2': shipping_addr.get('address2', ''),
                'city': shipping_addr.get('city', ''),
                'state': shipping_addr.get('state', ''),
                'zip': shipping_addr.get('zip_code', ''),
                'country': 'US',
                'phone': shipping_addr.get('phone', ''),
            }

            rates = shippo.get_shipping_rates(to_address)

            # Find matching rate by carrier and service level
            matching_rate = None
            for rate in rates:
                if (rate.get('carrier', '').upper() == batch_request.carrier.upper() and
                    rate.get('service_level', '') == batch_request.service_level):
                    matching_rate = rate
                    break

            # If no exact match, use first rate from preferred carrier
            if not matching_rate:
                for rate in rates:
                    if rate.get('carrier', '').upper() == batch_request.carrier.upper():
                        matching_rate = rate
                        break

            # If still no match, use cheapest rate
            if not matching_rate and rates:
                matching_rate = rates[0]

            if not matching_rate or matching_rate.get('is_fallback'):
                errors.append({
                    'order_id': order_id,
                    'order_number': order.order_number,
                    'error': 'No valid shipping rate available'
                })
                failed_count += 1
                continue

            # Create label
            label_result = shippo.create_shipping_label(
                rate_id=matching_rate.get('rate_id'),
                label_file_type=batch_request.label_file_type
            )

            # Update order
            order.tracking_number = label_result.get('tracking_number')
            order.tracking_url = label_result.get('tracking_url')
            order.fulfillment_status = 'shipped'
            order.shipped_at = datetime.utcnow()
            order.status = 'shipped'
            db.commit()

            labels.append(CreateLabelResponse(
                order_id=str(order.id),
                order_number=order.order_number,
                transaction_id=label_result.get('transaction_id'),
                tracking_number=label_result.get('tracking_number'),
                tracking_url=label_result.get('tracking_url'),
                label_url=label_result.get('label_url'),
                carrier=label_result.get('carrier'),
                service=label_result.get('service'),
                status='SUCCESS'
            ))
            success_count += 1

            logger.info(f"Batch label created for order {order.order_number}: {label_result.get('tracking_number')}")

        except Exception as e:
            logger.error(f"Failed to create batch label for order {order.order_number}: {e}")
            errors.append({
                'order_id': order_id,
                'order_number': order.order_number,
                'error': str(e)
            })
            failed_count += 1

    return BatchLabelResponse(
        success_count=success_count,
        failed_count=failed_count,
        labels=labels,
        errors=errors
    )
