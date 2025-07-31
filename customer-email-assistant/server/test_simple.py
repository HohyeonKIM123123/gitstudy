#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
sys.path.append('.')

# Load environment variables first
from dotenv import load_dotenv
load_dotenv('../.env')

from simple_email_reader import SimpleEmailReader

async def test_simple_reader():
    """SimpleEmailReader 테스트"""
    
    try:
        reader = SimpleEmailReader()
        print("✅ SimpleEmailReader 연결 성공")
        
        print("\n📧 이메일 가져오는 중...")
        emails = await reader.fetch_emails(limit=5)
        
        print(f"📊 가져온 이메일: {len(emails)}개")
        
        for i, email in enumerate(emails, 1):
            print(f"\n{i}. {email['subject']}")
            print(f"   발신자: {email['sender_email']}")
            print(f"   내용: {email['text_content'][:200]}...")
            
            # 한국어 체크
            if any('\uac00' <= char <= '\ud7af' for char in email['text_content']):
                print(f"   🇰🇷 한국어 이메일 감지!")
        
        reader.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_reader())