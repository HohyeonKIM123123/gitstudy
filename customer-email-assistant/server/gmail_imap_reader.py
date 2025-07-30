import os
import imaplib
import email
import base64
from datetime import datetime
from typing import List, Dict, Optional
from email.header import decode_header
from email.utils import parsedate_to_datetime
import re

class GmailIMAPReader:
    def __init__(self):
        self.mail = None
        self.email_address = os.getenv("GMAIL_EMAIL")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")
        self._connect()
    
    def _connect(self):
        """Connect to Gmail via IMAP"""
        try:
            if not self.email_address or not self.app_password:
                raise Exception("Gmail email and app password must be set in environment variables")
            
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(self.email_address, self.app_password)
            print(f"Connected to Gmail IMAP for {self.email_address}")
            
        except Exception as e:
            print(f"Error connecting to Gmail IMAP: {e}")
            raise
    
    async def fetch_emails(self, limit: int = 50, query: str = "UNSEEN") -> List[Dict]:
        """Fetch emails from Gmail via IMAP - OPTIMIZED"""
        try:
            # Select inbox
            self.mail.select("inbox")
            
            # Search for emails
            result, data = self.mail.search(None, query)
            email_ids = data[0].split()
            
            # Limit results and get most recent
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            # Process emails in batches for speed
            emails = []
            batch_size = 10
            
            for i in range(0, len(email_ids), batch_size):
                batch = email_ids[i:i + batch_size]
                
                # Process batch concurrently (simulate async)
                batch_emails = []
                for eid in reversed(batch):  # Most recent first
                    try:
                        email_data = self._get_email_details_fast(eid)
                        if email_data:
                            batch_emails.append(email_data)
                    except Exception as e:
                        print(f"Error processing email {eid}: {e}")
                        continue
                
                emails.extend(batch_emails)
                print(f"Processed batch {i//batch_size + 1}, total emails: {len(emails)}")
            
            return emails
            
        except Exception as e:
            print(f'Error fetching emails: {e}')
            return []
    
    async def _get_email_details(self, email_id: bytes) -> Optional[Dict]:
        """Get detailed information about a specific email"""
        try:
            # Fetch email
            result, msg_data = self.mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract basic info
            subject = self._decode_header(msg.get("Subject", ""))
            sender = self._decode_header(msg.get("From", ""))
            date_str = msg.get("Date", "")
            message_id = msg.get("Message-ID", "")
            
            # Parse sender
            sender_email, sender_name = self._parse_sender(sender)
            
            # Extract body
            body = self._extract_body(msg)
            
            # Parse date
            received_at = self._parse_date(date_str)
            
            return {
                'id': email_id.decode(),
                'gmail_id': message_id,
                'subject': subject or 'No Subject',
                'sender_email': sender_email,
                'sender_name': sender_name,
                'body': body,
                'text_content': self._html_to_text(body),
                'received_at': received_at,
                'thread_id': message_id,  # Using message ID as thread ID
                'labels': ['INBOX']
            }
            
        except Exception as e:
            print(f'Error getting email details: {e}')
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header"""
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or 'utf-8')
                else:
                    decoded_string += part
            
            return decoded_string
        except:
            return header_value
    
    def _parse_sender(self, sender: str) -> tuple:
        """Parse sender string to extract email and name"""
        if '<' in sender and '>' in sender:
            # Format: "Name <email@domain.com>"
            match = re.match(r'^(.*?)\s*<(.+?)>$', sender)
            if match:
                name = match.group(1).strip().strip('"')
                email_addr = match.group(2).strip()
                return email_addr, name
        
        # Format: "email@domain.com" or fallback
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        if email_match:
            return email_match.group(), None
        
        return sender.strip(), None
    
    def _extract_body(self, msg) -> str:
        """Extract email body from message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8')
            except:
                body = str(msg.get_payload())
        
        return body
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text"""
        if not html_content:
            return ""
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(strip=True)
        except:
            # Simple HTML tag removal if BeautifulSoup fails
            import re
            clean = re.compile('<.*?>')
            return re.sub(clean, '', html_content)
    
    def _parse_date(self, date_str: str) -> str:
        """Parse email date to ISO format"""
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    async def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read"""
        try:
            self.mail.store(email_id, '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            print(f'Error marking email as read: {e}')
            return False
    
    def close(self):
        """Close IMAP connection"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass
    
    def _get_email_details_fast(self, email_id: bytes) -> Optional[Dict]:
        """Fast email processing - only essential data"""
        try:
            # Fetch only headers first for speed
            result, msg_data = self.mail.fetch(email_id, '(BODY.PEEK[HEADER])')
            if not msg_data or not msg_data[0]:
                return None
                
            header_data = msg_data[0][1]
            msg = email.message_from_bytes(header_data)
            
            # Extract basic info quickly
            subject = self._decode_header(msg.get("Subject", ""))[:200]  # Limit length
            sender = self._decode_header(msg.get("From", ""))
            date_str = msg.get("Date", "")
            message_id = msg.get("Message-ID", email_id.decode())
            
            # Parse sender quickly
            sender_email, sender_name = self._parse_sender(sender)
            
            # Get body only if needed (fetch minimal)
            try:
                result, body_data = self.mail.fetch(email_id, '(BODY.PEEK[TEXT])')
                if body_data and body_data[0] and body_data[0][1]:
                    body_msg = email.message_from_bytes(body_data[0][1])
                    body = self._extract_body_fast(body_msg)
                else:
                    body = "Email body not available"
            except:
                body = "Email body not available"
            
            # Parse date quickly
            received_at = self._parse_date(date_str)
            
            return {
                'id': email_id.decode(),
                'gmail_id': message_id,
                'subject': subject or 'No Subject',
                'sender_email': sender_email,
                'sender_name': sender_name,
                'body': body[:1000],  # Limit body length for speed
                'text_content': body[:500],  # Even shorter for text
                'received_at': received_at,
                'thread_id': message_id,
                'labels': ['INBOX']
            }
            
        except Exception as e:
            print(f'Error getting email details fast: {e}')
            return None
    
    def _extract_body_fast(self, msg) -> str:
        """Fast body extraction - simplified"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode('utf-8', errors='ignore')[:1000]
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')[:1000]
        except:
            pass
        
        return "Email content not available"