#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from dotenv import load_dotenv
from db import Database
from gmail_imap_reader import GmailIMAPReader
from classifier import EmailClassifier

# Load environment variables
load_dotenv('../.env')

async def fix_database():
    """Fix database by removing corrupted emails and re-syncing"""
    
    try:
        # Initialize services
        db = Database()
        await db.connect()
        
        gmail_reader = GmailIMAPReader()
        email_classifier = EmailClassifier()
        
        print("🔧 Fixing database with proper Korean decoding...")
        
        # 1. Find and remove corrupted Skyscanner emails
        print("\n1️⃣ Removing corrupted emails...")
        
        # Get all emails
        all_emails = await db.get_emails(limit=100)
        corrupted_count = 0
        
        for email in all_emails:
            # Check if email body contains quoted-printable encoding
            body = email.get('body', '')
            if ('=EA=' in body or '=EB=' in body or '=EC=' in body or '=ED=' in body) and 'Content-Transfer-Encoding: quoted-printable' in body:
                print(f"   Removing corrupted email: {email.get('subject', 'No subject')[:50]}...")
                # Remove from database
                await db.delete_email(email['id'])
                corrupted_count += 1
        
        print(f"   Removed {corrupted_count} corrupted emails")
        
        # 2. Re-sync emails with proper decoding
        print(f"\n2️⃣ Re-syncing emails with proper Korean decoding...")
        
        # Fetch fresh emails from Gmail
        new_emails = await gmail_reader.fetch_emails(limit=20, query="ALL")
        
        processed_count = 0
        for email_data in new_emails:
            # Check if email already exists (by gmail_id)
            existing = await db.get_email_by_gmail_id(email_data['gmail_id'])
            if not existing:
                # Quick classification
                classification = email_classifier.quick_classify(
                    email_data['body'], 
                    email_data['subject']
                )
                
                # Store email with classification
                email_data.update({
                    'priority': classification['priority'],
                    'tags': classification['tags'],
                    'status': 'unread'
                })
                
                await db.store_email(email_data)
                processed_count += 1
                
                print(f"   Stored: {email_data['subject'][:50]}...")
                
                # Show Korean content for verification
                if any('\uac00' <= char <= '\ud7af' for char in email_data.get('text_content', '')):
                    print(f"     Korean content: {email_data['text_content'][:100]}...")
        
        print(f"\n✅ Database fix completed!")
        print(f"   Removed: {corrupted_count} corrupted emails")
        print(f"   Added: {processed_count} properly decoded emails")
        
        # 3. Verify fix
        print(f"\n3️⃣ Verifying fix...")
        skyscanner_emails = []
        all_emails = await db.get_emails(limit=50)
        
        for email in all_emails:
            if 'skyscanner' in email.get('sender_email', '').lower():
                skyscanner_emails.append(email)
        
        if skyscanner_emails:
            for email in skyscanner_emails:
                print(f"   ✅ Skyscanner email: {email['subject']}")
                print(f"      Body preview: {email['body'][:100]}...")
                print(f"      Text content: {email.get('text_content', '')[:100]}...")
                
                # Check if properly decoded
                if any('\uac00' <= char <= '\ud7af' for char in email.get('text_content', '')):
                    print(f"      🇰🇷 Korean text properly decoded!")
                else:
                    print(f"      ⚠️  Korean text still not decoded")
        else:
            print(f"   No Skyscanner emails found")
        
        await db.disconnect()
        gmail_reader.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_database())