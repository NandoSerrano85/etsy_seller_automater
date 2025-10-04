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

def create_gang_sheets_from_mockups(template_name: str, current_user, db, printer_id=None, canvas_config_id=None):
    """Create gang sheets from mockup images stored in the database."""
    from server.src.entities.printer import Printer
    from server.src.entities.canvas_config import CanvasConfig

    # Get user information from database
    user_id = current_user.get_uuid()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.shop_name:
        raise HTTPException(status_code=400, detail="User shop name not set")

    # Get default printer if not specified
    if printer_id is None:
        default_printer = db.query(Printer).filter(
            Printer.user_id == user_id,
            Printer.is_default == True,
            Printer.is_active == True
        ).first()
        if default_printer:
            printer_id = default_printer.id
            logging.info(f"Using default printer: {default_printer.name}")

    # Get canvas config from template if not specified
    if canvas_config_id is None:
        template = db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.name == template_name,
            EtsyProductTemplate.user_id == user_id
        ).first()
        if template and template.canvas_configs:
            # Use first active canvas config
            for canvas in template.canvas_configs:
                if canvas.is_active:
                    canvas_config_id = canvas.id
                    logging.info(f"Using canvas config: {canvas.name}")
                    break

    # Use temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "Printfiles")
        os.makedirs(output_dir, exist_ok=True)

        result = create_gang_sheets_from_db(
            db=db,
            user_id=user_id,
            template_name=template_name,
            output_path=output_dir,
            printer_id=printer_id,
            canvas_config_id=canvas_config_id
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

def create_print_files(current_user, db, printer_id=None, canvas_config_id=None):
    """Get item summary from Etsy and optionally create gang sheets."""
    from server.src.entities.printer import Printer
    from server.src.entities.canvas_config import CanvasConfig

    try:
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

        logging.info(f"Creating print files for user: {user_id}, shop: {shop_name}, template: {template_name}")

        # Get default printer if not specified
        if printer_id is None:
            default_printer = db.query(Printer).filter(
                Printer.user_id == user_id,
                Printer.is_default == True,
                Printer.is_active == True
            ).first()
            if default_printer:
                printer_id = default_printer.id
                logging.info(f"Using default printer: {default_printer.name}")

        # Get canvas config from template if not specified
        if canvas_config_id is None and template and template.canvas_configs:
            # Use first active canvas config
            for canvas in template.canvas_configs:
                if canvas.is_active:
                    canvas_config_id = canvas.id
                    logging.info(f"Using canvas config: {canvas.name}")
                    break

        # Use NAS-compatible version for production, fallback to local for development
        if nas_storage.enabled:
            logging.info("Using NAS storage - fetching design files from QNAP NAS")
            # Use NAS-compatible method to get item summary with design files from NAS
            item_summary = etsy_api.fetch_open_orders_items_nas(shop_name, template_name) if etsy_api else None
        else:
            # Fallback to local storage if NAS is not available (development mode)
            local_root = os.getenv('LOCAL_ROOT_PATH')
            if not local_root:
                raise HTTPException(status_code=500, detail="Neither NAS storage nor LOCAL_ROOT_PATH are available")
            item_summary = etsy_api.fetch_open_orders_items(f"{local_root}{shop_name}/", template_name) if etsy_api else None
        if item_summary and isinstance(item_summary, dict):
            # Use temporary directory for gang sheet generation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_printfiles_dir = os.path.join(temp_dir, "Printfiles")
                temp_designs_dir = os.path.join(temp_dir, "Designs")
                os.makedirs(temp_printfiles_dir, exist_ok=True)
                os.makedirs(temp_designs_dir, exist_ok=True)

                # Download design files from NAS if using NAS storage
                processed_item_data = item_summary[template_name] if template_name in item_summary else item_summary.get("UVDTF 16oz", {})

                if nas_storage.enabled and processed_item_data.get('Title'):
                    # Download design files from NAS to temp directory and update paths
                    updated_titles = []
                    for design_file_path in processed_item_data['Title']:
                        if design_file_path:  # Skip empty paths
                            # Skip placeholder files that don't actually exist
                            if "MISSING_" in design_file_path:
                                logging.warning(f"Skipping download of placeholder file: {design_file_path}")
                                updated_titles.append(design_file_path)  # Keep placeholder path
                                continue

                            # Design file path is relative to shop (e.g., "UVDTF 16oz/design.png")
                            local_filename = os.path.basename(design_file_path)
                            local_file_path = os.path.join(temp_designs_dir, local_filename)

                            # Download from NAS
                            success = nas_storage.download_file(
                                shop_name=shop_name,
                                relative_path=design_file_path,
                                local_file_path=local_file_path
                            )

                            if success:
                                updated_titles.append(local_file_path)
                                logging.info(f"Downloaded design file from NAS: {design_file_path} -> {local_file_path}")
                            else:
                                logging.error(f"Failed to download design file from NAS: {design_file_path}")
                                # Keep original path as fallback (though it might fail)
                                updated_titles.append(design_file_path)
                        else:
                            updated_titles.append(design_file_path)

                    # Update the processed data with local file paths
                    processed_item_data = processed_item_data.copy()
                    processed_item_data['Title'] = updated_titles

                result = create_gang_sheets(
                    processed_item_data,
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