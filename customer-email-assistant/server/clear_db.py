#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from dotenv import load_dotenv
from db import Database

load_dotenv('../.env')

async def clear_database():
    """데이터베이스 완전 초기화"""
    
    try:
        db = Database()
        await db.connect()
        
        print("🗑️ 데이터베이스 완전 초기화...")
        
        # MongoDB 컬렉션 완전 삭제
        if hasattr(db, 'collection'):
            result = await db.collection.delete_many({})
            print(f"   삭제된 문서: {result.deleted_count}개")
        
        print("✅ 데이터베이스 초기화 완료!")
        
        await db.disconnect()
        
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    asyncio.run(clear_database())