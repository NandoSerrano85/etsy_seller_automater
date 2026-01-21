"""
Subscription service layer for Stripe integration
"""

import logging
import os
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import stripe

from server.src.entities.subscription import Subscription, BillingHistory, SubscriptionUsage
from server.src.entities.user import User
from server.src.entities.ecommerce.storefront_settings import StorefrontSettings
import secrets

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Subscription tier configurations with Stripe Price IDs
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'stripe_price_id': None,
        'description': 'Get started with basic mockup creation',
        'features': {
            # Mockup Generator - Limited
            'mockup_generator': True,
            'monthly_mockup_limit': 15,
            'mockups_per_batch': 1,  # Can only create 1 mockup at a time
            'max_templates': 1,
            'max_canvas': 1,
            'max_sizes': 1,
            # Etsy - View & Edit
            'etsy_integration': True,
            'etsy_view_mockups': True,
            'etsy_view_designs': True,
            'etsy_view_listings': True,
            'etsy_edit_listings': True,
            'etsy_view_orders': True,
            # Not included
            'shopify_integration': False,
            'craftflow_commerce': False,
            'batch_uploads': False,
            'file_cleaner': False,
            'auto_naming': False,
            'advanced_resizing': False,
            'print_file_generator': False,
            'csv_export': False,
            'multi_shop_support': False,
            'priority_support': False
        },
        'limits': {
            'monthly_mockups': 15,
            'mockups_per_batch': 1,
            'templates': 1,
            'canvas': 1,
            'sizes': 1
        }
    },
    'starter': {
        'name': 'Starter',
        'price': 19.99,
        'stripe_price_id': os.getenv('STRIPE_STARTER_PRICE_ID'),
        'description': 'Perfect for growing sellers',
        'features': {
            # Mockup Generator - Enhanced
            'mockup_generator': True,
            'monthly_mockup_limit': 100,
            'mockups_per_batch': 10,
            'max_templates': 10,
            'max_canvas': 5,
            'max_sizes': 10,
            # Etsy - Full access
            'etsy_integration': True,
            'etsy_view_mockups': True,
            'etsy_view_designs': True,
            'etsy_view_listings': True,
            'etsy_edit_listings': True,
            'etsy_view_orders': True,
            'etsy_manage_orders': True,
            # Additional features
            'file_cleaner': True,
            'auto_naming': True,
            'batch_uploads': True,
            # Not included
            'shopify_integration': False,
            'craftflow_commerce': False,
            'advanced_resizing': False,
            'print_file_generator': False,
            'csv_export': False,
            'multi_shop_support': False,
            'priority_support': False
        },
        'limits': {
            'monthly_mockups': 100,
            'mockups_per_batch': 10,
            'templates': 10,
            'canvas': 5,
            'sizes': 10
        }
    },
    'pro': {
        'name': 'Pro',
        'price': 39.99,
        'stripe_price_id': os.getenv('STRIPE_PRO_PRICE_ID'),
        'description': 'For serious sellers who want more',
        'features': {
            # Mockup Generator - Unlimited
            'mockup_generator': True,
            'monthly_mockup_limit': -1,  # Unlimited
            'mockups_per_batch': 50,
            'max_templates': -1,  # Unlimited
            'max_canvas': -1,
            'max_sizes': -1,
            # Etsy - Full access
            'etsy_integration': True,
            'etsy_view_mockups': True,
            'etsy_view_designs': True,
            'etsy_view_listings': True,
            'etsy_edit_listings': True,
            'etsy_view_orders': True,
            'etsy_manage_orders': True,
            # Shopify integration
            'shopify_integration': True,
            # All additional features
            'file_cleaner': True,
            'auto_naming': True,
            'batch_uploads': True,
            'advanced_resizing': True,
            'print_file_generator': True,
            'csv_export': True,
            # Not included
            'craftflow_commerce': False,
            'multi_shop_support': False,
            'priority_support': False
        },
        'limits': {
            'monthly_mockups': -1,
            'mockups_per_batch': 50,
            'templates': -1,
            'canvas': -1,
            'sizes': -1
        }
    },
    'full': {
        'name': 'Full',
        'price': 99.99,
        'stripe_price_id': os.getenv('STRIPE_FULL_PRICE_ID'),
        'description': 'Everything you need to scale',
        'features': {
            # Mockup Generator - Unlimited
            'mockup_generator': True,
            'monthly_mockup_limit': -1,
            'mockups_per_batch': -1,  # Unlimited
            'max_templates': -1,
            'max_canvas': -1,
            'max_sizes': -1,
            # Etsy - Full access
            'etsy_integration': True,
            'etsy_view_mockups': True,
            'etsy_view_designs': True,
            'etsy_view_listings': True,
            'etsy_edit_listings': True,
            'etsy_view_orders': True,
            'etsy_manage_orders': True,
            # Shopify integration
            'shopify_integration': True,
            # CraftFlow Commerce
            'craftflow_commerce': True,
            # All features
            'file_cleaner': True,
            'auto_naming': True,
            'batch_uploads': True,
            'advanced_resizing': True,
            'print_file_generator': True,
            'csv_export': True,
            'multi_shop_support': True,
            'priority_support': True
        },
        'limits': {
            'monthly_mockups': -1,
            'mockups_per_batch': -1,
            'templates': -1,
            'canvas': -1,
            'sizes': -1
        }
    }
}


class SubscriptionService:

    @staticmethod
    def get_or_create_customer(db: Session, user_id: UUID, email: str) -> str:
        """Get or create a Stripe customer for the user"""
        try:
            # Check if user already has a subscription with customer ID
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            if subscription and subscription.stripe_customer_id:
                return subscription.stripe_customer_id

            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={'user_id': str(user_id)}
            )

            # Create or update subscription record
            if not subscription:
                subscription = Subscription(
                    user_id=user_id,
                    stripe_customer_id=customer.id,
                    tier='free',
                    status='active'
                )
                db.add(subscription)
            else:
                subscription.stripe_customer_id = customer.id

            db.commit()
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating Stripe customer: {e}")
            raise

    @staticmethod
    def create_checkout_session(
        db: Session,
        user_id: UUID,
        email: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> dict:
        """Create a Stripe checkout session for subscription"""
        try:
            customer_id = SubscriptionService.get_or_create_customer(db, user_id, email)

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'user_id': str(user_id)}
            )

            logger.info(f"Created checkout session {session.id} for user {user_id}")
            return {
                'session_id': session.id,
                'url': session.url
            }

        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise

    @staticmethod
    def get_subscription(db: Session, user_id: UUID) -> Optional[Subscription]:
        """Get user's subscription"""
        logger.info(f"Querying subscription for user_id: {user_id} (type: {type(user_id)})")
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        if subscription:
            logger.info(f"Found subscription: id={subscription.id}, tier={subscription.tier}, user_id={subscription.user_id}")
        else:
            logger.info(f"No subscription found for user_id: {user_id}")
        return subscription

    @staticmethod
    def update_subscription_from_stripe(
        db: Session,
        stripe_subscription: dict
    ) -> Subscription:
        """Update subscription from Stripe webhook data"""
        try:
            user_id = UUID(stripe_subscription['metadata'].get('user_id'))

            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            if not subscription:
                subscription = Subscription(user_id=user_id)
                db.add(subscription)

            # Map Stripe data to our model
            subscription.stripe_subscription_id = stripe_subscription['id']
            subscription.stripe_customer_id = stripe_subscription['customer']
            subscription.stripe_price_id = stripe_subscription['items']['data'][0]['price']['id']
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription['current_period_start'],
                tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription['current_period_end'],
                tz=timezone.utc
            )
            subscription.cancel_at_period_end = stripe_subscription.get('cancel_at_period_end', False)

            # Determine tier from price ID
            old_tier = subscription.tier
            price_id = subscription.stripe_price_id
            for tier_key, tier_config in SUBSCRIPTION_TIERS.items():
                if tier_config.get('stripe_price_id') == price_id:
                    subscription.tier = tier_key
                    break

            new_tier = subscription.tier

            # Update user's subscription plan
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.subscription_plan = subscription.tier

            db.commit()
            db.refresh(subscription)

            logger.info(f"Updated subscription for user {user_id} to tier {subscription.tier}")

            # Handle subscription upgrade side effects (auto-provisioning, etc.)
            if old_tier != new_tier:
                SubscriptionService.handle_subscription_upgrade(db, user_id, old_tier, new_tier)

            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating subscription from Stripe: {e}")
            raise

    @staticmethod
    def cancel_subscription(
        db: Session,
        user_id: UUID,
        cancel_immediately: bool = False
    ) -> Subscription:
        """Cancel a subscription"""
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            if not subscription or not subscription.stripe_subscription_id:
                raise ValueError("No active subscription found")

            # Cancel in Stripe
            if cancel_immediately:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.now(timezone.utc)
            else:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True

            db.commit()
            db.refresh(subscription)

            logger.info(f"Canceled subscription for user {user_id}")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"Error canceling subscription: {e}")
            raise

    @staticmethod
    def update_subscription_tier(
        db: Session,
        user_id: UUID,
        new_price_id: str
    ) -> Subscription:
        """Update subscription to a new tier"""
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            if not subscription or not subscription.stripe_subscription_id:
                raise ValueError("No active subscription found")

            # Get current subscription from Stripe
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )

            # Update subscription in Stripe
            updated_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations'
            )

            # Update local subscription
            subscription.stripe_price_id = new_price_id

            # Determine new tier
            for tier_key, tier_config in SUBSCRIPTION_TIERS.items():
                if tier_config.get('stripe_price_id') == new_price_id:
                    subscription.tier = tier_key
                    break

            # Update user's subscription plan
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.subscription_plan = subscription.tier

            db.commit()
            db.refresh(subscription)

            logger.info(f"Updated subscription tier for user {user_id} to {subscription.tier}")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating subscription tier: {e}")
            raise

    @staticmethod
    def get_billing_history(db: Session, user_id: UUID, limit: int = 10) -> List[BillingHistory]:
        """Get billing history for a user"""
        return db.query(BillingHistory).filter(
            BillingHistory.user_id == user_id
        ).order_by(BillingHistory.invoice_date.desc()).limit(limit).all()

    @staticmethod
    def create_customer_portal_session(
        db: Session,
        user_id: UUID,
        return_url: str
    ) -> dict:
        """Create a Stripe customer portal session"""
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            if not subscription or not subscription.stripe_customer_id:
                raise ValueError("No Stripe customer found")

            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url
            )

            return {'url': session.url}

        except Exception as e:
            logger.error(f"Error creating customer portal session: {e}")
            raise

    @staticmethod
    def record_invoice(db: Session, stripe_invoice: dict):
        """Record an invoice from Stripe webhook"""
        try:
            user_id = UUID(stripe_invoice['metadata'].get('user_id'))

            # Check if invoice already exists
            existing = db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == stripe_invoice['id']
            ).first()

            if existing:
                return existing

            # Get subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            invoice = BillingHistory(
                user_id=user_id,
                subscription_id=subscription.id if subscription else None,
                stripe_invoice_id=stripe_invoice['id'],
                stripe_charge_id=stripe_invoice.get('charge'),
                amount=stripe_invoice['amount_paid'] / 100,  # Convert cents to dollars
                currency=stripe_invoice['currency'],
                status=stripe_invoice['status'],
                invoice_date=datetime.fromtimestamp(stripe_invoice['created'], tz=timezone.utc),
                paid_at=datetime.fromtimestamp(stripe_invoice['status_transitions']['paid_at'], tz=timezone.utc) if stripe_invoice['status_transitions'].get('paid_at') else None,
                invoice_pdf_url=stripe_invoice.get('invoice_pdf'),
                hosted_invoice_url=stripe_invoice.get('hosted_invoice_url'),
                description=stripe_invoice.get('description')
            )

            db.add(invoice)
            db.commit()

            logger.info(f"Recorded invoice {invoice.stripe_invoice_id} for user {user_id}")
            return invoice

        except Exception as e:
            db.rollback()
            logger.error(f"Error recording invoice: {e}")
            raise

    @staticmethod
    def get_tier_config(tier: str) -> dict:
        """Get configuration for a subscription tier"""
        return SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS['free'])

    @staticmethod
    def get_all_tier_configs() -> dict:
        """Get all tier configurations"""
        return SUBSCRIPTION_TIERS

    @staticmethod
    def get_usage_stats(db: Session, user_id: UUID) -> dict:
        """Get usage statistics for the current month"""
        from sqlalchemy import func
        from server.src.entities.mockup import Mockups, MockupImage
        from server.src.entities.designs import DesignImages

        try:
            now = datetime.now(timezone.utc)
            current_month = now.month
            current_year = now.year

            # Get start of current month
            month_start = datetime(current_year, current_month, 1, tzinfo=timezone.utc)

            # Count mockups created this month
            mockups_count = db.query(func.count(Mockups.id)).filter(
                Mockups.user_id == user_id,
                Mockups.created_at >= month_start
            ).scalar() or 0

            # Count total mockups (all-time)
            total_mockups = db.query(func.count(Mockups.id)).filter(
                Mockups.user_id == user_id
            ).scalar() or 0

            # Count total mockup images/options (all-time)
            total_mockup_images = db.query(func.count(MockupImage.id)).join(
                Mockups, MockupImage.mockups_id == Mockups.id
            ).filter(
                Mockups.user_id == user_id
            ).scalar() or 0

            # Count designs uploaded this month
            designs_count = db.query(func.count(DesignImages.id)).filter(
                DesignImages.user_id == user_id,
                DesignImages.created_at >= month_start
            ).scalar() or 0

            # Get tier from users.subscription_plan (single source of truth)
            user = db.query(User).filter(User.id == user_id).first()
            tier = user.subscription_plan if user and user.subscription_plan else 'free'
            tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS['free'])
            limits = tier_config.get('limits', {})

            # Calculate next billing date (1st of next month)
            if current_month == 12:
                next_billing_date = datetime(current_year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                next_billing_date = datetime(current_year, current_month + 1, 1, tzinfo=timezone.utc)

            return {
                "mockups_created": mockups_count,
                "total_mockups": total_mockups,
                "total_mockup_images": total_mockup_images,
                "designs_uploaded": designs_count,
                "mockups_limit": limits.get('monthly_mockups', -1),
                "month": current_month,
                "year": current_year,
                "tier": tier,
                "next_billing_date": next_billing_date.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {
                "mockups_created": 0,
                "total_mockups": 0,
                "total_mockup_images": 0,
                "designs_uploaded": 0,
                "mockups_limit": -1,
                "month": datetime.now(timezone.utc).month,
                "year": datetime.now(timezone.utc).year,
                "tier": "free",
                "next_billing_date": None
            }

    @staticmethod
    def provision_storefront_for_tier(db: Session, user_id: UUID, tier: str) -> Optional[StorefrontSettings]:
        """
        Auto-provision storefront settings when a user upgrades to a qualifying tier.

        For "full" or "pro" tier users, this creates their StorefrontSettings if they don't exist,
        enabling them to set up their own storefront.

        Args:
            db: Database session
            user_id: The user's UUID
            tier: The subscription tier

        Returns:
            StorefrontSettings if created/updated, None if not applicable
        """
        # Only provision for full tier (CraftFlow Commerce access)
        qualifying_tiers = ['full']

        if tier not in qualifying_tiers:
            return None

        try:
            # Check if user already has storefront settings
            existing = db.query(StorefrontSettings).filter(
                StorefrontSettings.user_id == user_id
            ).first()

            if existing:
                logger.info(f"User {user_id} already has storefront settings")
                return existing

            # Get user info for defaults
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found for storefront provisioning")
                return None

            # Generate a unique subdomain suggestion based on shop name
            base_subdomain = (user.shop_name or user.email.split('@')[0]).lower()
            # Clean the subdomain - only allow alphanumeric and hyphens
            base_subdomain = ''.join(c if c.isalnum() else '-' for c in base_subdomain)
            base_subdomain = base_subdomain.strip('-')[:50]  # Limit length

            # Check if subdomain is available
            subdomain = base_subdomain
            counter = 1
            while db.query(StorefrontSettings).filter(
                StorefrontSettings.subdomain == subdomain
            ).first():
                subdomain = f"{base_subdomain}-{counter}"
                counter += 1

            # Generate verification token
            verification_token = secrets.token_urlsafe(32)

            # Create storefront settings with defaults
            storefront = StorefrontSettings(
                user_id=user_id,
                store_name=user.shop_name or "My Store",
                store_description=f"Welcome to {user.shop_name or 'my store'}",
                subdomain=subdomain,
                domain_verification_token=verification_token,
                # Default theme colors
                primary_color="#10b981",
                secondary_color="#059669",
                accent_color="#34d399",
                text_color="#111827",
                background_color="#ffffff",
                font_family="Inter",
                # Default settings
                currency="USD",
                timezone="America/New_York",
                # Status
                is_active=True,
                is_published=False,  # Start unpublished until user configures
                maintenance_mode=False,
            )

            db.add(storefront)
            db.commit()
            db.refresh(storefront)

            logger.info(f"Auto-provisioned storefront for user {user_id} with subdomain: {subdomain}")
            return storefront

        except Exception as e:
            db.rollback()
            logger.error(f"Error provisioning storefront for user {user_id}: {e}")
            return None

    @staticmethod
    def handle_subscription_upgrade(db: Session, user_id: UUID, old_tier: str, new_tier: str):
        """
        Handle side effects of subscription tier changes.

        This is called when a subscription is upgraded or downgraded.

        Args:
            db: Database session
            user_id: The user's UUID
            old_tier: Previous subscription tier
            new_tier: New subscription tier
        """
        try:
            # Define tier hierarchy
            tier_levels = {
                'free': 0,
                'starter': 1,
                'pro': 2,
                'full': 3
            }

            old_level = tier_levels.get(old_tier, 0)
            new_level = tier_levels.get(new_tier, 0)

            # Upgrade: provision new features
            if new_level > old_level:
                logger.info(f"User {user_id} upgraded from {old_tier} to {new_tier}")

                # Auto-provision storefront for qualifying tiers
                if new_tier in ['full']:
                    storefront = SubscriptionService.provision_storefront_for_tier(db, user_id, new_tier)
                    if storefront:
                        logger.info(f"Storefront provisioned for user {user_id} on upgrade to {new_tier}")

            # Downgrade: optionally clean up or notify
            elif new_level < old_level:
                logger.info(f"User {user_id} downgraded from {old_tier} to {new_tier}")
                # Note: We don't remove storefront settings on downgrade
                # The user retains their data but loses access to features

        except Exception as e:
            logger.error(f"Error handling subscription upgrade for user {user_id}: {e}")
