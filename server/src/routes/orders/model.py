from typing import List, Optional
from pydantic import BaseModel

class OrderItem(BaseModel):
    title: str
    quantity: int
    price: float
    listing_id: Optional[int]

class Order(BaseModel):
    order_id: int
    order_date: int
    shipping_method: str
    shipping_cost: float
    customer_name: str
    items: List[OrderItem]

class OrdersResponse(BaseModel):
    orders: List[Order]
    count: int
    total: int
