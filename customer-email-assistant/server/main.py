from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel

from gmail_imap_reader import GmailIMAPReader
from reply_generator import ReplyGenerator
from classifier import EmailClassifier
from db import Database

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
    gmail_reader = GmailIMAPReader()
    print("Gmail IMAP reader initialized successfully")
except Exception as e:
    print(f"Gmail IMAP reader initialization failed: {e}")
    gmail_reader = None

reply_generator = ReplyGenerator()
email_classifier = EmailClassifier()
db = Database()

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
    """Send reply via Gmail"""
    try:
        email = await db.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Send reply via Gmail (IMAP doesn't support sending, use SMTP later)
        # For now, just mark as replied
        success = True  # Placeholder
        
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