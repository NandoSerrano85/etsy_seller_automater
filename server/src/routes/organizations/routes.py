"""
Organization API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from server.src.database.core import get_db
from server.src.auth.dependencies import get_current_user
from server.src.entities.user import User
from . import model
from .service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=model.OrganizationResponse)
def create_organization(
    org_data: model.OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new organization"""
    try:
        org = OrganizationService.create_organization(
            db=db,
            org_data=org_data,
            owner_user_id=current_user.id
        )
        return model.OrganizationResponse.model_validate(org)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=model.OrganizationListResponse)
def get_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of organizations"""
    orgs, total = OrganizationService.get_organizations(db=db, skip=skip, limit=limit)
    
    return model.OrganizationListResponse(
        organizations=[model.OrganizationResponse.model_validate(org) for org in orgs],
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/{org_id}", response_model=model.OrganizationResponse)
def get_organization(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization by ID"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    org = OrganizationService.get_organization_by_id(db=db, org_id=org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return model.OrganizationResponse.model_validate(org)

@router.put("/{org_id}", response_model=model.OrganizationResponse)
def update_organization(
    org_id: UUID,
    org_data: model.OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    org = OrganizationService.update_organization(
        db=db,
        org_id=org_id,
        org_data=org_data,
        user_id=current_user.id
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return model.OrganizationResponse.model_validate(org)

@router.delete("/{org_id}")
def delete_organization(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete organization and all related data"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    success = OrganizationService.delete_organization(
        db=db,
        org_id=org_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {"message": "Organization deleted successfully"}

@router.get("/{org_id}/features")
def get_organization_features(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization feature flags"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    features = OrganizationService.get_organization_features(db=db, org_id=org_id)
    if features is None:
        raise HTTPException(status_code=404, detail="Organization or features not found")
    
    return {"features": features}

@router.put("/{org_id}/features")
def update_organization_features(
    org_id: UUID,
    features_data: model.OrganizationFeatureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization feature flags"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    features = OrganizationService.update_organization_features(
        db=db,
        org_id=org_id,
        features_data=features_data,
        user_id=current_user.id
    )
    if features is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {"features": features}

@router.get("/{org_id}/stats", response_model=model.OrganizationStatsResponse)
def get_organization_stats(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization statistics"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    org = OrganizationService.get_organization_by_id(db=db, org_id=org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    stats = OrganizationService.get_organization_stats(db=db, org_id=org_id)
    
    return model.OrganizationStatsResponse(
        id=org.id,
        name=org.name,
        shop_name=org.shop_name,
        stats=stats
    )