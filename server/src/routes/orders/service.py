import os
import logging
import requests
from typing import Any
from fastapi import HTTPException
from dotenv import load_dotenv

from server.src.entities.user import User
from . import model
from server.src.utils.gangsheet_engine import create_gang_sheets_from_db, create_gang_sheets
from server.src.utils.etsy_api_engine import EtsyAPI
from server.src.entities.template import EtsyProductTemplate

load_dotenv()
API_CONFIG = {
    'base_url': 'https://openapi.etsy.com/v3',
}

def get_oauth_variables():
    return {
        'clientID': os.getenv('CLIENT_ID'),
        'clientSecret': os.getenv('CLIENT_SECRET'),
    }

def get_orders(access_token: str, current_user, db) -> model.OrdersResponse:
    try:
        etsy_api = EtsyAPI(current_user.get_uuid(), db)
        orders = etsy_api.fetch_order_summary(model)
        if orders['success_code'] != 200:
            raise HTTPException(status_code=orders['success_code'], detail=orders['message'])
        return model.OrdersResponse(
            orders=orders['orders'],
            count=orders['count'],
            total=orders['total']
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

def create_gang_sheets_from_mockups(template_name: str, current_user, db):
    """Create gang sheets from mockup images stored in the database."""
    local_root_path = os.getenv('LOCAL_ROOT_PATH', '')
    if not local_root_path:
        raise Exception("LOCAL_ROOT_PATH environment variable not set")
    output_dir = f"{local_root_path}{current_user.shop_name}/Printfiles/"
    os.makedirs(output_dir, exist_ok=True)
    result = create_gang_sheets_from_db(
        db=db,
        user_id=current_user.id,
        template_name=template_name,
        output_path=output_dir
    )
    if result is None:
        return {
            "success": False,
            "error": f"No mockup images found for template '{template_name}'"
        }
    return {
        "success": True,
        "message": f"Successfully created gang sheets from mockup images for template '{template_name}'",
        "output_directory": output_dir
    }

def create_print_files(current_user, db):
    """Get item summary from Etsy and optionally create gang sheets."""
    user_id = current_user.get_uuid()
    etsy_api = EtsyAPI(user_id, db)
    template = db.query(EtsyProductTemplate).filter(EtsyProductTemplate.user_id == user_id).first() if hasattr(db, 'query') else None
    template_name = template.name if template else "UVDTF 16oz"
    user = db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    shop_name = user.shop_name
    if not shop_name:
        raise HTTPException(status_code=400, detail="User shop name not set")
    
    local_root = os.getenv('LOCAL_ROOT_PATH')
    if not local_root:
        raise HTTPException(status_code=500, detail="LOCAL_ROOT_PATH environment variable not set")
    item_summary = etsy_api.fetch_open_orders_items(f"{local_root}{shop_name}/", template_name) if etsy_api else None
    try:
        if item_summary and isinstance(item_summary, dict):
            create_gang_sheets(
                item_summary[template_name] if template_name in item_summary else item_summary.get("UVDTF 16oz", {}),
                template_name,
                f"{local_root}{shop_name}/Printfiles/",
                item_summary["Total QTY"] if "Total QTY" in item_summary else 0
            )
    except Exception as e:
        logging.error(f"Error creating gang sheets: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to create gang sheets: {str(e)}"
        }
    return {"success": True, "message": "Print files created successfully"}