import os
import base64
import email
from datetime import datetime
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from bs4 import BeautifulSoup

class GmailReader:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
              'https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Gmail API service"""
        try:
            # Load credentials from environment or file
            creds = None
            
            # Check if we have stored credentials
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Use environment variables for OAuth flow
                    client_config = {
                        "installed": {
                            "client_id": os.getenv("GMAIL_CLIENT_ID"),
                            "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            print(f"Error initializing Gmail service: {e}")
            raise
    
    async def fetch_emails(self, limit: int = 50, query: str = "is:unread") -> List[Dict]:
        """Fetch emails from Gmail"""
        try:
            # Search for emails
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = await self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    async def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get detailed information about a specific email"""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            
            # Extract header information
            subject = self._get_header_value(headers, 'Subject')
            sender = self._get_header_value(headers, 'From')
            date = self._get_header_value(headers, 'Date')
            
            # Parse sender email and name
            sender_email, sender_name = self._parse_sender(sender)
            
            # Extract email body
            body = self._extract_body(message['payload'])
            
            # Convert date to ISO format
            received_at = self._parse_date(date)
            
            return {
                'id': message_id,
                'gmail_id': message_id,
                'subject': subject or 'No Subject',
                'sender_email': sender_email,
                'sender_name': sender_name,
                'body': body,
                'text_content': self._html_to_text(body),
                'received_at': received_at,
                'thread_id': message.get('threadId'),
                'labels': message.get('labelIds', [])
            }
            
        except HttpError as error:
            print(f'An error occurred fetching email {message_id}: {error}')
            return None
    
    def _get_header_value(self, headers: List[Dict], name: str) -> str:
        """Extract header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ''
    
    def _parse_sender(self, sender: str) -> tuple:
        """Parse sender string to extract email and name"""
        if '<' in sender and '>' in sender:
            # Format: "Name <email@domain.com>"
            name = sender.split('<')[0].strip().strip('"')
            email_addr = sender.split('<')[1].split('>')[0].strip()
            return email_addr, name
        else:
            # Format: "email@domain.com"
            return sender.strip(), None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['body'].get('data'):
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
        
        return body
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text"""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(strip=True)
        except:
            return html_content
    
    def _parse_date(self, date_str: str) -> str:
        """Parse email date to ISO format"""
        try:
            # Parse various date formats
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    async def send_reply(self, original_email_id: str, reply_content: str, 
                        to_email: str, subject: str) -> bool:
        """Send a reply to an email"""
        try:
            # Create the reply message
            message = self._create_reply_message(
                to_email, subject, reply_content, original_email_id
            )
            
            # Send the message
            result = self.service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            return bool(result.get('id'))
            
        except HttpError as error:
            print(f'An error occurred sending reply: {error}')
            return False
    
    def _create_reply_message(self, to_email: str, subject: str, 
                             content: str, thread_id: str) -> Dict:
        """Create a reply message"""
        import email.mime.text
        import email.mime.multipart
        
        message = email.mime.multipart.MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        
        # Add the reply content
        msg = email.mime.text.MIMEText(content, 'plain')
        message.attach(msg)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')
        
        return {
            'raw': raw_message,
            'threadId': thread_id
        }
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            print(f'An error occurred marking email as read: {error}')
            return False