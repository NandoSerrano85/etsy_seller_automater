"""Pydantic models for Email Messaging API."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


# ============================================================================
# Email Template Models
# ============================================================================

class EmailTemplateRequest(BaseModel):
    """Request model for creating/updating email templates."""
    name: str = Field(..., max_length=255, description="Template name")
    template_type: Literal["transactional", "marketing"] = Field(..., description="Template type")
    email_type: str = Field(..., max_length=50, description="Email type (order_confirmation, shipping_notification, marketing)")
    subject: str = Field(..., max_length=500, description="Email subject line with {{variables}}")
    blocks: List[Dict[str, Any]] = Field(default=[], description="Template content blocks for visual editor")
    primary_color: str = Field("#10b981", pattern="^#[0-9A-Fa-f]{6}$", description="Primary brand color")
    secondary_color: str = Field("#059669", pattern="^#[0-9A-Fa-f]{6}$", description="Secondary brand color")
    logo_url: Optional[str] = Field(None, max_length=512, description="Logo URL")
    is_active: bool = Field(True, description="Whether template is active")


class EmailTemplateResponse(BaseModel):
    """Response model for email templates."""
    id: str
    user_id: str
    name: str
    template_type: str
    email_type: str
    subject: str
    blocks: List[Dict[str, Any]]
    primary_color: str
    secondary_color: str
    logo_url: Optional[str]
    sendgrid_template_id: Optional[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Email Log Models
# ============================================================================

class EmailLogResponse(BaseModel):
    """Response model for email logs."""
    id: str
    user_id: str
    template_id: Optional[str]
    email_type: str
    recipient_email: str
    subject: str
    order_id: Optional[str]
    customer_id: Optional[str]
    sendgrid_message_id: Optional[str]
    sendgrid_status: Optional[str]
    sent_at: datetime
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EmailLogFilters(BaseModel):
    """Filter parameters for email logs."""
    email_type: Optional[str] = None
    order_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


# ============================================================================
# Email Subscriber Models
# ============================================================================

class EmailSubscriberRequest(BaseModel):
    """Request model for creating/updating email subscribers."""
    email: str = Field(..., max_length=255, description="Subscriber email address")
    customer_id: Optional[str] = Field(None, description="Associated customer ID")
    tags: List[str] = Field(default=[], description="Segmentation tags")
    is_subscribed: bool = Field(True, description="Subscription status")


class EmailSubscriberResponse(BaseModel):
    """Response model for email subscribers."""
    id: str
    user_id: str
    email: str
    customer_id: Optional[str]
    is_subscribed: bool
    unsubscribed_at: Optional[datetime]
    tags: List[str]
    total_sent: int
    total_opened: int
    total_clicked: int
    last_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailSubscriberFilters(BaseModel):
    """Filter parameters for email subscribers."""
    tags: Optional[str] = Field(None, description="Comma-separated tags to filter by")
    is_subscribed: Optional[bool] = None


# ============================================================================
# Marketing Email Models
# ============================================================================

class SendMarketingEmailRequest(BaseModel):
    """Request model for sending marketing emails."""
    template_id: str = Field(..., description="Marketing email template ID")
    recipient_filter: Optional[Dict[str, Any]] = Field(None, description="Filter criteria for recipients (e.g., {'tags': ['vip']})")
    recipient_emails: Optional[List[str]] = Field(None, description="Manual list of recipient emails")
    schedule_for: Optional[datetime] = Field(None, description="Schedule for future sending (None = send immediately)")


class SendMarketingEmailResponse(BaseModel):
    """Response model for sending marketing emails."""
    scheduled_email_id: Optional[str] = None
    recipient_count: int
    sent_count: Optional[int] = None
    status: str  # "sent", "scheduled", "failed"
    message: str


# ============================================================================
# Scheduled Email Models
# ============================================================================

class ScheduledEmailResponse(BaseModel):
    """Response model for scheduled emails."""
    id: str
    user_id: str
    template_id: str
    recipient_filter: Optional[Dict[str, Any]]
    recipient_count: Optional[int]
    scheduled_for: datetime
    status: str
    sent_count: int
    failed_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Email Analytics Models
# ============================================================================

class EmailAnalyticsSummary(BaseModel):
    """Summary analytics for emails."""
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_failed: int
    delivery_rate: float  # Percentage
    open_rate: float  # Percentage
    click_rate: float  # Percentage
    by_email_type: Dict[str, int]  # Counts by email type


class EmailAnalyticsResponse(BaseModel):
    """Response model for email analytics."""
    period: str  # e.g., "last_7_days", "last_30_days", "custom"
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    summary: EmailAnalyticsSummary


# ============================================================================
# Template Preview Models
# ============================================================================

class TemplatePreviewRequest(BaseModel):
    """Request model for previewing email templates."""
    context: Dict[str, Any] = Field(default={}, description="Sample data for template variables")


class TemplatePreviewResponse(BaseModel):
    """Response model for template preview."""
    html_content: str
    subject: str


# ============================================================================
# Pagination Models
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int = Field(1, ge=1)
    page_size: int = Field(100, ge=1, le=100)
    total_pages: int

    class Config:
        from_attributes = True
