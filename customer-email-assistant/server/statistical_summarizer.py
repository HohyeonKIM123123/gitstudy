import re
from collections import Counter
from typing import List
from konlpy.tag import Okt # pip install konlpy, JVM 설치 필요
import tiktoken
from config import Config # config.py에서 설정 임포트

class StatisticalSummarizer:
    def __init__(self, tokenizer_name: str = "Okt", openai_model_name: str = Config.OPENAI_MODEL_NAME):
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


