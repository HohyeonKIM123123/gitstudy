import smtplib
from email.mime.text import MIMEText
from config.settings import EMAIL, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
from utils.logger import log_error

def send_email(to_address, subject, body):
    try:
        msg = MIMEText(body, "plain")
        msg["From"] = EMAIL
        msg["To"] = to_address
        msg["Subject"] = subject

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD)
            server.sendmail(EMAIL, to_address, msg.as_string())

        return True
    except Exception as e:
        log_error(f"SMTP Send Error: {str(e)}")
        return False
