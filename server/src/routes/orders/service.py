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
from server.src.routes.designs.service import get_etsy_shop_name

load_dotenv()
API_CONFIG = {
    'base_url': 'https://openapi.etsy.com/v3',
}

def get_oauth_variables():
    return {
        'clientID': os.getenv('CLIENT_ID'),
        'clientSecret': os.getenv('CLIENT_SECRET'),
    }

def get_orders(current_user, db, was_shipped=None, was_paid=None, was_canceled=None) -> model.OrdersResponse:
    """
    Get orders with optional status filters.

    Args:
        current_user: Current authenticated user
        db: Database session
        was_shipped: Filter by shipped status ('true', 'false', or None for all)
        was_paid: Filter by paid status ('true', 'false', or None for all)
        was_canceled: Filter by canceled status ('true', 'false', or None for all)

    Returns:
        OrdersResponse with filtered orders
    """
    try:
        etsy_api = EtsyAPI(current_user.get_uuid(), db)
        orders = etsy_api.fetch_order_summary(
            model,
            was_shipped=was_shipped,
            was_paid=was_paid,
            was_canceled=was_canceled
        )
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
    import time
    from server.src.entities.printer import Printer
    from server.src.entities.canvas_config import CanvasConfig
    from sqlalchemy.orm import joinedload

    # Track total execution time
    start_time = time.time()

    # Get user information from database
    user_id = current_user.get_uuid()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get shop name from etsy_stores table, fallback to user.shop_name
    shop_name = get_etsy_shop_name(db, user_id)
    if not shop_name or shop_name.startswith("user_"):
        # Fallback to user.shop_name for backwards compatibility
        shop_name = user.shop_name if hasattr(user, 'shop_name') else None
        if not shop_name:
            raise HTTPException(status_code=400, detail="No shop name configured. Please connect your Etsy store or set shop name in settings.")

    # OPTIMIZATION: Fetch printer, template, and canvas config in a single optimized query
    db_fetch_start = time.time()

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

    # Get canvas config from template if not specified (with eager loading)
    if canvas_config_id is None:
        template = db.query(EtsyProductTemplate).options(
            joinedload(EtsyProductTemplate.canvas_configs)
        ).filter(
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

    db_fetch_time = time.time() - db_fetch_start
    logging.info(f"Database configuration fetch completed in {db_fetch_time:.3f}s")

    # Use temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "Printfiles")
        os.makedirs(output_dir, exist_ok=True)

        gangsheet_start = time.time()
        result = create_gang_sheets_from_db(
            db=db,
            user_id=user_id,
            template_name=template_name,
            output_path=output_dir,
            printer_id=printer_id,
            canvas_config_id=canvas_config_id
        )
        gangsheet_time = time.time() - gangsheet_start
        logging.info(f"Gangsheet creation completed in {gangsheet_time:.2f}s")

        if result is None:
            total_time = time.time() - start_time
            logging.info(f"Total request time: {total_time:.2f}s (failed - no mockup images)")
            return {
                "success": False,
                "error": f"No mockup images found for template '{template_name}'"
            }

        # Upload generated print files to NAS
        upload_start = time.time()
        uploaded_files = []
        try:
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    file_ext = filename.lower().split('.')[-1]
                    if file_ext in ('png', 'jpg', 'jpeg', 'pdf', 'svg', 'psd'):
                        file_path = os.path.join(output_dir, filename)
                        relative_path = f"Printfiles/{filename}"
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
        except Exception as e:
            logging.error(f"Error uploading print files to NAS: {e}")
            # Don't fail the entire process if NAS upload fails

        upload_time = time.time() - upload_start
        total_time = time.time() - start_time
        logging.info(f"NAS upload completed in {upload_time:.2f}s")
        logging.info(f"✅ TOTAL REQUEST TIME: {total_time:.2f}s (DB: {db_fetch_time:.2f}s, Gangsheet: {gangsheet_time:.2f}s, Upload: {upload_time:.2f}s)")

        return {
            "success": True,
            "message": f"Successfully created gang sheets from mockup images for template '{template_name}'",
            "uploaded_files": uploaded_files,
            "files_count": len(uploaded_files),
            "execution_time": f"{total_time:.2f}s"
        }

def create_print_files(current_user, db, printer_id=None, canvas_config_id=None, format='PNG'):
    """Get item summary from Etsy and optionally create gang sheets."""
    from server.src.entities.printer import Printer
    from server.src.entities.canvas_config import CanvasConfig

    try:
        logging.info("🚀 create_print_files: Starting request")

        user_id = current_user.get_uuid()
        logging.info(f"📋 create_print_files: User ID: {user_id}")

        etsy_api = EtsyAPI(user_id, db)
        logging.info("✅ create_print_files: EtsyAPI initialized")

        template = db.query(EtsyProductTemplate).filter(EtsyProductTemplate.user_id == user_id).first() if hasattr(db, 'query') else None
        template_name = template.name if template else "UVDTF 16oz"
        logging.info(f"📋 create_print_files: Template name: {template_name}")

        user = db.query(User).filter(User.id==user_id).first()
        if not user:
            logging.error(f"❌ create_print_files: User not found for ID {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        logging.info(f"✅ create_print_files: User found: {user.email if hasattr(user, 'email') else 'no email'}")

        # Get shop name from etsy_stores table, fallback to user.shop_name
        shop_name = get_etsy_shop_name(db, user_id)
        logging.info(f"📋 create_print_files: Shop name from etsy_stores: {shop_name}")

        if not shop_name or shop_name.startswith("user_"):
            # Fallback to user.shop_name for backwards compatibility
            shop_name = user.shop_name if hasattr(user, 'shop_name') else None
            logging.info(f"📋 create_print_files: Using fallback shop_name from user: {shop_name}")
            if not shop_name:
                logging.error("❌ create_print_files: No shop name found in etsy_stores or user table")
                raise HTTPException(status_code=400, detail="No shop name configured. Please connect your Etsy store or set shop name in settings.")

        logging.info(f"✅ Creating print files for user: {user_id}, shop: {shop_name}, template: {template_name}")

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
            logging.info("🔵 Using NAS storage - fetching design files from QNAP NAS")
            try:
                # Use NAS-compatible method to get item summary with design files from NAS
                item_summary = etsy_api.fetch_open_orders_items_nas(shop_name, template_name) if etsy_api else None
                logging.info(f"✅ fetch_open_orders_items_nas completed. Summary exists: {item_summary is not None}")
            except Exception as e:
                logging.error(f"❌ Error in fetch_open_orders_items_nas: {str(e)}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                raise
        else:
            # Fallback to local storage if NAS is not available (development mode)
            logging.info("🔵 Using local storage")
            local_root = os.getenv('LOCAL_ROOT_PATH')
            if not local_root:
                raise HTTPException(status_code=500, detail="Neither NAS storage nor LOCAL_ROOT_PATH are available")
            item_summary = etsy_api.fetch_open_orders_items(f"{local_root}{shop_name}/", template_name) if etsy_api else None
            logging.info(f"✅ fetch_open_orders_items completed. Summary exists: {item_summary is not None}")
        if item_summary and isinstance(item_summary, dict):
            # Use temporary directory for gang sheet generation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_printfiles_dir = os.path.join(temp_dir, "Printfiles")
                temp_designs_dir = os.path.join(temp_dir, "Designs")
                os.makedirs(temp_printfiles_dir, exist_ok=True)
                os.makedirs(temp_designs_dir, exist_ok=True)

                # Initialize counters
                download_count = 0
                skipped_count = 0

                # Download design files from NAS if using NAS storage
                processed_item_data = item_summary[template_name] if template_name in item_summary else item_summary.get("UVDTF 16oz", {})

                if nas_storage.enabled and processed_item_data.get('Title'):
                    # Download design files from NAS to temp directory and update paths
                    import time
                    download_start = time.time()
                    logging.info(f"Starting download of {len(processed_item_data['Title'])} design files from NAS")

                    updated_titles = []
                    updated_totals = []
                    updated_sizes = []
                    original_totals = processed_item_data.get('Total', [])
                    original_sizes = processed_item_data.get('Size', [])

                    for idx, design_file_path in enumerate(processed_item_data['Title']):
                        if design_file_path:  # Skip empty paths
                            # Skip placeholder files that don't actually exist
                            if "MISSING_" in design_file_path:
                                logging.warning(f"Skipping placeholder file: {design_file_path}")
                                skipped_count += 1
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
                                # Keep the corresponding quantity and size
                                if idx < len(original_totals):
                                    updated_totals.append(original_totals[idx])
                                if idx < len(original_sizes):
                                    updated_sizes.append(original_sizes[idx])
                                else:
                                    updated_sizes.append('')  # Default to empty if size not available
                                download_count += 1
                                logging.debug(f"✅ Downloaded: {design_file_path} -> {local_file_path}")
                            else:
                                logging.warning(f"⚠️  Skipping missing file: {design_file_path}")
                                skipped_count += 1
                                # Don't add failed files to the list - skip them entirely
                        else:
                            # Empty path - skip it
                            skipped_count += 1

                    download_duration = time.time() - download_start
                    logging.info(f"✅ Downloaded {download_count} files, ⚠️  skipped {skipped_count} missing files in {download_duration:.2f}s")

                    # Update the processed data with local file paths and updated arrays
                    processed_item_data = processed_item_data.copy()
                    processed_item_data['Title'] = updated_titles
                    processed_item_data['Total'] = updated_totals
                    processed_item_data['Size'] = updated_sizes

                    # Verify array lengths match
                    if len(updated_titles) != len(updated_totals) or len(updated_titles) != len(updated_sizes):
                        logging.error(f"❌ Array length mismatch: Title={len(updated_titles)}, Total={len(updated_totals)}, Size={len(updated_sizes)}")
                        return {
                            "success": False,
                            "error": "Data mismatch after filtering missing files"
                        }

                    # If we have no valid files, return early with error
                    if not updated_titles:
                        logging.error("❌ No valid design files found - all files missing or failed to download")
                        return {
                            "success": False,
                            "error": f"No design files available. {skipped_count} files were missing or failed to download.",
                            "skipped_files": skipped_count
                        }

                logging.info("Starting gangsheet creation (all NAS connections now closed)")
                result = create_gang_sheets(
                    processed_item_data,
                    template_name,
                    temp_printfiles_dir + "/",
                    item_summary["Total QTY"] if "Total QTY" in item_summary else 0,
                    file_format=format
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
                                file_ext = filename.lower().split('.')[-1]
                                if file_ext in ('png', 'jpg', 'jpeg', 'pdf', 'svg', 'psd'):
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

                    success_message = f"Print files created successfully - {result.get('sheets_created', 0)} sheets generated"
                    if skipped_count > 0:
                        success_message += f" (⚠️  {skipped_count} missing files skipped)"

                    return {
                        "success": True,
                        "message": success_message,
                        "sheets_created": result.get('sheets_created', 0),
                        "uploaded_files": uploaded_files,
                        "storage_mode": "NAS" if nas_storage.enabled else "Local",
                        "files_downloaded": download_count,
                        "files_skipped": skipped_count
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
    except HTTPException as e:
        # Re-raise HTTPExceptions so they propagate with proper status codes
        logging.error(f"❌ HTTP Error in create_print_files: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logging.error(f"❌ Error creating print files: {str(e)}")
        logging.error(f"📋 Full traceback:\n{error_traceback}")
        return {
            "success": False,
            "error": f"Failed to create print files: {str(e)}",
            "traceback": error_traceback[:500]  # Include first 500 chars of traceback for debugging
        }

def get_all_orders_with_details(current_user, db, limit=100, offset=0, was_shipped=None, was_paid=None, was_canceled=None):
    """
    Get all Etsy orders with full details for selection interface.

    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of orders to return
        offset: Number of orders to skip (for pagination)
        was_shipped: Filter by shipped status ('true', 'false', or None for all)
        was_paid: Filter by paid status ('true', 'false', or None for all)
        was_canceled: Filter by canceled status ('true', 'false', or None for all)

    Returns:
        Dictionary with orders list and metadata
    """
    try:
        user_id = current_user.get_uuid()
        etsy_api = EtsyAPI(user_id, db)

        # Get user for shop info
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.etsy_shop_id:
            raise HTTPException(status_code=400, detail="User shop not configured")

        logging.info(f"Fetching all orders for user {user_id} (limit={limit}, offset={offset})")

        # Fetch orders with items from Etsy API
        orders_data = etsy_api.get_shop_receipts_with_items(
            shop_id=user.etsy_shop_id,
            limit=limit,
            offset=offset,
            was_shipped=was_shipped,
            was_paid=was_paid,
            was_canceled=was_canceled
        )

        if not orders_data:
            return {
                "success": True,
                "orders": [],
                "count": 0,
                "total": 0,
                "limit": limit,
                "offset": offset
            }

        # Process orders to include item details
        processed_orders = []
        for order in orders_data.get('results', []):
            # Get items for this order
            items = []
            for transaction in order.get('transactions', []):
                items.append({
                    "transaction_id": transaction.get('transaction_id'),
                    "title": transaction.get('title', 'Unknown Item'),
                    "quantity": transaction.get('quantity', 1),
                    "price": transaction.get('price', {}).get('amount', 0),
                    "listing_id": transaction.get('listing_id'),
                    "product_id": transaction.get('product_id'),
                    "variation": transaction.get('variations', [])
                })

            processed_orders.append({
                "receipt_id": order.get('receipt_id'),
                "order_id": order.get('receipt_id'),  # Use receipt_id as order_id
                "buyer_name": f"{order.get('name', '')} {order.get('first_line', '')}".strip(),
                "customer_name": f"{order.get('name', '')} {order.get('first_line', '')}".strip(),  # Add customer_name for frontend compatibility
                "buyer_email": order.get('buyer_email', ''),
                "create_timestamp": order.get('create_timestamp'),
                "status": order.get('status', 'unknown'),
                "grandtotal": order.get('grandtotal', {}).get('amount', 0),
                "items_count": len(items),
                "items": items,
                "is_gift": order.get('is_gift', False),
                "message_from_buyer": order.get('message_from_buyer', ''),
                "shipments": order.get('shipments', [])
            })

        return {
            "success": True,
            "orders": processed_orders,
            "count": len(processed_orders),
            "total": orders_data.get('count', len(processed_orders)),
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching all orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

def create_print_files_from_selected_orders(order_ids, template_name, current_user, db, printer_id=None, canvas_config_id=None, format='PNG'):
    """
    Create print files (gang sheets) from specific selected orders.

    Args:
        order_ids: List of order/receipt IDs to process
        template_name: Template name to use for gang sheet
        current_user: Current authenticated user
        db: Database session
        printer_id: Optional printer ID
        canvas_config_id: Optional canvas config ID
        format: File format for output (PNG, SVG, or PSD)

    Returns:
        Dictionary with success status and file information
    """
    print(f"Starting create_print_files_from_selected_orders with order_ids: {order_ids} and template_name: {template_name}")
    print(type(order_ids))
    import time
    from server.src.entities.printer import Printer
    from server.src.entities.canvas_config import CanvasConfig
    from sqlalchemy.orm import joinedload

    # Track total execution time
    start_time = time.time()

    try:
        user_id = current_user.get_uuid()
        etsy_api = EtsyAPI(user_id, db)

        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get shop name from etsy_stores table, fallback to user.shop_name
        shop_name = get_etsy_shop_name(db, user_id)
        if not shop_name or shop_name.startswith("user_"):
            # Fallback to user.shop_name for backwards compatibility
            shop_name = user.shop_name if hasattr(user, 'shop_name') else None
            if not shop_name:
                raise HTTPException(status_code=400, detail="No shop name configured. Please connect your Etsy store or set shop name in settings.")

        logging.info(f"Creating print files for {len(order_ids)} selected orders")

        # CRITICAL: Check memory BEFORE starting - prevent OOM kills early
        try:
            from server.src.utils.memory_emergency import get_memory_guard, log_memory_warning, get_max_safe_batch_size

            memory_guard = get_memory_guard()
            initial_mem = memory_guard.check_memory()

            if 'percent' in initial_mem:
                log_memory_warning(initial_mem['percent'])

                # If memory is already high, abort before downloading anything
                if initial_mem['percent'] > 70:
                    logging.error(f"🔥 ABORT: Memory already at {initial_mem['percent']:.1f}% before starting")
                    logging.error(f"🔥 Cannot safely process {len(order_ids)} orders")
                    logging.error(f"💡 Current memory: {initial_mem['current_gb']:.2f}GB / {initial_mem['total_gb']:.2f}GB")

                    # Get recommendation for safe batch size
                    recommendations = memory_guard.get_recommendations(needed_gb=3.0)
                    if recommendations:
                        logging.error(f"💡 Recommendations:")
                        for rec in recommendations:
                            logging.error(f"   {rec['priority']}: {rec['action']}")

                    return {
                        "success": False,
                        "error": f"Insufficient memory: {initial_mem['percent']:.1f}% usage before starting",
                        "current_memory_gb": initial_mem['current_gb'],
                        "total_memory_gb": initial_mem['total_gb'],
                        "recommendation": f"Reduce batch size to 10-15 orders (you selected {len(order_ids)})"
                    }

                # Calculate safe batch size
                safe_batch = get_max_safe_batch_size(item_count=len(order_ids), avg_item_memory_mb=100)
                if safe_batch < len(order_ids):
                    logging.warning(f"⚠️  Selected {len(order_ids)} orders, but safe batch size is {safe_batch}")
                    logging.warning(f"⚠️  Risk of OOM kill is HIGH - consider processing fewer orders")

                logging.info(f"✅ Initial memory check passed: {initial_mem['percent']:.1f}%")

        except Exception as mem_error:
            logging.warning(f"Memory check error (non-critical): {mem_error}")

        # Fetch order items for selected orders only
        order_items_data = etsy_api.fetch_selected_order_items(
            shop_id=user.etsy_shop_id,
            order_ids=order_ids,
            template_name=template_name,
            shop_name=shop_name
        )

        if not order_items_data or not order_items_data.get('items'):
            return {
                "success": False,
                "error": "No items found in selected orders"
            }

        logging.info(f"Found {order_items_data['items']} items in selected orders")

        # Get configuration (same as create_print_files)
        db_fetch_start = time.time()

        if printer_id is None:
            default_printer = db.query(Printer).filter(
                Printer.user_id == user_id,
                Printer.is_default == True,
                Printer.is_active == True
            ).first()
            if default_printer:
                printer_id = default_printer.id
                logging.info(f"Using default printer: {default_printer.name}")

        if canvas_config_id is None:
            template = db.query(EtsyProductTemplate).options(
                joinedload(EtsyProductTemplate.canvas_configs)
            ).filter(
                EtsyProductTemplate.name == template_name,
                EtsyProductTemplate.user_id == user_id
            ).first()
            if template and template.canvas_configs:
                for canvas in template.canvas_configs:
                    if canvas.is_active:
                        canvas_config_id = canvas.id
                        logging.info(f"Using canvas config: {canvas.name}")
                        break

        db_fetch_time = time.time() - db_fetch_start
        logging.info(f"Database configuration fetch completed in {db_fetch_time:.3f}s")

        # Create gang sheets
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "Printfiles")
            temp_designs_dir = os.path.join(temp_dir, "Designs")
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(temp_designs_dir, exist_ok=True)

            # Download design files from NAS to temp directory
            if nas_storage.enabled and order_items_data.get('Title'):
                download_start = time.time()
                logging.info(f"Starting download of {len(order_items_data['Title'])} design files from NAS")

                updated_titles = []
                download_count = 0
                skipped_count = 0

                # Memory monitoring during downloads
                try:
                    from server.src.utils.memory_emergency import get_memory_guard
                    memory_guard = get_memory_guard()
                except:
                    memory_guard = None

                for idx, design_file_path in enumerate(order_items_data['Title']):
                    # Check memory every 5 downloads to avoid OOM during download phase
                    if memory_guard and idx > 0 and idx % 5 == 0:
                        mem_status = memory_guard.check_memory()
                        if 'percent' in mem_status and mem_status['percent'] > 80:
                            logging.error(f"🔥 ABORT DURING DOWNLOADS: Memory at {mem_status['percent']:.1f}% after {download_count} downloads")
                            logging.error(f"🔥 Stopping downloads to prevent OOM kill")
                            logging.error(f"💡 Successfully downloaded {download_count} files, skipping remaining {len(order_items_data['Title']) - idx}")
                            logging.error(f"💡 Reduce batch size to process fewer orders at once")
                            return {
                                "success": False,
                                "error": f"Memory limit reached during downloads: {mem_status['percent']:.1f}%",
                                "downloads_completed": download_count,
                                "downloads_total": len(order_items_data['Title']),
                                "recommendation": "Reduce batch size - process 10-15 orders instead"
                            }

                    if design_file_path:  # Skip empty paths
                        # Skip placeholder files that don't actually exist
                        if "MISSING_" in design_file_path:
                            logging.warning(f"Skipping download of placeholder file: {design_file_path}")
                            updated_titles.append(design_file_path)  # Keep placeholder path
                            skipped_count += 1
                            continue

                        # Design file path is relative to shop (e.g., "UVDTF 16oz/UV840.png")
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
                            download_count += 1
                            logging.debug(f"Downloaded design file from NAS: {design_file_path} -> {local_file_path}")
                        else:
                            logging.error(f"Failed to download design file from NAS: {design_file_path}")
                            # Keep original path as fallback (though it might fail)
                            updated_titles.append(design_file_path)
                            skipped_count += 1
                    else:
                        updated_titles.append(design_file_path)

                download_duration = time.time() - download_start
                if skipped_count > 0:
                    logging.info(f"Downloaded {download_count} design files from NAS in {download_duration:.2f}s ({skipped_count} skipped)")
                else:
                    logging.info(f"Downloaded {download_count} design files from NAS in {download_duration:.2f}s")

                # Update the data with local file paths
                order_items_data = order_items_data.copy()
                order_items_data['Title'] = updated_titles

            gangsheet_start = time.time()
            result = create_gang_sheets(
                image_data=order_items_data,
                image_type=template_name,
                output_path=output_dir,
                total_images=len(order_items_data.get('Title', [])),
                dpi=400,
                std_dpi=400,
                file_format=format
            )
            gangsheet_time = time.time() - gangsheet_start
            logging.info(f"Gangsheet creation completed in {gangsheet_time:.2f}s")

            if result is None:
                total_time = time.time() - start_time
                logging.info(f"Total request time: {total_time:.2f}s (failed)")
                return {
                    "success": False,
                    "error": "Gang sheet creation failed"
                }

            # Upload to NAS
            upload_start = time.time()
            uploaded_files = []
            try:
                if os.path.exists(output_dir):
                    for filename in os.listdir(output_dir):
                        file_ext = filename.lower().split('.')[-1]
                        if file_ext in ('png', 'jpg', 'jpeg', 'pdf', 'svg', 'psd'):
                            file_path = os.path.join(output_dir, filename)
                            relative_path = f"Printfiles/{filename}"
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
            except Exception as e:
                logging.error(f"Error uploading print files to NAS: {e}")

            upload_time = time.time() - upload_start
            total_time = time.time() - start_time
            logging.info(f"NAS upload completed in {upload_time:.2f}s")
            logging.info(f"✅ TOTAL REQUEST TIME: {total_time:.2f}s (Selected Orders: {len(order_ids)}, Gangsheet: {gangsheet_time:.2f}s, Upload: {upload_time:.2f}s)")

            return {
                "success": True,
                "message": f"Successfully created gang sheets from {len(order_ids)} selected orders",
                "orders_processed": len(order_ids),
                "items_processed": len(order_items_data.get('Title', [])),
                "uploaded_files": uploaded_files,
                "files_count": len(uploaded_files),
                "execution_time": f"{total_time:.2f}s",
                "sheets_created": result.get('sheets_created', 0)
            }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating print files from selected orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create print files: {str(e)}")