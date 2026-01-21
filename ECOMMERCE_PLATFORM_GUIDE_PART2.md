# 🛒 Custom Ecommerce Platform - Part 2: Implementation Details

_Continuation from ECOMMERCE_PLATFORM_GUIDE.md_

---

## 🔨 Phase 2: Database & Backend API (Continued)

### **Step 2.3: Shopping Cart Implementation**

`server/src/routes/ecommerce/cart.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from server.src.database.core import get_db
from server.src.entities.ecommerce.cart import ShoppingCart
from server.src.entities.ecommerce.product import Product, ProductVariant
from pydantic import BaseModel
import uuid

router = APIRouter(
    prefix='/api/storefront/cart',
    tags=['Storefront - Cart']
)

class AddToCartRequest(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1

class UpdateCartRequest(BaseModel):
    item_id: str
    quantity: int

def get_or_create_cart(session_id: Optional[str], db: Session):
    """Get existing cart or create new one."""
    if not session_id:
        # Create new cart
        cart = ShoppingCart(
            id=uuid.uuid4(),
            session_id=str(uuid.uuid4()),
            items=[],
            subtotal=0
        )
        db.add(cart)
        db.commit()
        return cart

    # Get existing cart
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.session_id == session_id,
        ShoppingCart.is_active == True
    ).first()

    if not cart:
        # Create new cart with this session
        cart = ShoppingCart(
            id=uuid.uuid4(),
            session_id=session_id,
            items=[],
            subtotal=0
        )
        db.add(cart)
        db.commit()

    return cart

@router.post('/add')
async def add_to_cart(
    request: AddToCartRequest,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Add item to shopping cart."""
    # Get or create cart
    cart = get_or_create_cart(session_id, db)

    # Get product
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get variant if specified
    variant = None
    if request.variant_id:
        variant = db.query(ProductVariant).filter(
            ProductVariant.id == request.variant_id
        ).first()
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")

    # Calculate price
    price = variant.price if variant and variant.price else product.price

    # Check if item already in cart
    items = cart.items or []
    item_found = False

    for item in items:
        if (item.get('product_id') == str(request.product_id) and
            item.get('variant_id') == str(request.variant_id)):
            # Update quantity
            item['quantity'] += request.quantity
            item_found = True
            break

    if not item_found:
        # Add new item
        items.append({
            'id': str(uuid.uuid4()),
            'product_id': str(request.product_id),
            'product_name': product.name,
            'variant_id': str(request.variant_id) if request.variant_id else None,
            'variant_name': variant.name if variant else None,
            'price': price,
            'quantity': request.quantity,
            'image': product.featured_image
        })

    # Update cart
    cart.items = items
    cart.subtotal = sum(item['price'] * item['quantity'] for item in items)
    db.commit()

    return {
        "success": True,
        "cart": {
            "session_id": cart.session_id,
            "items": cart.items,
            "subtotal": cart.subtotal,
            "item_count": sum(item['quantity'] for item in items)
        }
    }

@router.get('/')
async def get_cart(
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Get current cart."""
    cart = get_or_create_cart(session_id, db)

    return {
        "session_id": cart.session_id,
        "items": cart.items or [],
        "subtotal": cart.subtotal or 0,
        "item_count": sum(item['quantity'] for item in (cart.items or []))
    }

@router.put('/update')
async def update_cart_item(
    request: UpdateCartRequest,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Update cart item quantity."""
    cart = get_or_create_cart(session_id, db)

    items = cart.items or []
    item_found = False

    for item in items:
        if item.get('id') == request.item_id:
            if request.quantity <= 0:
                items.remove(item)
            else:
                item['quantity'] = request.quantity
            item_found = True
            break

    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    cart.items = items
    cart.subtotal = sum(item['price'] * item['quantity'] for item in items)
    db.commit()

    return {"success": True, "cart": cart}

@router.delete('/remove/{item_id}')
async def remove_from_cart(
    item_id: str,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Remove item from cart."""
    cart = get_or_create_cart(session_id, db)

    items = cart.items or []
    cart.items = [item for item in items if item.get('id') != item_id]
    cart.subtotal = sum(item['price'] * item['quantity'] for item in cart.items)
    db.commit()

    return {"success": True, "cart": cart}
```

### **Step 2.4: Stripe Payment Integration**

First, install Stripe:

```bash
pip install stripe==5.0.0
```

`server/src/routes/ecommerce/checkout.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.entities.ecommerce.cart import ShoppingCart
from server.src.entities.ecommerce.order import Order, OrderItem
from server.src.entities.ecommerce.customer import Customer
from pydantic import BaseModel, EmailStr
from typing import Optional
import stripe
import os
import uuid
from datetime import datetime

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

router = APIRouter(
    prefix='/api/storefront/checkout',
    tags=['Storefront - Checkout']
)

class ShippingAddress(BaseModel):
    first_name: str
    last_name: str
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    phone: str

class CheckoutInitRequest(BaseModel):
    email: EmailStr
    shipping_address: ShippingAddress
    billing_address: Optional[ShippingAddress] = None

class PaymentRequest(BaseModel):
    payment_method_id: str  # Stripe Payment Method ID
    save_card: bool = False

@router.post('/init')
async def init_checkout(
    request: CheckoutInitRequest,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Initialize checkout process.
    Validates cart, calculates totals, creates draft order.
    """
    # Get cart
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.session_id == session_id,
        ShoppingCart.is_active == True
    ).first()

    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate totals
    subtotal = cart.subtotal
    tax = calculate_tax(subtotal, request.shipping_address.state)
    shipping = calculate_shipping(cart.items, request.shipping_address)
    total = subtotal + tax + shipping

    # Create or get customer
    customer = db.query(Customer).filter(Customer.email == request.email).first()
    if not customer:
        customer = Customer(
            id=uuid.uuid4(),
            email=request.email,
            first_name=request.shipping_address.first_name,
            last_name=request.shipping_address.last_name
        )
        db.add(customer)

    # Generate order number
    order_number = generate_order_number(db)

    # Create draft order
    order = Order(
        id=uuid.uuid4(),
        order_number=order_number,
        customer_id=customer.id,
        guest_email=request.email,
        subtotal=subtotal,
        tax=tax,
        shipping=shipping,
        total=total,
        shipping_address=request.shipping_address.dict(),
        billing_address=request.billing_address.dict() if request.billing_address else request.shipping_address.dict(),
        payment_status='pending',
        fulfillment_status='unfulfilled',
        status='pending'
    )
    db.add(order)

    # Create order items
    for cart_item in cart.items:
        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=cart_item['product_id'],
            variant_id=cart_item.get('variant_id'),
            product_name=cart_item['product_name'],
            variant_name=cart_item.get('variant_name'),
            price=cart_item['price'],
            quantity=cart_item['quantity'],
            total=cart_item['price'] * cart_item['quantity']
        )
        db.add(order_item)

    db.commit()

    # Create Stripe Payment Intent
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # Stripe uses cents
            currency='usd',
            customer=get_or_create_stripe_customer(customer.email),
            metadata={
                'order_id': str(order.id),
                'order_number': order_number
            }
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "order_id": str(order.id),
        "order_number": order_number,
        "totals": {
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "total": total
        },
        "payment_intent": {
            "client_secret": payment_intent.client_secret,
            "id": payment_intent.id
        }
    }

@router.post('/payment')
async def process_payment(
    request: PaymentRequest,
    order_id: str,
    db: Session = Depends(get_db)
):
    """
    Process payment with Stripe.
    """
    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Confirm payment with Stripe
    try:
        payment_intent = stripe.PaymentIntent.confirm(
            order.payment_id,
            payment_method=request.payment_method_id
        )

        if payment_intent.status == 'succeeded':
            # Update order
            order.payment_status = 'paid'
            order.status = 'processing'
            order.payment_id = payment_intent.id

            # Update customer stats
            customer = order.customer
            customer.total_spent += order.total
            customer.order_count += 1

            db.commit()

            return {
                "success": True,
                "order_number": order.order_number,
                "payment_status": "paid"
            }
        else:
            return {
                "success": False,
                "error": "Payment failed",
                "status": payment_intent.status
            }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/complete')
async def complete_order(
    order_id: str,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Complete order and clear cart.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Clear cart
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.session_id == session_id
    ).first()
    if cart:
        cart.is_active = False
        cart.items = []

    db.commit()

    # Trigger order fulfillment (async)
    # TODO: Add to background job queue
    # await trigger_order_fulfillment(order.id)

    # Send confirmation email
    # TODO: Implement email service
    # await send_order_confirmation_email(order)

    return {
        "success": True,
        "order": {
            "order_number": order.order_number,
            "total": order.total,
            "email": order.guest_email
        }
    }

# Helper functions
def calculate_tax(subtotal: float, state: str) -> float:
    """Calculate sales tax based on state."""
    tax_rates = {
        'CA': 0.0725,  # California
        'NY': 0.04,    # New York
        'TX': 0.0625,  # Texas
        # Add more states...
    }
    rate = tax_rates.get(state, 0)
    return round(subtotal * rate, 2)

def calculate_shipping(items: list, address: dict) -> float:
    """Calculate shipping cost."""
    # Simple flat rate for now
    # TODO: Implement dynamic shipping rates
    return 5.99

def generate_order_number(db: Session) -> str:
    """Generate unique order number."""
    from datetime import datetime
    year = datetime.now().year
    count = db.query(Order).filter(
        Order.order_number.like(f'ORD-{year}-%')
    ).count() + 1
    return f"ORD-{year}-{count:05d}"

def get_or_create_stripe_customer(email: str) -> str:
    """Get or create Stripe customer."""
    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            return customers.data[0].id
        else:
            customer = stripe.Customer.create(email=email)
            return customer.id
    except stripe.error.StripeError:
        return None
```

### **Step 2.5: Customer Authentication**

`server/src/routes/ecommerce/customers.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.entities.ecommerce.customer import Customer
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
from datetime import datetime, timedelta
import os

router = APIRouter(
    prefix='/api/storefront/auth',
    tags=['Storefront - Auth']
)

security = HTTPBearer()

JWT_SECRET = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 72

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    accepts_marketing: bool = False

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(customer_id: str) -> str:
    """Create JWT access token."""
    payload = {
        'customer_id': customer_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Customer:
    """Get current authenticated customer."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        customer_id = payload.get('customer_id')
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return customer
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post('/register')
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new customer."""
    # Check if email exists
    existing = db.query(Customer).filter(Customer.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create customer
    customer = Customer(
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        accepts_marketing=request.accepts_marketing,
        is_active=True,
        email_verified=False
    )
    db.add(customer)
    db.commit()

    # Generate token
    access_token = create_access_token(str(customer.id))

    return {
        "success": True,
        "customer": {
            "id": str(customer.id),
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name
        },
        "access_token": access_token
    }

@router.post('/login')
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login customer."""
    customer = db.query(Customer).filter(Customer.email == request.email).first()

    if not customer or not verify_password(request.password, customer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not customer.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Update last login
    customer.last_login = datetime.utcnow()
    db.commit()

    # Generate token
    access_token = create_access_token(str(customer.id))

    return {
        "success": True,
        "customer": {
            "id": str(customer.id),
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name
        },
        "access_token": access_token
    }

@router.get('/profile')
async def get_profile(customer: Customer = Depends(get_current_customer)):
    """Get customer profile."""
    return {
        "id": str(customer.id),
        "email": customer.email,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "phone": customer.phone,
        "total_spent": customer.total_spent,
        "order_count": customer.order_count
    }
```

### **Step 2.6: Register Routes in Main App**

Update `server/src/api.py`:

```python
# Add ecommerce imports
from server.src.routes.ecommerce import products, cart, checkout, customers, orders, admin

def register_routes(app: FastAPI):
    # ... existing routes ...

    # Ecommerce routes
    app.include_router(products.router)
    app.include_router(cart.router)
    app.include_router(checkout.router)
    app.include_router(customers.router)
    app.include_router(orders.router)
    app.include_router(admin.router, prefix="/api/admin")
```

---

## 🎨 Phase 3: Customer-Facing Storefront (Week 5-6)

### **Goals**

- [ ] Build React storefront
- [ ] Create product catalog pages
- [ ] Implement shopping cart UI
- [ ] Build checkout flow
- [ ] Customer account pages

### **Step 3.1: Project Structure**

Create separate storefront app or integrate into existing frontend:

**Option A: Separate Storefront App**

```
storefront/              # New React app
├── public/
├── src/
│   ├── components/
│   │   ├── product/
│   │   │   ├── ProductCard.jsx
│   │   │   ├── ProductGrid.jsx
│   │   │   └── ProductDetail.jsx
│   │   ├── cart/
│   │   │   ├── CartItem.jsx
│   │   │   ├── CartSidebar.jsx
│   │   │   └── CartPage.jsx
│   │   ├── checkout/
│   │   │   ├── CheckoutForm.jsx
│   │   │   ├── ShippingForm.jsx
│   │   │   └── PaymentForm.jsx
│   │   └── layout/
│   │       ├── Header.jsx
│   │       ├── Footer.jsx
│   │       └── Navigation.jsx
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Products.jsx
│   │   ├── ProductDetail.jsx
│   │   ├── Cart.jsx
│   │   ├── Checkout.jsx
│   │   ├── OrderConfirmation.jsx
│   │   └── Account.jsx
│   ├── hooks/
│   │   ├── useCart.js
│   │   ├── useProducts.js
│   │   └── useAuth.js
│   ├── services/
│   │   ├── api.js
│   │   ├── cart.js
│   │   └── products.js
│   ├── store/
│   │   ├── cartStore.js
│   │   └── authStore.js
│   └── App.jsx
├── package.json
└── tailwind.config.js
```

**Option B: Integrate into Existing Frontend**

```
frontend/src/
├── pages/
│   ├── admin/           # Your existing admin pages
│   └── storefront/      # New storefront pages
│       ├── Home.jsx
│       ├── Products.jsx
│       └── ...
```

### **Step 3.2: Setup Storefront App**

```bash
cd /Users/fserrano/Documents/Projects/etsy_seller_automater

# Create new React app for storefront
npx create-react-app storefront
cd storefront

# Install dependencies
npm install react-router-dom@6 zustand axios @stripe/stripe-js @stripe/react-stripe-js
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Configure Tailwind (`tailwind.config.js`):

```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        secondary: "#8b5cf6",
      },
    },
  },
  plugins: [],
};
```

**📄 Continue to:** [ECOMMERCE_PLATFORM_GUIDE_PART3.md](./ECOMMERCE_PLATFORM_GUIDE_PART3.md) for React Storefront components, Zustand cart store, and Order Fulfillment integration.

---
