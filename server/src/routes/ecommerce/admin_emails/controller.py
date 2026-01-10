"""Admin Email API endpoints for managing email templates, logs, and campaigns."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from server.src.database.core import get_db
from server.src.entities.ecommerce.email_template import EmailTemplate
from server.src.entities.ecommerce.email_log import EmailLog
from server.src.entities.ecommerce.email_subscriber import EmailSubscriber
from server.src.entities.ecommerce.scheduled_email import ScheduledEmail
from server.src.entities.user import User
from server.src.routes.auth.service import get_current_user_db as get_current_user
from server.src.routes.auth.plan_access import require_pro_plan
from server.src.services.email_service import EmailService
from server.src.routes.ecommerce.admin_emails.model import (
    EmailTemplateRequest,
    EmailTemplateResponse,
    EmailLogResponse,
    EmailLogFilters,
    EmailSubscriberRequest,
    EmailSubscriberResponse,
    EmailSubscriberFilters,
    SendMarketingEmailRequest,
    SendMarketingEmailResponse,
    ScheduledEmailResponse,
    EmailAnalyticsResponse,
    EmailAnalyticsSummary,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    PaginatedResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/ecommerce/admin/emails',
    tags=['Ecommerce - Admin - Email Messaging']
)


# ============================================================================
# Email Template Endpoints
# ============================================================================

@router.get('/templates', response_model=List[EmailTemplateResponse])
async def list_email_templates(
    email_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    List all email templates for the current user.

    Filter by email type or active status if provided.
    """
    query = db.query(EmailTemplate).filter(EmailTemplate.user_id == current_user.id)

    if email_type:
        query = query.filter(EmailTemplate.email_type == email_type)

    if is_active is not None:
        query = query.filter(EmailTemplate.is_active == is_active)

    templates = query.order_by(EmailTemplate.created_at.desc()).all()
    return templates


@router.get('/templates/{template_id}', response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Get a specific email template by ID."""
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_uuid,
        EmailTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.post('/templates', response_model=EmailTemplateResponse)
async def create_email_template(
    template_data: EmailTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Create a new email template."""
    try:
        template = EmailTemplate(
            user_id=current_user.id,
            name=template_data.name,
            template_type=template_data.template_type,
            email_type=template_data.email_type,
            subject=template_data.subject,
            blocks=template_data.blocks,
            primary_color=template_data.primary_color,
            secondary_color=template_data.secondary_color,
            logo_url=template_data.logo_url,
            is_active=template_data.is_active,
            is_default=False
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(f"Created email template: {template.name} (ID: {template.id})")
        return template

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create email template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@router.put('/templates/{template_id}', response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: str,
    template_data: EmailTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Update an existing email template."""
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_uuid,
        EmailTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Don't allow updating default templates
    if template.is_default:
        raise HTTPException(status_code=403, detail="Cannot modify default templates. Create a copy instead.")

    try:
        # Update fields
        for key, value in template_data.dict(exclude_unset=True).items():
            setattr(template, key, value)

        template.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(template)

        logger.info(f"Updated email template: {template.name} (ID: {template.id})")
        return template

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update email template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")


@router.delete('/templates/{template_id}')
async def delete_email_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Delete an email template."""
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_uuid,
        EmailTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Don't allow deleting default templates
    if template.is_default:
        raise HTTPException(status_code=403, detail="Cannot delete default templates")

    try:
        db.delete(template)
        db.commit()

        logger.info(f"Deleted email template: {template.name} (ID: {template.id})")
        return {"message": "Template deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete email template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


@router.post('/templates/{template_id}/preview', response_model=TemplatePreviewResponse)
async def preview_email_template(
    template_id: str,
    preview_data: TemplatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Preview email template with sample data."""
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_uuid,
        EmailTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        email_service = EmailService(db=db)
        html_content = email_service._render_template(template, preview_data.context)
        subject = email_service._substitute_vars(template.subject, preview_data.context)

        return TemplatePreviewResponse(
            html_content=html_content,
            subject=subject
        )

    except Exception as e:
        logger.error(f"Failed to preview template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview template: {str(e)}")


# ============================================================================
# Email Log Endpoints
# ============================================================================

@router.get('/logs', response_model=PaginatedResponse)
async def list_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    email_type: Optional[str] = None,
    order_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    List email logs with pagination and filtering.

    Filters:
    - email_type: Filter by email type (order_confirmation, shipping_notification, marketing)
    - order_id: Filter by specific order
    - start_date/end_date: Date range filter
    - status: SendGrid status (sent, delivered, opened, clicked, bounced, failed)
    """
    query = db.query(EmailLog).filter(EmailLog.user_id == current_user.id)

    # Apply filters
    if email_type:
        query = query.filter(EmailLog.email_type == email_type)

    if order_id:
        try:
            order_uuid = UUID(order_id)
            query = query.filter(EmailLog.order_id == order_uuid)
        except ValueError:
            pass

    if start_date:
        query = query.filter(EmailLog.sent_at >= start_date)

    if end_date:
        query = query.filter(EmailLog.sent_at <= end_date)

    if status:
        query = query.filter(EmailLog.sendgrid_status == status)

    # Get total count
    total = query.count()

    # Paginate
    logs = query.order_by(EmailLog.sent_at.desc()).offset(skip).limit(limit).all()

    return PaginatedResponse(
        items=logs,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=((total - 1) // limit) + 1 if total > 0 else 0
    )


@router.get('/analytics/summary', response_model=EmailAnalyticsResponse)
async def get_email_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Get email analytics summary.

    Returns delivery rates, open rates, click rates, and breakdowns by email type.
    """
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    query = db.query(EmailLog).filter(
        EmailLog.user_id == current_user.id,
        EmailLog.sent_at >= start_date,
        EmailLog.sent_at <= end_date
    )

    # Calculate metrics
    total_sent = query.count()
    total_delivered = query.filter(EmailLog.delivered_at.isnot(None)).count()
    total_opened = query.filter(EmailLog.opened_at.isnot(None)).count()
    total_clicked = query.filter(EmailLog.clicked_at.isnot(None)).count()
    total_bounced = query.filter(EmailLog.sendgrid_status == "bounced").count()
    total_failed = query.filter(EmailLog.sendgrid_status == "failed").count()

    # Calculate rates
    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
    open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
    click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0

    # Breakdown by email type
    by_email_type = {}
    type_counts = db.query(
        EmailLog.email_type,
        func.count(EmailLog.id)
    ).filter(
        EmailLog.user_id == current_user.id,
        EmailLog.sent_at >= start_date,
        EmailLog.sent_at <= end_date
    ).group_by(EmailLog.email_type).all()

    for email_type, count in type_counts:
        by_email_type[email_type] = count

    summary = EmailAnalyticsSummary(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_opened=total_opened,
        total_clicked=total_clicked,
        total_bounced=total_bounced,
        total_failed=total_failed,
        delivery_rate=round(delivery_rate, 2),
        open_rate=round(open_rate, 2),
        click_rate=round(click_rate, 2),
        by_email_type=by_email_type
    )

    return EmailAnalyticsResponse(
        period="custom" if start_date and end_date else "last_30_days",
        start_date=start_date,
        end_date=end_date,
        summary=summary
    )


# ============================================================================
# Email Subscriber Endpoints
# ============================================================================

@router.get('/subscribers', response_model=PaginatedResponse)
async def list_subscribers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    tags: Optional[str] = None,
    is_subscribed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    List email subscribers with pagination and filtering.

    Filters:
    - tags: Comma-separated tags to filter by
    - is_subscribed: Filter by subscription status
    """
    query = db.query(EmailSubscriber).filter(EmailSubscriber.user_id == current_user.id)

    # Apply filters
    if is_subscribed is not None:
        query = query.filter(EmailSubscriber.is_subscribed == is_subscribed)

    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        for tag in tag_list:
            # PostgreSQL JSONB contains operator
            query = query.filter(EmailSubscriber.tags.contains([tag]))

    # Get total count
    total = query.count()

    # Paginate
    subscribers = query.order_by(EmailSubscriber.created_at.desc()).offset(skip).limit(limit).all()

    return PaginatedResponse(
        items=subscribers,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=((total - 1) // limit) + 1 if total > 0 else 0
    )


@router.post('/subscribers', response_model=EmailSubscriberResponse)
async def add_subscriber(
    subscriber_data: EmailSubscriberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Add a new email subscriber."""
    # Check if subscriber already exists
    existing = db.query(EmailSubscriber).filter(
        EmailSubscriber.user_id == current_user.id,
        EmailSubscriber.email == subscriber_data.email
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Subscriber already exists")

    try:
        subscriber = EmailSubscriber(
            user_id=current_user.id,
            email=subscriber_data.email,
            customer_id=UUID(subscriber_data.customer_id) if subscriber_data.customer_id else None,
            tags=subscriber_data.tags,
            is_subscribed=subscriber_data.is_subscribed
        )

        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)

        logger.info(f"Added email subscriber: {subscriber.email}")
        return subscriber

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add subscriber: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add subscriber: {str(e)}")


@router.put('/subscribers/{subscriber_id}', response_model=EmailSubscriberResponse)
async def update_subscriber(
    subscriber_id: str,
    subscriber_data: EmailSubscriberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Update an email subscriber."""
    try:
        subscriber_uuid = UUID(subscriber_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscriber ID format")

    subscriber = db.query(EmailSubscriber).filter(
        EmailSubscriber.id == subscriber_uuid,
        EmailSubscriber.user_id == current_user.id
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    try:
        subscriber.email = subscriber_data.email
        subscriber.customer_id = UUID(subscriber_data.customer_id) if subscriber_data.customer_id else None
        subscriber.tags = subscriber_data.tags
        subscriber.is_subscribed = subscriber_data.is_subscribed

        if not subscriber_data.is_subscribed and subscriber.is_subscribed:
            subscriber.unsubscribed_at = datetime.utcnow()

        subscriber.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(subscriber)

        logger.info(f"Updated email subscriber: {subscriber.email}")
        return subscriber

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update subscriber: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update subscriber: {str(e)}")


@router.delete('/subscribers/{subscriber_id}')
async def delete_subscriber(
    subscriber_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Delete an email subscriber."""
    try:
        subscriber_uuid = UUID(subscriber_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscriber ID format")

    subscriber = db.query(EmailSubscriber).filter(
        EmailSubscriber.id == subscriber_uuid,
        EmailSubscriber.user_id == current_user.id
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    try:
        db.delete(subscriber)
        db.commit()

        logger.info(f"Deleted email subscriber: {subscriber.email}")
        return {"message": "Subscriber deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete subscriber: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete subscriber: {str(e)}")


# ============================================================================
# Marketing Email Endpoints
# ============================================================================

@router.post('/send-marketing', response_model=SendMarketingEmailResponse)
async def send_marketing_email(
    request: SendMarketingEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """
    Send marketing email to recipients.

    Can send immediately or schedule for later.
    Recipients can be specified manually or filtered by criteria.
    """
    try:
        template_uuid = UUID(request.template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    # Verify template exists and belongs to user
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_uuid,
        EmailTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Get recipients
    if request.recipient_emails:
        recipients = request.recipient_emails
    elif request.recipient_filter:
        # Query subscribers based on filter
        query = db.query(EmailSubscriber).filter(
            EmailSubscriber.user_id == current_user.id,
            EmailSubscriber.is_subscribed == True
        )

        if "tags" in request.recipient_filter:
            for tag in request.recipient_filter["tags"]:
                query = query.filter(EmailSubscriber.tags.contains([tag]))

        subscribers = query.all()
        recipients = [s.email for s in subscribers]
    else:
        # No recipients specified
        raise HTTPException(status_code=400, detail="Must specify recipient_emails or recipient_filter")

    if not recipients:
        raise HTTPException(status_code=400, detail="No recipients found")

    # Schedule for later or send immediately
    if request.schedule_for and request.schedule_for > datetime.utcnow():
        # Create scheduled email
        scheduled_email = ScheduledEmail(
            user_id=current_user.id,
            template_id=template_uuid,
            recipient_filter=request.recipient_filter,
            recipient_count=len(recipients),
            scheduled_for=request.schedule_for,
            status="pending"
        )

        db.add(scheduled_email)
        db.commit()
        db.refresh(scheduled_email)

        logger.info(f"Scheduled marketing email for {request.schedule_for}, {len(recipients)} recipients")
        return SendMarketingEmailResponse(
            scheduled_email_id=str(scheduled_email.id),
            recipient_count=len(recipients),
            status="scheduled",
            message=f"Email scheduled for {request.schedule_for}"
        )

    else:
        # Send immediately
        try:
            email_service = EmailService(db=db)
            logs = email_service.send_marketing_email(
                user_id=current_user.id,
                template_id=template_uuid,
                recipients=recipients
            )

            sent_count = len([log for log in logs if log.sendgrid_status == "sent"])

            logger.info(f"Sent marketing email to {sent_count}/{len(recipients)} recipients")
            return SendMarketingEmailResponse(
                recipient_count=len(recipients),
                sent_count=sent_count,
                status="sent",
                message=f"Email sent to {sent_count}/{len(recipients)} recipients"
            )

        except Exception as e:
            logger.error(f"Failed to send marketing email: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


# ============================================================================
# Scheduled Email Endpoints
# ============================================================================

@router.get('/scheduled', response_model=List[ScheduledEmailResponse])
async def list_scheduled_emails(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """List scheduled marketing emails."""
    query = db.query(ScheduledEmail).filter(ScheduledEmail.user_id == current_user.id)

    if status:
        query = query.filter(ScheduledEmail.status == status)

    scheduled_emails = query.order_by(ScheduledEmail.scheduled_for.desc()).all()
    return scheduled_emails


@router.delete('/scheduled/{scheduled_email_id}')
async def cancel_scheduled_email(
    scheduled_email_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pro_plan)
):
    """Cancel a scheduled email."""
    try:
        scheduled_uuid = UUID(scheduled_email_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scheduled email ID format")

    scheduled_email = db.query(ScheduledEmail).filter(
        ScheduledEmail.id == scheduled_uuid,
        ScheduledEmail.user_id == current_user.id
    ).first()

    if not scheduled_email:
        raise HTTPException(status_code=404, detail="Scheduled email not found")

    if scheduled_email.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending scheduled emails")

    try:
        scheduled_email.status = "cancelled"
        scheduled_email.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Cancelled scheduled email: {scheduled_email.id}")
        return {"message": "Scheduled email cancelled successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cancel scheduled email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel scheduled email: {str(e)}")
