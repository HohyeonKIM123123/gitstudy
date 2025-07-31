#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from dotenv import load_dotenv
from db import Database

load_dotenv('../.env')

async def debug_api_response():
    """API 응답 디버깅"""
    
    try:
        db = Database()
        await db.connect()
        
        print("🔍 API 응답 디버깅...")
        
        # 이메일 가져오기
        emails = await db.get_emails(limit=5)
        
        print(f"📊 데이터베이스에서 가져온 이메일: {len(emails)}개")
        
        for i, email in enumerate(emails, 1):
            print(f"\n{i}. 제목: {email.get('subject', 'No subject')}")
            print(f"   발신자: {email.get('sender_email', 'Unknown')}")
            print(f"   본문 타입: {type(email.get('body', ''))}")
            print(f"   본문 길이: {len(email.get('body', ''))}")
            print(f"   본문 미리보기: {repr(email.get('body', '')[:100])}")
            print(f"   텍스트 내용 타입: {type(email.get('text_content', ''))}")
            print(f"   텍스트 내용 길이: {len(email.get('text_content', ''))}")
            print(f"   텍스트 내용 미리보기: {repr(email.get('text_content', '')[:100])}")
            
            # JSON 직렬화 테스트
            try:
                json_str = json.dumps(email, ensure_ascii=False, default=str)
                print(f"   JSON 직렬화: 성공 ({len(json_str)} 문자)")
                
                # JSON 파싱 테스트
                parsed = json.loads(json_str)
                print(f"   JSON 파싱: 성공")
                print(f"   파싱된 제목: {parsed.get('subject', 'No subject')}")
                print(f"   파싱된 텍스트 내용: {repr(parsed.get('text_content', '')[:100])}")
                
            except Exception as e:
                print(f"   JSON 오류: {e}")
        
        await db.disconnect()
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_response())