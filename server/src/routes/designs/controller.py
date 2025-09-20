from fastapi import APIRouter, status, Query, UploadFile, File, Depends, Form
from fastapi.responses import StreamingResponse
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.message import InvalidUserToken
from server.src.utils.progress_manager import progress_manager
from server.src.services.cache_service import ApiCache
from . import model
from . import service
import json
import asyncio
import logging

router = APIRouter(
    prefix='/designs',
    tags=['Designs']
)

@router.post('/start-upload')
async def start_upload(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(None)
):
    """Start a new upload session with file size estimation for progress tracking"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Calculate total file size for time estimation
    total_size_bytes = 0
    file_count = 0
    if files:
        for file in files:
            file_count += 1
            # Read file size
            file.file.seek(0, 2)  # Seek to end
            size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            total_size_bytes += size

    total_size_mb = total_size_bytes / (1024 * 1024)  # Convert to MB

    session_id = progress_manager.create_session(total_size_mb, file_count)
    return {
        "session_id": session_id,
        "estimated_time": progress_manager._file_info[session_id]['estimated_time'],
        "total_size_mb": total_size_mb,
        "file_count": file_count
    }

@router.get('/progress/{session_id}')
async def get_upload_progress(
    session_id: str,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get upload progress via Server-Sent Events"""
    # For SSE, we need to handle auth via query param since EventSource doesn't support custom headers
    if token:
        # Manually validate the token for SSE
        from server.src.routes.auth.service import verify_token
        try:
            current_user = verify_token(token)
            user_id = current_user.get_uuid() if current_user else None
        except Exception as e:
            logging.error(f"SSE auth error: {e}")
            user_id = None
    else:
        user_id = None

    if not user_id:
        raise InvalidUserToken()

    async def event_generator():
        async for data in progress_manager.subscribe(session_id):
            yield data

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.post('/', response_model=model.DesignImageListResponse, status_code=status.HTTP_201_CREATED)
async def create_design(
    current_user: CurrentUser,
    design_data: str = Form(...),
    files: List[UploadFile] = File(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new design for the current user with optional progress tracking"""
    user_id = current_user.get_uuid()
    design_data_dict = json.loads(design_data)
    design_model = model.DesignImageCreate(**design_data_dict)
    if not user_id:
        raise InvalidUserToken()

    # Create progress callback if session_id is provided
    progress_callback = None
    if session_id:
        def progress_callback(step: int, message: str, total_steps: int = 4, file_progress: float = 0):
            progress_manager.update_progress(session_id, step + 1, total_steps, message, file_progress)

    try:
        result = await service.create_design(db, user_id, design_model, files, progress_callback)

        # Mark session as completed if using progress tracking
        if session_id:
            progress_manager.complete_session(session_id, success=True, final_message="Upload completed successfully")

        return result
    except Exception as e:
        # Mark session as failed if using progress tracking
        if session_id:
            progress_manager.complete_session(session_id, success=False, final_message=f"Upload failed: {str(e)}")
        raise

@router.get('/list', response_model=model.DesignImageListResponse)
async def get_designs(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of designs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of designs to return")
):
    """Get all designs for the current user with pagination"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_designs_by_user_id(db, user_id, skip, limit)

@router.get('/by-id/{design_id}', response_model=model.DesignImageResponse)
async def get_design(
    design_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific design by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_design_by_id(db, design_id, user_id)

@router.put('/update/{design_id}', response_model=model.DesignImageResponse)
async def update_design(
    design_id: UUID,
    design_data: model.DesignImageUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a specific design by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.update_design(db, design_id, user_id, design_data)

@router.delete('/delete/{design_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_design(
    design_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a specific design by ID for the current user (soft delete)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    service.delete_design(db, design_id, user_id)

@router.get('/gallery', response_model=model.DesignGalleryResponse)
async def get_design_gallery(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get design gallery data including Etsy mockups and QNAP design files (cached for 30 minutes)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    user_id_str = str(user_id)

    # Try to get from cache first (30 minutes TTL)
    cached_result = await ApiCache.get_gallery_cache(user_id_str)
    if cached_result is not None:
        logging.debug(f"Cache hit for gallery user {user_id_str}")
        return cached_result

    # Get fresh data
    result = await service.get_design_gallery_data(db, user_id)

    # Cache the result for 30 minutes
    await ApiCache.set_gallery_cache(user_id_str, 1, result, 1800)

    logging.debug(f"Cached gallery result for user {user_id_str}")
    return result

@router.get('/nas-file/{shop_name}/{path:path}')
async def serve_nas_file(
    shop_name: str,
    path: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Serve design files from QNAP NAS"""
    from fastapi.responses import StreamingResponse
    from server.src.utils.nas_storage import nas_storage
    import io

    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Verify user owns this shop
    user = service.get_user_by_id(db, user_id)
    if not user or user.shop_name != shop_name:
        raise InvalidUserToken()

    try:
        # Download file from NAS to memory
        file_data = nas_storage.download_file_to_memory(shop_name, path)
        if not file_data:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="File not found")

        # Determine content type based on file extension
        import mimetypes
        filename = path.split('/')[-1]
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = 'application/octet-stream'

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")
