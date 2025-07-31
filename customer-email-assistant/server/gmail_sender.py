#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional

class GmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_address = os.getenv("GMAIL_EMAIL")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")
        
    def send_reply(self, to_email: str, subject: str, reply_content: str, 
                   original_message_id: Optional[str] = None) -> bool:
        """Gmail로 답장 보내기"""
        try:
            # SMTP 연결
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.app_password)
            
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            # 답장 제목 (Re: 추가)
            if not subject.startswith('Re:'):
                subject = f'Re: {subject}'
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 원본 메시지 ID가 있으면 답장 헤더 추가
            if original_message_id:
                msg['In-Reply-To'] = original_message_id
                msg['References'] = original_message_id
            
            # 본문 추가
            msg.attach(MIMEText(reply_content, 'plain', 'utf-8'))
            
            # 이메일 전송
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            print(f"✅ 답장 전송 성공: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ 답장 전송 실패: {e}")
            return False
    
    def send_html_reply(self, to_email: str, subject: str, reply_content: str,
                       original_message_id: Optional[str] = None) -> bool:
        """HTML 형식으로 답장 보내기"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.app_password)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            if not subject.startswith('Re:'):
                subject = f'Re: {subject}'
            msg['Subject'] = Header(subject, 'utf-8')
            
            if original_message_id:
                msg['In-Reply-To'] = original_message_id
                msg['References'] = original_message_id
            
            # 텍스트와 HTML 버전 모두 추가
            text_part = MIMEText(reply_content, 'plain', 'utf-8')
            html_part = MIMEText(f'<html><body><pre>{reply_content}</pre></body></html>', 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            print(f"✅ HTML 답장 전송 성공: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ HTML 답장 전송 실패: {e}")
            return False