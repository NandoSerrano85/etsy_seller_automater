"""Checkout and payment processing for ecommerce storefront."""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import uuid
import os
import logging

from server.src.database.core import get_db
from server.src.entities.ecommerce.cart import ShoppingCart
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.entities.ecommerce.customer import Customer
from server.src.entities.ecommerce.product import Product, ProductVariant
from server.src.entities.ecommerce.storefront_settings import StorefrontSettings
from server.src.entities.user import User
from server.src.services.shippo_service import shippo_service

# Stripe SDK - Install with: pip install stripe
try:
    import stripe
    stripe.api_key = os.getenv('STRIPE_API_KEY', os.getenv('STRIPE_SECRET_KEY'))
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    STRIPE_PUBLIC_KEY = None
    logging.warning("Stripe SDK not installed. Install with: pip install stripe")

# JWT Authentication imports
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import status

security = HTTPBearer(auto_error=False)


router = APIRouter(
    prefix='/api/storefront/checkout',
    tags=['Storefront - Checkout']
)


# ============================================================================
# Authentication Helpers
# ============================================================================

def get_current_customer_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Customer]:
    """
    Get current authenticated customer from JWT token.

    Returns None if no token provided or token is invalid (for guest checkout).
    Does not raise errors - allows optional authentication.
    """
    if not credentials:
        return None

    try:
        SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here-change-in-production')
        ALGORITHM = "HS256"

        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        customer_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if customer_id is None or token_type != "ecommerce_customer":
            return None

        # Get customer from database
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        return customer

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        # Token is invalid - allow guest checkout
        return None


# ============================================================================
# Pydantic Models
# ============================================================================

class AddressModel(BaseModel):
    """Address model for checkout."""
    first_name: str
    last_name: str
    company: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    phone: Optional[str] = None


class CheckoutInitRequest(BaseModel):
    """Request to initialize checkout."""
    shipping_address: AddressModel
    billing_address: Optional[AddressModel] = None  # Use shipping if not provided
    shipping_method: Optional[str] = None  # Selected shipping method (service_level or rate_id)
    customer_note: Optional[str] = None
    guest_email: Optional[EmailStr] = None  # Required if not authenticated


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    session_id: str
    cart_id: str
    subtotal: float
    tax: float
    shipping: float
    total: float
    shipping_address: dict
    billing_address: dict


class StripePaymentRequest(BaseModel):
    """Stripe payment processing request."""
    session_id: str
    payment_method_id: str  # Stripe PaymentMethod ID from frontend
    save_payment_method: bool = False


class OrderCreatedResponse(BaseModel):
    """Response after order is created."""
    order_id: str
    order_number: str
    total: float
    payment_status: str
    message: str


class ShippingRateRequest(BaseModel):
    """Request to get shipping rates."""
    shipping_address: AddressModel


class ShippingRateResponse(BaseModel):
    """Individual shipping rate option."""
    carrier: str
    service: str
    service_level: str
    amount: float
    currency: str = "USD"
    estimated_days: Optional[int] = None
    duration_terms: Optional[str] = None
    rate_id: str


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_tax(subtotal: float, state: str) -> float:
    """
    Calculate sales tax based on state.

    TODO: Implement proper tax calculation or integrate with tax service.
    This is a placeholder - use TaxJar, Avalara, or similar in production.
    """
    # Placeholder tax rates by state (simplified)
    TAX_RATES = {
        "CA": 0.0725,  # California
        "NY": 0.08,    # New York
        "TX": 0.0625,  # Texas
        "FL": 0.06,    # Florida
        # Add more states as needed
    }

    tax_rate = TAX_RATES.get(state.upper(), 0.0)
    return round(subtotal * tax_rate, 2)


def calculate_shipping(items: List[dict], address: dict) -> float:
    """
    Calculate shipping cost.

    TODO: Implement proper shipping calculation based on:
    - Item weight/dimensions
    - Destination address
    - Shipping method (standard, expedited, etc.)
    - Integration with shipping carriers (USPS, UPS, FedEx)
    """
    # Placeholder: flat rate shipping
    FLAT_RATE_SHIPPING = 5.99

    # Free shipping over $50
    subtotal = sum(item.get('subtotal', 0) for item in items)
    if subtotal >= 50:
        return 0.0

    return FLAT_RATE_SHIPPING


def generate_order_number() -> str:
    """Generate unique order number."""
    # Format: ORD-YYYYMMDD-XXXXX
    date_str = datetime.utcnow().strftime('%Y%m%d')
    random_suffix = str(uuid.uuid4())[:5].upper()
    return f"ORD-{date_str}-{random_suffix}"


def get_cart_by_session(db: Session, session_id: str, customer_id: Optional[str] = None) -> ShoppingCart:
    """Get cart by session ID or customer ID."""
    if customer_id:
        cart = db.query(ShoppingCart).filter(
            ShoppingCart.customer_id == uuid.UUID(customer_id),
            ShoppingCart.is_active == True
        ).first()
    else:
        cart = db.query(ShoppingCart).filter(
            ShoppingCart.session_id == session_id,
            ShoppingCart.is_active == True
        ).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if not cart.items or len(cart.items) == 0:
        raise HTTPException(status_code=400, detail="Cart is empty")

    return cart


# ============================================================================
# Checkout Endpoints
# ============================================================================

@router.get('/config')
async def get_stripe_config():
    """
    Get Stripe public configuration for frontend.

    Returns the Stripe publishable key needed for client-side payment processing.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Stripe integration not configured"
        )

    if not STRIPE_PUBLIC_KEY:
        raise HTTPException(
            status_code=500,
            detail="STRIPE_PUBLIC_KEY not configured in environment"
        )

    return {
        "stripe_public_key": STRIPE_PUBLIC_KEY
    }


@router.post('/shipping-rates', response_model=List[ShippingRateResponse])
async def get_shipping_rates(
    request: ShippingRateRequest,
    db: Session = Depends(get_db)
):
    """
    Get real-time shipping rates from Shippo API.

    Returns available shipping options with carriers, services, and prices
    based on the destination address.
    """
    try:
        # Format address for Shippo
        to_address = {
            'name': f"{request.shipping_address.first_name} {request.shipping_address.last_name}",
            'street1': request.shipping_address.address1,
            'city': request.shipping_address.city,
            'state': request.shipping_address.state,
            'zip': request.shipping_address.zip_code,
            'country': request.shipping_address.country,
        }

        # Add optional fields
        if request.shipping_address.address2:
            to_address['street2'] = request.shipping_address.address2
        if request.shipping_address.phone:
            to_address['phone'] = request.shipping_address.phone

        # Get rates from Shippo
        rates = shippo_service.get_shipping_rates(to_address=to_address)

        # Convert to response format
        return [
            ShippingRateResponse(
                carrier=rate['carrier'],
                service=rate['service'],
                service_level=rate['service_level'],
                amount=rate['amount'],
                currency=rate['currency'],
                estimated_days=rate.get('estimated_days'),
                duration_terms=rate.get('duration_terms'),
                rate_id=rate['rate_id']
            )
            for rate in rates
        ]

    except Exception as e:
        logging.error(f"Failed to get shipping rates: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate shipping rates. Please try again."
        )


@router.post('/init', response_model=CheckoutResponse)
async def initialize_checkout(
    checkout_data: CheckoutInitRequest,
    x_session_id: Optional[str] = Header(None),
    current_customer: Optional[Customer] = Depends(get_current_customer_optional),
    db: Session = Depends(get_db)
):
    """
    Initialize checkout session.

    Validates cart, calculates totals (tax, shipping), and prepares for payment.
    Supports both authenticated and guest checkout.
    """
    # For guest checkout, require email
    if not current_customer and not checkout_data.guest_email:
        raise HTTPException(
            status_code=400,
            detail="Email is required for guest checkout"
        )

    # Get cart
    customer_id = str(current_customer.id) if current_customer else None
    cart = get_cart_by_session(db, x_session_id, customer_id)

    # Validate all cart items still exist and are in stock
    for item in cart.items:
        product_id = item.get('product_id')
        variant_id = item.get('variant_id')
        quantity = item.get('quantity', 0)

        # Check product
        product = db.query(Product).filter(
            Product.id == uuid.UUID(product_id),
            Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=400,
                detail=f"Product {item.get('product_name')} is no longer available"
            )

        # Check inventory if tracked
        if product.track_inventory and not product.allow_backorder:
            available_quantity = product.inventory_quantity

            if variant_id:
                variant = db.query(ProductVariant).filter(
                    ProductVariant.id == uuid.UUID(variant_id)
                ).first()
                if variant:
                    available_quantity = variant.inventory_quantity

            if available_quantity < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {item.get('product_name')}"
                )

    # Use shipping address for billing if not provided
    billing_address = checkout_data.billing_address or checkout_data.shipping_address

    # Calculate tax
    tax = calculate_tax(cart.subtotal, checkout_data.shipping_address.state)

    # Calculate shipping
    shipping = calculate_shipping(cart.items, checkout_data.shipping_address.dict())

    # Calculate total
    total = round(cart.subtotal + tax + shipping, 2)

    # Create checkout session ID
    session_id = str(uuid.uuid4())

    # Store checkout data in cart for later use
    cart.items = cart.items  # Keep items
    cart.updated_at = datetime.utcnow()

    # Store temporary checkout session data
    # In production, use Redis or similar for session storage
    # For now, we'll include it in the response

    db.commit()

    return CheckoutResponse(
        session_id=session_id,
        cart_id=str(cart.id),
        subtotal=cart.subtotal,
        tax=tax,
        shipping=shipping,
        total=total,
        shipping_address=checkout_data.shipping_address.dict(),
        billing_address=billing_address.dict()
    )


class PaymentIntentRequest(BaseModel):
    """Request model for creating payment intent."""
    amount: float = Field(..., description="Payment amount in dollars")
    currency: str = Field("usd", description="Currency code")


class CompleteCheckoutRequest(BaseModel):
    """Request to complete checkout after payment."""
    session_id: str
    payment_intent_id: str
    shipping_address: AddressModel
    billing_address: Optional[AddressModel] = None
    customer_note: Optional[str] = None
    guest_email: Optional[EmailStr] = None


@router.post('/create-payment-intent')
async def create_stripe_payment_intent(
    request: PaymentIntentRequest,
    db: Session = Depends(get_db)
):
    """
    Create Stripe PaymentIntent.

    Frontend will use this to collect payment details securely.
    """
    amount = request.amount
    currency = request.currency
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Stripe integration not configured"
        )

    try:
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            automatic_payment_methods={'enabled': True}
        )

        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }

    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/complete', response_model=OrderCreatedResponse)
async def complete_checkout(
    request: CompleteCheckoutRequest,
    x_session_id: Optional[str] = Header(None),
    current_customer: Optional[Customer] = Depends(get_current_customer_optional),
    db: Session = Depends(get_db)
):
    """
    Complete checkout and create order.

    Called after payment is confirmed by Stripe.
    Creates order record and clears cart.
    """
    # Extract data from request
    session_id = request.session_id
    payment_intent_id = request.payment_intent_id
    shipping_address = request.shipping_address
    billing_address = request.billing_address
    customer_note = request.customer_note
    guest_email = request.guest_email

    # For guest checkout, require email
    if not current_customer and not guest_email:
        raise HTTPException(status_code=400, detail="Email required")

    # Verify payment with Stripe
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    try:
        # Retrieve PaymentIntent to verify status
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status != 'succeeded':
            raise HTTPException(
                status_code=400,
                detail=f"Payment not successful. Status: {payment_intent.status}"
            )

    except stripe.error.StripeError as e:
        logging.error(f"Stripe verification error: {e}")
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Get cart
    customer_id = str(current_customer.id) if current_customer else None
    cart = get_cart_by_session(db, x_session_id, customer_id)

    # Use shipping address for billing if not provided
    billing_addr = billing_address or shipping_address

    # Calculate totals
    tax = calculate_tax(cart.subtotal, shipping_address.state)
    shipping = calculate_shipping(cart.items, shipping_address.dict())
    total = round(cart.subtotal + tax + shipping, 2)

    # Generate order number
    order_number = generate_order_number()

    # Get storefront owner user_id from settings, or fallback to first user
    storefront_settings = db.query(StorefrontSettings).first()
    if storefront_settings:
        storefront_owner_user_id = storefront_settings.user_id
    else:
        # Fallback: Get first user from users table
        first_user = db.query(User).first()
        if not first_user:
            raise HTTPException(
                status_code=500,
                detail="No users found. Please create a user account first."
            )
        storefront_owner_user_id = first_user.id
        logging.warning(f"No storefront settings found. Using first user {first_user.id} as storefront owner.")

    # Create order
    order = Order(
        id=uuid.uuid4(),
        order_number=order_number,
        user_id=storefront_owner_user_id,
        customer_id=uuid.UUID(customer_id) if customer_id else None,
        guest_email=guest_email if not customer_id else None,
        subtotal=cart.subtotal,
        tax=tax,
        shipping=shipping,
        discount=0,
        total=total,
        shipping_address=shipping_address.dict(),
        billing_address=billing_addr.dict(),
        payment_status="paid",
        payment_method="stripe",
        payment_id=payment_intent_id,
        fulfillment_status="unfulfilled",
        customer_note=customer_note,
        status="processing"
    )

    db.add(order)
    db.flush()  # Get order ID

    # Create order items from cart
    for cart_item in cart.items:
        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=uuid.UUID(cart_item.get('product_id')) if cart_item.get('product_id') else None,
            variant_id=uuid.UUID(cart_item.get('variant_id')) if cart_item.get('variant_id') else None,
            product_name=cart_item.get('product_name'),
            variant_name=cart_item.get('variant_name'),
            sku=cart_item.get('sku'),
            price=cart_item.get('price'),
            quantity=cart_item.get('quantity'),
            total=cart_item.get('subtotal')
        )
        db.add(order_item)

        # Update inventory if tracked
        if cart_item.get('product_id'):
            product = db.query(Product).filter(
                Product.id == uuid.UUID(cart_item.get('product_id'))
            ).first()

            if product and product.track_inventory:
                if cart_item.get('variant_id'):
                    variant = db.query(ProductVariant).filter(
                        ProductVariant.id == uuid.UUID(cart_item.get('variant_id'))
                    ).first()
                    if variant:
                        variant.inventory_quantity -= cart_item.get('quantity', 0)
                else:
                    product.inventory_quantity -= cart_item.get('quantity', 0)

    # Update customer stats if authenticated
    if current_customer:
        current_customer.total_spent += total
        current_customer.order_count += 1

    # Clear cart
    cart.items = []
    cart.subtotal = 0
    cart.is_active = False

    db.commit()
    db.refresh(order)

    # TODO: Send order confirmation email

    return OrderCreatedResponse(
        order_id=str(order.id),
        order_number=order.order_number,
        total=order.total,
        payment_status=order.payment_status,
        message="Order created successfully"
    )


@router.post('/webhook')
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks.

    Important for events like:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - charge.refunded
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    # Get webhook secret from environment
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        logging.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # Get the signature header
    sig_header = request.headers.get('stripe-signature')
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature header")

    try:
        # Get raw body
        payload = await request.body()

        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event['type']
    logging.info(f"Received Stripe webhook: {event_type}")

    if event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Payment was successful
        # Update order if needed
        logging.info(f"PaymentIntent {payment_intent['id']} succeeded")

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        # Payment failed
        # Update order status
        logging.warning(f"PaymentIntent {payment_intent['id']} failed")

        # Find order and update status
        order = db.query(Order).filter(
            Order.payment_id == payment_intent['id']
        ).first()

        if order:
            order.payment_status = "failed"
            order.status = "cancelled"
            db.commit()

    elif event_type == 'charge.refunded':
        charge = event['data']['object']
        logging.info(f"Charge {charge['id']} refunded")

        # Find order and update status
        payment_intent_id = charge.get('payment_intent')
        if payment_intent_id:
            order = db.query(Order).filter(
                Order.payment_id == payment_intent_id
            ).first()

            if order:
                order.payment_status = "refunded"
                db.commit()

    return {"status": "success"}
