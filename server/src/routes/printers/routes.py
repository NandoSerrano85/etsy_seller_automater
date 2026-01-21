"""
Printer API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from server.src.database.core import get_db
from server.src.routes.auth.service import get_current_user_db
from server.src.entities.user import User
from server.src.routes.organizations.service import OrganizationService
from . import model
from .service import PrinterService

router = APIRouter(prefix="/printers", tags=["printers"])

@router.post("/", response_model=model.PrinterResponse)
def create_printer(
    printer_data: model.PrinterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Create a new printer"""
    # Get or create default organization for user if multi-tenant is enabled
    org_id = None
    if hasattr(current_user, 'org_id'):
        org_id = current_user.org_id
        if not org_id:
            # Create a default organization for the user
            from server.src.routes.organizations.service import OrganizationService
            try:
                org = OrganizationService.create_default_organization_for_user(db, current_user.id)
                org_id = org.id
                # Update user with the new org_id
                current_user.org_id = org_id
                db.commit()
            except Exception as e:
                # If organization creation fails, continue without org_id for backward compatibility
                pass

    try:
        printer = PrinterService.create_printer(
            db=db,
            user_id=current_user.id,
            org_id=org_id,
            printer_data=printer_data
        )
        return model.PrinterResponse.model_validate(printer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=model.PrinterListResponse)
def get_my_printers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True, description="Show only active printers"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Get current user's printers"""
    # Handle both legacy users (without org_id) and multi-tenant users
    org_id = None
    if hasattr(current_user, 'org_id'):
        org_id = current_user.org_id

    printers, total = PrinterService.get_user_printers(
        db=db,
        user_id=current_user.id,
        org_id=org_id,
        skip=skip,
        limit=limit,
        active_only=active_only
    )

    return model.PrinterListResponse(
        printers=[model.PrinterResponse.model_validate(printer) for printer in printers],
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/{printer_id}", response_model=model.PrinterResponse)
def get_printer(
    printer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Get printer by ID"""
    printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    # Check ownership
    if printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")
    
    return model.PrinterResponse.model_validate(printer)

@router.put("/{printer_id}", response_model=model.PrinterResponse)
def update_printer(
    printer_id: UUID,
    printer_data: model.PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Update printer"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")
    
    updated_printer = PrinterService.update_printer(
        db=db,
        printer_id=printer_id,
        printer_data=printer_data,
        user_id=current_user.id
    )
    if not updated_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    return model.PrinterResponse.model_validate(updated_printer)

@router.delete("/{printer_id}")
def delete_printer(
    printer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Delete printer"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")
    
    success = PrinterService.delete_printer(
        db=db,
        printer_id=printer_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    return {"message": "Printer deleted successfully"}

@router.post("/{printer_id}/check-capability", response_model=model.PrinterCapabilityResponse)
def check_printer_capability(
    printer_id: UUID,
    capability_check: model.PrinterCapabilityCheck,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Check if printer can handle specific dimensions and template"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")
    
    try:
        return PrinterService.check_printer_capability(
            db=db,
            printer_id=printer_id,
            width_inches=capability_check.width_inches,
            height_inches=capability_check.height_inches,
            template_id=capability_check.template_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/compatible/find", response_model=model.PrinterListResponse)
def find_compatible_printers(
    width_inches: float = Query(..., gt=0, description="Required width in inches"),
    height_inches: float = Query(..., gt=0, description="Required height in inches"),
    template_id: Optional[UUID] = Query(None, description="Template ID to check compatibility"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Find printers compatible with given dimensions and template"""
    # Handle both legacy users (without org_id) and multi-tenant users
    org_id = None
    if hasattr(current_user, 'org_id'):
        org_id = current_user.org_id

    compatible_printers = PrinterService.find_compatible_printers(
        db=db,
        user_id=current_user.id,
        org_id=org_id,
        width_inches=width_inches,
        height_inches=height_inches,
        template_id=template_id
    )

    return model.PrinterListResponse(
        printers=[model.PrinterResponse.model_validate(printer) for printer in compatible_printers],
        total=len(compatible_printers),
        limit=len(compatible_printers),
        offset=0
    )

@router.get("/default/get", response_model=Optional[model.PrinterResponse])
def get_default_printer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Get user's default printer"""
    # Handle both legacy users (without org_id) and multi-tenant users
    org_id = None
    if hasattr(current_user, 'org_id'):
        org_id = current_user.org_id

    default_printer = PrinterService.get_default_printer(
        db=db,
        user_id=current_user.id,
        org_id=org_id
    )

    if default_printer:
        return model.PrinterResponse.model_validate(default_printer)
    return None

@router.post("/{printer_id}/set-default", response_model=model.PrinterResponse)
def set_default_printer(
    printer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Set printer as default"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")
    
    updated_printer = PrinterService.set_default_printer(
        db=db,
        printer_id=printer_id,
        user_id=current_user.id
    )
    if not updated_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    return model.PrinterResponse.model_validate(updated_printer)

@router.get("/stats/summary", response_model=model.PrinterStatsResponse)
def get_printer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Get printer statistics for current user"""
    # Handle both legacy users (without org_id) and multi-tenant users
    org_id = None
    if hasattr(current_user, 'org_id'):
        org_id = current_user.org_id

    return PrinterService.get_printer_stats(
        db=db,
        user_id=current_user.id,
        org_id=org_id
    )

@router.get("/suggestions/config", response_model=model.PrinterSuggestionsResponse)
def get_printer_suggestions():
    """Get printer configuration suggestions"""
    return PrinterService.get_suggestions()

@router.post("/{printer_id}/templates/{template_id}", response_model=model.PrinterResponse)
def add_template_to_printer(
    printer_id: UUID,
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Add a template to printer's supported templates"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")

    updated_printer = PrinterService.add_template_to_printer(
        db=db,
        printer_id=printer_id,
        template_id=template_id,
        user_id=current_user.id
    )

    if not updated_printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    return model.PrinterResponse.model_validate(updated_printer)

@router.delete("/{printer_id}/templates/{template_id}", response_model=model.PrinterResponse)
def remove_template_from_printer(
    printer_id: UUID,
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Remove a template from printer's supported templates"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")

    updated_printer = PrinterService.remove_template_from_printer(
        db=db,
        printer_id=printer_id,
        template_id=template_id,
        user_id=current_user.id
    )

    if not updated_printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    return model.PrinterResponse.model_validate(updated_printer)

@router.get("/{printer_id}/templates")
def get_printer_templates(
    printer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    """Get all templates supported by a printer"""
    # Verify ownership
    existing_printer = PrinterService.get_printer_by_id(db=db, printer_id=printer_id)
    if not existing_printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    if existing_printer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this printer")

    templates = PrinterService.get_printer_templates(
        db=db,
        printer_id=printer_id,
        user_id=current_user.id
    )

    return {"templates": [{"id": str(t.id), "name": t.name, "template_title": t.template_title} for t in templates]}