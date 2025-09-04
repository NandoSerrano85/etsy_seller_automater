from fastapi import APIRouter, Depends, Query, Form
from sqlalchemy.orm import Session
from server.src.database.core import get_db
from server.src.routes.auth.service import CurrentUser
from . import model
from . import service

router = APIRouter(
    prefix='/orders',
    tags=['Orders']
)

@router.get('/', response_model=model.OrdersResponse)
async def get_orders(
    current_user: CurrentUser,
    access_token: str = Query(..., description="Etsy access token"),
    db: Session = Depends(get_db)
):
    return service.get_orders(access_token, current_user, db)

@router.post('/print-files')
async def create_gang_sheets_from_mockups(
    current_user: CurrentUser,
    template_name: str = Form(...),
    db: Session = Depends(get_db)
):
    return service.create_gang_sheets_from_mockups(template_name, current_user, db)

@router.get('/create-print-files', response_model=model.PrintFilesResponse)
async def create_print_files(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    return service.create_print_files(current_user, db)
