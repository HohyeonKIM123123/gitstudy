
import sqlite3

DB_NAME = "emails.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 이메일 수신 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS received_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            subject TEXT,
            body TEXT,
            classification TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 이메일 발신 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT,
            subject TEXT,
            body TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
