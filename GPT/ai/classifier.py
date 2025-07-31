import re

def classify_email(subject, body):
    """
    단순 규칙 기반 분류. 필요시 GPT API와 연동 가능
    """
    text = f"{subject} {body}".lower()
    if "urgent" in text or "긴급" in text:
        return "긴급"
    elif re.search(r"(meeting|회의|보고)", text):
        return "업무"
    else:
        return "기타"

