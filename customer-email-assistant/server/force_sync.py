#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from dotenv import load_dotenv
from db import Database
from simple_email_reader import SimpleEmailReader
from classifier import EmailClassifier

load_dotenv('../.env')

async def force_sync():
    """강제로 이메일 다시 동기화"""
    
    try:
        db = Database()
        await db.connect()
        
        reader = SimpleEmailReader()
        classifier = EmailClassifier()
        
        print("🔄 강제 동기화 시작...")
        
        # 1. 기존 이메일 모두 삭제
        print("1️⃣ 기존 이메일 삭제 중...")
        emails = await db.get_emails(limit=1000)
        for email in emails:
            await db.delete_email(email['id'])
        print(f"   삭제됨: {len(emails)}개")
        
        # 2. 새로운 이메일 가져오기
        print("2️⃣ 새 이메일 가져오는 중...")
        new_emails = await reader.fetch_emails(limit=20)
        print(f"   가져옴: {len(new_emails)}개")
        
        # 3. 저장
        print("3️⃣ 저장 중...")
        for email_data in new_emails:
            classification = classifier.quick_classify(email_data['body'], email_data['subject'])
            email_data.update({
                'priority': classification['priority'],
                'tags': classification['tags'],
                'status': 'unread'
            })
            await db.store_email(email_data)
            print(f"   저장: {email_data['subject'][:50]}...")
        
        print("✅ 강제 동기화 완료!")
        
        await db.disconnect()
        reader.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    asyncio.run(force_sync())