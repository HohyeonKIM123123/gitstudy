# import openai
# from config.settings import OPENAI_API_KEY

# openai.api_key = OPENAI_API_KEY

# def generate_reply(email_body, classification):
#     """
#     GPT를 이용한 회신 초안 생성
#     """
#     prompt = f"""
#     이메일 분류: {classification}
#     아래 이메일에 대한 회신 초안을 핵심 요약해서 작성해 주세요.

#     이메일 내용:
#     {email_body}
#     """

#     response = openai.ChatCompletion.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "system", "content": "당신은 이메일 회신을 도와주는 비서입니다."},
#                     {"role": "user", "content": prompt}],
#         temperature=0.7
#     )

#     return response.choices[0].message["content"]

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_reply(email_body, classification):
    prompt = f"""
    다음 이메일을 읽고 적절한 회신 초안을 요약해서 작성하세요.
    분류: {classification}
    이메일 본문: {email_body}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 이메일 회신 비서입니다. 회신을 간결하고 정중하게 작성하세요."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
