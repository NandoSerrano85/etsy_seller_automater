# Back-compatibility module to export auth dependency functions.
# This makes old imports `server.src.auth.dependencies` work while
# keeping the implementation inside `server.src.routes.auth.service`.

from server.src.routes.auth import service as auth_service

get_current_user = auth_service.get_current_user
get_current_user_db = auth_service.get_current_user_db
get_current_shop_info = auth_service.get_current_shop_info
create_user_profile = auth_service.create_user_profile
get_user_by_token = auth_service.get_user_by_token
login_for_access_token = auth_service.login_for_access_token
refresh_access_token = auth_service.refresh_access_token

# Export TokenData and other types for callers if needed
TokenData = auth_service.TokenData
CurrentUser = auth_service.CurrentUser
CurrentShopInfo = auth_service.CurrentShopInfo

__all__ = [
    "get_current_user",
    "get_current_user_db",
    "get_current_shop_info",
    "create_user_profile",
    "get_user_by_token",
    "login_for_access_token",
    "refresh_access_token",
    "TokenData",
    "CurrentUser",
    "CurrentShopInfo",
]
