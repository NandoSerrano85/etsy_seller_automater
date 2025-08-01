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
    logging.info(oauth_vars)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        third_party_oauth_token = db.query(ThirdPartyOAuthToken).filter(ThirdPartyOAuthToken.user_id == user_id).one()
    except:
        third_party_oauth_token = None
    
    # if third_party_oauth_token:
    #     payload = {
    #         'grant_type': 'refresh_token',
    #         'client_id': oauth_vars['clientID'],
    #         'client_secret': oauth_vars['clientSecret'],
    #         'refresh_token': third_party_oauth_token.refresh_token
    #     }
        
    # else:
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
        expires_at = tokenData.get('expires_in', DEFAULTS['default_expires_in'])
        

        third_party_oauth_token = ThirdPartyOAuthToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc.utc) + timedelta(seconds=expires_at)
        )
        db.merge(third_party_oauth_token)
        db.commit()
        db.refresh(third_party_oauth_token)
        
        # Return JSON response with token data for frontend
        return model.ThirdPartyOauthResponse(
            status_code=200,
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_at,
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