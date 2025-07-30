from openai import OpenAI

client = OpenAI()

def summarize_email(email_body: str) -> str:
    """이메일 내용을 요약하는 함수"""
    prompt = f"다음 이메일 내용을 간결하게 요약해 주세요:\n\n{email_body}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "당신은 이메일 요약 비서입니다."},
                    {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

