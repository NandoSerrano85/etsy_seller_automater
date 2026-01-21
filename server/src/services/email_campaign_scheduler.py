"""
Email Campaign Scheduler Service.

Background service that polls the database for scheduled email campaigns
and executes them at the scheduled time.
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List

from server.src.database import SessionLocal
from server.src.entities.ecommerce.scheduled_email import ScheduledEmail
from server.src.entities.ecommerce.email_subscriber import EmailSubscriber
from server.src.services.email_service import EmailService

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
_scheduler_running = False


async def start_email_campaign_scheduler():
    """Start the email campaign scheduler background task."""
    global _scheduler_running
    _scheduler_running = True

    logger.info("Email campaign scheduler starting...")

    # Run continuously, checking every 60 seconds
    while _scheduler_running:
        try:
            process_scheduled_campaigns()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")

        # Wait 60 seconds before next check
        await asyncio.sleep(60)

    logger.info("Email campaign scheduler stopped")


def stop_email_campaign_scheduler():
    """Stop the email campaign scheduler."""
    global _scheduler_running
    logger.info("Stopping email campaign scheduler...")
    _scheduler_running = False


def process_scheduled_campaigns():
    """Poll database for pending campaigns and execute them."""
    db = SessionLocal()

    try:
        # Find campaigns ready to send
        now = datetime.utcnow()
        campaigns = db.query(ScheduledEmail).filter(
            ScheduledEmail.status == 'pending',
            ScheduledEmail.scheduled_for <= now
        ).all()

        if campaigns:
            logger.info(f"Found {len(campaigns)} scheduled campaigns ready to execute")

        for campaign in campaigns:
            try:
                execute_campaign(campaign, db)
            except Exception as e:
                logger.error(f"Error executing campaign {campaign.id}: {e}")
                # Mark campaign as failed
                campaign.status = 'failed'
                campaign.completed_at = datetime.utcnow()
                try:
                    db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to commit campaign failure: {commit_error}")
                    db.rollback()

    except Exception as e:
        logger.error(f"Error in process_scheduled_campaigns: {e}")

    finally:
        db.close()


def execute_campaign(campaign: ScheduledEmail, db: Session):
    """
    Execute a single email campaign.

    Args:
        campaign: ScheduledEmail instance to execute
        db: Database session
    """
    logger.info(f"Executing campaign {campaign.id} scheduled for {campaign.scheduled_for}")

    # Update status to processing
    campaign.status = 'processing'
    campaign.started_at = datetime.utcnow()
    db.commit()

    try:
        # Resolve recipients from filter
        recipients = resolve_recipients(campaign, db)

        if not recipients:
            logger.warning(f"Campaign {campaign.id} has no recipients")
            campaign.status = 'completed'
            campaign.sent_count = 0
            campaign.failed_count = 0
            campaign.completed_at = datetime.utcnow()
            db.commit()
            return

        logger.info(f"Sending campaign {campaign.id} to {len(recipients)} recipients")

        # Send emails via EmailService
        email_service = EmailService(db=db)
        logs = email_service.send_marketing_email(
            user_id=campaign.user_id,
            template_id=campaign.template_id,
            recipients=recipients,
            scheduled_email_id=campaign.id
        )

        # Update campaign with results
        campaign.sent_count = len([log for log in logs if log.sendgrid_status != 'failed'])
        campaign.failed_count = len([log for log in logs if log.sendgrid_status == 'failed'])
        campaign.status = 'completed'
        campaign.completed_at = datetime.utcnow()

        db.commit()
        logger.info(f"Campaign {campaign.id} completed: {campaign.sent_count} sent, {campaign.failed_count} failed")

    except Exception as e:
        logger.error(f"Failed to execute campaign {campaign.id}: {e}")
        campaign.status = 'failed'
        campaign.completed_at = datetime.utcnow()
        db.commit()
        raise


def resolve_recipients(campaign: ScheduledEmail, db: Session) -> List[str]:
    """
    Resolve recipient email addresses from campaign filter.

    Args:
        campaign: ScheduledEmail instance with recipient_filter
        db: Database session

    Returns:
        List of recipient email addresses
    """
    recipients = []

    if campaign.recipient_filter:
        # Query subscribers based on filter
        query = db.query(EmailSubscriber).filter(
            EmailSubscriber.user_id == campaign.user_id,
            EmailSubscriber.is_subscribed == True
        )

        # Apply tag filters if present
        if 'tags' in campaign.recipient_filter:
            tags = campaign.recipient_filter['tags']
            if isinstance(tags, list):
                # Filter for subscribers that have all the specified tags
                for tag in tags:
                    query = query.filter(EmailSubscriber.tags.contains([tag]))

        # Get all matching subscribers
        subscribers = query.all()
        recipients = [sub.email for sub in subscribers]

        logger.info(f"Resolved {len(recipients)} recipients from filter: {campaign.recipient_filter}")

    return recipients
