from db.database import get_connection

def save_received_email(sender, subject, body, classification):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO received_emails (sender, subject, body, classification)
        VALUES (?, ?, ?, ?)
    """, (sender, subject, body, classification))
    conn.commit()
    conn.close()

def save_sent_email(recipient, subject, body):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sent_emails (recipient, subject, body)
        VALUES (?, ?, ?)
    """, (recipient, subject, body))
    conn.commit()
    conn.close()

def get_received_emails(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, subject, classification, received_at FROM received_emails
        ORDER BY received_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_sent_emails(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT recipient, subject, sent_at FROM sent_emails
        ORDER BY sent_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
