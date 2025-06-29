from dotenv import load_dotenv, set_key
import os, hashlib, base64, secrets, random, string, time, subprocess

# Import constants
from server.constants import DEFAULTS

# Get the project root directory (2 levels up from this file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

# Load or generate necessary environment variables
clientID = os.getenv('CLIENT_ID')
redirectUri = os.getenv('REDIRECT_URI')

# Generate a secure code verifier and code challenge
def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(DEFAULTS['code_verifier_length'])).decode('utf-8').replace('=', '')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').replace('=', '')
    return code_verifier, code_challenge

def generate_and_store_state():
    state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=DEFAULTS['state_length']))
    set_key(dotenv_path, 'STATE_ID', state)
    return state

# Check if code_challenge and client_verifier exist, if not create them
clientVerifier = os.getenv('CLIENT_VERIFIER')
codeChallenge = os.getenv('CODE_CHALLENGE')

if not clientVerifier or not codeChallenge:
    clientVerifier, codeChallenge = generate_code_verifier_and_challenge()
    set_key(dotenv_path, "CLIENT_VERIFIER", clientVerifier)
    set_key(dotenv_path, "CODE_CHALLENGE", codeChallenge)
    
state = generate_and_store_state()

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
        'redirectUri': redirectUri,
        'clientVerifier': clientVerifier,
        'codeChallenge': codeChallenge,
        'state': state,
        'dotenv_path': dotenv_path
    }

def store_oauth_tokens(access_token, refresh_token=None, expires_in=None):
    """Store OAuth tokens in the .env file."""
    if expires_in is None:
        expires_in = DEFAULTS['default_expires_in']
    
    expiry_time = time.time() + expires_in
    set_key(dotenv_path, "ETSY_OAUTH_TOKEN", access_token)
    if refresh_token:
        set_key(dotenv_path, "ETSY_REFRESH_TOKEN", refresh_token)
    set_key(dotenv_path, "ETSY_OAUTH_TOKEN_EXPIRY", str(expiry_time))

    