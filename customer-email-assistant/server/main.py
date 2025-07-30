from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel

# 새로 생성된 config.py에서 설정 임포트
from config import Config

from gmail_reader import GmailReader
from reply_generator import ReplyGenerator
from classifier import EmailClassifier
from db import Database
from email_processor import EmailProcessor # 새로 임포트

# Load environment variables
load_dotenv()

app = FastAPI(title="Customer Email Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS, # config에서 가져옴
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
gmail_reader = GmailReader()
reply_generator = ReplyGenerator()
email_classifier = EmailClassifier()
db = Database()
email_processor = EmailProcessor() # EmailProcessor 인스턴스 생성

# Pydantic models
class EmailResponse(BaseModel):
    id: str
    subject: str
    sender_email: str
    sender_name: Optional[str] = None
    body: str
    received_at: str
    status: str = "unread"
    priority: Optional[str] = None
    tags: List[str] = []

class ReplyRequest(BaseModel):
    content: str

class ClassificationResponse(BaseModel):
    priority: str
    tags: List[str]
    confidence: float

@app.get("/")
async def root():
    return {"message": "Customer Email Assistant API", "version": "1.0.0"}

@app.get("/emails", response_model=List[EmailResponse])
async def get_emails(limit: int = 50, status: Optional[str] = None):
    """Fetch emails from database"""
    try:
        emails = await db.get_emails(limit=limit, status=status)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(email_id: str):
    """Get specific email by ID"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/classify", response_model=ClassificationResponse)
async def classify_email(email_id: str):
    """Classify email using AI"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        classification = await email_classifier.classify(email['body'], email['subject'])
        
        # Update email with classification
        await db.update_email(email_id, {
            'priority': classification['priority'],
            'tags': classification['tags']
        })
        
        return classification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/generate-reply")
async def generate_reply(email_id: str, context: dict = {}):
    """Generate AI reply for email"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # reply_generator의 generate_reply 함수가 이제 EmailProcessor를 내부적으로 사용합니다.
        # 따라서 여기서는 email['body']와 기타 필요한 context만 전달합니다.
        reply = await reply_generator.generate_reply(
            email_content=email['body'],
            subject=email['subject'], # subject는 generate_reply 내부에서 prompt 구성에 사용될 수 있음
            sender=email['sender_email'], # sender도 generate_reply 내부에서 prompt 구성에 사용될 수 있음
            context=context # 분류 결과 등 추가 컨텍스트 전달
        )
        
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/send-reply")
async def send_reply(email_id: str, reply_request: ReplyRequest):
    """Send reply via Gmail"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Send reply via Gmail
        success = await gmail_reader.send_reply(
            original_email_id=email['gmail_id'],
            reply_content=reply_request.content,
            to_email=email['sender_email'],
            subject=f"Re: {email['subject']}"
        )
        
        if success:
            # Update email status
            await db.update_email(email_id, {'status': 'replied'})
            return {"message": "Reply sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send reply")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/emails/{email_id}")
async def update_email(email_id: str, update_data: dict):
    """Update email status or other fields"""
    try:
        await db.update_email(email_id, update_data)
        return {"message": "Email updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_emails():
    """Manually sync emails from Gmail"""
    try:
        # Fetch new emails from Gmail
        new_emails = await gmail_reader.fetch_emails(limit=50)
        
        # Process and store emails
        processed_count = 0
        for email_data in new_emails:
            # Check if email already exists
            existing = await db.get_email_by_gmail_id(email_data['id'])
            if not existing:
                # Classify new email
                classification = await email_classifier.classify(
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
        
        return {
            "message": f"Sync completed. {processed_count} new emails processed.",
            "processed_count": processed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get email statistics"""
    try:
        stats = await db.get_email_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize database connection"""
    await db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await db.disconnect()

if __name__ == "__main__":
    port = Config.SERVER_PORT # config에서 가져옴
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)


