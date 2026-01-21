"""Ecommerce routes package."""

from .products import router as products_router
from .cart import router as cart_router
from .customers import router as customers_router
from .checkout import router as checkout_router
from .orders import router as orders_router
from .storefront_settings import router as storefront_settings_router
from .storefront_domain import router as storefront_domain_router
from .storefront_public import router as storefront_public_router

__all__ = [
    "products_router",
    "cart_router",
    "customers_router",
    "checkout_router",
    "orders_router",
    "storefront_settings_router",
    "storefront_domain_router",
    "storefront_public_router",
]
