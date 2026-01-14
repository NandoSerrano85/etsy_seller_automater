"""
Organization API routes - Simplified for multi-tenant migration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.routes.organizations.service import OrganizationService
from typing import Annotated
from uuid import UUID

router = APIRouter(prefix="/organizations", tags=["organizations"])

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

        # Check if user has direct organization assignment
        if hasattr(user, 'org_id') and user.org_id:
            org = db.query(Organization).filter(Organization.id == user.org_id).first()
            if org:
                organizations.append({
                    "id": str(org.id),
                    "name": org.name,
                    "description": org.description,
                    "role": user.role or "member"
                })

        # Also check organization memberships
        memberships = db.query(OrganizationMember, Organization).join(
            Organization, OrganizationMember.organization_id == Organization.id
        ).filter(OrganizationMember.user_id == user_id).all()

        for membership, org in memberships:
            # Avoid duplicates
            if not any(existing_org["id"] == str(org.id) for existing_org in organizations):
                organizations.append({
                    "id": str(org.id),
                    "name": org.name,
                    "description": org.description,
                    "role": membership.role
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