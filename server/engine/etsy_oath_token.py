import os, hashlib, base64, secrets, random, string, time, subprocess, json
from dotenv import load_dotenv
from server.constants import DEFAULTS

# Get the project root directory (2 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../state.json')
load_dotenv(dotenv_path)

# Helper functions for state.json

def read_state():
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    return {}

def write_state(data):
    with open(state_path, 'w') as f:
        json.dump(data, f)

# Load or generate necessary environment variables
clientID = os.getenv('CLIENT_ID')

# Generate a secure code verifier and code challenge
def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(DEFAULTS['code_verifier_length'])).decode('utf-8').replace('=', '')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').replace('=', '')
    return code_verifier, code_challenge

def generate_and_store_state(state_data):
    state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=DEFAULTS['state_length']))
    state_data['STATE_ID'] = state
    write_state(state_data)
    return state

# Load or initialize state.json
def ensure_state():
    state_data = read_state()
    changed = False
    if 'CLIENT_VERIFIER' not in state_data or 'CODE_CHALLENGE' not in state_data:
        verifier, challenge = generate_code_verifier_and_challenge()
        state_data['CLIENT_VERIFIER'] = verifier
        state_data['CODE_CHALLENGE'] = challenge
        changed = True
    if 'STATE_ID' not in state_data:
        state_data['STATE_ID'] = generate_and_store_state(state_data)
        changed = True
    if changed:
        write_state(state_data)
    return state_data

state_data = ensure_state()
clientVerifier = state_data['CLIENT_VERIFIER']
codeChallenge = state_data['CODE_CHALLENGE']
state = state_data['STATE_ID']

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

def run_upload_script():
    """Function to run a script specified in the .env file."""
    script_name = os.getenv('RETURN_TO_PROCESSES', 'ProcessUploadListings.py')  # Default to 'ProcessUploadListings.py' if not set
    script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), script_name)
    try:
        # Execute the specified script using Python
        subprocess.run(['python', script_path], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"Failed to run the script '{script_name}'. Please ensure that the script exists. "
            "To resolve this issue, please add or update the 'RETURN_TO_PROCESSES' variable "
            "in the .env file with the correct file name of the script to be run after authentication completes."
        )

# Export OAuth variables and functions for use in routes
def get_oauth_variables():
    """Get OAuth variables for use in routes."""
    return {
        'clientID': clientID,
        'redirectUri': get_redirect_uri(),
        'clientVerifier': clientVerifier,
        'codeChallenge': codeChallenge,
        'state': state,
        'dotenv_path': dotenv_path
    }

def store_oauth_tokens(access_token, refresh_token=None, expires_in=None):
    """Store OAuth tokens in state.json."""
    if expires_in is None:
        expires_in = DEFAULTS['default_expires_in']
    
    expiry_time = time.time() + expires_in
    state_data = read_state()
    state_data['ETSY_OAUTH_TOKEN'] = access_token
    if refresh_token:
        state_data['ETSY_REFRESH_TOKEN'] = refresh_token
    state_data['ETSY_OAUTH_TOKEN_EXPIRY'] = expiry_time
    write_state(state_data)

    