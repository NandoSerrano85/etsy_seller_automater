from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from . import model
from . import service
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

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
    order_ids: list[int] = Form(...),
    template_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create print files from selected order IDs (threaded - heavy file processing)"""
    @run_in_thread
    def create_from_selection_threaded():
        return service.create_print_files_from_selected_orders(
            order_ids,
            template_name,
            current_user,
            db
        )

    return await create_from_selection_threaded()
