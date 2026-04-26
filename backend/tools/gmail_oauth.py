"""
Google OAuth 2.0 Authentication Module for Gmail API
Handles the full OAuth flow: authorization, token exchange, refresh, and Gmail API access
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

logger = logging.getLogger("gmail_oauth")

# OAuth 2.0 Configuration
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback")

# Scopes for Gmail API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

# Token storage path
BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_DIR = BASE_DIR / "data" / "tokens"
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Ensure token directory exists
TOKEN_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials_file():
    """Create credentials.json from environment variables if it doesn't exist"""
    if not CREDENTIALS_FILE.exists():
        credentials_config = {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        }
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials_config, f, indent=2)
        logger.info(f"Created credentials.json at {CREDENTIALS_FILE}")
        return True
    return False


def get_stored_credentials() -> Optional[Credentials]:
    """Load stored credentials from token.json if they exist and are valid"""
    if not TOKEN_FILE.exists():
        logger.info("No stored credentials found")
        return None
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        # Check if credentials are expired and need refresh
        if creds.expired and creds.refresh_token:
            logger.info("Credentials expired, attempting refresh...")
            creds.refresh(Request())
            # Save refreshed credentials
            save_credentials(creds)
            logger.info("Credentials refreshed successfully")
        
        if creds.valid:
            logger.info("Valid credentials loaded from storage")
            return creds
        else:
            logger.warning("Stored credentials are invalid")
            return None
            
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return None


def save_credentials(creds: Credentials):
    """Save credentials to token.json"""
    try:
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        logger.info(f"Credentials saved to {TOKEN_FILE}")
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")


def get_authorization_url() -> str:
    """Generate the OAuth authorization URL for user consent"""
    save_credentials_file()
    
    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state for verification during callback
        state_file = TOKEN_DIR / "oauth_state.json"
        with open(state_file, 'w') as f:
            json.dump({'state': state}, f)
        
        logger.info("Authorization URL generated")
        return authorization_url
        
    except Exception as e:
        logger.error(f"Error generating authorization URL: {e}")
        raise


def handle_oauth_callback(authorization_response: str, state: str) -> Credentials:
    """
    Handle the OAuth callback after user grants permission
    authorization_response: The full callback URL from Google
    state: The state parameter to verify
    """
    try:
        # Verify state matches
        state_file = TOKEN_DIR / "oauth_state.json"
        if state_file.exists():
            with open(state_file, 'r') as f:
                stored_state = json.load(f).get('state')
            
            if state != stored_state:
                raise ValueError("State mismatch - possible CSRF attack")
        
        save_credentials_file()
        
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state=state
        )
        
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        
        # Save the credentials
        save_credentials(creds)
        
        logger.info("OAuth flow completed successfully")
        return creds
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise


def get_gmail_service(creds: Credentials):
    """Build and return Gmail API service"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service initialized")
        return service
    except Exception as e:
        logger.error(f"Error building Gmail service: {e}")
        raise


def create_message_with_attachment(
    sender: str,
    to: str,
    subject: str,
    body_text: str,
    pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a MIME message with optional PDF attachment"""
    try:
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        
        # Add body
        message.attach(MIMEText(body_text, 'plain'))
        
        # Add PDF attachment if provided
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(pdf_path)
            )
            message.attach(pdf_attachment)
            logger.info(f"Attached PDF: {pdf_path}")
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
        
    except Exception as e:
        logger.error(f"Error creating email message: {e}")
        raise


def send_email_via_gmail_api(
    creds: Credentials,
    sender: str,
    to: str,
    subject: str,
    body_text: str,
    pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """Send email using Gmail API with OAuth credentials"""
    try:
        service = get_gmail_service(creds)
        message = create_message_with_attachment(sender, to, subject, body_text, pdf_path)
        
        # Send the email
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        logger.info(f"Email sent successfully to {to}. Message ID: {sent_message['id']}")
        return {
            'status': 'success',
            'message_id': sent_message['id'],
            'thread_id': sent_message.get('threadId')
        }
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise
    except Exception as e:
        logger.error(f"Error sending email via Gmail API: {e}")
        raise


def get_user_profile(creds: Credentials) -> Dict[str, Any]:
    """Get the authenticated user's profile information"""
    try:
        service = get_gmail_service(creds)
        profile = service.users().getProfile(userId='me').execute()
        
        return {
            'email': profile.get('emailAddress'),
            'history_id': profile.get('historyId'),
            'messages_total': profile.get('messagesTotal'),
            'threads_total': profile.get('threadsTotal')
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise


def refresh_credentials_if_needed() -> Optional[Credentials]:
    """Check and refresh credentials if needed, return valid credentials or None"""
    creds = get_stored_credentials()
    
    if creds and creds.valid:
        return creds
    
    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
            save_credentials(creds)
            return creds
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            return None
    
    return None


def revoke_credentials(creds: Credentials) -> bool:
    """Revoke OAuth credentials (logout)"""
    try:
        import requests
        revoke_url = f"https://oauth2.googleapis.com/revoke"
        params = {'token': creds.token}
        response = requests.post(revoke_url, params=params)
        
        if response.status_code == 200:
            # Delete local token file
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            logger.info("Credentials revoked successfully")
            return True
        else:
            logger.error(f"Failed to revoke credentials: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error revoking credentials: {e}")
        return False


def create_draft_via_oauth(
    to: str,
    subject: str,
    body_text: str,
    pdf_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a draft using OAuth credentials"""
    try:
        creds = refresh_credentials_if_needed()
        if not creds:
            logger.warning("No valid credentials for draft creation")
            return {'status': 'unauthorized'}
        
        service = get_gmail_service(creds)
        
        # Get sender from profile
        profile = get_user_profile(creds)
        sender = f"Kuvera Pulse AI Engine <{profile['email']}>"
        
        message = create_message_with_attachment(sender, to, subject, body_text, pdf_path)
        
        draft = service.users().drafts().create(
            userId='me',
            body={'message': message}
        ).execute()
        
        logger.info(f"Draft created successfully: {draft['id']}")
        return {
            'status': 'success',
            'draft_id': draft['id']
        }
    except Exception as e:
        logger.error(f"Error creating draft via OAuth: {e}")
        return {'status': 'error', 'message': str(e)}


if __name__ == "__main__":
    # Test the OAuth flow
    logging.basicConfig(level=logging.INFO)
    
    print("=== Google OAuth 2.0 Flow Test ===\n")
    
    # Step 1: Check for existing credentials
    creds = get_stored_credentials()
    
    if creds and creds.valid:
        print("✓ Valid credentials found!")
        profile = get_user_profile(creds)
        print(f"✓ Authenticated as: {profile['email']}")
    else:
        print("No valid credentials found.")
        print("\nStep 1: Visit this URL to authorize:")
        auth_url = get_authorization_url()
        print(auth_url)
        print("\nStep 2: After authorization, you'll be redirected to the callback URL")
        print("Step 3: The callback handler will exchange the code for tokens")
