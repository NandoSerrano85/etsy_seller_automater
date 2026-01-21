"""
Admin endpoints for user management.

Allows administrators to manage user accounts and subscription plans.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from server.src.database.core import get_db
from server.src.entities.user import User
from server.src.routes.auth.service import get_current_user_db as get_current_user


router = APIRouter(
    prefix='/api/admin/users',
    tags=['Admin - User Management']
)


# ============================================================================
# Pydantic Models
# ============================================================================

class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: Optional[str] = None
    shop_name: Optional[str] = None
    subscription_plan: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response."""
    users: List[UserResponse]
    total: int


class UpdateSubscriptionRequest(BaseModel):
    """Request to update user subscription plan."""
    subscription_plan: str


# ============================================================================
# Helper Functions
# ============================================================================

def is_admin(user: User) -> bool:
    """
    Check if user is an admin.

    For now, checks if user has enterprise plan.
    You can customize this logic as needed.
    """
    # Option 1: Check subscription plan
    if user.subscription_plan == 'enterprise':
        return True

    # Option 2: Check if user is the first user (system admin)
    # You can add an is_admin column to users table if needed

    return False


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin access."""
    if not is_admin(user):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user


# ============================================================================
# Routes
# ============================================================================

@router.get('/', response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    subscription_plan: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all users (admin only).

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Max number of records to return
    - search: Search by email or username
    - subscription_plan: Filter by subscription plan
    """
    query = db.query(User)

    # Apply filters
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%")) |
            (User.shop_name.ilike(f"%{search}%"))
        )

    if subscription_plan:
        query = query.filter(User.subscription_plan == subscription_plan)

    # Get total count
    total = query.count()

    # Apply pagination
    users = query.offset(skip).limit(limit).all()

    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total
    )


@router.get('/{user_id}', response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get specific user by ID (admin only).
    """
    from uuid import UUID

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = db.query(User).filter(User.id == user_uuid).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.from_orm(user)


@router.put('/{user_id}/subscription', response_model=UserResponse)
async def update_user_subscription(
    user_id: str,
    request: UpdateSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user's subscription plan (admin only).

    Valid plans: free, basic, pro, enterprise
    """
    from uuid import UUID

    # Validate subscription plan
    valid_plans = ['free', 'basic', 'pro', 'enterprise']
    if request.subscription_plan not in valid_plans:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subscription plan. Must be one of: {', '.join(valid_plans)}"
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Get user
    user = db.query(User).filter(User.id == user_uuid).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent downgrading yourself if you're the only admin
    if user.id == current_user.id and request.subscription_plan != 'enterprise':
        admin_count = db.query(User).filter(User.subscription_plan == 'enterprise').count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot downgrade yourself - you're the only admin"
            )

    # Update subscription
    old_plan = user.subscription_plan
    user.subscription_plan = request.subscription_plan

    db.commit()
    db.refresh(user)

    print(f"✅ User {user.email} subscription updated: {old_plan} → {request.subscription_plan}")

    return UserResponse.from_orm(user)


@router.post('/bulk-upgrade-to-pro')
async def bulk_upgrade_to_pro(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Upgrade all free/basic users to Pro plan (admin only).

    This is a bulk operation for convenience.
    """
    # Count users that will be upgraded
    count = db.query(User).filter(
        User.subscription_plan.in_(['free', 'basic'])
    ).count()

    if count == 0:
        return {
            "message": "No users to upgrade",
            "upgraded_count": 0
        }

    # Upgrade users
    db.query(User).filter(
        User.subscription_plan.in_(['free', 'basic'])
    ).update(
        {User.subscription_plan: 'pro'},
        synchronize_session=False
    )

    db.commit()

    return {
        "message": f"Successfully upgraded {count} user(s) to Pro plan",
        "upgraded_count": count
    }
