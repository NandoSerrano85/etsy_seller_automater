from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from . import model
from . import service
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import functools
from datetime import datetime, timezone
import io

router = APIRouter(
    prefix='/orders',
    tags=['Orders']
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="orders-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

@router.get('/', response_model=model.OrdersResponse)
async def get_orders(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    was_shipped: str = None,
    was_paid: str = None,
    was_canceled: str = None
):
    """
    Get orders with optional status filters (threaded)

    Args:
        was_shipped: Filter by shipped status ('true', 'false', or omit for all)
        was_paid: Filter by paid status ('true', 'false', or omit for all)
        was_canceled: Filter by canceled status ('true', 'false', or omit for all)
    """
    @run_in_thread
    def get_orders_threaded():
        return service.get_orders(
            current_user,
            db,
            was_shipped=was_shipped,
            was_paid=was_paid,
            was_canceled=was_canceled
        )

    return await get_orders_threaded()

@router.post('/print-files')
async def create_gang_sheets_from_mockups(
    current_user: CurrentUser,
    template_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create gang sheets from mockups (threaded - heavy file processing)"""
    @run_in_thread
    def create_gang_sheets_threaded():
        return service.create_gang_sheets_from_mockups(template_name, current_user, db)

    return await create_gang_sheets_threaded()

@router.get('/create-print-files', response_model=model.PrintFilesResponse)
async def create_print_files(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Create print files (threaded - heavy file processing)"""
    @run_in_thread
    def create_print_files_threaded():
        return service.create_print_files(current_user, db)

    return await create_print_files_threaded()

@router.get('/all-orders')
async def get_all_orders(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    was_shipped: str = None,
    was_paid: str = None,
    was_canceled: str = None
):
    """
    Get all Etsy orders with full details for selection (threaded)

    Args:
        limit: Maximum number of orders to return
        offset: Number of orders to skip (for pagination)
        was_shipped: Filter by shipped status ('true', 'false', or omit for all)
        was_paid: Filter by paid status ('true', 'false', or omit for all)
        was_canceled: Filter by canceled status ('true', 'false', or omit for all)
    """
    @run_in_thread
    def get_all_orders_threaded():
        return service.get_all_orders_with_details(
            current_user,
            db,
            limit,
            offset,
            was_shipped=was_shipped,
            was_paid=was_paid,
            was_canceled=was_canceled
        )

    return await get_all_orders_threaded()

@router.post('/print-files-from-selection')
async def create_print_files_from_selected_orders(
    current_user: CurrentUser,
    request_body: model.PrintFilesFromSelectionRequest,
    db: Session = Depends(get_db)
):
    """
    Create print files from selected order IDs (threaded - heavy file processing)
    """
    logging.info(f"📦 Received request: order_ids={request_body.order_ids}, type={type(request_body.order_ids)}, template={request_body.template_name}")

    print(f"📦 Received request: order_ids={request_body.order_ids}, type={type(request_body.order_ids)}, template={request_body.template_name}")
    # Ensure order_ids is always a list
    order_ids = request_body.order_ids if isinstance(request_body.order_ids, list) else [request_body.order_ids]
    logging.info(f"📦 Normalized order_ids: {order_ids}")

    @run_in_thread
    def create_from_selection_threaded():
        return service.create_print_files_from_selected_orders(
            order_ids,
            request_body.template_name,
            current_user,
            db
        )

    return await create_from_selection_threaded()

@router.get('/print-files')
async def list_print_files(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    List available print files from NAS for the user's Etsy shop
    """
    from server.src.utils.nas_storage import nas_storage

    if not nas_storage.enabled:
        return {"files": [], "message": "NAS storage is not enabled"}

    # Get user's shop name
    shop_name = current_user.shop_name
    if not shop_name:
        raise HTTPException(status_code=404, detail="No shop name configured for user")

    print_files_path = f"PrintFiles"

    try:
        with nas_storage.get_sftp_connection() as sftp:
            # Full path: /share/Graphics/<shop_name>/PrintFiles/
            full_path = f"{nas_storage.base_path}/{shop_name}/{print_files_path}"

            try:
                files = sftp.listdir(full_path)
                # Filter for PNG files and get file info
                print_files = []
                for filename in files:
                    if filename.endswith('.png'):
                        file_path = f"{full_path}/{filename}"
                        stat_info = sftp.stat(file_path)
                        print_files.append({
                            "filename": filename,
                            "size": stat_info.st_size,
                            "modified": datetime.fromtimestamp(float(stat_info.st_mtime), tz=timezone.utc).isoformat()
                        })

                # Sort by modified date (newest first)
                print_files.sort(key=lambda x: x['modified'], reverse=True)

                logging.info(f"Found {len(print_files)} print files for {shop_name}")
                return {"files": print_files, "shop_name": shop_name}

            except FileNotFoundError:
                logging.info(f"PrintFiles directory not found for {shop_name}")
                return {"files": [], "shop_name": shop_name, "message": "No print files directory found"}

    except Exception as e:
        logging.error(f"Error listing print files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list print files: {str(e)}")

@router.get('/print-files/{filename}')
async def download_print_file(
    filename: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Download a print file from NAS
    """
    from server.src.utils.nas_storage import nas_storage

    if not nas_storage.enabled:
        raise HTTPException(status_code=503, detail="NAS storage is not enabled")

    # Get user's shop name
    shop_name = current_user.shop_name
    if not shop_name:
        raise HTTPException(status_code=404, detail="No shop name configured for user")

    # Security: Prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith('.png'):
        raise HTTPException(status_code=400, detail="Only PNG files are supported")

    try:
        # Download file from NAS to memory
        file_path = f"PrintFiles/{filename}"
        file_content = nas_storage.download_file_to_memory(shop_name, file_path)

        if not file_content:
            raise HTTPException(status_code=404, detail="Print file not found")

        logging.info(f"Downloading print file: {shop_name}/PrintFiles/{filename} ({len(file_content)} bytes)")

        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading print file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download print file: {str(e)}")
