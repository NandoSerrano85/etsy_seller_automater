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