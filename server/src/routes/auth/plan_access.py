"""
Plan-based access control for subscription tiers.

Subscription tiers (from lowest to highest):
- free: Basic features (15 mockups/month)
- starter: Additional features (100 mockups/month)
- pro: Shopify integration, advanced features (unlimited mockups)
- full: All features including CraftFlow Commerce, multi-tenant storefronts

This module provides dependencies to restrict access based on subscription plan.
"""

from fastapi import HTTPException, status, Depends
from server.src.entities.user import User
from server.src.routes.auth.service import get_current_user_db as get_current_user
from typing import List


# Define plan hierarchy (higher index = higher tier)
# Note: 'basic' is aliased to 'starter', 'enterprise' is aliased to 'full' for backwards compatibility
PLAN_HIERARCHY = ["free", "starter", "pro", "full"]
PLAN_ALIASES = {
    "basic": "starter",
    "enterprise": "full",
}


def get_plan_level(plan: str) -> int:
    """Get the numeric level of a subscription plan."""
    if not plan:
        return 0

    plan_lower = plan.lower()

    # Handle aliases
    plan_lower = PLAN_ALIASES.get(plan_lower, plan_lower)

    try:
        return PLAN_HIERARCHY.index(plan_lower)
    except ValueError:
        return 0  # Default to free if plan is unknown


def has_plan_access(user_plan: str, required_plan: str) -> bool:
    """
    Check if a user's plan has access to features requiring a certain plan.

    Args:
        user_plan: The user's current subscription plan
        required_plan: The minimum required plan

    Returns:
        True if user has access, False otherwise
    """
    user_level = get_plan_level(user_plan)
    required_level = get_plan_level(required_plan)
    return user_level >= required_level


def require_plan(required_plan: str):
    """
    Dependency to require a minimum subscription plan.

    Usage:
        @router.get("/")
        async def my_endpoint(user: User = Depends(require_plan("pro"))):
            # Only users with 'pro' or 'enterprise' plans can access this
            ...

    Args:
        required_plan: Minimum required plan (e.g., "pro")

    Returns:
        Dependency function that checks plan access
    """
    async def check_plan_access(user: User = Depends(get_current_user)) -> User:
        if not has_plan_access(user.subscription_plan, required_plan):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"This feature requires a {required_plan} plan or higher",
                    "current_plan": user.subscription_plan,
                    "required_plan": required_plan,
                    "upgrade_needed": True
                }
            )
        return user

    return check_plan_access


# Pre-made dependencies for common plan requirements
require_starter_plan = require_plan("starter")
require_pro_plan = require_plan("pro")
require_full_plan = require_plan("full")

# Backwards compatibility aliases
require_basic_plan = require_starter_plan
require_enterprise_plan = require_full_plan


def get_user_with_plan_info(user: User = Depends(get_current_user)) -> dict:
    """
    Get current user with plan access information.

    Returns:
        Dictionary with user and plan access levels
    """
    return {
        "user": user,
        "subscription_plan": user.subscription_plan,
        "plan_level": get_plan_level(user.subscription_plan),
        "has_pro_access": has_plan_access(user.subscription_plan, "pro"),
        "has_basic_access": has_plan_access(user.subscription_plan, "basic"),
        "has_enterprise_access": has_plan_access(user.subscription_plan, "enterprise"),
    }
