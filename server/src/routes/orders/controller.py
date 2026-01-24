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

@router.get('/print-files-debug')
async def print_files_debug(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Debug endpoint to check what's failing in create_print_files"""
    try:
        from server.src.entities.printer import Printer
        from server.src.routes.third_party.service import EtsyAPI
        from server.src.entities.etsy_product_template import EtsyProductTemplate
        from server.src.entities.user import User
        from server.src.utils.file_storage import nas_storage

        user_id = current_user.get_uuid()
        debug_info = {
            "user_id": str(user_id),
            "nas_enabled": nas_storage.enabled if hasattr(nas_storage, 'enabled') else False,
            "checks": {}
        }

        # Check 1: User exists
        try:
            user = db.query(User).filter(User.id == user_id).first()
            debug_info["checks"]["user_found"] = user is not None
            debug_info["checks"]["shop_name"] = user.shop_name if user else None
        except Exception as e:
            debug_info["checks"]["user_error"] = str(e)

        # Check 2: Template exists
        try:
            template = db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id
            ).first()
            debug_info["checks"]["template_found"] = template is not None
            debug_info["checks"]["template_name"] = template.name if template else None
        except Exception as e:
            debug_info["checks"]["template_error"] = str(e)

        # Check 3: Printer exists
        try:
            printer = db.query(Printer).filter(
                Printer.user_id == user_id,
                Printer.is_default == True,
                Printer.is_active == True
            ).first()
            debug_info["checks"]["printer_found"] = printer is not None
        except Exception as e:
            debug_info["checks"]["printer_error"] = str(e)

        # Check 4: Etsy API connection
        try:
            etsy_api = EtsyAPI(user_id, db)
            debug_info["checks"]["etsy_api_created"] = True
        except Exception as e:
            debug_info["checks"]["etsy_api_error"] = str(e)

        return debug_info

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get('/create-print-files', response_model=model.PrintFilesResponse)
async def create_print_files(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    format: str = 'PNG'
):
    """Create print files (threaded - heavy file processing)"""
    try:
        @run_in_thread
        def create_print_files_threaded():
            return service.create_print_files(current_user, db, format=format)

        result = await create_print_files_threaded()
        return result
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error in create_print_files: {str(e)}")
        print(f"📋 Traceback: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create print files: {str(e)}"
        )

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
            db,
            format=request_body.format
        )

    return await create_from_selection_threaded()

@router.get('/get-print-files')
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
                # Filter for print files (PNG, SVG, PSD) and get file info
                print_files = []
                for filename in files:
                    file_ext = filename.lower().split('.')[-1]
                    if file_ext in ('png', 'svg', 'psd', 'jpg', 'jpeg', 'pdf'):
                        file_path = f"{full_path}/{filename}"
                        stat_info = sftp.stat(file_path)
                        print_files.append({
                            "filename": filename,
                            "size": stat_info.st_size,
                            "modified": datetime.fromtimestamp(float(stat_info.st_mtime), tz=timezone.utc).isoformat(),
                            "format": file_ext.upper()
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

@router.get('/get-print-files/{filename}')
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

    # Check file extension
    file_ext = filename.lower().split('.')[-1]
    if file_ext not in ('png', 'svg', 'psd', 'jpg', 'jpeg', 'pdf'):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    try:
        # Download file from NAS to memory
        file_path = f"PrintFiles/{filename}"
        file_content = nas_storage.download_file_to_memory(shop_name, file_path)

        if not file_content:
            raise HTTPException(status_code=404, detail="Print file not found")

        logging.info(f"Downloading print file: {shop_name}/PrintFiles/{filename} ({len(file_content)} bytes)")

        # Determine media type based on file extension
        file_ext = filename.lower().split('.')[-1]
        media_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'svg': 'image/svg+xml',
            'psd': 'image/vnd.adobe.photoshop',
            'pdf': 'application/pdf'
        }
        media_type = media_types.get(file_ext, 'application/octet-stream')

        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading print file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download print file: {str(e)}")
