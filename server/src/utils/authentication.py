# Back-compatibility module for older imports expecting
# `server.src.utils.authentication.get_current_user`.

from server.src.routes.auth import service as auth_service

# Provide convenient names expected by older imports
get_current_user = auth_service.get_current_user
get_current_user_db = auth_service.get_current_user_db
get_current_shop_info = auth_service.get_current_shop_info

__all__ = [
    "get_current_user",
    "get_current_user_db",
    "get_current_shop_info",
]
