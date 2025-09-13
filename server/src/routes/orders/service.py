import os
import tempfile
import logging
from fastapi import HTTPException
from dotenv import load_dotenv

from server.src.entities.user import User
from . import model
from server.src.utils.gangsheet_engine import create_gang_sheets_from_db, create_gang_sheets
from server.src.utils.etsy_api_engine import EtsyAPI
from server.src.utils.nas_storage import nas_storage
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

def get_orders(current_user, db) -> model.OrdersResponse:
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
    # Get user information from database
    user_id = current_user.get_uuid()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.shop_name:
        raise HTTPException(status_code=400, detail="User shop name not set")

    # Use temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "Printfiles")
        os.makedirs(output_dir, exist_ok=True)

        result = create_gang_sheets_from_db(
            db=db,
            user_id=user_id,
            template_name=template_name,
            output_path=output_dir
        )

        if result is None:
            return {
                "success": False,
                "error": f"No mockup images found for template '{template_name}'"
            }

        # Upload generated print files to NAS
        uploaded_files = []
        try:
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                        file_path = os.path.join(output_dir, filename)
                        relative_path = f"Printfiles/{filename}"
                        success = nas_storage.upload_file(
                            local_file_path=file_path,
                            shop_name=user.shop_name,
                            relative_path=relative_path
                        )
                        if success:
                            logging.info(f"Successfully uploaded print file to NAS: {relative_path}")
                            uploaded_files.append(filename)
                        else:
                            logging.warning(f"Failed to upload print file to NAS: {relative_path}")
        except Exception as e:
            logging.error(f"Error uploading print files to NAS: {e}")
            # Don't fail the entire process if NAS upload fails

        return {
            "success": True,
            "message": f"Successfully created gang sheets from mockup images for template '{template_name}'",
            "uploaded_files": uploaded_files,
            "files_count": len(uploaded_files)
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

    # For NAS-enabled production, we'll use database-driven gang sheet creation instead of file-based
    if nas_storage.enabled:
        logging.info("Using NAS storage - switching to database-driven gang sheet creation")
        # Use database-stored mockups instead of file-based approach
        return create_gang_sheets_from_mockups(template_name, current_user, db)
    else:
        # Fallback to local storage if NAS is not available (development mode)
        local_root = os.getenv('LOCAL_ROOT_PATH')
        if not local_root:
            raise HTTPException(status_code=500, detail="Neither NAS storage nor LOCAL_ROOT_PATH are available")
        item_summary = etsy_api.fetch_open_orders_items(f"{local_root}{shop_name}/", template_name) if etsy_api else None
    try:
        if item_summary and isinstance(item_summary, dict):
            # Use temporary directory for gang sheet generation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_printfiles_dir = os.path.join(temp_dir, "Printfiles")
                os.makedirs(temp_printfiles_dir, exist_ok=True)

                result = create_gang_sheets(
                    item_summary[template_name] if template_name in item_summary else item_summary.get("UVDTF 16oz", {}),
                    template_name,
                    temp_printfiles_dir + "/",
                    item_summary["Total QTY"] if "Total QTY" in item_summary else 0
                )

                if result is None:
                    return {
                        "success": False,
                        "error": "Failed to create gang sheets - check logs for details"
                    }
                elif isinstance(result, dict) and result.get("success"):
                    # Upload generated print files to NAS or handle local storage
                    uploaded_files = []
                    try:
                        if os.path.exists(temp_printfiles_dir):
                            for filename in os.listdir(temp_printfiles_dir):
                                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                                    file_path = os.path.join(temp_printfiles_dir, filename)
                                    relative_path = f"Printfiles/{filename}"

                                    if nas_storage.enabled:
                                        # Upload to NAS in production
                                        success = nas_storage.upload_file(
                                            local_file_path=file_path,
                                            shop_name=shop_name,
                                            relative_path=relative_path
                                        )
                                        if success:
                                            logging.info(f"Successfully uploaded print file to NAS: {relative_path}")
                                            uploaded_files.append(filename)
                                        else:
                                            logging.warning(f"Failed to upload print file to NAS: {relative_path}")
                                    else:
                                        # Copy to local storage as fallback
                                        local_root = os.getenv('LOCAL_ROOT_PATH')
                                        if local_root:
                                            local_printfiles_dir = f"{local_root}{shop_name}/Printfiles/"
                                            os.makedirs(local_printfiles_dir, exist_ok=True)
                                            local_file_path = os.path.join(local_printfiles_dir, filename)

                                            import shutil
                                            shutil.copy2(file_path, local_file_path)
                                            logging.info(f"Copied print file to local storage: {local_file_path}")
                                            uploaded_files.append(filename)
                    except Exception as e:
                        logging.error(f"Error handling print files: {e}")
                        # Don't fail the entire process if file handling fails

                    return {
                        "success": True,
                        "message": f"Print files created successfully - {result.get('sheets_created', 0)} sheets generated",
                        "sheets_created": result.get('sheets_created', 0),
                        "uploaded_files": uploaded_files,
                        "storage_mode": "NAS" if nas_storage.enabled else "Local"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Gang sheet creation returned unexpected result"
                    }
        else:
            return {
                "success": False,
                "error": "No valid item summary data available"
            }
    except Exception as e:
        logging.error(f"Error creating gang sheets: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to create gang sheets: {str(e)}"
        }