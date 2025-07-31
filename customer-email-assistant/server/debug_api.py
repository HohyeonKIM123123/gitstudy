#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from dotenv import load_dotenv
from db import Database
from gmail_imap_reader import GmailIMAPReader
import json

# Load environment variables
load_dotenv('../.env')

async def debug_api_data():
    """Debug what the API actually returns"""
    
    try:
        # Initialize services
        db = Database()
        await db.connect()
        
        gmail_reader = GmailIMAPReader()
        
        print("🔍 Debugging API data flow...")
        
        # 1. Check what Gmail reader returns
        print("\n1️⃣ Gmail IMAP Reader Output:")
        emails = await gmail_reader.fetch_emails(limit=5, query="ALL")
        
        skyscanner_email = None
        for email_data in emails:
            if 'skyscanner' in email_data.get('sender_email', '').lower():
                skyscanner_email = email_data
                break
        
        if skyscanner_email:
            print(f"   Subject: {skyscanner_email['subject']}")
            print(f"   Body type: {type(skyscanner_email['body'])}")
            print(f"   Body preview: {repr(skyscanner_email['body'][:200])}")
            print(f"   Text content: {repr(skyscanner_email['text_content'][:200])}")
            
            # 2. Check what gets stored in database
            print(f"\n2️⃣ Storing in database...")
            
            # Check if already exists
            existing = await db.get_email_by_gmail_id(skyscanner_email['gmail_id'])
            if existing:
                print(f"   Email already exists in DB")
                stored_email = existing
            else:
                print(f"   Storing new email...")
                await db.store_email(skyscanner_email)
                stored_email = await db.get_email_by_gmail_id(skyscanner_email['gmail_id'])
            
            print(f"   DB Body type: {type(stored_email['body'])}")
            print(f"   DB Body preview: {repr(stored_email['body'][:200])}")
            print(f"   DB Text content: {repr(stored_email.get('text_content', '')[:200])}")
            
            # 3. Check what API endpoint returns
            print(f"\n3️⃣ API Endpoint Response:")
            api_email = await db.get_email(stored_email['_id'])
            if api_email:
                print(f"   API Body type: {type(api_email['body'])}")
                print(f"   API Body preview: {repr(api_email['body'][:200])}")
                print(f"   API Text content: {repr(api_email.get('text_content', '')[:200])}")
                
                # 4. Test JSON serialization
                print(f"\n4️⃣ JSON Serialization Test:")
                try:
                    json_str = json.dumps(api_email, ensure_ascii=False, default=str)
                    print(f"   JSON serialization: SUCCESS")
                    print(f"   JSON size: {len(json_str)} chars")
                    
                    # Parse back
                    parsed = json.loads(json_str)
                    print(f"   Parsed body preview: {repr(parsed['body'][:200])}")
                    print(f"   Parsed text_content: {repr(parsed.get('text_content', '')[:200])}")
                    
                except Exception as e:
                    print(f"   JSON error: {e}")
            else:
                print(f"   ❌ API returned None")
        else:
            print(f"   ❌ No Skyscanner email found")
        
        await db.disconnect()
        gmail_reader.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_data())