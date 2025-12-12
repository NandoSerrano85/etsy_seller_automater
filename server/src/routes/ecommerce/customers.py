"""Customer authentication and account management for ecommerce storefront."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import uuid
import bcrypt
import jwt
import os

from server.src.database.core import get_db
from server.src.entities.ecommerce.customer import Customer, CustomerAddress


router = APIRouter(
    prefix='/api/storefront/customers',
    tags=['Storefront - Customers']
)

security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# ============================================================================
# Pydantic Models
# ============================================================================

class CustomerRegisterRequest(BaseModel):
    """Customer registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    accepts_marketing: bool = False


class CustomerLoginRequest(BaseModel):
    """Customer login request."""
    email: EmailStr
    password: str


class CustomerResponse(BaseModel):
    """Customer response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    accepts_marketing: bool = False
    email_verified: bool = False
    total_spent: float = 0
    order_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class AuthTokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    customer: CustomerResponse


class AddressRequest(BaseModel):
    """Address request model."""
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    company: Optional[str] = Field(None, max_length=255)
    address1: str = Field(..., max_length=255)
    address2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    zip_code: str = Field(..., max_length=20)
    country: str = Field("United States", max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_default_shipping: bool = False
    is_default_billing: bool = False


class AddressResponse(BaseModel):
    """Address response model."""
    id: str
    first_name: str
    last_name: str
    company: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str
    phone: Optional[str] = None
    is_default_shipping: bool = False
    is_default_billing: bool = False

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update customer profile request."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    accepts_marketing: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


# ============================================================================
# Helper Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(customer_id: str, email: str) -> str:
    """Create JWT access token."""
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": customer_id,
        "email": email,
        "exp": expire,
        "type": "ecommerce_customer"
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Customer:
    """
    Get current authenticated customer from JWT token.

    Raises:
        HTTPException: If token is invalid or customer not found
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        customer_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if customer_id is None or token_type != "ecommerce_customer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    # Get customer from database
    customer = db.query(Customer).filter(
        Customer.id == uuid.UUID(customer_id),
        Customer.is_active == True
    ).first()

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found"
        )

    return customer


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post('/register', response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(
    registration: CustomerRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new customer account.

    Creates account and returns authentication token.
    """
    # Check if email already exists
    existing = db.query(Customer).filter(Customer.email == registration.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = hash_password(registration.password)

    # Create customer
    customer = Customer(
        id=uuid.uuid4(),
        email=registration.email,
        password_hash=password_hash,
        first_name=registration.first_name,
        last_name=registration.last_name,
        phone=registration.phone,
        accepts_marketing=registration.accepts_marketing,
        is_active=True,
        email_verified=False,
        total_spent=0,
        order_count=0
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Create access token
    access_token = create_access_token(str(customer.id), customer.email)

    # Format response
    customer_response = CustomerResponse(
        id=str(customer.id),
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone=customer.phone,
        accepts_marketing=customer.accepts_marketing,
        email_verified=customer.email_verified,
        total_spent=customer.total_spent,
        order_count=customer.order_count,
        created_at=customer.created_at
    )

    return AuthTokenResponse(
        access_token=access_token,
        customer=customer_response
    )


@router.post('/login', response_model=AuthTokenResponse)
async def login_customer(
    login: CustomerLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns authentication token on success.
    """
    # Find customer by email
    customer = db.query(Customer).filter(
        Customer.email == login.email,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(login.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    customer.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(str(customer.id), customer.email)

    # Format response
    customer_response = CustomerResponse(
        id=str(customer.id),
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone=customer.phone,
        accepts_marketing=customer.accepts_marketing,
        email_verified=customer.email_verified,
        total_spent=customer.total_spent,
        order_count=customer.order_count,
        created_at=customer.created_at
    )

    return AuthTokenResponse(
        access_token=access_token,
        customer=customer_response
    )


@router.get('/me', response_model=CustomerResponse)
async def get_current_customer_profile(
    current_customer: Customer = Depends(get_current_customer)
):
    """
    Get current customer profile.

    Requires authentication token.
    """
    return CustomerResponse(
        id=str(current_customer.id),
        email=current_customer.email,
        first_name=current_customer.first_name,
        last_name=current_customer.last_name,
        phone=current_customer.phone,
        accepts_marketing=current_customer.accepts_marketing,
        email_verified=current_customer.email_verified,
        total_spent=current_customer.total_spent,
        order_count=current_customer.order_count,
        created_at=current_customer.created_at
    )


@router.put('/me', response_model=CustomerResponse)
async def update_customer_profile(
    update: UpdateProfileRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Update customer profile.

    Requires authentication token.
    """
    # Update fields if provided
    if update.first_name is not None:
        current_customer.first_name = update.first_name

    if update.last_name is not None:
        current_customer.last_name = update.last_name

    if update.phone is not None:
        current_customer.phone = update.phone

    if update.accepts_marketing is not None:
        current_customer.accepts_marketing = update.accepts_marketing

    db.commit()
    db.refresh(current_customer)

    return CustomerResponse(
        id=str(current_customer.id),
        email=current_customer.email,
        first_name=current_customer.first_name,
        last_name=current_customer.last_name,
        phone=current_customer.phone,
        accepts_marketing=current_customer.accepts_marketing,
        email_verified=current_customer.email_verified,
        total_spent=current_customer.total_spent,
        order_count=current_customer.order_count,
        created_at=current_customer.created_at
    )


@router.post('/me/change-password')
async def change_password(
    password_change: ChangePasswordRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Change customer password.

    Requires authentication token.
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash and set new password
    current_customer.password_hash = hash_password(password_change.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


# ============================================================================
# Address Management Endpoints
# ============================================================================

@router.get('/me/addresses', response_model=List[AddressResponse])
async def get_customer_addresses(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get all addresses for current customer.

    Requires authentication token.
    """
    addresses = db.query(CustomerAddress).filter(
        CustomerAddress.customer_id == current_customer.id
    ).all()

    return addresses


@router.post('/me/addresses', response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def add_customer_address(
    address: AddressRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Add a new address for current customer.

    Requires authentication token.
    """
    # If setting as default, unset other defaults
    if address.is_default_shipping:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_customer.id,
            CustomerAddress.is_default_shipping == True
        ).update({CustomerAddress.is_default_shipping: False})

    if address.is_default_billing:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_customer.id,
            CustomerAddress.is_default_billing == True
        ).update({CustomerAddress.is_default_billing: False})

    # Create new address
    new_address = CustomerAddress(
        id=uuid.uuid4(),
        customer_id=current_customer.id,
        **address.dict()
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


@router.put('/me/addresses/{address_id}', response_model=AddressResponse)
async def update_customer_address(
    address_id: str,
    address: AddressRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Update an existing address.

    Requires authentication token.
    """
    try:
        address_uuid = uuid.UUID(address_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid address ID format")

    # Get address
    existing_address = db.query(CustomerAddress).filter(
        CustomerAddress.id == address_uuid,
        CustomerAddress.customer_id == current_customer.id
    ).first()

    if not existing_address:
        raise HTTPException(status_code=404, detail="Address not found")

    # If setting as default, unset other defaults
    if address.is_default_shipping and not existing_address.is_default_shipping:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_customer.id,
            CustomerAddress.id != address_uuid,
            CustomerAddress.is_default_shipping == True
        ).update({CustomerAddress.is_default_shipping: False})

    if address.is_default_billing and not existing_address.is_default_billing:
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == current_customer.id,
            CustomerAddress.id != address_uuid,
            CustomerAddress.is_default_billing == True
        ).update({CustomerAddress.is_default_billing: False})

    # Update address fields
    for field, value in address.dict().items():
        setattr(existing_address, field, value)

    db.commit()
    db.refresh(existing_address)

    return existing_address


@router.delete('/me/addresses/{address_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_address(
    address_id: str,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Delete an address.

    Requires authentication token.
    """
    try:
        address_uuid = uuid.UUID(address_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid address ID format")

    # Get address
    address = db.query(CustomerAddress).filter(
        CustomerAddress.id == address_uuid,
        CustomerAddress.customer_id == current_customer.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()

    return None
