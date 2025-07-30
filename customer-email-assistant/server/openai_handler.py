import openai
import os
from config import Config # config.py에서 설정 임포트

def call_llm_api(prompt: str, model_name: str, max_tokens_to_generate: int, temperature: float = 0.7) -> str:
    """
    OpenAI API를 호출하여 텍스트를 생성합니다.
    :param prompt: 사용자 프롬프트
    :param model_name: 사용할 LLM 모델 이름
    :param max_tokens_to_generate: 생성할 최대 토큰 수
    :param temperature: 창의성 조절 (낮을수록 보수적, 높을수록 창의적)
    :return: LLM이 생성한 텍스트 또는 오류 메시지
    """
    try:
        # API 키는 환경 변수 또는 Streamlit Secrets에서 가져옵니다.
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful and concise assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens_to_generate,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR: OpenAI API 호출 오류 ({model_name}): {e}")
        return f"API 호출 중 오류 발생: {e}"


