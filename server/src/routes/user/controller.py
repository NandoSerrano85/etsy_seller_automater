from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from . import model
from . import service
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

# Thread pool for background processing
thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="user-")

def run_in_thread(func):
    """Decorator to run sync functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, functools.partial(func, *args, **kwargs))
    return wrapper

@router.get('/me', response_model=model.UserResponse)
async def get_current_user(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Get current user (threaded)"""
    @run_in_thread
    def get_current_user_threaded():
        return service.get_user_by_id(db, current_user.get_uuid())

    return await get_current_user_threaded()

@router.put('/change-password', status_code=status.HTTP_200_OK)
async def change_passwordr(password_change: model.PasswordChangeRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Change password (threaded)"""
    @run_in_thread
    def change_password_threaded():
        return service.change_password(db, current_user.get_uuid(), password_change)

    await change_password_threaded()