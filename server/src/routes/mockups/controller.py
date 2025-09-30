from fastapi import APIRouter, status, Query, UploadFile, File, Depends, Form
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from server.src.message import InvalidUserToken
from . import model
from . import service
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix='/mockups',
    tags=['Mockups']
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="mockups-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

# Mockups endpoints
@router.get('/', response_model=model.MockupsListResponse)
async def get_mockups(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of mockups to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of mockups to return")
):
    """Get all mockups for the current user with pagination (threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Run database query in thread to prevent blocking
    @run_in_thread
    def get_mockups_threaded():
        return service.get_mockups_by_user_id(db, user_id, skip, limit)

    return await get_mockups_threaded()

@router.post('/', response_model=model.MockupImageResponse, status_code=status.HTTP_201_CREATED)
async def create_mockup(
    mockup_data: model.MockupFullCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create and store a complete mockup (image + DB record) for the current user (threaded)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    # Run mockup creation in thread (involves image processing)
    @run_in_thread
    def create_mockup_threaded():
        return service.create_mockup(db, user_id, mockup_data)

    return await create_mockup_threaded()

@router.post('/group', response_model=model.MockupsResponse, status_code=status.HTTP_201_CREATED)
async def create_mockup_group(
    mockup_data: model.MockupsCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new mockup group/metadata record (no images) for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.create_mockup_group(db, user_id, mockup_data)

# File upload endpoint for mockup images (must come before parameterized routes)
@router.post('/upload', response_model=model.MockupImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_mockup_files(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(...),
    mockup_id: UUID = Form(...),
    watermark_file: UploadFile = Form(...),
):
    """Upload mockup files with template name (legacy compatibility)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    result = await service.upload_mockup_files(db, user_id, files, mockup_id, watermark_file)
    print(f"Controller returning: {type(result)} - {result}")
    return result

# Legacy endpoints for backward compatibility
@router.get('/by-id/{mockup_id}', response_model=model.MockupsResponse)
async def get_mockup_legacy(
    mockup_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific mockup by ID for the current user (legacy endpoint)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_mockup_by_id(db, mockup_id, user_id)

@router.put('/update/{mockup_id}', response_model=model.MockupsResponse)
async def update_mockup_legacy(
    mockup_id: UUID,
    mockup_data: model.MockupsUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a specific mockup by ID for the current user (legacy endpoint)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.update_mockup(db, mockup_id, user_id, mockup_data)

@router.delete('/delete/{mockup_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_mockup_legacy(
    mockup_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a specific mockup by ID for the current user (legacy endpoint)"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    service.delete_mockup(db, mockup_id, user_id)

# Mockup Images endpoints
@router.post('/images/{mockup_id}/create', response_model=model.MockupImageResponse, status_code=status.HTTP_201_CREATED)
async def create_mockup_image(
    mockup_id: UUID,
    image_data: model.MockupImageCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create a new mockup image for a specific mockup"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.create_mockup_image(db, mockup_id, user_id, image_data)

@router.get('/images/{mockup_id}/list', response_model=model.MockupImageListResponse)
async def get_mockup_images(
    mockup_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of images to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of images to return")
):
    """Get all images for a specific mockup"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_mockup_images_by_mockup_id(db, mockup_id, user_id, skip, limit)

@router.get('/images/{image_id}', response_model=model.MockupImageResponse)
async def get_mockup_image(
    image_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific mockup image by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_mockup_image_by_id(db, image_id, user_id)

@router.put('/images/{image_id}', response_model=model.MockupImageResponse)
async def update_mockup_image(
    image_id: UUID,
    image_data: model.MockupImageUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a specific mockup image by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.update_mockup_image(db, image_id, user_id, image_data)

@router.delete('/images/{image_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_mockup_image(
    image_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a specific mockup image by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    service.delete_mockup_image(db, image_id, user_id)

@router.put('/images/{image_id}/watermark', response_model=model.MockupImageResponse)
async def update_mockup_image_watermark(
    image_id: UUID,
    watermark_data: model.MockupImageWatermarkUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update the watermark_path for a specific mockup image."""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.update_mockup_image_watermark(db, image_id, user_id, watermark_data.watermark_path)

@router.put('/images/{image_id}/watermark-upload', response_model=model.MockupImageResponse)
async def upload_mockup_image_watermark(
    image_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    watermark: UploadFile = File(...)
):
    """Upload and set a watermark image for a specific mockup image."""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return await service.upload_mockup_image_watermark(db, image_id, user_id, watermark)

@router.put('/{mockup_id}/update-watermark', response_model=model.MockupsResponse)
async def update_mockup_watermark(
    mockup_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    watermark: UploadFile = File(...)
):
    """Update the watermark for all images in a mockup."""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return await service.update_mockup_watermark(db, mockup_id, user_id, watermark)



# Mockup Mask Data endpoints
@router.post('/images/{image_id}/mask-data', response_model=model.MockupMaskDataResponse, status_code=status.HTTP_201_CREATED)
async def create_mockup_mask_data(
    image_id: UUID,
    mask_data: model.MockupMaskDataCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create new mask data for a specific mockup image"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.create_mockup_mask_data(db, image_id, user_id, mask_data)

@router.get('/images/{image_id}/mask-data', response_model=model.MockupMaskDataListResponse)
async def get_mockup_mask_data(
    image_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of mask data entries to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of mask data entries to return")
):
    """Get all mask data for a specific mockup image"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_mockup_mask_data_by_image_id(db, image_id, user_id, skip, limit)

@router.get('/mask-data/{mask_data_id}', response_model=model.MockupMaskDataResponse)
async def get_mockup_mask_data_by_id(
    mask_data_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get a specific mask data entry by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.get_mockup_mask_data_by_id(db, mask_data_id, user_id)

@router.put('/mask-data/{mask_data_id}', response_model=model.MockupMaskDataResponse)
async def update_mockup_mask_data(
    mask_data_id: UUID,
    mask_data: model.MockupMaskDataUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update a specific mask data entry by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    return service.update_mockup_mask_data(db, mask_data_id, user_id, mask_data)

@router.delete('/mask-data/{mask_data_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_mockup_mask_data(
    mask_data_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete a specific mask data entry by ID for the current user"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()
    service.delete_mockup_mask_data(db, mask_data_id, user_id)


@router.post('/upload-mockup', response_model=model.UploadToEtsyResponse, status_code=status.HTTP_201_CREATED)
async def upload_mockup(
    current_user: CurrentUser,
    product_data:str = Form(...),
    async_mode: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Upload mockup files and create Etsy listings

    Args:
        async_mode: If True, enqueue job and return immediately. If False, process synchronously (legacy behavior)
    """
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    product_data_dict = json.loads(product_data)
    product_request_model = model.UploadToEtsyRequest(**product_data_dict)

    # Async mode: Enqueue job and return immediately
    if async_mode:
        from server.src.services.mockup_queue import enqueue_mockup_generation

        job_id = await enqueue_mockup_generation(
            user_id=str(user_id),
            design_ids=[str(d) for d in product_request_model.design_ids],
            product_template_id=str(product_request_model.product_template_id),
            mockup_id=str(product_request_model.mockup_id),
            priority="normal"
        )

        return model.UploadToEtsyResponse(
            result={
                "message": f"Mockup generation job enqueued successfully",
                "job_id": job_id,
                "status": "pending",
                "design_count": len(product_request_model.design_ids),
                "async_mode": True
            }
        )

    # Synchronous mode (legacy): Process immediately
    @run_in_thread
    def upload_mockup_threaded():
        # Note: We need to use asyncio.run since service function is async
        import asyncio
        return asyncio.run(service.upload_mockup_files_to_etsy(
            db=db,
            user_id=user_id,
            product_data=product_request_model
        ))

    return await upload_mockup_threaded()


@router.get('/job-status/{job_id}')
async def get_mockup_job_status(
    job_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get status of an async mockup generation job"""
    user_id = current_user.get_uuid()
    if not user_id:
        raise InvalidUserToken()

    from server.src.services.mockup_queue import get_mockup_job_status

    status = await get_mockup_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify user owns this job
    if status.get("user_id") and status["user_id"] != str(user_id):
        raise InvalidUserToken()

    return status