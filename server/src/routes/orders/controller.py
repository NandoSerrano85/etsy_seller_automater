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
    db: Session = Depends(get_db)
):
    """Get orders (threaded)"""
    @run_in_thread
    def get_orders_threaded():
        return service.get_orders(current_user, db)

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
