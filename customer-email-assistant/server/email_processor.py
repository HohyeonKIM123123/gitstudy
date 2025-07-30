import re
import uuid
import tiktoken
from typing import Dict, Any, List, Optional

# Polyglot 언어 감지 (선택 사항)
try:
    from polyglot.detect import Detector
except ImportError:
    print("경고: polyglot 라이브러리가 설치되지 않았습니다. 언어 감지 기능이 제한될 수 있습니다.")
    Detector = None

# config.py에서 설정 임포트
from config import Config

# statistical_summarizer.py에서 통계 기반 요약기 임포트
from statistical_summarizer import StatisticalSummarizer

class EmailProcessor:
    def __init__(self, main_llm_model: str = Config.OPENAI_MODEL_NAME,
                 max_main_llm_tokens: int = Config.MAX_TOKENS_FOR_CHATGPT,
                 max_summary_tokens: int = Config.MAX_SUMMARY_TOKENS,
                 pivot_token_limit: int = Config.PIVOT_TOKEN_LIMIT):
        """
        메일 전처리기 및 스레드 요약 기능을 초기화합니다.
        :param main_llm_model: 주 답변 생성에 사용할 LLM 모델 이름 (토큰 계산용)
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

    def process_email_for_llm(self, email_body: str) -> Dict[str, Any]:
        """
        메일 본문을 전처리하고, 조건부 스레드 요약을 수행하여 LLM에 전달할 텍스트를 준비합니다.
        :param email_body: 원본 메일 본문
        :return: LLM에 전달될 최종 텍스트, 개인정보 대체 테이블, 예측 토큰 수 등
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
        
        return {
            "processed_email_content": final_text_for_llm, # LLM에 전달될 최종 질의용 메일 전문
            "placeholder_table": self.placeholder_map, # 원본 -> 플레이스홀더 매핑 테이블
            "reverse_placeholder_table": self.reverse_placeholder_map, # 플레이스홀더 -> 원본 매핑 테이블
            "initial_token_count": initial_token_count, # 요약 전 전체 메일 토큰 수
            "final_llm_input_token_count": final_llm_input_token_count, # 최종 LLM 입력 토큰 수
            "detected_language": detected_language,
            "has_thread_processed": has_thread,
            "thread_summary_applied": thread_summary_applied,
        }

    def restore_original_keywords(self, generated_text: str, reverse_placeholder_table: Dict[str, str]) -> str:
        """
        LLM이 생성한 텍스트에서 플레이스홀더를 원본 키워드로 복원합니다.
        :param generated_text: LLM이 생성한 텍스트
        :param reverse_placeholder_table: 플레이스홀더 -> 원본 키워드 매핑 테이블
        :return: 원본 키워드가 복원된 텍스트
        """
        restored_text = generated_text
        for placeholder, original_keyword in reverse_placeholder_table.items():
            restored_text = restored_text.replace(placeholder, original_keyword)
        return restored_text


