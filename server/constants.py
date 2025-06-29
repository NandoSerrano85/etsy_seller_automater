"""
Constants and configuration data for the Etsy Seller Automaker application.
This file contains templates, default values, and other static configuration.
"""

# Etsy Listing Templates
ETSY_TEMPLATES = {
    'UVDTF 16oz': {
        'title': '| UVDTF Cup wrap | Ready to apply | High Quality | Double Sided | Easy application | Cup Transfer | Waterproof',
        'description': """*** Details ***
 - This listing is for a physical single 16 oz UV DTF cup wrap transfer. Cup, straw, lid are NOT included.
 - UV DTF cup wraps are an approximate measurement of 9.5" wide and 4.3" tall, perfect for 16 oz glass & acrylic cans.
 - UV DTF products are permanent & waterproof.

 *** Note ***
 - Not all 16 oz glass & acrylic cans are the same dimensions, please make sure to check your measurements before purchase.
 - All orders are printed in house on commercial UV DTF printers with high quality materials.
 - Printed colors and design resolution may appear slightly different from your phone, tablet or computer screen/monitor.

*** Care Instructions ***
- All UV DTF transfers are not dishwasher or microwave safe. Hand wash only.

*** Policy ***
 - Seller is not responsible for any application errors or any errors that may occur during placement of UV DTF transfer.
 - Seller is not responsible for any wear and tear of UV DTF transfer.
 - Seller is not responsible for any improper storage of transfer.
 - Seller is not responsible for care of UV DTF transfer after applied to the surface.
 - All claims require photos and/or videos to be considered for reprint or refund at seller's discretion.
 - All orders have a 48 hour window after receiving your order to make us aware of any issues such as missing or damaged transfers.
 - All orders go through multiple stages of quality and accuracy checks before packing and shipping of orders to ensure the highest quality service.

*** Shipping Policy ***
 - Seller is not responsible for lost, late arriving, stolen or damaged packages caused by USPS, UPS, FedEx or other carrier your order is shipped with. Buyer will need to file a claim with the carrier in the event packages do not arrive, are misdelivered, lost, stolen, damaged, etc. Once a package has a scan acceptance by the carrier, the seller is no longer responsible for the order. Please purchase shipping insurance whenever possible to ensure your order can be reshipped in these cases.

*** Thank You ***
Thank you so much! Your purchase truly means the world to me & my family and it helps my small business grow! Please make sure to explore our other UV DTF and DTF transfer options from wraps to decals and shirt transfers for all sizes.
""",
        'who_made': 'i_did',
        'when_made': 'made_to_order',
        'taxonomy_id': 1,
        'price': 4.00,
        'materials': ['UV DTF'],
        'shop_section_id': 2,
        'quantity': 100,
        'tags': ['UV DTF', 'Cup Wrap', 'Waterproof', 'Permanent', 'Transfer', 'Prints', 'Wholesale', 'Mug', '16oz', '17oz'],
        'item_weight': 2.5,
        'item_weight_unit': 'oz',
        'item_length': 11,
        'item_width': 9.5,
        'item_height': 1,
        'item_dimensions_unit': 'in',
        'is_taxable': True,
        'type': 'physical',
        'processing_min': 1,
        'processing_max': 3,
    },
}

# OAuth Configuration
OAUTH_CONFIG = {
    'scopes': 'listings_w listings_r shops_r shops_w transactions_r',
    'code_challenge_method': 'S256',
    'response_type': 'code',
}

# API Configuration
API_CONFIG = {
    'base_url': 'https://openapi.etsy.com/v3',
    'ping_url': 'https://api.etsy.com/v3/application/openapi-ping',
    'token_url': 'https://api.etsy.com/v3/public/oauth/token',
    'oauth_connect_url': 'https://www.etsy.com/oauth/connect',
}

# Server Configuration
SERVER_CONFIG = {
    'default_host': '127.0.0.1',
    'default_port': 3003,
    'default_debug': False,
}

# File Paths
PATHS = {
    'frontend_build': 'frontend/build',
    'frontend_static': 'frontend/build/static',
    'frontend_index': 'frontend/build/index.html',
}

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

# Default Values
DEFAULTS = {
    'token_expiry_buffer': 60,  # seconds before expiry to refresh
    'default_expires_in': 3600,  # 1 hour in seconds
    'state_length': 7,
    'code_verifier_length': 32,
} 