"""Admin Customer API endpoints for CraftFlow Commerce management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
import uuid

from server.src.database.core import get_db
from server.src.entities.ecommerce.customer import Customer
from server.src.entities.ecommerce.order import Order
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.entities.user import User


router = APIRouter(
    prefix='/api/ecommerce/admin/customers',
    tags=['Ecommerce Admin - Customers']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class CustomerResponse(BaseModel):
    """Customer response model for admin."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    accepts_marketing: bool = False
    is_subscribed: bool = False
    is_active: bool = True
    email_verified: bool = False
    total_spent: float = 0
    total_orders: int = 0
    order_count: int = 0
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Paginated customer list response."""
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get('/', response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of customers for admin management.
    """
    query = db.query(Customer)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.email.ilike(search_term),
                Customer.first_name.ilike(search_term),
                Customer.last_name.ilike(search_term)
            )
        )

    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)

    # Get total count
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    customers = query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size).all()

    # Convert to response
    items = []
    for customer in customers:
        # Get order count and total spent from orders
        order_stats = db.query(
            func.count(Order.id).label('order_count'),
            func.coalesce(func.sum(Order.total), 0).label('total_spent')
        ).filter(
            Order.customer_id == customer.id
        ).first()

        items.append(CustomerResponse(
            id=str(customer.id),
            email=customer.email,
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone=customer.phone,
            accepts_marketing=customer.accepts_marketing or False,
            is_subscribed=customer.accepts_marketing or False,
            is_active=customer.is_active,
            email_verified=customer.email_verified or False,
            total_spent=float(order_stats.total_spent) if order_stats else 0,
            total_orders=order_stats.order_count if order_stats else 0,
            order_count=order_stats.order_count if order_stats else 0,
            created_at=customer.created_at.isoformat() if customer.created_at else None,
            last_login=customer.last_login.isoformat() if customer.last_login else None
        ))

    total_pages = (total + page_size - 1) // page_size

    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get('/{customer_id}', response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single customer by ID."""
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

    customer = db.query(Customer).filter(Customer.id == customer_uuid).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get order stats
    order_stats = db.query(
        func.count(Order.id).label('order_count'),
        func.coalesce(func.sum(Order.total), 0).label('total_spent')
    ).filter(
        Order.customer_id == customer.id
    ).first()

    return CustomerResponse(
        id=str(customer.id),
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone=customer.phone,
        accepts_marketing=customer.accepts_marketing or False,
        is_subscribed=customer.accepts_marketing or False,
        is_active=customer.is_active,
        email_verified=customer.email_verified or False,
        total_spent=float(order_stats.total_spent) if order_stats else 0,
        total_orders=order_stats.order_count if order_stats else 0,
        order_count=order_stats.order_count if order_stats else 0,
        created_at=customer.created_at.isoformat() if customer.created_at else None,
        last_login=customer.last_login.isoformat() if customer.last_login else None
    )
