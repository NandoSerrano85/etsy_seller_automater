# """
# Additional endpoints for token refresh and validation
# """
# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy.orm import Session
# import requests
# import logging
# from datetime import datetime, timedelta

# from ...database.core import get_db
# from ...entities.third_party_oauth import ThirdPartyOAuth
# from ...entities.user import User

# logger = logging.getLogger(__name__)
# router = APIRouter()

# @router.post("/refresh-token")
# async def refresh_access_token(
#     refresh_data: dict,
#     db: Session = Depends(get_db)
# ):
#     """
#     Refresh Etsy access token using refresh token
#     """
#     try:
#         refresh_token = refresh_data.get("refresh_token")
#         if not refresh_token:
#             raise HTTPException(status_code=400, detail="Refresh token is required")
        
#         # Find the OAuth record
#         oauth_record = db.query(ThirdPartyOAuth).filter(
#             ThirdPartyOAuth.refresh_token == refresh_token,
#             ThirdPartyOAuth.provider == "etsy"
#         ).first()
        
#         if not oauth_record:
#             raise HTTPException(status_code=404, detail="Refresh token not found")
        
#         # Check if refresh token is still valid (not expired)
#         if oauth_record.refresh_expires_at and oauth_record.refresh_expires_at < datetime.utcnow():
#             raise HTTPException(status_code=401, detail="Refresh token expired")
        
#         # Make request to Etsy token endpoint
#         token_url = "https://api.etsy.com/v3/public/oauth/token"
        
#         # Get client credentials from environment or config
#         import os
#         client_id = os.getenv("ETSY_CLIENT_ID")
#         client_secret = os.getenv("ETSY_CLIENT_SECRET")
        
#         if not client_id or not client_secret:
#             raise HTTPException(status_code=500, detail="OAuth client credentials not configured")
        
#         token_data = {
#             "grant_type": "refresh_token",
#             "refresh_token": refresh_token,
#             "client_id": client_id,
#         }
        
#         headers = {
#             "Content-Type": "application/x-www-form-urlencoded"
#         }
        
#         response = requests.post(token_url, data=token_data, headers=headers, auth=(client_id, client_secret))
        
#         if response.status_code != 200:
#             logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
#             raise HTTPException(status_code=400, detail="Failed to refresh token")
        
#         token_response = response.json()
        
#         # Update the OAuth record with new tokens
#         oauth_record.access_token = token_response.get("access_token")
#         oauth_record.token_expires_at = datetime.utcnow() + timedelta(seconds=token_response.get("expires_in", 3600))
        
#         # Update refresh token if provided
#         if "refresh_token" in token_response:
#             oauth_record.refresh_token = token_response["refresh_token"]
        
#         db.commit()
        
#         return {
#             "access_token": oauth_record.access_token,
#             "refresh_token": oauth_record.refresh_token,
#             "expires_in": token_response.get("expires_in", 3600),
#             "token_type": token_response.get("token_type", "Bearer"),
#             "expires_at": int(oauth_record.token_expires_at.timestamp() * 1000)  # Convert to milliseconds
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Token refresh error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error during token refresh")


# @router.get("/verify-connection")
# async def verify_etsy_connection(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Verify if the current Etsy connection is valid
#     """
#     try:
#         oauth_record = db.query(ThirdPartyOAuth).filter(
#             ThirdPartyOAuth.user_id == current_user.id,
#             ThirdPartyOAuth.provider == "etsy"
#         ).first()
        
#         if not oauth_record or not oauth_record.access_token:
#             return {
#                 "connected": False,
#                 "message": "No Etsy connection found"
#             }
        
#         # Check if token is expired
#         if oauth_record.token_expires_at and oauth_record.token_expires_at < datetime.utcnow():
#             return {
#                 "connected": False,
#                 "message": "Access token expired"
#             }
        
#         # Make a test request to Etsy API to verify token validity
#         headers = {
#             "Authorization": f"Bearer {oauth_record.access_token}",
#             "x-api-key": os.getenv("ETSY_CLIENT_ID")
#         }
        
#         # Test endpoint - get user info
#         test_response = requests.get(
#             "https://openapi.etsy.com/v3/application/users/me",
#             headers=headers
#         )
        
#         if test_response.status_code == 200:
#             user_data = test_response.json()
            
#             # Also get shop info if available
#             shop_info = None
#             try:
#                 shops_response = requests.get(
#                     "https://openapi.etsy.com/v3/application/users/me/shops",
#                     headers=headers
#                 )
#                 if shops_response.status_code == 200:
#                     shops_data = shops_response.json()
#                     if shops_data.get("results") and len(shops_data["results"]) > 0:
#                         shop_info = shops_data["results"][0]
#             except Exception as e:
#                 logger.warning(f"Failed to get shop info: {str(e)}")
            
#             return {
#                 "connected": True,
#                 "user_info": user_data,
#                 "shop_info": shop_info,
#                 "expires_at": int(oauth_record.token_expires_at.timestamp() * 1000) if oauth_record.token_expires_at else None
#             }
#         else:
#             return {
#                 "connected": False,
#                 "message": "Token validation failed"
#             }
            
#     except Exception as e:
#         logger.error(f"Connection verification error: {str(e)}")
#         return {
#             "connected": False,
#             "message": "Connection verification failed"
#         }


# @router.post("/revoke-token")
# async def revoke_etsy_token(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Revoke Etsy access token and remove connection
#     """
#     try:
#         oauth_record = db.query(ThirdPartyOAuth).filter(
#             ThirdPartyOAuth.user_id == current_user.id,
#             ThirdPartyOAuth.provider == "etsy"
#         ).first()
        
#         if not oauth_record:
#             return {"success": True, "message": "No connection found to revoke"}
        
#         # Try to revoke token on Etsy's end (if they support it)
#         # Note: Etsy doesn't have a token revocation endpoint as of 2024
#         # So we just remove it from our database
        
#         # Remove the OAuth record
#         db.delete(oauth_record)
#         db.commit()
        
#         return {"success": True, "message": "Connection revoked successfully"}
        
#     except Exception as e:
#         logger.error(f"Token revocation error: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to revoke token")


# # You'll need to import this function from your auth module
# def get_current_user():
#     """
#     Dependency to get current authenticated user
#     This should be implemented based on your auth system
#     """
#     pass  # Implement based on your existing auth system