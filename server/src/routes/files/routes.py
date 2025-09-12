"""
File management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from server.src.database.core import get_db
from server.src.auth.dependencies import get_current_user
from server.src.entities.user import User
from server.src.routes.organizations.service import OrganizationService
from . import model
from .service import FileService

router = APIRouter(prefix="/organizations/{org_id}/files", tags=["files"])

@router.post("/upload", response_model=model.FileUploadResponse)
async def upload_file(
    org_id: UUID,
    file: UploadFile = FastAPIFile(...),
    file_type: model.FileTypeEnum = Query(...),
    metadata: Optional[str] = Query(None, description="JSON metadata"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload file to NAS storage"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    # Parse metadata if provided
    file_metadata = {}
    if metadata:
        import json
        try:
            file_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    
    # Read file content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Create upload request
    upload_request = model.FileUploadRequest(
        file_type=file_type,
        filename=file.filename or "unknown",
        mime_type=file.content_type,
        metadata=file_metadata
    )
    
    try:
        file_record = FileService.upload_file(
            db=db,
            org_id=org_id,
            file_data=upload_request,
            file_content=content,
            user_id=current_user.id
        )
        
        return model.FileUploadResponse(
            file_id=file_record.id,
            nas_path=file_record.nas_path,
            message="File uploaded successfully" if file_record.status.value == "ready" else "File upload failed"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=model.FileListResponse)
def search_files(
    org_id: UUID,
    file_type: Optional[model.FileTypeEnum] = None,
    status: Optional[model.FileStatusEnum] = None,
    filename_contains: Optional[str] = None,
    sha256: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search files with filters"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    search_params = model.FileSearchRequest(
        file_type=file_type,
        status=status,
        filename_contains=filename_contains,
        sha256=sha256
    )
    
    files, total = FileService.search_files(
        db=db,
        org_id=org_id,
        search_params=search_params,
        skip=skip,
        limit=limit
    )
    
    return model.FileListResponse(
        files=[model.FileResponse.model_validate(f) for f in files],
        total=total,
        limit=limit,
        offset=skip
    )

@router.get("/{file_id}", response_model=model.FileResponse)
def get_file(
    org_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get file metadata by ID"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    file_record = FileService.get_file_by_id(db=db, file_id=file_id)
    if not file_record or file_record.org_id != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    return model.FileResponse.model_validate(file_record)

@router.put("/{file_id}", response_model=model.FileResponse)
def update_file(
    org_id: UUID,
    file_id: UUID,
    file_data: model.FileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update file metadata"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    file_record = FileService.get_file_by_id(db=db, file_id=file_id)
    if not file_record or file_record.org_id != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    updated_file = FileService.update_file(
        db=db,
        file_id=file_id,
        file_data=file_data,
        user_id=current_user.id
    )
    if not updated_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return model.FileResponse.model_validate(updated_file)

@router.delete("/{file_id}")
def delete_file(
    org_id: UUID,
    file_id: UUID,
    permanent: bool = Query(False, description="Permanently delete file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete file (soft delete by default)"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    file_record = FileService.get_file_by_id(db=db, file_id=file_id)
    if not file_record or file_record.org_id != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    success = FileService.delete_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        soft_delete=not permanent
    )
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    action = "permanently deleted" if permanent else "archived"
    return {"message": f"File {action} successfully"}

@router.get("/{file_id}/download")
async def download_file(
    org_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download file content from NAS"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    file_record = FileService.get_file_by_id(db=db, file_id=file_id)
    if not file_record or file_record.org_id != org_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.status.value != "ready":
        raise HTTPException(status_code=400, detail="File is not ready for download")
    
    content = FileService.get_file_content(db=db, file_id=file_id)
    if content is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve file content")
    
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file_record.filename}"
        }
    )

@router.get("/stats/storage")
def get_storage_stats(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get file storage statistics for organization"""
    if not OrganizationService.check_user_access(db, current_user.id, org_id):
        raise HTTPException(status_code=403, detail="Access denied to this organization")
    
    stats = FileService.get_storage_stats(db=db, org_id=org_id)
    return stats