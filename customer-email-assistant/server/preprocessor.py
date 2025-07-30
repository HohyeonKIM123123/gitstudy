import os
import re
import uuid
import tiktoken
import openai
from typing import Dict, Any, List, Optional
from collections import Counter

# --- 0. 설정 파일 (config.py) 가정 ---
# 실제 프로젝트에서는 별도의 config.py 파일에서 임포트해야 합니다.
# 이 코드를 단일 파일로 실행하기 위해 여기에 임시로 정의합니다.
class Config:
    # OpenAI API 키는 환경 변수 또는 Streamlit Secrets에서 가져옵니다.
    # 실제 배포 시에는 'YOUR_OPENAI_API_KEY_HERE'를 실제 키로 대체하거나 환경 변수를 설정해야 합니다.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE") 
    
    # 메인 초안 작성 모델 설정
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
    
    # 통계 기반 요약에 할당할 최대 토큰 수 (LLM 호출 없음)
    MAX_SUMMARY_TOKENS = 300 
    
    # 요약 적용을 위한 토큰 Pivot 지점 (이 토큰 수를 초과하면 스레드 요약 적용)
    PIVOT_TOKEN_LIMIT = 600 

# 실제 config.py에서 임포트하는 것처럼 사용
OPENAI_MODEL_NAME = Config.OPENAI_MODEL_NAME
MAX_TOKENS_FOR_CHATGPT = Config.MAX_TOKENS_FOR_CHATGPT
PROMPT_TEMPLATE = Config.PROMPT_TEMPLATE
MAX_SUMMARY_TOKENS = Config.MAX_SUMMARY_TOKENS
PIVOT_TOKEN_LIMIT = Config.PIVOT_TOKEN_LIMIT

# --- 1. 외부 LLM 호출 함수 (openai_handler.py 가정) ---
# 이 함수는 실제 OpenAI API를 호출합니다.
def call_llm_api(prompt: str, model_name: str, max_tokens_to_generate: int, temperature: float = 0.4) -> str:
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

# --- 2. Polyglot 언어 감지 (선택 사항) ---
# 설치 필요: pip install polyglot pyicu pycld2 morfessor
# 시스템에 따라: sudo apt-get install python3-icu libicu-dev (Ubuntu/Debian)
try:
    from polyglot.detect import Detector
except ImportError:
    print("경고: polyglot 라이브러리가 설치되지 않았습니다. 언어 감지 기능이 제한될 수 있습니다.")
    Detector = None

# --- 3. 통계 기반 요약 (StatisticalSummarizer) ---
# pip install konlpy
# JVM 설치 필요: https://www.java.com/ko/download/
from konlpy.tag import Okt 

class StatisticalSummarizer:
    def __init__(self, tokenizer_name: str = "Okt", openai_model_name: str = OPENAI_MODEL_NAME):
        """
        통계 기반 요약기를 초기화합니다.
        :param tokenizer_name: 사용할 한국어 형태소 분석기 이름 (예: "Okt")
        :param openai_model_name: 토큰 계산에 사용할 OpenAI 모델 이름
        """
        if tokenizer_name == "Okt":
            self.tagger = Okt()
        else:
            raise ValueError(f"지원하지 않는 형태소 분석기: {tokenizer_name}")
        self.tokenizer = tiktoken.encoding_for_model(openai_model_name)

    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분리합니다 (한국어)."""
        # . ? ! 에 이어지는 공백 문자로 분리
        sentences = re.split(r'(?<=[.?!])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_meaningful_tokens(self, text: str) -> List[str]:
        """텍스트에서 의미 있는 토큰(명사, 동사, 형용사 등)을 추출합니다."""
        # 명사, 동사, 형용사 등 중요하다고 판단되는 품사만 추출
        tokens = [word for word, pos in self.tagger.pos(text) if pos in ['Noun', 'Verb', 'Adjective']]
        return tokens

    def summarize_thread_content(self, thread_text: str, max_summary_tokens: int) -> str:
        """
        통계 기반으로 메일 스레드 내용을 요약합니다.
        :param thread_text: 메일 스레드의 원문
        :param max_summary_tokens: 요약 결과의 최대 토큰 수
        :return: 요약된 텍스트
        """
        sentences = self._split_sentences(thread_text)
        if not sentences:
            return ""

        all_meaningful_tokens = []
        for sentence in sentences:
            all_meaningful_tokens.extend(self._get_meaningful_tokens(sentence))
        word_frequencies = Counter(all_meaningful_tokens)

        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            for token in self._get_meaningful_tokens(sentence):
                score += word_frequencies[token] 
            sentence_scores[i] = score
        
        # 점수 순으로 문장 정렬 (내림차순)
        sorted_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)

        selected_sentences_with_indices = []
        current_tokens = 0

        for idx in sorted_sentence_indices:
            sentence = sentences[idx]
            sentence_tokens = len(self.tokenizer.encode(sentence))

            if current_tokens + sentence_tokens <= max_summary_tokens:
                selected_sentences_with_indices.append((idx, sentence))
                current_tokens += sentence_tokens
            else:
                break
        
        # 원본 문장 순서대로 정렬
        selected_sentences_with_indices.sort(key=lambda x: x[0])
        
        summary = " ".join([s[1] for s_idx, s in selected_sentences_with_indices])
        
        # 마지막으로 다시 한번 토큰 제한 체크 (혹시 모를 오차)
        if len(self.tokenizer.encode(summary)) > max_summary_tokens:
            encoded_summary = self.tokenizer.encode(summary)
            summary = self.tokenizer.decode(encoded_summary[:max_summary_tokens]) + "..." # 잘렸음을 표시
            
        return summary.strip()

# --- 4. 메일 전처리기 및 초안 생성기 (EmailPreprocessorAndDraftGenerator) ---
class EmailPreprocessorAndDraftGenerator:
    def __init__(self, main_llm_model: str = OPENAI_MODEL_NAME,
                 max_main_llm_tokens: int = MAX_TOKENS_FOR_CHATGPT,
                 max_summary_tokens: int = MAX_SUMMARY_TOKENS,
                 pivot_token_limit: int = PIVOT_TOKEN_LIMIT):
        """
        메일 전처리기 및 초안 생성기를 초기화합니다.
        :param main_llm_model: 주 답변 생성에 사용할 LLM 모델 이름
        :param max_main_llm_tokens: 주 LLM의 최대 입력+출력 토큰
        :param max_summary_tokens: 통계 기반 요약 결과의 최대 토큰 수
        :param pivot_token_limit: 스레드 요약 적용을 위한 토큰 Pivot 지점
        """
        self.main_tokenizer = tiktoken.encoding_for_model(main_llm_model)
        self.max_main_llm_tokens = max_main_llm_tokens
        self.max_summary_tokens = max_summary_tokens
        self.pivot_token_limit = pivot_token_limit

        self.placeholder_map: Dict[str, str] = {}
        self.reverse_placeholder_map: Dict[str, str] = {}
        
        self.statistical_summarizer = StatisticalSummarizer(openai_model_name=main_llm_model)

    def _count_tokens(self, text: str) -> int:
        """주어진 텍스트의 토큰 수를 계산합니다."""
        return len(self.main_tokenizer.encode(text))

    def _split_email_and_thread(self, email_body: str) -> Dict[str, str]:
        """
        메일 본문을 현재 메시지와 이전 스레드로 분리합니다.
        가장 일반적인 구분자를 사용하며, 필요시 정교한 튜닝이 필요합니다.
        """
        # 스레드 구분자 패턴 (가장 흔한 것부터)
        thread_separators = [
            r"\n\s*---[\s]*Original Message[\s]*---\n",
            r"\n\s*On\s+.+wrote:\n",
            r"\n\s*From:.*Sent:.*To:.*Subject:.*\n", 
            r"\n[\s]*\n^-+\s*\n" # 긴 줄 (---) 이후에 스레드가 시작하는 경우
        ]
        
        for sep in thread_separators:
            match = re.search(sep, email_body, flags=re.DOTALL | re.IGNORECASE)
            if match:
                current_message = email_body[:match.start()].strip()
                thread_content = email_body[match.end():].strip()
                return {"current_message": current_message, "thread_content": thread_content, "has_thread": True}
        
        # 스레드 구분자를 찾지 못하면 전체를 현재 메시지로 간주
        return {"current_message": email_body.strip(), "thread_content": "", "has_thread": False}

    def _remove_boilerplate(self, text: str) -> str:
        """
        텍스트에서 불필요한 상용구(서명, 푸터 등)를 제거합니다.
        """
        cleaned_text = text
        # 이메일 서명 및 푸터 제거
        cleaned_text = re.sub(r"Best regards,.*|Sincerely,.*|Thanks,.*", "", cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        cleaned_text = re.sub(r"Sent from my (iPhone|Android|BlackBerry|Samsung|LG).*|--[\s]*\n[\s\S]*", "", cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # 연속된 빈 줄을 하나로 줄임
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()
        return cleaned_text

    def _identify_and_replace_sensitive_keywords(self, text: str) -> str:
        """
        텍스트에서 민감한 키워드(ID, 전화번호, 이메일 등)를 식별하고 플레이스홀더로 대체합니다.
        """
        processed_text = text
        
        # 키워드 패턴 정의 (필요에 따라 추가/수정)
        # 1. 고객/주문/계좌 ID 패턴
        id_patterns = [
            r"\b(?:CUS|ORD|ACC)[-._]?[A-Za-z0-9]{6,15}\b",  # CUS-12345678, ORD_ABC987
            r"(?:ID|고객ID|Customer ID|주문번호|Account No|계좌번호)[:\s]*([a-zA-Z0-9_-]+)"
        ]
        for pattern in id_patterns:
            processed_text = re.sub(pattern, self._replace_and_store_keyword, processed_text, flags=re.IGNORECASE)

        # 2. 이메일 주소 패턴
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        processed_text = re.sub(email_pattern, self._replace_and_store_keyword, processed_text)

        # 3. 전화번호 패턴 (한국 기준: 010-XXXX-XXXX, 02-XXX-XXXX, 1588-XXXX 등)
        phone_pattern = r"\b010[-.\s]?\d{4}[-.\s]?\d{4}\b|\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b|\b15(?:88|77)[-.\s]?\d{4}\b"
        processed_text = re.sub(phone_pattern, self._replace_and_store_keyword, processed_text)
        
        return processed_text

    def _replace_and_store_keyword(self, match: re.Match) -> str:
        """정규식에 매치된 키워드를 플레이스홀더로 대체하고 맵에 저장합니다."""
        original_keyword = match.group(0) 
        
        if original_keyword in self.placeholder_map:
            return self.placeholder_map[original_keyword]
            
        placeholder = f"[PH_{uuid.uuid4().hex[:8].upper()}]" # 고유한 플레이스홀더 생성
        
        self.placeholder_map[original_keyword] = placeholder
        self.reverse_placeholder_map[placeholder] = original_keyword
        
        return placeholder

    def preprocess_and_generate_draft(self, email_body: str, classification: str = "일반 문의") -> Dict[str, Any]:
        """
        메일 본문을 전처리하고, 조건부 요약을 수행한 후, LLM에 회신 초안을 요청합니다.
        :param email_body: 원본 메일 본문
        :param classification: 메일 분류 결과 (프롬프트에 사용)
        :return: 생성된 회신 초안, 개인정보 대체 테이블, 예측 토큰 수 등
        """
        self.placeholder_map = {}
        self.reverse_placeholder_map = {}

        print("--- 1. 메일 전처리 시작 ---")
        # 1. 불필요한 상용구 제거 (전체 메일에 적용)
        boilerplate_removed_email = self._remove_boilerplate(email_body)
        
        # 2. 민감한 키워드 식별 및 플레이스홀더로 대체 (전체 메일에 적용)
        processed_email_full = self._identify_and_replace_sensitive_keywords(boilerplate_removed_email)
        print(f"  - 개인정보 대체 완료. 대체된 키워드: {self.placeholder_map.keys()}")

        # 3. 현재 메시지와 스레드 내용 분리
        split_result = self._split_email_and_thread(processed_email_full)
        current_message = split_result["current_message"]
        thread_content = split_result["thread_content"]
        has_thread = split_result["has_thread"]

        # 4. 질의용 메일 전문 (요약 전)의 토큰 수 확인
        # 현재 메시지와 스레드 내용을 합친 전체 길이를 기준으로 Pivot 판단
        full_query_text_before_summary = current_message
        if thread_content:
            full_query_text_before_summary += f"\n\n--- 이전 대화 ---\n{thread_content}"

        initial_token_count = self._count_tokens(full_query_text_before_summary)
        print(f"  - 요약 전 질의용 메일 전문 토큰 수: {initial_token_count} 토큰")
        print(f"  - Pivot 토큰 기준: {self.pivot_token_limit} 토큰")

        final_text_for_llm = ""
        thread_summary_applied = False

        # 5. Pivot 지점 확인 및 조건부 스레드 요약
        if has_thread and initial_token_count > self.pivot_token_limit:
            print(f"  - 토큰 수가 Pivot({self.pivot_token_limit})을 초과하여 스레드 요약을 수행합니다.")
            thread_summary = self.statistical_summarizer.summarize_thread_content(
                thread_content, 
                self.max_summary_tokens
            )
            if thread_summary:
                final_text_for_llm = f"{current_message}\n\n--- 이전 대화 요약 ---\n{thread_summary}"
                thread_summary_applied = True
            else: # 요약 내용이 없으면 원본 스레드 사용 (예외 처리)
                final_text_for_llm = full_query_text_before_summary
                print("  - 스레드 요약 실패 또는 내용 없음. 원본 스레드를 사용합니다.")
        else:
            print("  - 토큰 수가 Pivot을 초과하지 않거나 스레드가 없어 요약을 건너뜀.")
            final_text_for_llm = full_query_text_before_summary
        
        # 6. 최종 질의용 메일 전문의 토큰 수 로깅
        final_llm_input_token_count = self._count_tokens(final_text_for_llm)
        print(f"  - 최종 LLM 입력용 메일 전문 토큰 수: {final_llm_input_token_count} 토큰")

        # 7. Polyglot을 이용한 언어 감지
        detected_language = "ko" 
        if Detector:
            try:
                for lang in Detector(final_text_for_llm).languages:
                    detected_language = lang.code
                    print(f"  - 감지된 언어: {detected_language} (신뢰도: {lang.confidence})")
                    break 
            except Exception as e:
                print(f"  - 경고: Polyglot 언어 감지 오류: {e}. 기본값 '{detected_language}' 사용.")
        
        # 8. 메일 회신 초안 작성을 위한 LLM 질의
        print("--- 2. 메일 회신 초안 작성 질의 시작 ---")
        # 프롬프트 템플릿에 전처리된 메일 내용을 삽입
        prompt_for_draft = PROMPT_TEMPLATE.format(
            classification=classification,
            email_content=final_text_for_llm
        )
        
        # 메인 LLM에 전달할 최대 토큰 수 계산 (프롬프트 + 예상 답변 길이)
        # 예상 답변 길이를 250 토큰으로 가정하고, 전체 MAX_TOKENS_FOR_CHATGPT를 넘지 않도록
        max_tokens_to_generate_for_draft = self.max_main_llm_tokens - self._count_tokens(prompt_for_draft)
        if max_tokens_to_generate_for_draft < 50: # 최소한의 답변 토큰 보장
            max_tokens_to_generate_for_draft = 50
        print(f"  - LLM에 요청할 답변 최대 토큰 수: {max_tokens_to_generate_for_draft} 토큰")

        draft_response = call_llm_api(
            prompt=prompt_for_draft,
            model_name=self.main_tokenizer.encoding_name.split('/')[-1], # 모델명만 추출 (예: gpt-4o)
            max_tokens_to_generate=max_tokens_to_generate_for_draft,
            temperature=0.7 # 일반적인 답변 생성 온도
        )
        print("--- 3. LLM 응답 수신 완료 ---")

        # 9. 생성된 초안에서 플레이스홀더를 원본 키워드로 복원
        final_draft = self.restore_original_keywords(draft_response)
        print("  - 개인정보 복원 완료.")
        
        return {
            "query_mail_full_text": final_text_for_llm, # LLM에 전달된 최종 질의용 메일 전문
            "placeholder_table": self.placeholder_map, # 원본 -> 플레이스홀더 매핑 테이블
            "reverse_placeholder_table": self.reverse_placeholder_map, # 플레이스홀더 -> 원본 매핑 테이블
            "initial_token_count": initial_token_count, # 요약 전 전체 메일 토큰 수
            "final_llm_input_token_count": final_llm_input_token_count, # 최종 LLM 입력 토큰 수
            "detected_language": detected_language,
            "has_thread_processed": has_thread,
            "thread_summary_applied": thread_summary_applied,
            "generated_draft": final_draft # 최종 생성된 회신 초안 (개인정보 복원 완료)
        }

    def restore_original_keywords(self, generated_text: str) -> str:
        """
        LLM이 생성한 텍스트에서 플레이스홀더를 원본 키워드로 복원합니다.
        """
        restored_text = generated_text
        for placeholder, original_keyword in self.reverse_placeholder_map.items():
            restored_text = restored_text.replace(placeholder, original_keyword)
        return restored_text

# --- 사용 예시 ---
if __name__ == "__main__":
    # 실제 메일 본문 예시 (스레드 포함)
    sample_email_body_with_thread = """
    안녕하세요, 고객지원팀.

    지난번 문의드렸던 주문번호 ORD-98765432에 대한 환불 처리가 어떻게 진행되고 있는지 궁금합니다.
    제 고객 ID는 CUS-12345678입니다.
    빠른 확인 부탁드립니다.

    감사합니다.
    김영희 드림 (younghee.kim@example.com)
    연락처: 010-9876-5432

    --- Original Message ---
    From: younghee.kim@example.com
    To: support@company.com
    Subject: 주문 환불 문의 (ORD-98765432)
    Date: 2025-07-29

    안녕하세요,
    주문번호 ORD-98765432에 대한 환불 문의드립니다.
    제품 불량으로 인해 반품 신청했는데, 아직 환불이 안 되고 있습니다.
    고객 ID는 CUS-12345678입니다.
    확인 후 연락 부탁드립니다.
    감사합니다.
    """

    # 짧은 메일 본문 예시 (스레드 없음)
    sample_email_body_short = """
    안녕하세요.

    제품 XYZ의 사용법에 대해 문의드립니다.
    간단한 설명 부탁드립니다.

    감사합니다.
    """

    # -----------------------------------------------------------------------
    # 1. 스레드가 있는 긴 메일 처리 예시
    print("\n\n===== 스레드가 있는 긴 메일 처리 예시 =====")
    processor = EmailPreprocessorAndDraftGenerator()
    result_long_email = processor.preprocess_and_generate_draft(
        sample_email_body_with_thread, 
        classification="환불 문의"
    )

    print("\n--- 최종 결과 (긴 메일) ---")
    print(f"LLM에 전달된 질의용 메일 전문:\n{result_long_email['query_mail_full_text']}")
    print(f"\n개인정보 대체 테이블: {result_long_email['placeholder_table']}")
    print(f"초기 전체 메일 토큰 수: {result_long_email['initial_token_count']}")
    print(f"최종 LLM 입력 토큰 수: {result_long_email['final_llm_input_token_count']}")
    print(f"스레드 요약 적용 여부: {result_long_email['thread_summary_applied']}")
    print(f"감지된 언어: {result_long_email['detected_language']}")
    print(f"\n생성된 회신 초안:\n{result_long_email['generated_draft']}")

    # -----------------------------------------------------------------------
    # 2. 스레드 없는 짧은 메일 처리 예시
    print("\n\n===== 스레드 없는 짧은 메일 처리 예시 =====")
    processor_short = EmailPreprocessorAndDraftGenerator()
    result_short_email = processor_short.preprocess_and_generate_draft(
        sample_email_body_short, 
        classification="제품 사용법 문의"
    )

    print("\n--- 최종 결과 (짧은 메일) ---")
    print(f"LLM에 전달된 질의용 메일 전문:\n{result_short_email['query_mail_full_text']}")
    print(f"\n개인정보 대체 테이블: {result_short_email['placeholder_table']}")
    print(f"초기 전체 메일 토큰 수: {result_short_email['initial_token_count']}")
    print(f"최종 LLM 입력 토큰 수: {result_short_email['final_llm_input_token_count']}")
    print(f"스레드 요약 적용 여부: {result_short_email['thread_summary_applied']}")
    print(f"감지된 언어: {result_short_email['detected_language']}")
    print(f"\n생성된 회신 초안:\n{result_short_email['generated_draft']}")

