"""
Organization API routes - Simplified for multi-tenant migration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import verify_token
from typing import Annotated

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("/")
def get_user_organizations(
    token: Annotated[str, Depends(verify_token)],
    db: Session = Depends(get_db)
):
    """Get organizations for the current user"""
    try:
        # For now, return empty list to satisfy frontend check
        # The frontend will redirect to organization selection if this returns empty
        # TODO: Implement proper organization listing after full migration
        return []
    except Exception as e:
        print(f"Organization route error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load organizations")