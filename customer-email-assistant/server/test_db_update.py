#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from dotenv import load_dotenv
from db import Database

load_dotenv('../.env')

async def test_db_update():
    """DB 업데이트와 통계 테스트"""
    
    try:
        db = Database()
        await db.connect()
        
        print("📊 현재 이메일 통계:")
        stats = await db.get_email_stats()
        print(f"   총 이메일: {stats.get('total', 0)}")
        print(f"   읽지 않음: {stats.get('unread', 0)}")
        print(f"   답장함: {stats.get('replied', 0)}")
        print(f"   보관함: {stats.get('archived', 0)}")
        
        print("\n📧 최근 이메일 목록:")
        emails = await db.get_emails(limit=5)
        for i, email in enumerate(emails, 1):
            print(f"   {i}. {email['subject'][:50]}...")
            print(f"      상태: {email.get('status', 'unknown')}")
            print(f"      ID: {email['id']}")
        
        # 첫 번째 이메일의 상태를 'replied'로 변경해보기
        if emails:
            first_email = emails[0]
            print(f"\n🔄 첫 번째 이메일 상태를 'replied'로 변경 중...")
            print(f"   이메일 ID: {first_email['id']}")
            print(f"   현재 상태: {first_email.get('status', 'unknown')}")
            
            success = await db.update_email(first_email['id'], {'status': 'replied'})
            print(f"   업데이트 성공: {success}")
            
            # 업데이트 후 통계 다시 확인
            print(f"\n📊 업데이트 후 통계:")
            new_stats = await db.get_email_stats()
            print(f"   총 이메일: {new_stats.get('total', 0)}")
            print(f"   읽지 않음: {new_stats.get('unread', 0)}")
            print(f"   답장함: {new_stats.get('replied', 0)}")
            print(f"   보관함: {new_stats.get('archived', 0)}")
            
            # 변경된 이메일 다시 확인
            updated_email = await db.get_email(first_email['id'])
            if updated_email:
                print(f"\n✅ 업데이트된 이메일 확인:")
                print(f"   제목: {updated_email['subject'][:50]}...")
                print(f"   상태: {updated_email.get('status', 'unknown')}")
            else:
                print(f"\n❌ 업데이트된 이메일을 찾을 수 없음")
        
        await db.disconnect()
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_update())