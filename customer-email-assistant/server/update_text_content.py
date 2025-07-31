#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from dotenv import load_dotenv
from db import Database
from gmail_imap_reader import GmailIMAPReader

# Load environment variables
load_dotenv('../.env')

async def update_text_content():
    """Update text_content for existing emails with better HTML to text conversion"""
    
    try:
        # Initialize services
        db = Database()
        await db.connect()
        
        gmail_reader = GmailIMAPReader()
        
        print("🔄 Updating text_content for existing emails...")
        
        # Get all emails
        all_emails = await db.get_emails(limit=100)
        updated_count = 0
        
        for email in all_emails:
            body = email.get('body', '')
            current_text_content = email.get('text_content', '')
            
            # Check if text_content needs updating (contains HTML tags or is same as body)
            if ('<' in current_text_content and '>' in current_text_content) or current_text_content == body:
                # Convert HTML body to clean text
                new_text_content = gmail_reader._html_to_text(body)
                
                if new_text_content != current_text_content:
                    # Update the email
                    await db.update_email(email['id'], {'text_content': new_text_content})
                    updated_count += 1
                    
                    print(f"   Updated: {email.get('subject', 'No subject')[:50]}...")
                    print(f"     Old text: {current_text_content[:100]}...")
                    print(f"     New text: {new_text_content[:100]}...")
                    print()
        
        print(f"\n✅ Text content update completed!")
        print(f"   Updated: {updated_count} emails")
        
        # Verify updates
        print(f"\n3️⃣ Verifying updates...")
        skyscanner_emails = []
        all_emails = await db.get_emails(limit=50)
        
        for email in all_emails:
            if 'skyscanner' in email.get('sender_email', '').lower():
                skyscanner_emails.append(email)
        
        if skyscanner_emails:
            for email in skyscanner_emails[:3]:  # Show first 3
                print(f"   ✅ {email['subject'][:50]}...")
                print(f"      Text content: {email.get('text_content', '')[:200]}...")
                print()
        
        await db.disconnect()
        gmail_reader.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_text_content())