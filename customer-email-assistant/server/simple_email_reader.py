#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

class SimpleEmailReader:
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
    
    async def fetch_emails(self, limit: int = 50) -> List[Dict]:
        """Fetch emails - SIMPLE VERSION"""
        try:
            self.mail.select("inbox")
            result, data = self.mail.search(None, "ALL")
            email_ids = data[0].split()
            
            # Get most recent emails
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for eid in reversed(email_ids):  # Most recent first
                try:
                    email_data = self._get_email_simple(eid)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    print(f"Error processing email {eid}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            print(f'Error fetching emails: {e}')
            return []
    
    def _get_email_simple(self, email_id: bytes) -> Optional[Dict]:
        """Get email - SUPER SIMPLE VERSION"""
        try:
            # Fetch full email
            result, msg_data = self.mail.fetch(email_id, '(RFC822)')
            if not msg_data or not msg_data[0]:
                return None
                
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract basic info
            subject = self._decode_header(msg.get("Subject", ""))
            sender = self._decode_header(msg.get("From", ""))
            date_str = msg.get("Date", "")
            message_id = msg.get("Message-ID", email_id.decode())
            
            # Parse sender
            sender_email, sender_name = self._parse_sender(sender)
            
            # Extract body - SIMPLE WAY
            body_text = self._extract_text_simple(msg)
            
            # Parse date
            received_at = self._parse_date(date_str)
            
            return {
                'id': email_id.decode(),
                'gmail_id': message_id,
                'subject': subject or 'No Subject',
                'sender_email': sender_email,
                'sender_name': sender_name,
                'body': body_text,
                'text_content': body_text,  # Same as body for simplicity
                'received_at': received_at,
                'thread_id': message_id,
                'labels': ['INBOX']
            }
            
        except Exception as e:
            print(f'Error getting email: {e}')
            return None
    
    def _extract_text_simple(self, msg) -> str:
        """Extract text - DEAD SIMPLE"""
        text_parts = []
        
        try:
            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        text = self._decode_payload_simple(payload, part)
                        if text and len(text.strip()) > 0:
                            text_parts.append(text)
                            break  # Take first text/plain part only
            
            # If no text/plain, try HTML
            if not text_parts:
                for part in msg.walk():
                    content_type = part.get_content_type()
                    
                    if content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            text = self._decode_payload_simple(payload, part)
                            if text:
                                # Simple HTML to text conversion
                                text = self._html_to_text_simple(text)
                                if text and len(text.strip()) > 0:
                                    text_parts.append(text)
                                    break
            
            return '\n'.join(text_parts) if text_parts else "No content available"
            
        except Exception as e:
            print(f"Text extraction error: {e}")
            return "Content extraction failed"
    
    def _decode_payload_simple(self, payload: bytes, part) -> str:
        """Decode payload - SIMPLE"""
        try:
            charset = part.get_content_charset() or 'utf-8'
            
            # Try UTF-8 first (most common)
            try:
                return payload.decode('utf-8')
            except UnicodeDecodeError:
                pass
            
            # Try the specified charset
            try:
                return payload.decode(charset)
            except UnicodeDecodeError:
                pass
            
            # Try common Korean charsets
            for test_charset in ['euc-kr', 'cp949', 'iso-8859-1']:
                try:
                    return payload.decode(test_charset)
                except UnicodeDecodeError:
                    continue
            
            # Last resort
            return payload.decode('utf-8', errors='replace')
            
        except Exception as e:
            print(f"Payload decode error: {e}")
            return str(payload)[:500]
    
    def _html_to_text_simple(self, html: str) -> str:
        """HTML to text - SUPER SIMPLE with CSS removal"""
        try:
            import re
            
            # Remove CSS styles (between <style> tags or @media queries)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'@media[^{]*\{[^}]*\}', '', html, flags=re.DOTALL)
            html = re.sub(r'@[^{]*\{[^}]*\}', '', html, flags=re.DOTALL)
            
            # Remove script tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            
            # Remove CSS-like content that might be left
            text = re.sub(r'\{[^}]*\}', '', text)
            text = re.sub(r'@media[^;]*;', '', text)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # Limit length
            if len(text) > 1000:
                text = text[:1000] + "..."
            
            return text
            
        except Exception as e:
            print(f"HTML to text error: {e}")
            return html[:500]
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header - SIMPLE"""
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        decoded_string += part.decode(encoding or 'utf-8')
                    except:
                        decoded_string += part.decode('utf-8', errors='replace')
                else:
                    decoded_string += part
            
            return decoded_string
        except:
            return header_value
    
    def _parse_sender(self, sender: str) -> tuple:
        """Parse sender - SIMPLE"""
        if '<' in sender and '>' in sender:
            match = re.match(r'^(.*?)\s*<(.+?)>', sender)
            if match:
                name = match.group(1).strip().strip('"')
                email_addr = match.group(2).strip()
                return email_addr, name
        
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        if email_match:
            return email_match.group(), None
        
        return sender.strip(), None
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date - SIMPLE"""
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    def close(self):
        """Close connection"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass