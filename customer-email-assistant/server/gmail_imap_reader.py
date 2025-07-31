import os
import imaplib
import email
import quopri
import base64
from datetime import datetime
from typing import List, Dict, Optional
from email.header import decode_header
from email.utils import parsedate_to_datetime
import re
from bs4 import BeautifulSoup

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
            
            # Extract body with improved Korean support
            body = self._extract_body_improved(msg)
            
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
    
    def _decode_body(self, body: str, encoding: str = None) -> str:
        """Decode quoted-printable or base64 encoded email body"""
        if encoding and encoding.lower() == "quoted-printable":
            try:
                # Handle both string and bytes input
                if isinstance(body, str):
                    body = body.encode('utf-8')
                decoded = quopri.decodestring(body)
                # Try different encodings for Korean text
                for charset in ['utf-8', 'euc-kr', 'cp949', 'iso-8859-1']:
                    try:
                        return decoded.decode(charset)
                    except UnicodeDecodeError:
                        continue
                return decoded.decode('utf-8', errors='replace')
            except Exception as e:
                print(f"Decoding error: {e}")
                return body
        elif encoding and encoding.lower() == "base64":
            try:
                import base64
                if isinstance(body, str):
                    body = body.encode('utf-8')
                decoded = base64.b64decode(body)
                # Try different encodings for Korean text
                for charset in ['utf-8', 'euc-kr', 'cp949', 'iso-8859-1']:
                    try:
                        return decoded.decode(charset)
                    except UnicodeDecodeError:
                        continue
                return decoded.decode('utf-8', errors='replace')
            except Exception as e:
                print(f"Base64 decoding error: {e}")
                return body
        return body

    def _extract_body(self, msg) -> str:
        """Extract email body from IMAP message, prefer HTML if available"""
        html_body = ""
        text_body = ""
        for part in msg.walk():
            content_type = part.get_content_type()
            encoding = part.get('Content-Transfer-Encoding')
            if part.get_content_maintype() == 'multipart':
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or 'utf-8'
            
            # Decode based on transfer encoding
            if encoding and encoding.lower() == "quoted-printable":
                try:
                    # First decode quoted-printable
                    decoded_bytes = quopri.decodestring(payload)
                    # Try different charsets for Korean text
                    for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949', 'iso-8859-1']:
                        try:
                            decoded = decoded_bytes.decode(test_charset)
                            # Remove soft line breaks (quoted-printable spec)
                            decoded = decoded.replace('=\r\n', '').replace('=\n', '')
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        decoded = decoded_bytes.decode(charset, errors='replace')
                        decoded = decoded.replace('=\r\n', '').replace('=\n', '')
                except Exception as e:
                    print(f"Quoted-printable decoding error: {e}")
                    decoded = payload.decode(charset, errors='replace')
            else:
                # Try different charsets for Korean text
                for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949', 'iso-8859-1']:
                    try:
                        decoded = payload.decode(test_charset)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    decoded = payload.decode(charset, errors='replace')
            
            if content_type == 'text/html':
                html_body = decoded
            elif content_type == 'text/plain':
                text_body = decoded
        
        # Prefer HTML body if available
        return html_body if html_body else text_body
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to clean plain text"""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up multiple spaces and newlines
            import re
            text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up multiple newlines
            
            # Limit length for preview
            if len(text) > 1000:
                text = text[:1000] + "..."
            
            return text.strip()
        except Exception as e:
            print(f"HTML to text conversion error: {e}")
            # Fallback: try to extract Korean text manually
            if any('\uac00' <= char <= '\ud7af' for char in html_content):
                import re
                korean_text = re.findall(r'[\uac00-\ud7af\s\w₩,.-]+', html_content)
                if korean_text:
                    return ' '.join(korean_text[:10])  # First 10 Korean text segments
            return html_content[:200] + "..." if len(html_content) > 200 else html_content
    
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
        """Fast email processing with improved Korean support"""
        try:
            # Fetch full email for better Korean decoding
            result, msg_data = self.mail.fetch(email_id, '(RFC822)')
            if not msg_data or not msg_data[0]:
                return None
                
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract basic info quickly
            subject = self._decode_header(msg.get("Subject", ""))[:200]  # Limit length
            sender = self._decode_header(msg.get("From", ""))
            date_str = msg.get("Date", "")
            message_id = msg.get("Message-ID", email_id.decode())
            
            # Parse sender quickly
            sender_email, sender_name = self._parse_sender(sender)
            
            # Extract body with improved Korean support
            body = self._extract_body_improved(msg)
            
            # Parse date quickly
            received_at = self._parse_date(date_str)
            
            return {
                'id': email_id.decode(),
                'gmail_id': message_id,
                'subject': subject or 'No Subject',
                'sender_email': sender_email,
                'sender_name': sender_name,
                'body': body[:2000],  # Increased limit for Korean content
                'text_content': self._html_to_text(body)[:1000],
                'received_at': received_at,
                'thread_id': message_id,
                'labels': ['INBOX']
            }
            
        except Exception as e:
            print(f'Error getting email details fast: {e}')
            return None
    
    def _extract_body_improved(self, msg) -> str:
        """Improved body extraction with better Korean quoted-printable support"""
        html_body = ""
        text_body = ""
        
        try:
            for part in msg.walk():
                content_type = part.get_content_type()
                encoding = part.get('Content-Transfer-Encoding', '').lower()
                
                if part.get_content_maintype() == 'multipart':
                    continue
                
                # Get raw payload without decoding first
                raw_payload = part.get_payload()
                if not raw_payload:
                    continue
                
                charset = part.get_content_charset() or 'utf-8'
                decoded_text = ""
                
                # Handle quoted-printable encoding specifically
                if encoding == "quoted-printable":
                    try:
                        # If payload is string, it's already the quoted-printable text
                        if isinstance(raw_payload, str):
                            # Remove soft line breaks first
                            cleaned_payload = raw_payload.replace('=\r\n', '').replace('=\n', '')
                            # Decode quoted-printable
                            decoded_bytes = quopri.decodestring(cleaned_payload.encode('utf-8'))
                            # Try different charsets
                            for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                try:
                                    decoded_text = decoded_bytes.decode(test_charset)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                decoded_text = decoded_bytes.decode('utf-8', errors='replace')
                        else:
                            # If payload is bytes, decode normally
                            payload = part.get_payload(decode=True)
                            if payload:
                                for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                    try:
                                        decoded_text = payload.decode(test_charset)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                else:
                                    decoded_text = payload.decode('utf-8', errors='replace')
                    except Exception as e:
                        print(f"Quoted-printable decoding error: {e}")
                        # Fallback to regular decoding
                        payload = part.get_payload(decode=True)
                        if payload:
                            decoded_text = payload.decode('utf-8', errors='replace')
                
                # Handle base64 encoding
                elif encoding == "base64":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                try:
                                    decoded_text = payload.decode(test_charset)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                decoded_text = payload.decode('utf-8', errors='replace')
                    except Exception as e:
                        print(f"Base64 decoding error: {e}")
                        decoded_text = str(raw_payload)
                
                # Handle regular encoding or no encoding
                else:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                try:
                                    decoded_text = payload.decode(test_charset)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                decoded_text = payload.decode('utf-8', errors='replace')
                        else:
                            decoded_text = str(raw_payload)
                    except Exception as e:
                        print(f"Regular decoding error: {e}")
                        decoded_text = str(raw_payload)
                
                # Store based on content type
                if content_type == 'text/html':
                    html_body = decoded_text
                elif content_type == 'text/plain':
                    text_body = decoded_text
            
            # Return HTML if available, otherwise text
            return html_body if html_body else text_body
            
        except Exception as e:
            print(f"Body extraction error: {e}")
            return "Email content extraction failed"

    def _extract_body_fast(self, msg) -> str:
        """Fast body extraction with Korean support"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type in ["text/plain", "text/html"]:
                        payload = part.get_payload(decode=True)
                        if payload:
                            encoding = part.get('Content-Transfer-Encoding')
                            charset = part.get_content_charset() or 'utf-8'
                            
                            # Handle quoted-printable encoding
                            if encoding and encoding.lower() == "quoted-printable":
                                try:
                                    decoded_bytes = quopri.decodestring(payload)
                                    # Try different charsets for Korean text
                                    for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                        try:
                                            decoded = decoded_bytes.decode(test_charset)
                                            # Remove soft line breaks
                                            decoded = decoded.replace('=\r\n', '').replace('=\n', '')
                                            return decoded[:1000]
                                        except UnicodeDecodeError:
                                            continue
                                except:
                                    pass
                            
                            # Regular decoding with charset fallback
                            for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                try:
                                    return payload.decode(test_charset)[:1000]
                                except UnicodeDecodeError:
                                    continue
                            
                            # Fallback
                            return payload.decode('utf-8', errors='ignore')[:1000]
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    encoding = msg.get('Content-Transfer-Encoding')
                    charset = msg.get_content_charset() or 'utf-8'
                    
                    # Handle quoted-printable encoding
                    if encoding and encoding.lower() == "quoted-printable":
                        try:
                            decoded_bytes = quopri.decodestring(payload)
                            for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                                try:
                                    decoded = decoded_bytes.decode(test_charset)
                                    decoded = decoded.replace('=\r\n', '').replace('=\n', '')
                                    return decoded[:1000]
                                except UnicodeDecodeError:
                                    continue
                        except:
                            pass
                    
                    # Regular decoding
                    for test_charset in [charset, 'utf-8', 'euc-kr', 'cp949']:
                        try:
                            return payload.decode(test_charset)[:1000]
                        except UnicodeDecodeError:
                            continue
                    
                    return payload.decode('utf-8', errors='ignore')[:1000]
        except Exception as e:
            print(f"Fast body extraction error: {e}")
        
        return "Email content not available"