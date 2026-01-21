"""
Subscription API models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session"""
    price_id: str = Field(..., description="Stripe Price ID for the subscription tier")
    success_url: str = Field(..., description="URL to redirect on successful payment")
    cancel_url: str = Field(..., description="URL to redirect on canceled payment")


class CreateCheckoutSessionResponse(BaseModel):
    """Response containing checkout session details"""
    session_id: str
    url: str


class SubscriptionResponse(BaseModel):
    """Subscription details response"""
    id: str
    user_id: str
    tier: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription"""
    new_price_id: str = Field(..., description="New Stripe Price ID to switch to")


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription"""
    cancel_immediately: bool = Field(default=False, description="Cancel immediately vs at period end")


class BillingHistoryResponse(BaseModel):
    """Billing history entry"""
    id: str
    amount: float
    currency: str
    status: str
    invoice_date: datetime
    paid_at: Optional[datetime]
    invoice_pdf_url: Optional[str]
    hosted_invoice_url: Optional[str]
    description: Optional[str]


class CustomerPortalResponse(BaseModel):
    """Customer portal session response"""
    url: str


class SubscriptionTier(BaseModel):
    """Subscription tier configuration"""
    id: str
    name: str
    price: float
    stripe_price_id: str
    features: dict
    limits: dict
