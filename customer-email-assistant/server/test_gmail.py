import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
load_dotenv('../.env')
load_dotenv('../../.env')

def test_gmail_connection():
    try:
        refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
        client_id = os.getenv("GMAIL_CLIENT_ID")
        client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        
        print(f"Client ID: {client_id[:20]}...")
        print(f"Client Secret: {client_secret[:10]}...")
        print(f"Refresh Token: {refresh_token[:20]}...")
        
        # Create credentials
        creds_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "type": "authorized_user"
        }
        
        creds = Credentials.from_authorized_user_info(creds_info)
        print("Credentials created successfully")
        
        # Try to refresh
        creds.refresh(Request())
        print("Token refreshed successfully!")
        
        # Test Gmail API
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"Gmail connection successful! Email: {profile.get('emailAddress')}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_gmail_connection()