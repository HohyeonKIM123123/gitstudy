from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel

from simple_email_reader import SimpleEmailReader
from reply_generator import ReplyGenerator
from classifier import EmailClassifier
from db import Database
from gmail_sender import GmailSender
from pension_analyzer import PensionAnalyzer

# Load environment variables
load_dotenv()

app = FastAPI(title="Customer Email Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    gmail_reader = SimpleEmailReader()
    print("Simple email reader initialized successfully")
except Exception as e:
    print(f"Simple email reader initialization failed: {e}")
    gmail_reader = None

reply_generator = ReplyGenerator()
email_classifier = EmailClassifier()
db = Database()
gmail_sender = GmailSender()
pension_analyzer = PensionAnalyzer()

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

class PensionInfoRequest(BaseModel):
    raw_text: str
    analyzed_info: Optional[dict] = None

class PensionAnalyzeRequest(BaseModel):
    text: str

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
    """Generate AI reply for email with pension info"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # 펜션 정보 가져오기
        pension_info = await db.get_pension_info()
        if pension_info and pension_info.get('analyzed_info'):
            context['pension_info'] = pension_info['analyzed_info']
        
        reply = await reply_generator.generate_reply(
            email_content=email['body'],
            subject=email['subject'],
            sender=email['sender_email'],
            context=context
        )
        
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/{email_id}/send-reply")
async def send_reply(email_id: str, reply_request: ReplyRequest):
    """Send reply via Gmail SMTP"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        print(f"📧 답장 전송 시도: {email['sender_email']}")
        print(f"📝 답장 내용: {reply_request.content[:100]}...")
        
        # 실제 Gmail로 답장 전송
        success = gmail_sender.send_reply(
            to_email=email['sender_email'],
            subject=email['subject'],
            reply_content=reply_request.content,
            original_message_id=email.get('gmail_id')
        )
        
        if success:
            # DB에서 이메일 상태를 'replied'로 업데이트
            print(f"✅ Gmail 전송 성공, DB 업데이트 중...")
            update_result = await db.update_email(email_id, {'status': 'replied'})
            print(f"📊 DB 업데이트 결과: {update_result}")
            
            return {
                "message": "Reply sent successfully to Gmail",
                "sent_to": email['sender_email'],
                "status": "replied"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send reply to Gmail")
            
    except Exception as e:
        print(f"❌ 답장 전송 오류: {e}")
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

# 펜션 정보 관리 API
@app.get("/pension-info")
async def get_pension_info():
    """펜션 정보 조회"""
    try:
        pension_info = await db.get_pension_info()
        return pension_info or {
            "raw_text": "",
            "analyzed_info": None,
            "updated_at": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pension-info")
async def save_pension_info(request: PensionInfoRequest):
    """펜션 정보 저장"""
    try:
        await db.save_pension_info(request.raw_text, request.analyzed_info)
        return {"message": "펜션 정보가 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pension-info/analyze")
async def analyze_pension_info(request: PensionAnalyzeRequest):
    """펜션 정보 AI 분석"""
    try:
        analyzed_info = await pension_analyzer.analyze_pension_info(request.text)
        return {"analyzed_info": analyzed_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and sync emails"""
    await db.connect()
    
    # Auto-sync emails on startup
    if gmail_reader:
        try:
            print("Auto-syncing emails from Gmail...")
            new_emails = await gmail_reader.fetch_emails(limit=50)
            
            processed_count = 0
            for email_data in new_emails:
                # Check if email already exists
                existing = await db.get_email_by_gmail_id(email_data['gmail_id'])
                if not existing:
                    # Quick classification (skip AI for now, use keywords)
                    classification = email_classifier.quick_classify(
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
            
            print(f"Auto-sync completed. {processed_count} new emails processed.")
            
        except Exception as e:
            print(f"Auto-sync failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await db.disconnect()

if __name__ == "__main__":
    port = int(os.getenv("SERVER_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)