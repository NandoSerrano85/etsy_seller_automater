"""
Organization API routes - Simplified for multi-tenant migration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.routes.organizations.service import OrganizationService
from server.src.routes.organizations import model
from typing import Annotated
from uuid import UUID

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("")
def create_organization(
    org_data: model.OrganizationCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new organization with the current user as owner"""
    try:
        user_id = current_user.get_uuid()
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Create organization with current user as owner
        org = OrganizationService.create_organization(
            db=db,
            org_data=org_data,
            owner_user_id=user_id
        )

        return {
            "id": str(org.id),
            "name": org.name,
            "description": org.description,
            "user_role": "owner",  # Creator is always the owner
            "created_at": org.created_at.isoformat() if org.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create organization")

@router.get("/")
def get_user_organizations(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get organizations for the current user"""
    try:
        from server.src.entities.user import User
        from server.src.entities.organization import Organization, OrganizationMember

        user_id = current_user.get_uuid()
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        organizations = []

        # Check organization memberships first (preferred method)
        memberships = db.query(OrganizationMember, Organization).join(
            Organization, OrganizationMember.organization_id == Organization.id
        ).filter(OrganizationMember.user_id == user_id).all()

        for membership, org in memberships:
            organizations.append({
                "id": str(org.id),
                "name": org.name,
                "description": org.description,
                "user_role": membership.role  # Use user_role to match frontend expectations
            })

        # Also check if user has direct organization assignment (legacy support)
        if hasattr(user, 'org_id') and user.org_id:
            org = db.query(Organization).filter(Organization.id == user.org_id).first()
            if org:
                # Avoid duplicates - check if already added via membership
                if not any(existing_org["id"] == str(org.id) for existing_org in organizations):
                    organizations.append({
                        "id": str(org.id),
                        "name": org.name,
                        "description": org.description,
                        "user_role": user.role or "member"
                    })

        return organizations

    except Exception as e:
        print(f"Organization route error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load organizations")

@router.get("/{organization_id}/members")
def get_organization_members(
    organization_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get members of an organization"""
    try:
        user_id = current_user.get_uuid()
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Check if user has access to this organization
        if not OrganizationService.check_user_access(db, user_id, organization_id):
            raise HTTPException(status_code=403, detail="Access denied to this organization")

        # Get members
        members = OrganizationService.get_organization_members(db, organization_id)

        return {
            "success": True,
            "data": members
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting organization members: {e}")
        raise HTTPException(status_code=500, detail="Failed to get organization members")