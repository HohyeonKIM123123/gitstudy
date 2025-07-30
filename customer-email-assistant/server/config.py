import os

class Config:
    # --- OpenAI API 설정 ---
    # OpenAI API 키는 환경 변수 또는 Streamlit Secrets에서 가져옵니다.
    # 실제 배포 시에는 'YOUR_OPENAI_API_KEY_HERE'를 실제 키로 대체하거나 환경 변수를 설정해야 합니다.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE") 
    
    # --- 메인 초안 작성 LLM 설정 ---
    OPENAI_MODEL_NAME = "gpt-4o" 
    # 메인 LLM의 최대 입력+출력 토큰 (모델의 컨텍스트 윈도우에 따라 조정)
    # gpt-4o는 128k 토큰까지 지원하지만, 비용 및 응답 속도를 위해 적절히 제한
    MAX_TOKENS_FOR_CHATGPT = 4000 
    
    # 메인 LLM에 전달할 프롬프트 템플릿
    PROMPT_TEMPLATE = """
    다음 메일 내용에 대해 {classification}에 맞춰 친절하고 전문적인 답장 초안을 작성해주세요.
    답변은 200자 이내로 간결하게 작성하고, 필요한 경우 추가 정보를 요청하는 내용을 포함해 주세요.

    --- 메일 내용 ---
    {email_content}
    ---
    """
    
    # --- 통계 기반 요약 설정 ---
    # 스레드 요약에 할당할 최대 토큰 수 (LLM 호출 없음)
    MAX_SUMMARY_TOKENS = 300 
    
    # 요약 적용을 위한 토큰 Pivot 지점 (이 토큰 수를 초과하면 스레드 요약 적용)
    PIVOT_TOKEN_LIMIT = 600 

    # --- 메일 분류 모델 설정 (classifier.py에서 사용) ---
    CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "gpt-3.5-turbo")

    # --- CORS 설정 (main.py에서 사용) ---
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # --- MongoDB 설정 (db.py에서 사용) ---
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/email_assistant")

    # --- Gmail API 설정 (gmail_reader.py에서 사용) ---
    GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

    # --- 서버 포트 설정 (main.py에서 사용) ---
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))


