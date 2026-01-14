"""
Subscription Entity for Stripe Integration
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid
from typing import Dict, Any

from ..database.core import Base


class Subscription(Base):
    """User subscription managed by Stripe"""
    __tablename__ = 'subscriptions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Stripe IDs
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Subscription details
    tier = Column(String(50), nullable=False, default='free')  # free, pro, print_pro
    status = Column(String(50), nullable=False, default='active')  # active, canceled, past_due, incomplete

    # Billing
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)

    # Payment
    default_payment_method = Column(String(255), nullable=True)

    # Additional data
    extra_metadata = Column(JSONB, default={})

    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier={self.tier}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'tier': self.tier,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start is not None else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end is not None else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None
        }


class SubscriptionUsage(Base):
    """Track monthly usage limits for subscriptions"""
    __tablename__ = 'subscription_usage'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Usage tracking
    mockups_this_month = Column(Integer, default=0)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SubscriptionUsage(user_id={self.user_id}, month={self.month}/{self.year}, mockups={self.mockups_this_month})>"


class BillingHistory(Base):
    """Track billing and invoice history"""
    __tablename__ = 'billing_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True)

    # Stripe info
    stripe_invoice_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True)

    # Invoice details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='usd')
    status = Column(String(50), nullable=False)  # paid, failed, pending, void

    # Dates
    invoice_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    # Invoice data
    invoice_pdf_url = Column(String(500), nullable=True)
    hosted_invoice_url = Column(String(500), nullable=True)

    # Description
    description = Column(String(500), nullable=True)

    # Additional data
    extra_metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<BillingHistory(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'stripe_invoice_id': self.stripe_invoice_id,
            'amount': float(self.amount) if self.amount is not None else 0,
            'currency': self.currency,
            'status': self.status,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date is not None else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at is not None else None,
            'invoice_pdf_url': self.invoice_pdf_url,
            'hosted_invoice_url': self.hosted_invoice_url,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None
        }
