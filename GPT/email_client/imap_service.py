import imaplib
import email
from email.header import decode_header
from config.settings import EMAIL, EMAIL_PASSWORD, IMAP_SERVER
from utils.logger import log_error

def fetch_emails(limit=20):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, EMAIL_PASSWORD)
        mail.select("inbox")

        result, data = mail.search(None, "ALL")
        email_ids = data[0].split()[-limit:]

        emails = []
        for e_id in reversed(email_ids):
            result, msg_data = mail.fetch(e_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            from_ = msg.get("From")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            emails.append({
                "from": from_,
                "subject": subject,
                "body": body
            })

        return emails
    except Exception as e:
        log_error(f"IMAP Fetch Error: {str(e)}")
        return []
