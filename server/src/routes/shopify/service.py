from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from server.src.utils.shopify_client import (
    ShopifyClient,
    ShopifyAPIError,
    ShopifyAuthError,
    ShopifyNotFoundError,
    ShopifyRateLimitError
)
from server.src.entities.shopify_store import ShopifyStore
import logging

logger = logging.getLogger(__name__)

class ShopifyService:
    """
    Service layer for Shopify operations, providing a clean interface between
    the API routes and the Shopify client.
    """

    def __init__(self, db: Session):
        """
        Initialize Shopify service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.client = ShopifyClient(db)

    def _handle_shopify_error(self, error: Exception, operation: str = "operation") -> None:
        """
        Convert Shopify errors to appropriate HTTP exceptions.

        Args:
            error: The exception that occurred
            operation: Description of the operation for logging
        """
        if isinstance(error, ShopifyAuthError):
            logger.error(f"Authentication failed during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Shopify authentication failed. Please reconnect your store."
            )
        elif isinstance(error, ShopifyNotFoundError):
            logger.error(f"Resource not found during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error)
            )
        elif isinstance(error, ShopifyRateLimitError):
            logger.error(f"Rate limit exceeded during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Shopify rate limit exceeded. Retry after {error.retry_after} seconds."
            )
        elif isinstance(error, ShopifyAPIError):
            logger.error(f"Shopify API error during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shopify API error: {str(error)}"
            )
        else:
            logger.error(f"Unexpected error during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred during {operation}"
            )

    def get_user_store(self, user_id: UUID) -> Optional[ShopifyStore]:
        """
        Get the connected Shopify store for a user.

        Args:
            user_id: User UUID

        Returns:
            ShopifyStore object or None if not found
        """
        return self.db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.is_active == True
        ).first()

    def get_orders(self, user_id: UUID, since_time: Optional[datetime] = None,
                   limit: int = 250, status: str = "any") -> List[Dict[str, Any]]:
        """
        Fetch orders for a user's connected Shopify store.

        Args:
            user_id: User UUID
            since_time: Optional datetime to fetch orders since
            limit: Maximum number of orders to fetch
            status: Order status filter

        Returns:
            List of order dictionaries

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.get_orders(
                store_id=str(store.id),
                since_time=since_time,
                limit=limit,
                status=status
            )
        except Exception as e:
            self._handle_shopify_error(e, "fetching orders")

    def get_products(self, user_id: UUID, limit: int = 250,
                    published_status: str = "published") -> List[Dict[str, Any]]:
        """
        Fetch products for a user's connected Shopify store.

        Args:
            user_id: User UUID
            limit: Maximum number of products to fetch
            published_status: Filter by published status

        Returns:
            List of product dictionaries

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.get_products(
                store_id=str(store.id),
                limit=limit,
                published_status=published_status
            )
        except Exception as e:
            self._handle_shopify_error(e, "fetching products")

    def create_product(self, user_id: UUID, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product in user's connected Shopify store.

        Args:
            user_id: User UUID
            product_data: Product data dictionary

        Returns:
            Created product dictionary

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.create_product(
                store_id=str(store.id),
                product_data=product_data
            )
        except Exception as e:
            self._handle_shopify_error(e, "creating product")

    def upload_product_image(self, user_id: UUID, product_id: str,
                           image_file: UploadFile, alt_text: Optional[str] = None,
                           position: Optional[int] = None) -> Dict[str, Any]:
        """
        Upload an image to a product in user's connected Shopify store.

        Args:
            user_id: User UUID
            product_id: Shopify product ID
            image_file: Uploaded image file
            alt_text: Optional alt text for the image
            position: Optional position of the image

        Returns:
            Created image dictionary

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.upload_product_image(
                store_id=str(store.id),
                product_id=product_id,
                image_file=image_file.file,
                filename=image_file.filename,
                alt_text=alt_text,
                position=position
            )
        except Exception as e:
            self._handle_shopify_error(e, "uploading product image")

    def update_product(self, user_id: UUID, product_id: str,
                      product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product in user's connected Shopify store.

        Args:
            user_id: User UUID
            product_id: Shopify product ID
            product_data: Updated product data

        Returns:
            Updated product dictionary

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.update_product(
                store_id=str(store.id),
                product_id=product_id,
                product_data=product_data
            )
        except Exception as e:
            self._handle_shopify_error(e, "updating product")

    def delete_product(self, user_id: UUID, product_id: str) -> bool:
        """
        Delete a product from user's connected Shopify store.

        Args:
            user_id: User UUID
            product_id: Shopify product ID

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.delete_product(
                store_id=str(store.id),
                product_id=product_id
            )
        except Exception as e:
            self._handle_shopify_error(e, "deleting product")

    def get_product_by_id(self, user_id: UUID, product_id: str) -> Dict[str, Any]:
        """
        Get a specific product by ID from user's connected Shopify store.

        Args:
            user_id: User UUID
            product_id: Shopify product ID

        Returns:
            Product dictionary

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.get_product_by_id(
                store_id=str(store.id),
                product_id=product_id
            )
        except Exception as e:
            self._handle_shopify_error(e, "fetching product")

    def get_order_by_id(self, user_id: UUID, order_id: str) -> Dict[str, Any]:
        """
        Get a specific order by ID from user's connected Shopify store.

        Args:
            user_id: User UUID
            order_id: Shopify order ID

        Returns:
            Order dictionary

        Raises:
            HTTPException: If store not found or API error occurs
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.get_order_by_id(
                store_id=str(store.id),
                order_id=order_id
            )
        except Exception as e:
            self._handle_shopify_error(e, "fetching order")

    def test_connection(self, user_id: UUID) -> Dict[str, Any]:
        """
        Test the connection to user's Shopify store.

        Args:
            user_id: User UUID

        Returns:
            Shop information dictionary

        Raises:
            HTTPException: If store not found or connection test fails
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found. Please connect a store first."
            )

        try:
            return self.client.test_connection(store_id=str(store.id))
        except Exception as e:
            self._handle_shopify_error(e, "testing connection")

    @staticmethod
    def verify_webhook_signature(headers: Dict[str, str], body: bytes,
                                webhook_secret: Optional[str] = None) -> bool:
        """
        Verify the signature of a Shopify webhook.

        Args:
            headers: Request headers dictionary
            body: Raw request body as bytes
            webhook_secret: Optional webhook secret

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            return ShopifyClient.verify_webhook_signature(headers, body, webhook_secret)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    def create_print_files_from_selected_orders(
        self,
        user_id: UUID,
        order_ids: List[int],
        template_name: str
    ) -> Dict[str, Any]:
        """
        Create gang sheet print files from selected Shopify orders.

        Args:
            user_id: User UUID
            order_ids: List of Shopify order IDs
            template_name: Template name for gang sheet

        Returns:
            Dictionary with success status and details
        """
        import time
        import os
        import tempfile
        from server.src.utils.gangsheet_engine import create_gang_sheets
        from server.src.utils.nas_storage import nas_storage
        from server.src.entities.user import User
        from server.src.entities.designs import DesignImages

        logger.info(f"Creating print files for {len(order_ids)} selected Shopify orders")

        # Get user and store information
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(status_code=404, detail="No connected Shopify store found")

        # Initialize result structure
        image_data = {
            'Title': [],
            'Size': [],
            'Total': []
        }

        processed_items = 0

        # Fetch each order and extract line items
        for order_id in order_ids:
            try:
                order = self.client.get_order_by_id(str(store.id), order_id)

                fulfillment_status = order.get('fulfillment_status', 'unfulfilled')
                line_items = order.get('line_items', [])
                logger.info(f"📦 Order {order_id}: Found {len(line_items)} items | fulfillment: {fulfillment_status}")

                # Process each line item
                for idx, line_item in enumerate(line_items, 1):
                    item_title = line_item.get('name', '')
                    quantity = line_item.get('quantity', 1)
                    item_id = line_item.get('id', 'unknown')

                    logger.info(f"  Processing item {idx}/{len(line_items)} from order {order_id}: '{item_title}' (qty: {quantity}, item_id: {item_id})")

                    # Try to find design file for this item
                    design_path = self._find_design_for_shopify_item(item_title, template_name, user_id)

                    if design_path:
                        image_data['Title'].append(design_path)
                        image_data['Size'].append(template_name)
                        image_data['Total'].append(quantity)
                        processed_items += 1
                        logger.info(f"  ✅ Added item from order {order_id}: {item_title} (qty: {quantity}) -> {design_path}")
                    else:
                        logger.warning(f"  ❌ No design found for item: {item_title}")

            except Exception as e:
                logger.error(f"Error processing order {order_id}: {e}")
                continue

        logger.info(f"Processed {processed_items} items from {len(order_ids)} selected orders")

        if processed_items == 0:
            return {
                "success": False,
                "error": "No items found in selected orders"
            }

        # Download design files from NAS if needed
        temp_designs_dir = tempfile.mkdtemp(prefix="shopify_designs_")
        try:
            if nas_storage.enabled and image_data.get('Title'):
                download_start = time.time()
                logger.info(f"Starting download of {len(image_data['Title'])} design files from NAS")

                updated_titles = []
                download_count = 0
                for design_file_path in image_data['Title']:
                    if design_file_path and "MISSING_" not in design_file_path:
                        local_filename = os.path.basename(design_file_path)
                        local_file_path = os.path.join(temp_designs_dir, local_filename)

                        success = nas_storage.download_file(
                            shop_name=user.shop_name,
                            relative_path=design_file_path,
                            local_file_path=local_file_path
                        )
                        if success:
                            updated_titles.append(local_file_path)
                            download_count += 1
                        else:
                            logger.warning(f"Failed to download: {design_file_path}")
                            updated_titles.append(design_file_path)
                    else:
                        updated_titles.append(design_file_path)

                image_data['Title'] = updated_titles
                download_time = time.time() - download_start
                logger.info(f"Downloaded {download_count}/{len(image_data['Title'])} files from NAS in {download_time:.2f}s")

            # Create gang sheets
            gangsheet_start = time.time()
            result = create_gang_sheets(image_data, template_name, user.shop_name)
            gangsheet_time = time.time() - gangsheet_start

            logger.info(f"Gang sheet creation took {gangsheet_time:.2f}s")

            return {
                "success": True,
                "message": f"Created gang sheets from {processed_items} items",
                "sheets_created": result.get('sheets_created', 0)
            }

        except Exception as e:
            logger.error(f"Error creating gang sheets: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up temp directory
            import shutil
            if os.path.exists(temp_designs_dir):
                shutil.rmtree(temp_designs_dir)

    def _find_design_for_shopify_item(self, item_title: str, template_name: str, user_id: UUID) -> Optional[str]:
        """
        Find design file for a Shopify item.

        Args:
            item_title: Item title from Shopify order
            template_name: Template name
            user_id: User UUID

        Returns:
            Design file path or None
        """
        import re
        from server.src.entities.designs import DesignImages
        from server.src.entities.template import EtsyProductTemplate

        # Extract UV number or design identifier from title
        search_name = item_title
        match = re.match(r'^(UV\s*\d+)', item_title.strip(), re.IGNORECASE)
        if match:
            search_name = match.group(1).strip()
            logger.info(f"🔍 Extracted design number '{search_name}' from title '{item_title}'")
        else:
            logger.warning(f"⚠️ Could not extract UV number from title: '{item_title}'")

        # Try database first
        try:
            normalized_search = re.sub(r'\s+', ' ', search_name.strip())

            base_query = self.db.query(DesignImages).filter(
                DesignImages.user_id == user_id,
                DesignImages.is_active == True
            )

            # Filter by template if provided
            if template_name:
                base_query = base_query.join(DesignImages.product_templates).filter(
                    EtsyProductTemplate.name == template_name
                )

            # Try exact substring match
            design = base_query.filter(
                DesignImages.filename.ilike(f'%{normalized_search}%')
            ).first()

            if design:
                logger.info(f"✅ Found in database: {design.file_path}")
                return design.file_path

            # Try without spaces
            no_space_search = normalized_search.replace(" ", "")
            design = base_query.filter(
                DesignImages.filename.ilike(f'%{no_space_search}%')
            ).first()

            if design:
                logger.info(f"✅ Found in database (no-space match): {design.file_path}")
                return design.file_path

            # Try just the number
            parts = normalized_search.split(" ")
            if len(parts) > 1 and parts[1].isdigit():
                design = base_query.filter(
                    DesignImages.filename.ilike(f'%{parts[1]}%')
                ).first()

                if design:
                    logger.info(f"✅ Found in database (number match): {design.file_path}")
                    return design.file_path

            logger.warning(f"DB Search: No match found for '{normalized_search}' in template '{template_name}'")
            return None

        except Exception as e:
            logger.error(f"Error searching database for design: {e}")
            return None