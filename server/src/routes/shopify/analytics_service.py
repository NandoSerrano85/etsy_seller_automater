import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.utils.shopify_client import ShopifyClient, ShopifyAPIError, ShopifyAuthError
from src.entities.shopify_store import ShopifyStore
from src.entities.shopify_product import ShopifyProduct

logger = logging.getLogger(__name__)

class ShopifyAnalyticsService:
    """
    Service for analyzing Shopify order data and generating analytics insights.
    Provides order statistics, revenue trends, and product performance metrics.
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = ShopifyClient(db)

    def _handle_shopify_error(self, error: Exception, operation: str = "operation") -> None:
        """Convert Shopify errors to appropriate HTTP exceptions."""
        if isinstance(error, ShopifyAuthError):
            logger.error(f"Authentication failed during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Shopify authentication failed. Please reconnect your store."
            )
        else:
            logger.error(f"Shopify API error during {operation}: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shopify API error: {str(error)}"
            )

    def get_user_store(self, user_id: UUID) -> Optional[ShopifyStore]:
        """Get the connected Shopify store for a user."""
        return self.db.query(ShopifyStore).filter(
            ShopifyStore.user_id == user_id,
            ShopifyStore.is_active == True
        ).first()

    def get_order_stats(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """
        Get order statistics grouped by time period.

        Args:
            user_id: User UUID
            start_date: Start date for filtering (defaults to 30 days ago)
            end_date: End date for filtering (defaults to now)
            group_by: Grouping period ('day', 'week', 'month')

        Returns:
            Dictionary with order statistics and time series data
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found"
            )

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)

        try:
            # Fetch orders from Shopify
            orders = self.client.get_orders(
                store_id=str(store.id),
                since_time=start_date,
                limit=250,
                status="any"
            )

            # Process orders for analytics
            stats = self._process_order_stats(orders, start_date, end_date, group_by)

            return {
                "store_name": store.shop_name,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "group_by": group_by,
                "summary": stats["summary"],
                "time_series": stats["time_series"]
            }

        except Exception as e:
            self._handle_shopify_error(e, "fetching order statistics")

    def _process_order_stats(
        self,
        orders: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        group_by: str
    ) -> Dict[str, Any]:
        """Process raw orders into analytics statistics."""

        # Initialize time series data
        time_series = []
        summary_stats = {
            "total_orders": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "orders_growth": 0.0,
            "revenue_growth": 0.0
        }

        # Filter orders by date range
        filtered_orders = []
        for order in orders:
            try:
                order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
                if start_date <= order_date <= end_date:
                    filtered_orders.append(order)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping order with invalid date: {e}")
                continue

        if not filtered_orders:
            return {
                "summary": summary_stats,
                "time_series": []
            }

        # Group orders by time period
        grouped_data = defaultdict(lambda: {"orders": 0, "revenue": 0.0, "order_list": []})

        for order in filtered_orders:
            try:
                order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
                revenue = float(order.get("total_price", 0))

                # Generate grouping key based on period
                if group_by == "day":
                    key = order_date.strftime("%Y-%m-%d")
                elif group_by == "week":
                    # Get Monday of the week
                    monday = order_date - timedelta(days=order_date.weekday())
                    key = monday.strftime("%Y-%m-%d")
                elif group_by == "month":
                    key = order_date.strftime("%Y-%m")
                else:
                    key = order_date.strftime("%Y-%m-%d")

                grouped_data[key]["orders"] += 1
                grouped_data[key]["revenue"] += revenue
                grouped_data[key]["order_list"].append(order)

            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping order with invalid data: {e}")
                continue

        # Generate time series with all periods (including zeros)
        time_series = self._generate_complete_time_series(
            start_date, end_date, group_by, grouped_data
        )

        # Calculate summary statistics
        total_orders = len(filtered_orders)
        total_revenue = sum(float(order.get("total_price", 0)) for order in filtered_orders)

        summary_stats.update({
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(total_revenue / total_orders if total_orders > 0 else 0, 2),
            "orders_growth": self._calculate_growth(time_series, "orders"),
            "revenue_growth": self._calculate_growth(time_series, "revenue")
        })

        return {
            "summary": summary_stats,
            "time_series": time_series
        }

    def _generate_complete_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str,
        grouped_data: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate complete time series including periods with zero orders."""

        time_series = []
        current_date = start_date

        while current_date <= end_date:
            if group_by == "day":
                key = current_date.strftime("%Y-%m-%d")
                next_date = current_date + timedelta(days=1)
            elif group_by == "week":
                # Get Monday of the week
                monday = current_date - timedelta(days=current_date.weekday())
                key = monday.strftime("%Y-%m-%d")
                next_date = current_date + timedelta(weeks=1)
            elif group_by == "month":
                key = current_date.strftime("%Y-%m")
                # Move to next month
                if current_date.month == 12:
                    next_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    next_date = current_date.replace(month=current_date.month + 1)
            else:
                key = current_date.strftime("%Y-%m-%d")
                next_date = current_date + timedelta(days=1)

            data = grouped_data.get(key, {"orders": 0, "revenue": 0.0})

            time_series.append({
                "date": key,
                "orders": data["orders"],
                "revenue": round(data["revenue"], 2)
            })

            current_date = next_date

        return time_series

    def _calculate_growth(self, time_series: List[Dict[str, Any]], metric: str) -> float:
        """Calculate growth rate for a metric over the time series."""
        if len(time_series) < 2:
            return 0.0

        # Compare first half to second half of the period
        mid_point = len(time_series) // 2
        first_half = sum(point[metric] for point in time_series[:mid_point])
        second_half = sum(point[metric] for point in time_series[mid_point:])

        if first_half == 0:
            return 100.0 if second_half > 0 else 0.0

        growth = ((second_half - first_half) / first_half) * 100
        return round(growth, 2)

    def get_top_products(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get top-selling products ranked by sales volume and revenue.

        Args:
            user_id: User UUID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of products to return

        Returns:
            Dictionary with top products ranked by sales
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found"
            )

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)

        try:
            # Fetch orders from Shopify
            orders = self.client.get_orders(
                store_id=str(store.id),
                since_time=start_date,
                limit=250,
                status="any"
            )

            # Process orders to extract product sales data
            product_stats = self._process_product_sales(orders, start_date, end_date)

            # Get top products by sales volume
            top_by_quantity = sorted(
                product_stats.values(),
                key=lambda x: x["quantity_sold"],
                reverse=True
            )[:limit]

            # Get top products by revenue
            top_by_revenue = sorted(
                product_stats.values(),
                key=lambda x: x["total_revenue"],
                reverse=True
            )[:limit]

            return {
                "store_name": store.shop_name,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "top_by_quantity": top_by_quantity,
                "top_by_revenue": top_by_revenue,
                "total_products_sold": len(product_stats)
            }

        except Exception as e:
            self._handle_shopify_error(e, "fetching top products")

    def _process_product_sales(
        self,
        orders: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Process orders to extract product sales statistics."""

        product_stats = defaultdict(lambda: {
            "product_id": None,
            "title": "Unknown Product",
            "quantity_sold": 0,
            "total_revenue": 0.0,
            "average_price": 0.0,
            "orders_count": 0
        })

        for order in orders:
            try:
                # Check if order is in date range
                order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
                if not (start_date <= order_date <= end_date):
                    continue

                # Process line items in the order
                line_items = order.get("line_items", [])
                for item in line_items:
                    product_id = str(item.get("product_id", "unknown"))
                    if product_id == "unknown" or product_id == "None":
                        continue

                    title = item.get("title", "Unknown Product")
                    quantity = int(item.get("quantity", 0))
                    price = float(item.get("price", 0))
                    total_item_revenue = quantity * price

                    # Update product statistics
                    stats = product_stats[product_id]
                    stats["product_id"] = product_id
                    stats["title"] = title
                    stats["quantity_sold"] += quantity
                    stats["total_revenue"] += total_item_revenue
                    stats["orders_count"] += 1

            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping order with invalid data: {e}")
                continue

        # Calculate average prices
        for stats in product_stats.values():
            if stats["quantity_sold"] > 0:
                stats["average_price"] = round(
                    stats["total_revenue"] / stats["quantity_sold"], 2
                )
                stats["total_revenue"] = round(stats["total_revenue"], 2)

        return dict(product_stats)

    def get_order_analytics_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get a comprehensive analytics summary for the dashboard.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with summary analytics
        """
        store = self.get_user_store(user_id)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Shopify store found"
            )

        try:
            # Get statistics for different time periods
            end_date = datetime.now(timezone.utc)

            # Last 30 days
            stats_30d = self.get_order_stats(
                user_id,
                end_date - timedelta(days=30),
                end_date,
                "day"
            )

            # Last 7 days
            stats_7d = self.get_order_stats(
                user_id,
                end_date - timedelta(days=7),
                end_date,
                "day"
            )

            # Top products last 30 days
            top_products = self.get_top_products(
                user_id,
                end_date - timedelta(days=30),
                end_date,
                5
            )

            return {
                "store_name": store.shop_name,
                "last_30_days": stats_30d["summary"],
                "last_7_days": stats_7d["summary"],
                "top_products": top_products["top_by_revenue"][:5],
                "charts_data": {
                    "orders_trend": stats_30d["time_series"],
                    "revenue_trend": stats_30d["time_series"]
                }
            }

        except Exception as e:
            self._handle_shopify_error(e, "fetching analytics summary")