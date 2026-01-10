"""Webhook handlers for ecommerce integrations."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from server.src.database.core import get_db
from server.src.entities.ecommerce.email_log import EmailLog
from server.src.entities.ecommerce.email_subscriber import EmailSubscriber

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/ecommerce/webhooks',
    tags=['Ecommerce - Webhooks']
)


@router.post('/sendgrid')
async def sendgrid_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle SendGrid webhook events for email tracking.

    SendGrid Event Types:
    - delivered: Email was delivered to recipient's server
    - opened: Recipient opened the email
    - click: Recipient clicked a link in the email
    - bounce: Email bounced (hard or soft)
    - dropped: SendGrid dropped the email (spam, unsubscribed, etc.)
    - deferred: Temporary delivery failure
    - processed: SendGrid received and will attempt to deliver

    This endpoint updates email logs with delivery status and updates
    subscriber analytics (open/click counts).
    """
    try:
        # SendGrid sends events as JSON array
        events = await request.json()

        if not isinstance(events, list):
            events = [events]

        logger.info(f"Received {len(events)} SendGrid webhook events")

        for event in events:
            try:
                # Extract event data
                sendgrid_message_id = event.get('sg_message_id')
                event_type = event.get('event')  # delivered, open, click, bounce, etc.
                timestamp = event.get('timestamp')
                email = event.get('email')

                if not sendgrid_message_id or not event_type:
                    logger.warning(f"Incomplete event data: {event}")
                    continue

                # Convert timestamp to datetime
                event_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.utcnow()

                # Find email log by SendGrid message ID
                email_log = db.query(EmailLog).filter(
                    EmailLog.sendgrid_message_id == sendgrid_message_id
                ).first()

                if not email_log:
                    logger.warning(f"No email log found for message ID: {sendgrid_message_id}")
                    continue

                # Update email log status
                email_log.sendgrid_status = event_type

                if event_type == "delivered":
                    email_log.delivered_at = event_time
                    logger.info(f"Email delivered: {sendgrid_message_id} to {email}")

                elif event_type == "open":
                    if not email_log.opened_at:
                        email_log.opened_at = event_time
                        logger.info(f"Email opened: {sendgrid_message_id} by {email}")

                        # Update subscriber stats
                        if email_log.customer_id:
                            subscriber = db.query(EmailSubscriber).filter(
                                EmailSubscriber.user_id == email_log.user_id,
                                EmailSubscriber.customer_id == email_log.customer_id
                            ).first()
                            if subscriber:
                                subscriber.total_opened += 1

                        elif email:
                            subscriber = db.query(EmailSubscriber).filter(
                                EmailSubscriber.user_id == email_log.user_id,
                                EmailSubscriber.email == email
                            ).first()
                            if subscriber:
                                subscriber.total_opened += 1

                elif event_type == "click":
                    if not email_log.clicked_at:
                        email_log.clicked_at = event_time
                        logger.info(f"Email clicked: {sendgrid_message_id} by {email}")

                        # Update subscriber stats
                        if email_log.customer_id:
                            subscriber = db.query(EmailSubscriber).filter(
                                EmailSubscriber.user_id == email_log.user_id,
                                EmailSubscriber.customer_id == email_log.customer_id
                            ).first()
                            if subscriber:
                                subscriber.total_clicked += 1

                        elif email:
                            subscriber = db.query(EmailSubscriber).filter(
                                EmailSubscriber.user_id == email_log.user_id,
                                EmailSubscriber.email == email
                            ).first()
                            if subscriber:
                                subscriber.total_clicked += 1

                elif event_type == "bounce":
                    bounce_reason = event.get('reason', '')
                    email_log.error_message = f"Bounced: {bounce_reason}"
                    logger.warning(f"Email bounced: {sendgrid_message_id} - {bounce_reason}")

                elif event_type == "dropped":
                    drop_reason = event.get('reason', '')
                    email_log.error_message = f"Dropped: {drop_reason}"
                    email_log.sendgrid_status = "failed"
                    logger.warning(f"Email dropped: {sendgrid_message_id} - {drop_reason}")

                elif event_type == "spamreport":
                    # User marked email as spam - unsubscribe them
                    if email:
                        subscriber = db.query(EmailSubscriber).filter(
                            EmailSubscriber.user_id == email_log.user_id,
                            EmailSubscriber.email == email
                        ).first()
                        if subscriber and subscriber.is_subscribed:
                            subscriber.is_subscribed = False
                            subscriber.unsubscribed_at = datetime.utcnow()
                            logger.info(f"Auto-unsubscribed {email} due to spam report")

                # Commit after each event
                db.commit()

            except Exception as e:
                logger.error(f"Error processing individual webhook event: {e}")
                db.rollback()
                # Continue processing other events
                continue

        return {"status": "success", "processed": len(events)}

    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/sendgrid/health')
async def sendgrid_webhook_health():
    """Health check endpoint for SendGrid webhook configuration."""
    return {
        "status": "healthy",
        "webhook": "sendgrid",
        "message": "Webhook endpoint is ready to receive events"
    }
