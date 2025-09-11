import os, hashlib, base64, secrets, random, string, requests, logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta, timezone
from . import model
from server.src.entities.third_party_oauth import ThirdPartyOAuthToken
from server.src.message import ERROR_MESSAGES, SUCCESS_MESSAGES

# Get the project root directory (2 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

ETSY_API_CONFIG = {
    'base_url': 'https://openapi.etsy.com/v3',
    'ping_url': 'https://api.etsy.com/v3/application/openapi-ping',
    'token_url': 'https://api.etsy.com/v3/public/oauth/token',
    'oauth_connect_url': 'https://www.etsy.com/oauth/connect',
    'scopes': 'listings_w listings_r shops_r shops_w transactions_r',
    'code_challenge_method': 'S256',
    'response_type': 'code',
}

DEFAULTS = {
    'token_expiry_buffer': 60,  # seconds before expiry to refresh
    'default_expires_in': 3600,  # 1 hour in seconds
    'state_length': 7,
    'code_verifier_length': 32,
} 

# Load or generate necessary environment variables
clientID = os.getenv('CLIENT_ID')
clientSecret = os.getenv('CLIENT_SECRET')

if not clientID:
    raise ValueError("CLIENT_ID environment variable is required but not set")
if not clientSecret:
    raise ValueError("CLIENT_SECRET environment variable is required but not set")

# Generate a secure code verifier and code challenge
def generate_code_verifier_code_challenge_and_state():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(DEFAULTS['code_verifier_length'])).decode('utf-8').replace('=', '')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').replace('=', '')
    state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=DEFAULTS['state_length']))
    return code_verifier, code_challenge, state

clientVerifier, codeChallenge, state = generate_code_verifier_code_challenge_and_state()

def get_redirect_uri():
    """Get the correct redirect URI for OAuth flow."""
    # Temporarily use the working legacy redirect URI until Etsy app is updated
    # return "http://localhost:3003/oauth/redirect"
    # TODO: Change back to frontend redirect URI after updating Etsy app
    return "http://localhost:3000/oauth/redirect"

def get_redirect_uri_legacy():
    """Get legacy redirect URI for testing."""
    # Fallback to backend redirect URI if frontend is not configured
    return "http://localhost:3003/oauth/redirect"

# Export OAuth variables and functions for use in routes
def get_oauth_variables():
    """Get OAuth variables for use in routes."""
    return {
        'clientID': clientID,
        'clientSecret': clientSecret,
        'state': state,
        'redirectUri': get_redirect_uri(),
        'clientVerifier': clientVerifier,
        'codeChallenge': codeChallenge,
        'dotenv_path': dotenv_path
    }

def get_oauth_data() -> model.ThirdPartyOauthDataResponse:
    oauth_vars = get_oauth_variables()
    return model.ThirdPartyOauthDataResponse(
        clientId=oauth_vars['clientID'],
        redirectUri=oauth_vars['redirectUri'],
        codeChallenge=oauth_vars['codeChallenge'],
        state=oauth_vars['state'],
        scopes=ETSY_API_CONFIG['scopes'],
        codeChallengeMethod=ETSY_API_CONFIG['code_challenge_method'],
        responseType=ETSY_API_CONFIG['response_type'],
        oauthConnectUrl=ETSY_API_CONFIG['oauth_connect_url']
    )

def oauth_redirect(code:str, user_id: UUID, db: Session) -> model.ThirdPartyOauthResponse:
    oauth_vars = get_oauth_variables()
    logging.info(f"Starting OAuth redirect for user {user_id}")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        # Check if token already exists
        logging.info(f"Checking for existing OAuth token for user {user_id}")
        third_party_oauth_token = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id
        ).first()
        
        logging.info(f"Existing token found: {third_party_oauth_token is not None}")
        
        # Prepare payload based on whether we're refreshing or getting new token
        if third_party_oauth_token and third_party_oauth_token.refresh_token:
            logging.info("Using refresh token flow")
            payload = {
                'grant_type': 'refresh_token',
                'client_id': oauth_vars['clientID'],
                'client_secret': oauth_vars['clientSecret'],
                'refresh_token': third_party_oauth_token.refresh_token
            }
        else:
            logging.info("Using new token flow")
            payload = {
                'grant_type': 'authorization_code',
                'client_id': oauth_vars['clientID'],
                'redirect_uri': oauth_vars['redirectUri'],
                'code': code,
                'code_verifier': oauth_vars['clientVerifier'],
            }
        
        logging.info(f"Making token request with payload: {payload}")
        response = requests.post(ETSY_API_CONFIG['token_url'], data=payload, headers=headers)
        logging.info(f"Token response status: {response.status_code}")
        
        if response.ok:
            token_data = response.json()
            logging.info("Successfully received token data")
            
            # Create or update token record
            if not third_party_oauth_token:
                logging.info("Creating new OAuth token record")
                third_party_oauth_token = ThirdPartyOAuthToken(
                    user_id=user_id,
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    expires_at=datetime.now(timezone.utc) + timedelta(seconds=token_data.get('expires_in', DEFAULTS['default_expires_in']))
                )
                db.add(third_party_oauth_token)
            else:
                logging.info("Updating existing OAuth token record")
                third_party_oauth_token.access_token = token_data['access_token']
                third_party_oauth_token.refresh_token = token_data.get('refresh_token')
                third_party_oauth_token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get('expires_in', DEFAULTS['default_expires_in']))
            
            try:
                db.commit()
                logging.info("Successfully saved OAuth token to database")
            except Exception as e:
                logging.error(f"Database error while saving token: {str(e)}")
                db.rollback()
                raise
                
            return model.ThirdPartyOauthResponse(
                status_code=200,
                success=True,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_in=token_data.get('expires_in', DEFAULTS['default_expires_in']),
                message=SUCCESS_MESSAGES['oauth_success']
            )
        else:
            logging.error(f"Token request failed: {response.text}")
            return model.ThirdPartyOauthResponse(
                status_code=response.status_code,
                success=False,
                access_token="",
                refresh_token="",
                expires_in=0,
                message=f"Token exchange failed: {response.text}"
            )
            
    except Exception as e:
        logging.error(f"Error in oauth_redirect: {str(e)}")
        return model.ThirdPartyOauthResponse(
            status_code=500,
            success=False,
            access_token="",
            refresh_token="",
            expires_in=0,
            message=f"Internal error: {str(e)}"
        )

def oauth_redirect_legacy(code:str):
    oauth_vars = get_oauth_variables()
    
    authCode = code
    payload = {
        'grant_type': 'authorization_code',
        'client_id': oauth_vars['clientID'],
        'redirect_uri': oauth_vars['redirectUri'],
        'code': authCode,
        'code_verifier': oauth_vars['clientVerifier'],
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(ETSY_API_CONFIG['token_url'], data=payload, headers=headers)
    if response.ok:
        tokenData = response.json()
        access_token = tokenData['access_token']
        refresh_token = tokenData.get('refresh_token')
        expires_in = tokenData.get('expires_in', DEFAULTS['default_expires_in'])
        
        # Return JSON response with token data for frontend
        return model.ThirdPartyOauthResponse(
            status_code=200,
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            message=SUCCESS_MESSAGES['oauth_success']
        )
    else:
        print(f"Token exchange failed: {response.status_code} {response.text}")
        return model.ThirdPartyOauthResponse(
            status_code=404,
            success=False,
            access_token="",
            refresh_token="",
            expires_in=int(datetime.now(timezone.utc).timestamp()),
            message=ERROR_MESSAGES['token_exchange_failed']
        )
def oauth_callback(code: str, state: str) -> model.ThirdPartyOauthResponse:
    oauth_vars = get_oauth_variables()
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
    payload = {
        'grant_type': 'authorization_code',
        'client_id': oauth_vars['clientID'],
        'redirect_uri': oauth_vars['redirectUri'],
        'code': code,
        'code_verifier': oauth_vars['clientVerifier'],
    }

    response = requests.post(ETSY_API_CONFIG['token_url'], data=payload, headers=headers)
    
    if response.ok:
        tokenData = response.json()
        access_token = tokenData['access_token']
        refresh_token = tokenData.get('refresh_token')
        expires_in = tokenData.get('expires_in', DEFAULTS['default_expires_in'])
        
        return model.ThirdPartyOauthResponse(
            status_code=200,
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            message=SUCCESS_MESSAGES['oauth_success']
        )
    else:
        logging.warning(f"Token exchange failed: {response.status_code} {response.text}")
        return model.ThirdPartyOauthResponse(
            status_code=404,
            success=False,
            access_token="",
            refresh_token="",
            expires_in=int(datetime.now(timezone.utc).timestamp()),
            message=ERROR_MESSAGES['token_exchange_failed']
        )

def verify_etsy_connection(user_id: UUID, db: Session) -> dict:
    """Verify if the current Etsy connection is valid"""
    try:
        logging.info(f"🔍 Verifying Etsy connection for user {user_id}")
        
        oauth_record = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id
        ).first()
        
        logging.info(f"📊 OAuth record found: {oauth_record is not None}")
        if oauth_record:
            logging.info(f"🔑 Has access token: {oauth_record.access_token is not None}")
            logging.info(f"⏰ Token expires at: {oauth_record.expires_at}")
        
        if not oauth_record or not oauth_record.access_token:
            logging.warning(f"❌ No OAuth record or access token for user {user_id}")
            return {
                "connected": False,
                "message": "No Etsy connection found"
            }
        
        # Check if token is expired
        if oauth_record.expires_at and oauth_record.expires_at < datetime.now(timezone.utc):
            logging.warning(f"⏰ Token expired for user {user_id} - expired at {oauth_record.expires_at}, current time: {datetime.now(timezone.utc)}")
            return {
                "connected": False,
                "message": "Access token expired"
            }
        
        # Make a test request to Etsy API to verify token validity
        oauth_vars = get_oauth_variables()
        headers = {
            "Authorization": f"Bearer {oauth_record.access_token}",
            "x-api-key": oauth_vars['clientID']
        }
        
        logging.info(f"🌐 Making test request to Etsy API for user {user_id}")
        
        # Test endpoint - get user info
        test_response = requests.get(
            "https://openapi.etsy.com/v3/application/users/me",
            headers=headers
        )
        
        logging.info(f"📡 Etsy API response status: {test_response.status_code}")
        
        if test_response.status_code == 200:
            user_data = test_response.json()
            
            # Also get shop info if available
            shop_info = None
            try:
                shops_response = requests.get(
                    "https://openapi.etsy.com/v3/application/users/me/shops",
                    headers=headers
                )
                if shops_response.status_code == 200:
                    shops_data = shops_response.json()
                    if shops_data.get("results") and len(shops_data["results"]) > 0:
                        shop_info = shops_data["results"][0]
            except Exception as e:
                logging.warning(f"Failed to get shop info: {str(e)}")
            
            logging.info(f"✅ User {user_id} successfully connected to Etsy")
            return {
                "connected": True,
                "user_info": user_data,
                "shop_info": shop_info,
                "expires_at": int(oauth_record.expires_at.timestamp() * 1000) if oauth_record.expires_at else None
            }
        else:
            logging.warning(f"❌ Token validation failed for user {user_id} - Etsy API returned {test_response.status_code}")
            return {
                "connected": False,
                "message": f"Token validation failed (HTTP {test_response.status_code})"
            }
            
    except Exception as e:
        logging.error(f"Connection verification error: {str(e)}")
        return {
            "connected": False,
            "message": "Connection verification failed"
        }



def revoke_etsy_token(user_id: UUID, db: Session) -> dict:
    """Revoke Etsy access token and remove connection"""
    try:
        oauth_record = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id
        ).first()
        
        if not oauth_record:
            return {"success": True, "message": "No connection found to revoke"}
        
        # Try to revoke token on Etsy's end (if they support it)
        # Note: Etsy doesn't have a token revocation endpoint as of 2024
        # So we just remove it from our database
        
        # Remove the OAuth record
        db.delete(oauth_record)
        db.commit()
        
        return {"success": True, "message": "Connection revoked successfully"}
        
    except Exception as e:
        logging.error(f"Token revocation error: {str(e)}")
        return {"success": False, "error": str(e)}

