from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

class GeneralError(HTTPException):
    """Base exception for general-related errors"""
    pass

class InvalidUserToken(GeneralError):
    def __init__(self):
        super().__init__(status_code=401, detail="User ID cameback none. Invalid user token.")

class AuthError(HTTPException):
    """Base exception for auth-related errors"""
    pass

class AuthVerifyTokenError(AuthError):
    def __init__(self, token: str):
        super().__init__(status_code=401, detail=f"Could not properly decode token: {token}.")

class AuthUserNotFound(AuthError):
    def __init__(self):
        super().__init__(status_code=401, detail=f"Was not able to fetch auth from user.")

class UserError(HTTPException):
    """Base exception for user-related errors"""
    pass

class UserNotFoundError(UserError):
    def __init__(self, user_id=None):
        super().__init__(status_code=404, detail="User not found" if not user_id else f"User with ID: {user_id} could not be found.")

class InvalidPasswordError(UserError):
    def __init__(self, user_id=None):
        super().__init__(status_code=401, detail="Current password is incorrect.")

class PasswordLengthInvalidError(UserError):
    def __init__(self, user_id=None):
        super().__init__(status_code=400, detail="Password length is 6 characters or less")

class PasswordMismatchError(UserError):
    def __init__(self):
        super().__init__(status_code=400, detail="Password did match records.")

class UserChangePasswordError(UserError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not change password")

class ProductTemplateError(HTTPException):
    """Base exception for user-related errors"""
    pass

class EtsyProductTemplateAlreadyExists(ProductTemplateError):
    def __init__(self, product_template_id=None):
        super().__init__(status_code=400, detail=f"Product template with ID: {product_template_id} already exists.")

class EtsyProductTemplateCreateError(ProductTemplateError):
    def __init__(self):
        super().__init__(status_code=500, detail="Was not able to create new product template")

class EtsyProductTemplateGetAllError(ProductTemplateError):
    def __init__(self):
        super().__init__(status_code=500, detail=f"Was not able to get list of product templates.")

class EtsyProductTemplateNotFound(ProductTemplateError):
    def __init__(self, product_template_id=None):
        super().__init__(status_code=404, detail="Product template not found" if not product_template_id else f"Product template with ID: {product_template_id} could not be found.")

class EtsyProductTemplateGetByIdError(ProductTemplateError):
    def __init__(self, product_template_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch product template with ID: {product_template_id}.")

class EtsyProductTemplateUpdateError(ProductTemplateError):
    def __init__(self, product_template_id=None):
        super().__init__(status_code=500, detail=f"Could not update product template with ID: {product_template_id}.")
    
class EtsyProductTemplateDeleteError(ProductTemplateError):
    def __init__(self, product_template_id=None):
        super().__init__(status_code=500, detail=f"Could not delete product template with ID: {product_template_id}.")

class CanvasConfigError(HTTPException):
    """Base exception for user-related errors"""
    pass

class CanvasConfigAlreadyExists(CanvasConfigError):
    def __init__(self, canvas_config_id=None):
        super().__init__(status_code=400, detail=f"Canvas config with ID: {canvas_config_id} already exists.")

class CanvasConfigCreateError(CanvasConfigError):
    def __init__(self):
        super().__init__(status_code=500, detail="Was not able to create new canvas config.")

class CanvasConfigGetAllError(CanvasConfigError):
    def __init__(self):
        super().__init__(status_code=500, detail=f"Was not able to get list of canvas config")

class CanvasConfigNotFound(CanvasConfigError):
    def __init__(self, canvas_config_id=None):
        super().__init__(status_code=404, detail="Canvas config not found" if not canvas_config_id else f"Canvas config with ID: {canvas_config_id} could not be found.")

class CanvasConfigGetByIdError(CanvasConfigError):
    def __init__(self, canvas_config_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch canvas config with ID: {canvas_config_id}.")

class CanvasConfigUpdateError(CanvasConfigError):
    def __init__(self, canvas_config_id=None):
        super().__init__(status_code=500, detail=f"Could not update canvas config with ID: {canvas_config_id}.")
    
class CanvasConfigDeleteError(CanvasConfigError):
    def __init__(self, canvas_config_id=None):
        super().__init__(status_code=500, detail=f"Could not delete canvas config with ID: {canvas_config_id}.")

class SizeConfigError(HTTPException):
    """Base exception for user-related errors"""
    pass

class SizeConfigAlreadyExists(CanvasConfigError):
    def __init__(self, size_config_id=None):
        super().__init__(status_code=400, detail=f"Size config with ID: {size_config_id} already exists.")

class SizeConfigCreateError(CanvasConfigError):
    def __init__(self):
        super().__init__(status_code=500, detail="Was not able to create new size config.")

class SizeConfigGetAllError(CanvasConfigError):
    def __init__(self):
        super().__init__(status_code=500, detail=f"Was not able to get list of size config")

class SizeConfigNotFound(CanvasConfigError):
    def __init__(self, size_config_id=None):
        super().__init__(status_code=404, detail="Size config not found" if not size_config_id else f"Size config with ID: {size_config_id} could not be found.")

class SizeConfigGetByIdError(CanvasConfigError):
    def __init__(self, size_config_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch size config with ID: {size_config_id}.")

class SizeConfigUpdateError(CanvasConfigError):
    def __init__(self, size_config_id=None):
        super().__init__(status_code=500, detail=f"Could not update size config with ID: {size_config_id}.")
    
class SizeConfigDeleteError(CanvasConfigError):
    def __init__(self, size_config_id=None):
        super().__init__(status_code=500, detail=f"Could not delete size config with ID: {size_config_id}.")

class DesignError(HTTPException):
    """Base exception for design-related errors"""
    pass

class DesignNotFoundError(DesignError):
    def __init__(self, design_id=None):
        super().__init__(status_code=404, detail="Design not found" if not design_id else f"Design with ID: {design_id} could not be found.")

class DesignCreateError(DesignError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not create new design.")

class DesignGetAllError(DesignError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not get list of designs.")

class DesignGetByIdError(DesignError):
    def __init__(self, design_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch design with ID: {design_id}.")

class DesignUpdateError(DesignError):
    def __init__(self, design_id=None):
        super().__init__(status_code=500, detail=f"Could not update design with ID: {design_id}.")
    
class DesignDeleteError(DesignError):
    def __init__(self, design_id=None):
        super().__init__(status_code=500, detail=f"Could not delete design with ID: {design_id}.")

class MockupError(HTTPException):
    """Base exception for mockup-related errors"""
    pass

class MockupNotFoundError(MockupError):
    def __init__(self, mockup_id=None):
        super().__init__(status_code=404, detail="Mockup not found" if not mockup_id else f"Mockup with ID: {mockup_id} could not be found.")

class MockupCreateError(MockupError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not create new mockup.")

class MockupGetAllError(MockupError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not get list of mockups.")

class MockupGetByIdError(MockupError):
    def __init__(self, mockup_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch mockup with ID: {mockup_id}.")

class MockupUpdateError(MockupError):
    def __init__(self, mockup_id=None):
        super().__init__(status_code=500, detail=f"Could not update mockup with ID: {mockup_id}.")
    
class MockupDeleteError(MockupError):
    def __init__(self, mockup_id=None):
        super().__init__(status_code=500, detail=f"Could not delete mockup with ID: {mockup_id}.")

class MockupImageError(HTTPException):
    """Base exception for mockup image-related errors"""
    pass

class MockupImageNotFoundError(MockupImageError):
    def __init__(self, image_id=None):
        super().__init__(status_code=404, detail="Mockup image not found" if not image_id else f"Mockup image with ID: {image_id} could not be found.")

class MockupImageCreateError(MockupImageError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not create new mockup image.")

class MockupImageGetAllError(MockupImageError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not get list of mockup images.")

class MockupImageGetByIdError(MockupImageError):
    def __init__(self, image_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch mockup image with ID: {image_id}.")

class MockupImageUpdateError(MockupImageError):
    def __init__(self, image_id=None):
        super().__init__(status_code=500, detail=f"Could not update mockup image with ID: {image_id}.")
    
class MockupImageDeleteError(MockupImageError):
    def __init__(self, image_id=None):
        super().__init__(status_code=500, detail=f"Could not delete mockup image with ID: {image_id}.")

class MockupMaskDataError(HTTPException):
    """Base exception for mockup mask data-related errors"""
    pass

class MockupMaskDataNotFoundError(MockupMaskDataError):
    def __init__(self, mask_data_id=None):
        super().__init__(status_code=404, detail="Mockup mask data not found" if not mask_data_id else f"Mockup mask data with ID: {mask_data_id} could not be found.")

class MockupMaskDataCreateError(MockupMaskDataError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not create new mockup mask data.")

class MockupMaskDataGetAllError(MockupMaskDataError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not get list of mockup mask data.")

class MockupMaskDataGetByIdError(MockupMaskDataError):
    def __init__(self, mask_data_id=None):
        super().__init__(status_code=500, detail=f"Could not fetch mockup mask data with ID: {mask_data_id}.")

class MockupMaskDataUpdateError(MockupMaskDataError):
    def __init__(self, mask_data_id=None):
        super().__init__(status_code=500, detail=f"Could not update mockup mask data with ID: {mask_data_id}.")
    
class MockupMaskDataDeleteError(MockupMaskDataError):
    def __init__(self, mask_data_id=None):
        super().__init__(status_code=500, detail=f"Could not delete mockup mask data with ID: {mask_data_id}.")

class ThirdPartyListingError(HTTPException):
    """Base exception for third party listing-related errors"""
    pass

class ThirdPartyListingNotFoundError(ThirdPartyListingError):
    def __init__(self, listing_id: int):
        super().__init__(status_code=404, detail=f"Third party listing with ID: {listing_id} could not be found.")

class ThirdPartyListingUpdateError(ThirdPartyListingError):
    def __init__(self, listing_id: int, error_message: str = ""):
        super().__init__(status_code=500, detail=f"Could not update third party listing {listing_id}: {error_message}")

class ThirdPartyListingCreateError(ThirdPartyListingError):
    def __init__(self, error_message: str = ""):
        super().__init__(status_code=500, detail=f"Could not create third party listing: {error_message}")

class ThirdPartyListingGetAllError(ThirdPartyListingError):
    def __init__(self):
        super().__init__(status_code=500, detail="Could not retrieve third party listings.")

class ThirdPartyListingGetByIdError(ThirdPartyListingError):
    def __init__(self, listing_id: int):
        super().__init__(status_code=500, detail=f"Could not retrieve third party listing with ID: {listing_id}.")

class ThirdPartyListingDeleteError(ThirdPartyListingError):
    def __init__(self, listing_id: int):
        super().__init__(status_code=500, detail=f"Could not delete third party listing with ID: {listing_id}.")

# Error Messages
ERROR_MESSAGES = {
    'oauth_failed': 'OAuth authentication failed',
    'token_exchange_failed': 'Token exchange failed',
    'user_data_failed': 'Failed to fetch user data',
    'frontend_not_built': 'React frontend not built. Run "python build_frontend.py" to build the frontend.',
    'invalid_access_token': 'Invalid or missing access token',
}

# Success Messages
SUCCESS_MESSAGES = {
    'oauth_success': 'Authentication successful',
    'token_refreshed': 'Access token refreshed successfully',
    'user_data_loaded': 'User data loaded successfully',
}

def _redact_sensitive_fields(body_str: str) -> str:
    """Redact sensitive fields like passwords from log output."""
    import re
    # Redact password values in JSON-like strings
    # Matches "password": "value" or 'password': 'value' patterns
    redacted = re.sub(
        r'(["\']password["\'])\s*:\s*["\'][^"\']*["\']',
        r'\1: "[REDACTED]"',
        body_str,
        flags=re.IGNORECASE
    )
    # Also handle current_password, new_password variants
    redacted = re.sub(
        r'(["\'](?:current_|new_)?password["\'])\s*:\s*["\'][^"\']*["\']',
        r'\1: "[REDACTED]"',
        redacted,
        flags=re.IGNORECASE
    )
    return redacted


def log_and_return_422(request: Request, exc: RequestValidationError):
    logging.error(f"422 Validation Error: {exc.errors()}")

    # Handle body serialization safely
    body_info = "Unable to serialize body"
    try:
        if exc.body:
            # Try to decode as string first
            if isinstance(exc.body, bytes):
                body_info = exc.body.decode('utf-8', errors='ignore')[:500]  # Limit size
            else:
                body_info = str(exc.body)[:500]  # Limit size
            # Redact sensitive fields before logging
            body_info = _redact_sensitive_fields(body_info)
    except Exception:
        body_info = f"Body type: {type(exc.body).__name__}"

    logging.error(f"Request body info: {body_info}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body_info": body_info,
        },
    )

def register_error_handlers(app):
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(RequestValidationError, log_and_return_422)