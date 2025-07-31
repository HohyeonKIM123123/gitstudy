#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from dotenv import load_dotenv
from db import Database
from simple_email_reader import SimpleEmailReader
from classifier import EmailClassifier

# Load environment variables
load_dotenv('../.env')

async def reset_everything():
    """완전히 처음부터 다시 시작"""
    
    try:
        # Initialize services
        db = Database()
        await db.connect()
        
        email_reader = SimpleEmailReader()
        email_classifier = EmailClassifier()
        
        print("🔥 완전히 처음부터 다시 시작합니다...")
        
        # 1. 모든 이메일 삭제
        print("\n1️⃣ 기존 이메일 모두 삭제 중...")
        all_emails = await db.get_emails(limit=1000)
        deleted_count = 0
        
        for email in all_emails:
            await db.delete_email(email['id'])
            deleted_count += 1
        
        print(f"   삭제된 이메일: {deleted_count}개")
        
        # 2. 새로운 SimpleEmailReader로 이메일 가져오기
        print(f"\n2️⃣ 새로운 SimpleEmailReader로 이메일 가져오는 중...")
        
        new_emails = await email_reader.fetch_emails(limit=30)
        print(f"   가져온 이메일: {len(new_emails)}개")
        
        # 3. 이메일 저장
        print(f"\n3️⃣ 이메일 저장 중...")
        stored_count = 0
        
        for email_data in new_emails:
            try:
                # 간단한 분류
                classification = email_classifier.quick_classify(
                    email_data['body'], 
                    email_data['subject']
                )
                
                # 이메일 데이터 업데이트
                email_data.update({
                    'priority': classification['priority'],
                    'tags': classification['tags'],
                    'status': 'unread'
                })
                
                # 저장
                await db.store_email(email_data)
                stored_count += 1
                
                print(f"   저장됨: {email_data['subject'][:50]}...")
                
                # 한국어 이메일인지 확인
                if any('\uac00' <= char <= '\ud7af' for char in email_data.get('text_content', '')):
                    print(f"     🇰🇷 한국어 이메일 감지!")
                    print(f"     내용 미리보기: {email_data['text_content'][:100]}...")
                
            except Exception as e:
                print(f"   저장 실패: {e}")
                continue
        
        print(f"\n✅ 완전 초기화 완료!")
        print(f"   삭제: {deleted_count}개")
        print(f"   새로 저장: {stored_count}개")
        
        # 4. 결과 확인
        print(f"\n4️⃣ 결과 확인...")
        final_emails = await db.get_emails(limit=10)
        
        korean_count = 0
        for email in final_emails:
            print(f"   📧 {email['subject'][:50]}...")
            print(f"      발신자: {email['sender_email']}")
            print(f"      내용: {email.get('text_content', '')[:100]}...")
            
            if any('\uac00' <= char <= '\ud7af' for char in email.get('text_content', '')):
                korean_count += 1
                print(f"      🇰🇷 한국어 이메일!")
            print()
        
        print(f"📊 총 {len(final_emails)}개 이메일 중 {korean_count}개가 한국어 이메일입니다.")
        
        await db.disconnect()
        email_reader.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reset_everything())