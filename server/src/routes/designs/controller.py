from fastapi import APIRouter, status, Query, UploadFile, File, Depends, Form, HTTPException
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
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix='/designs',
    tags=['Designs']
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="designs-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

@router.post('/start-upload')
async def start_upload(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(default=[])
):
    """Start a new upload session with file size estimation for progress tracking (threaded)"""
    logging.info(f"start_upload called for user")
    user_id = current_user.get_uuid()
    if not user_id:
        logging.error("User not authenticated in start_upload")
        raise InvalidUserToken()

    logging.info(f"start_upload: user_id={user_id}, files_count={len(files) if files else 0}")

    @run_in_thread
    def start_upload_threaded():
        try:
            # Calculate total file size for time estimation
            total_size_bytes = 0
            file_count = 0

            # Handle empty or None files list
            if files and len(files) > 0:
                # Filter out any files that might be None or empty
                valid_files = [f for f in files if f is not None and hasattr(f, 'file')]

                for file in valid_files:
                    file_count += 1
                    # Read file size safely
                    try:
                        if file.file:
                            file.file.seek(0, 2)  # Seek to end
                            size = file.file.tell()
                            file.file.seek(0)  # Reset to beginning
                            total_size_bytes += size
                        else:
                            logging.warning(f"File {file.filename} has no file object")
                    except Exception as e:
                        logging.error(f"Error reading file size for {getattr(file, 'filename', 'unknown')}: {e}")
                        # Continue with 0 size for this file
            else:
                logging.info("No files provided for start-upload session")

            total_size_mb = total_size_bytes / (1024 * 1024)  # Convert to MB

            session_id = progress_manager.create_session(total_size_mb, file_count)
            result = {
                "session_id": session_id,
                "estimated_time": progress_manager._file_info[session_id]['estimated_time'],
                "total_size_mb": total_size_mb,
                "file_count": file_count
            }
            logging.info(f"start_upload successful: session_id={session_id}, size={total_size_mb}MB, count={file_count}")
            return result
        except Exception as e:
            logging.error(f"Error in start_upload: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start upload session: {str(e)}")

    return await start_upload_threaded()

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
    """Create a new design for the current user with optional progress tracking (threaded for heavy processing)"""
    user_id = current_user.get_uuid()
    design_data_dict = json.loads(design_data)
    design_model = model.DesignImageCreate(**design_data_dict)
    if not user_id:
        raise InvalidUserToken()

    # Create progress callback if session_id is provided
    progress_callback = None
    if session_id:
        def progress_callback(step: int, message: str, total_steps: int = 4, file_progress: float = 0, current_file: str = ""):
            progress_manager.update_progress(session_id, step + 1, total_steps, message, file_progress, current_file)

    @run_in_thread
    def create_design_threaded():
        """Run design creation in a separate thread to prevent blocking the event loop"""
        try:
            # Note: service.create_design is async, so we need to run it in asyncio
            import asyncio

            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    service.create_design(db, user_id, design_model, files, progress_callback)
                )

                # Mark session as completed if using progress tracking
                if session_id:
                    progress_manager.complete_session(session_id, success=True, final_message="Upload completed successfully")

                return result
            finally:
                loop.close()

        except Exception as e:
            # Mark session as failed if using progress tracking
            if session_id:
                progress_manager.complete_session(session_id, success=False, final_message=f"Upload failed: {str(e)}")
            raise

    return await create_design_threaded()

@router.get('/list', response_model=model.DesignImageListResponse)
async def get_designs(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of designs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of designs to return")
):
    """Get all designs for the current user with pagination (threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Run database query in thread to prevent blocking
    @run_in_thread
    def get_designs_threaded():
        return service.get_designs_by_user_id(db, user_id, skip, limit)

    return await get_designs_threaded()

@router.get('/by-id/{design_id}', response_model=model.DesignImageResponse)
async def get_design(
    design_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific design by ID for the current user (threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Run database query in thread to prevent blocking
    @run_in_thread
    def get_design_threaded():
        return service.get_design_by_id(db, design_id, user_id)

    return await get_design_threaded()

@router.put('/update/{design_id}', response_model=model.DesignImageResponse)
async def update_design(
    design_id: UUID,
    design_data: model.DesignImageUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a specific design by ID for the current user (threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Run database update in thread to prevent blocking
    @run_in_thread
    def update_design_threaded():
        return service.update_design(db, design_id, user_id, design_data)

    return await update_design_threaded()

@router.delete('/delete/{design_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_design(
    design_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a specific design by ID for the current user (soft delete, threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Run database delete in thread to prevent blocking
    @run_in_thread
    def delete_design_threaded():
        return service.delete_design(db, design_id, user_id)

    await delete_design_threaded()

@router.get('/gallery', response_model=model.DesignGalleryResponse)
async def get_design_gallery(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get design gallery data including Etsy mockups and QNAP design files (cached for 30 minutes, threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    user_id_str = str(user_id)

    # Try to get from cache first (30 minutes TTL)
    cached_result = await ApiCache.get_gallery_cache(user_id_str)
    if cached_result is not None:
        logging.debug(f"Cache hit for gallery user {user_id_str}")
        return cached_result

    # Get fresh data in thread (heavy operation with multiple data sources)
    @run_in_thread
    def get_gallery_data_threaded():
        return asyncio.run(service.get_design_gallery_data(db, user_id))

    result = await get_gallery_data_threaded()

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
    """Serve design files from QNAP NAS (threaded for file operations)"""
    from fastapi.responses import StreamingResponse
    from server.src.utils.nas_storage import nas_storage
    import io

    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Verify user owns this shop (threaded database query)
    @run_in_thread
    def verify_user_shop():
        user = service.get_user_by_id(db, user_id)
        if not user or user.shop_name != shop_name:
            raise InvalidUserToken()
        return user

    user = await verify_user_shop()

    try:
        # Download file from NAS to memory (threaded file operation)
        @run_in_thread
        def download_file_threaded():
            file_data = nas_storage.download_file_to_memory(shop_name, path)
            if not file_data:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="File not found")
            return file_data

        file_data = await download_file_threaded()

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
