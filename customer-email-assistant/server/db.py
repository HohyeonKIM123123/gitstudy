import os
import motor.motor_asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bson import ObjectId
import json

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.emails_collection = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/email_assistant")
            self.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
            
            # Use a simple database name
            self.db = self.client.emails
            self.emails_collection = self.db.emails
            
            # Create indexes for better performance
            await self._create_indexes()
            
            print("Connected to MongoDB successfully")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    async def _create_indexes(self):
        """Create database indexes"""
        try:
            # Index on gmail_id for uniqueness
            await self.emails_collection.create_index("gmail_id", unique=True)
            
            # Index on received_at for sorting
            await self.emails_collection.create_index("received_at")
            
            # Index on status for filtering
            await self.emails_collection.create_index("status")
            
            # Index on priority for filtering
            await self.emails_collection.create_index("priority")
            
            # Compound index for common queries
            await self.emails_collection.create_index([
                ("status", 1),
                ("received_at", -1)
            ])
            
        except Exception as e:
            print(f"Error creating indexes: {e}")
    
    async def store_email(self, email_data: Dict) -> str:
        """Store a new email in the database"""
        try:
            # Add timestamp
            email_data['created_at'] = datetime.utcnow()
            email_data['updated_at'] = datetime.utcnow()
            
            # Insert email
            result = await self.emails_collection.insert_one(email_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error storing email: {e}")
            raise
    
    async def get_emails(self, limit: int = 50, status: Optional[str] = None, 
                        priority: Optional[str] = None) -> List[Dict]:
        """Get emails from database with optional filtering"""
        try:
            # Build query
            query = {}
            if status:
                query['status'] = status
            if priority:
                query['priority'] = priority
            
            # Execute query
            cursor = self.emails_collection.find(query).sort("received_at", -1).limit(limit)
            emails = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for email in emails:
                email['id'] = str(email['_id'])
                del email['_id']
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    async def get_email(self, email_id: str) -> Optional[Dict]:
        """Get a specific email by ID"""
        try:
            email = await self.emails_collection.find_one({"_id": ObjectId(email_id)})
            
            if email:
                email['id'] = str(email['_id'])
                del email['_id']
                return email
            
            return None
            
        except Exception as e:
            print(f"Error fetching email {email_id}: {e}")
            return None
    
    async def get_email_by_gmail_id(self, gmail_id: str) -> Optional[Dict]:
        """Get email by Gmail ID"""
        try:
            email = await self.emails_collection.find_one({"gmail_id": gmail_id})
            
            if email:
                email['id'] = str(email['_id'])
                del email['_id']
                return email
            
            return None
            
        except Exception as e:
            print(f"Error fetching email by Gmail ID {gmail_id}: {e}")
            return None
    
    async def update_email(self, email_id: str, update_data: Dict) -> bool:
        """Update an email"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            result = await self.emails_collection.update_one(
                {"_id": ObjectId(email_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating email {email_id}: {e}")
            return False
    
    async def delete_email(self, email_id: str) -> bool:
        """Delete an email"""
        try:
            result = await self.emails_collection.delete_one({"_id": ObjectId(email_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error deleting email {email_id}: {e}")
            return False
    
    async def get_email_stats(self) -> Dict:
        """Get email statistics"""
        try:
            # Get total counts
            total = await self.emails_collection.count_documents({})
            unread = await self.emails_collection.count_documents({"status": "unread"})
            replied = await self.emails_collection.count_documents({"status": "replied"})
            archived = await self.emails_collection.count_documents({"status": "archived"})
            
            # Get priority distribution
            priority_pipeline = [
                {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
            ]
            priority_cursor = self.emails_collection.aggregate(priority_pipeline)
            priority_dist = {doc['_id']: doc['count'] async for doc in priority_cursor}
            
            # Get recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent = await self.emails_collection.count_documents({
                "received_at": {"$gte": week_ago.isoformat()}
            })
            
            # Calculate average response time (for replied emails)
            avg_response_time = await self._calculate_avg_response_time()
            
            return {
                'total': total,
                'unread': unread,
                'replied': replied,
                'archived': archived,
                'priority_distribution': priority_dist,
                'recent_activity': recent,
                'avg_response_time': avg_response_time,
                'totalChange': 0,  # Would need historical data
                'unreadChange': 0,  # Would need historical data
                'repliedChange': 0  # Would need historical data
            }
            
        except Exception as e:
            print(f"Error getting email stats: {e}")
            return {}
    
    async def _calculate_avg_response_time(self) -> str:
        """Calculate average response time for replied emails"""
        try:
            # This is a simplified calculation
            # In production, you'd track when replies were sent
            pipeline = [
                {"$match": {"status": "replied"}},
                {"$limit": 100},  # Sample recent replied emails
                {"$project": {
                    "response_time": {
                        "$subtract": ["$updated_at", "$created_at"]
                    }
                }},
                {"$group": {
                    "_id": None,
                    "avg_time": {"$avg": "$response_time"}
                }}
            ]
            
            cursor = self.emails_collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                # Convert milliseconds to hours
                avg_ms = result[0]['avg_time']
                avg_hours = avg_ms / (1000 * 60 * 60)
                return f"{avg_hours:.1f}h"
            
            return "N/A"
            
        except Exception as e:
            print(f"Error calculating response time: {e}")
            return "N/A"
    
    async def search_emails(self, query: str, limit: int = 20) -> List[Dict]:
        """Search emails by content or subject"""
        try:
            # Create text search query
            search_query = {
                "$or": [
                    {"subject": {"$regex": query, "$options": "i"}},
                    {"body": {"$regex": query, "$options": "i"}},
                    {"sender_email": {"$regex": query, "$options": "i"}},
                    {"tags": {"$in": [query]}}
                ]
            }
            
            cursor = self.emails_collection.find(search_query).sort("received_at", -1).limit(limit)
            emails = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for email in emails:
                email['id'] = str(email['_id'])
                del email['_id']
            
            return emails
            
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    async def cleanup_old_emails(self, days: int = 90) -> int:
        """Clean up emails older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.emails_collection.delete_many({
                "received_at": {"$lt": cutoff_date.isoformat()},
                "status": {"$in": ["archived", "spam"]}
            })
            
            return result.deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old emails: {e}")
            return 0
    
    async def get_email_trends(self, days: int = 30) -> Dict:
        """Get email trends over the specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {"$match": {"received_at": {"$gte": start_date.isoformat()}}},
                {"$group": {
                    "_id": {
                        "date": {"$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {"$dateFromString": {"dateString": "$received_at"}}
                        }},
                        "priority": "$priority"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.date": 1}}
            ]
            
            cursor = self.emails_collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            # Process results into a more usable format
            trends = {}
            for result in results:
                date = result['_id']['date']
                priority = result['_id']['priority'] or 'general'
                count = result['count']
                
                if date not in trends:
                    trends[date] = {}
                trends[date][priority] = count
            
            return trends
            
        except Exception as e:
            print(f"Error getting email trends: {e}")
            return {}
    
    # 펜션 정보 관리 메서드들
    async def get_pension_info(self) -> Optional[Dict]:
        """펜션 정보 조회"""
        try:
            # pension_info 컬렉션에서 최신 정보 조회
            if not hasattr(self, 'pension_collection'):
                self.pension_collection = self.db.pension_info
            
            pension_info = await self.pension_collection.find_one(
                {}, sort=[("updated_at", -1)]
            )
            
            if pension_info:
                pension_info['id'] = str(pension_info['_id'])
                del pension_info['_id']
                return pension_info
            
            return None
            
        except Exception as e:
            print(f"Error getting pension info: {e}")
            return None
    
    async def save_pension_info(self, raw_text: str, analyzed_info: Optional[Dict] = None) -> bool:
        """펜션 정보 저장"""
        try:
            if not hasattr(self, 'pension_collection'):
                self.pension_collection = self.db.pension_info
            
            pension_data = {
                'raw_text': raw_text,
                'analyzed_info': analyzed_info,
                'updated_at': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            
            # 기존 정보가 있으면 업데이트, 없으면 새로 생성
            existing = await self.pension_collection.find_one({})
            
            if existing:
                # 업데이트
                pension_data['created_at'] = existing.get('created_at', datetime.utcnow())
                await self.pension_collection.replace_one(
                    {"_id": existing["_id"]}, 
                    pension_data
                )
            else:
                # 새로 생성
                await self.pension_collection.insert_one(pension_data)
            
            return True
            
        except Exception as e:
            print(f"Error saving pension info: {e}")
            return False
    
    # 응답 설정 관리 메서드들
    async def get_response_settings(self) -> Optional[Dict]:
        """응답 설정 조회"""
        try:
            # response_settings 컬렉션에서 최신 설정 조회
            if not hasattr(self, 'response_settings_collection'):
                self.response_settings_collection = self.db.response_settings
            
            settings = await self.response_settings_collection.find_one(
                {}, sort=[("updated_at", -1)]
            )
            
            if settings:
                settings['id'] = str(settings['_id'])
                del settings['_id']
                return settings
            
            return None
            
        except Exception as e:
            print(f"Error getting response settings: {e}")
            return None
    
    async def save_response_settings(self, settings: Dict) -> bool:
        """응답 설정 저장"""
        try:
            if not hasattr(self, 'response_settings_collection'):
                self.response_settings_collection = self.db.response_settings
            
            settings_data = {
                'settings': settings,
                'updated_at': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            
            # 기존 설정이 있으면 업데이트, 없으면 새로 생성
            existing = await self.response_settings_collection.find_one({})
            
            if existing:
                # 업데이트
                settings_data['created_at'] = existing.get('created_at', datetime.utcnow())
                await self.response_settings_collection.replace_one(
                    {"_id": existing["_id"]}, 
                    settings_data
                )
            else:
                # 새로 생성
                await self.response_settings_collection.insert_one(settings_data)
            
            return True
            
        except Exception as e:
            print(f"Error saving response settings: {e}")
            return False