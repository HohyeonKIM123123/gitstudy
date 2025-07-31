#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from simple_email_reader import SimpleEmailReader

load_dotenv('../.env')

class JsonEmailProcessor:
    def __init__(self):
        self.json_file = "emails.json"
    
    def save_emails_to_json(self, emails):
        """이메일을 JSON 파일로 저장"""
        try:
            # 기존 데이터 로드
            existing_emails = self.load_emails_from_json()
            
            # 새 이메일 추가 (중복 제거)
            existing_ids = {email.get('gmail_id') for email in existing_emails}
            
            new_emails = []
            for email in emails:
                if email.get('gmail_id') not in existing_ids:
                    new_emails.append(email)
            
            # 전체 이메일 목록 업데이트
            all_emails = existing_emails + new_emails
            
            # JSON으로 저장
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(all_emails, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ {len(new_emails)}개의 새 이메일을 JSON에 저장했습니다.")
            return len(new_emails)
            
        except Exception as e:
            print(f"❌ JSON 저장 오류: {e}")
            return 0
    
    def load_emails_from_json(self):
        """JSON 파일에서 이메일 로드"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"❌ JSON 로드 오류: {e}")
            return []
    
    def get_email_by_id(self, email_id):
        """ID로 특정 이메일 가져오기"""
        emails = self.load_emails_from_json()
        for email in emails:
            if email.get('id') == email_id or email.get('gmail_id') == email_id:
                return email
        return None
    
    def get_emails(self, limit=50):
        """이메일 목록 가져오기"""
        emails = self.load_emails_from_json()
        # 최신순으로 정렬
        emails.sort(key=lambda x: x.get('received_at', ''), reverse=True)
        return emails[:limit]
    
    def clean_email_content(self, email):
        """이메일 내용 정리"""
        try:
            content = email.get('text_content', '') or email.get('body', '')
            
            if not content:
                return "내용 없음"
            
            # CSS 스타일 제거
            import re
            content = re.sub(r'@media[^{]*\{[^}]*\}', '', content, flags=re.DOTALL)
            content = re.sub(r'\{[^}]*\}', '', content)
            content = re.sub(r'<[^>]*>', ' ', content)
            
            # 불필요한 공백 정리
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            # 길이 제한
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            return content
            
        except Exception as e:
            print(f"내용 정리 오류: {e}")
            return email.get('text_content', '') or email.get('body', '') or "내용 없음"

async def fetch_and_save_emails():
    """이메일 가져와서 JSON으로 저장"""
    try:
        print("📧 이메일 가져오는 중...")
        
        # SimpleEmailReader로 이메일 가져오기
        reader = SimpleEmailReader()
        emails = await reader.fetch_emails(limit=20)
        reader.close()
        
        print(f"📊 가져온 이메일: {len(emails)}개")
        
        # JSON 프로세서로 저장
        processor = JsonEmailProcessor()
        saved_count = processor.save_emails_to_json(emails)
        
        print(f"💾 저장된 새 이메일: {saved_count}개")
        
        # 저장된 이메일 확인
        print("\n📋 저장된 이메일 목록:")
        saved_emails = processor.get_emails(limit=10)
        
        for i, email in enumerate(saved_emails, 1):
            print(f"\n{i}. {email.get('subject', 'No subject')}")
            print(f"   발신자: {email.get('sender_email', 'Unknown')}")
            
            # 내용 정리해서 표시
            clean_content = processor.clean_email_content(email)
            print(f"   내용: {clean_content[:100]}...")
            
            # 한국어 체크
            if any('\uac00' <= char <= '\ud7af' for char in clean_content):
                print(f"   🇰🇷 한국어 이메일!")
        
        return saved_emails
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(fetch_and_save_emails())