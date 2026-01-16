"""
Subscription API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.routes.subscriptions import model, service
from server.src.entities.user import User
from typing import List
import stripe
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/checkout", response_model=model.CreateCheckoutSessionResponse)
async def create_checkout_session(
    request_data: model.CreateCheckoutSessionRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for subscription"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get user email from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = service.SubscriptionService.create_checkout_session(
            db=db,
            user_id=user_id,
            email=user.email,
            price_id=request_data.price_id,
            success_url=request_data.success_url,
            cancel_url=request_data.cancel_url
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=model.SubscriptionResponse)
async def get_current_subscription(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get current user's subscription"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        subscription = service.SubscriptionService.get_subscription(db, user_id)

        if not subscription:
            # Return a default free subscription
            return model.SubscriptionResponse(
                id="",
                user_id=str(user_id),
                tier="free",
                status="active",
                current_period_start=None,
                current_period_end=None,
                cancel_at_period_end=False,
                canceled_at=None,
                stripe_customer_id=None,
                stripe_subscription_id=None
            )

        return model.SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            tier=subscription.tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id
        )

    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update", response_model=model.SubscriptionResponse)
async def update_subscription(
    request_data: model.UpdateSubscriptionRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update subscription to a new tier"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        subscription = service.SubscriptionService.update_subscription_tier(
            db=db,
            user_id=user_id,
            new_price_id=request_data.new_price_id
        )

        return model.SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            tier=subscription.tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    request_data: model.CancelSubscriptionRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Cancel subscription"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        subscription = service.SubscriptionService.cancel_subscription(
            db=db,
            user_id=user_id,
            cancel_immediately=request_data.cancel_immediately
        )

        return {
            "success": True,
            "message": "Subscription canceled successfully",
            "cancel_at_period_end": subscription.cancel_at_period_end
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billing-history", response_model=List[model.BillingHistoryResponse])
async def get_billing_history(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get billing history"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        history = service.SubscriptionService.get_billing_history(db, user_id, limit)

        return [
            model.BillingHistoryResponse(
                id=str(item.id),
                amount=float(item.amount),
                currency=item.currency,
                status=item.status,
                invoice_date=item.invoice_date,
                paid_at=item.paid_at,
                invoice_pdf_url=item.invoice_pdf_url,
                hosted_invoice_url=item.hosted_invoice_url,
                description=item.description
            )
            for item in history
        ]

    except Exception as e:
        logger.error(f"Error getting billing history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer-portal", response_model=model.CustomerPortalResponse)
async def create_customer_portal(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    return_url: str = "http://localhost:3000/account?tab=subscription"
):
    """Create Stripe customer portal session"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        result = service.SubscriptionService.create_customer_portal_session(
            db=db,
            user_id=user_id,
            return_url=return_url
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer portal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiers")
async def get_subscription_tiers():
    """Get all subscription tier configurations"""
    tiers = service.SubscriptionService.get_all_tier_configs()

    return {
        "tiers": [
            {
                "id": tier_key,
                "name": tier_config['name'],
                "price": tier_config['price'],
                "stripe_price_id": tier_config.get('stripe_price_id'),
                "description": tier_config.get('description', ''),
                "features": tier_config['features'],
                "limits": tier_config.get('limits', {})
            }
            for tier_key, tier_config in tiers.items()
        ]
    }


@router.get("/usage")
async def get_usage_stats(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get current month's usage statistics"""
    try:
        user_id = current_user.get_uuid()

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        usage = service.SubscriptionService.get_usage_stats(db, user_id)

        return usage

    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None)
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

        if not webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not set, skipping signature verification")
            event = stripe.Event.construct_from(
                await request.json(), stripe.api_key
            )
        else:
            try:
                event = stripe.Webhook.construct_event(
                    payload, stripe_signature, webhook_secret
                )
            except ValueError as e:
                logger.error(f"Invalid payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid signature: {e}")
                raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            logger.info(f"Checkout session completed: {session.id}")

            # Retrieve the subscription
            if session.subscription:
                subscription = stripe.Subscription.retrieve(session.subscription)
                service.SubscriptionService.update_subscription_from_stripe(db, subscription)

        elif event.type == 'customer.subscription.updated':
            subscription = event.data.object
            logger.info(f"Subscription updated: {subscription.id}")
            service.SubscriptionService.update_subscription_from_stripe(db, subscription)

        elif event.type == 'customer.subscription.deleted':
            subscription = event.data.object
            logger.info(f"Subscription deleted: {subscription.id}")
            service.SubscriptionService.update_subscription_from_stripe(db, subscription)

        elif event.type == 'invoice.paid':
            invoice = event.data.object
            logger.info(f"Invoice paid: {invoice.id}")
            service.SubscriptionService.record_invoice(db, invoice)

        elif event.type == 'invoice.payment_failed':
            invoice = event.data.object
            logger.warning(f"Invoice payment failed: {invoice.id}")
            service.SubscriptionService.record_invoice(db, invoice)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
