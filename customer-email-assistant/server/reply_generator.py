import os
import openai
from typing import Dict, Optional
import json

# config.py에서 설정 임포트
from config import Config
# email_processor.py에서 EmailProcessor 임포트
from email_processor import EmailProcessor
# openai_handler.py에서 call_llm_api 임포트
from openai_handler import call_llm_api

class ReplyGenerator:
    def __init__(self):
        # 기존 self.client = openai.OpenAI(...) 대신 call_llm_api를 사용
        # self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = Config.OPENAI_MODEL_NAME # config에서 모델 이름 가져옴
        self.email_processor = EmailProcessor() # EmailProcessor 인스턴스 생성
        
    async def generate_reply(self, email_content: str, subject: str, 
                           sender: str, context: Dict = {}) -> str:
        """Generate an AI reply to an email"""
        try:
            # 1. EmailProcessor를 사용하여 메일 내용 전처리
            print("--- ReplyGenerator: 메일 내용 전처리 시작 ---")
            processed_data = self.email_processor.process_email_for_llm(email_content)
            
            processed_email_content = processed_data["processed_email_content"]
            placeholder_table = processed_data["placeholder_table"]
            reverse_placeholder_table = processed_data["reverse_placeholder_table"]
            detected_language = processed_data["detected_language"]
            
            print(f"--- ReplyGenerator: 전처리 완료. 최종 LLM 입력 토큰 수: {processed_data['final_llm_input_token_count']} ---")

            # 2. 메인 LLM에 전달할 프롬프트 빌드
            # classification은 외부에서 주어지거나, EmailClassifier에서 가져올 수 있음
            # 여기서는 context에서 classification을 가져오거나 기본값 사용
            classification = context.get('classification', 'general') 
            
            prompt = Config.PROMPT_TEMPLATE.format(
                classification=classification,
                email_content=processed_email_content
            )
            
            # 3. LLM 호출을 위한 최대 토큰 수 계산
            # 전체 MAX_TOKENS_FOR_CHATGPT에서 프롬프트 토큰을 제외한 나머지
            prompt_tokens = self.email_processor._count_tokens(prompt)
            max_tokens_to_generate = Config.MAX_TOKENS_FOR_CHATGPT - prompt_tokens
            
            if max_tokens_to_generate < 50: # 최소한의 답변 토큰 보장
                max_tokens_to_generate = 50
                print(f"경고: 답변 생성에 할당된 토큰이 매우 적습니다 ({max_tokens_to_generate}). 프롬프트 길이를 확인하세요.")

            # 4. LLM에 초안 요청
            print("--- ReplyGenerator: LLM에 초안 요청 시작 ---")
            reply = call_llm_api(
                prompt=prompt,
                model_name=self.model,
                max_tokens_to_generate=max_tokens_to_generate,
                temperature=0.7 # 일반적인 답변 생성 온도
            )
            print("--- ReplyGenerator: LLM 응답 수신 완료 ---")
            
            # 5. 생성된 초안에서 플레이스홀더를 원본 키워드로 복원
            final_reply = self.email_processor.restore_original_keywords(reply, reverse_placeholder_table)
            print("--- ReplyGenerator: 개인정보 복원 완료 ---")

            # Add signature if requested
            if context.get('include_signature', True):
                final_reply += self._get_signature()
            
            return final_reply
            
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "Thank you for your email. We have received your message and will respond shortly."
    
    def _build_prompt(self, email_content: str, subject: str, 
                     sender: str, context: Dict) -> str:
        """
        이 함수는 더 이상 직접 사용되지 않고, EmailProcessor와 Config.PROMPT_TEMPLATE에 의해 대체됩니다.
        호환성을 위해 남겨두거나 제거할 수 있습니다.
        """
        prompt = f"""
Please generate a professional reply to the following customer email:

Subject: {subject}
From: {sender}

Email Content:
{email_content}

Context:
- Reply tone: {context.get('tone', 'professional')}
- Customer service context: This is a customer service email that requires a helpful and courteous response
- Keep the reply concise but comprehensive
- Address the customer's concerns directly
- Provide actionable next steps if applicable

Generate a reply that:
1. Acknowledges the customer's email
2. Addresses their specific concerns or questions
3. Provides helpful information or next steps
4. Maintains a {context.get('tone', 'professional')} tone
5. Is concise but complete
"""
        return prompt
    
    def _get_system_prompt(self, tone: str) -> str:
        """Get the system prompt based on tone"""
        base_prompt = """You are a helpful customer service representative. Your job is to generate professional, helpful, and courteous email replies to customer inquiries."""
        
        tone_instructions = {
            'professional': "Maintain a professional and formal tone throughout the response.",
            'friendly': "Use a warm, friendly, and approachable tone while remaining professional.",
            'formal': "Use very formal language and maintain strict business etiquette.",
            'casual': "Use a relaxed, conversational tone while still being helpful and professional."
        }
        
        return f"{base_prompt} {tone_instructions.get(tone, tone_instructions['professional'])}"
    
    def _get_signature(self) -> str:
        """Get email signature"""
        return """

Best regards,
Customer Service Team
[Company Name]
Email: support@company.com
Phone: (555) 123-4567
Website: www.company.com"""
    
    async def generate_classification_reply(self, email_content: str, 
                                          classification: str) -> str:
        """
        Generate a reply based on email classification.
        이 함수는 EmailProcessor와 통합된 generate_reply 함수를 사용하는 것이 좋습니다.
        """
        # 기존 로직 유지 (필요에 따라 generate_reply로 통합 권장)
        templates = {
            'urgent': self._get_urgent_template(),
            'support': self._get_support_template(),
            'sales': self._get_sales_template(),
            'general': self._get_general_template(),
            'spam': None  # Don't reply to spam
        }
        
        template = templates.get(classification)
        if not template:
            # 여기도 EmailProcessor를 거쳐 generate_reply를 호출하도록 변경 가능
            return await self.generate_reply(email_content, "", "", {})
        
        # Customize template based on email content
        try:
            # 기존 self.client 대신 call_llm_api 사용
            response_content = call_llm_api(
                prompt=f"Customize this template based on the customer email:\n\nTemplate:\n{template}\n\nCustomer Email:\n{email_content}",
                model_name=self.model, # Config.OPENAI_MODEL_NAME
                max_tokens_to_generate=300,
                temperature=0.5
            )
            
            return response_content.strip()
            
        except Exception as e:
            print(f"Error customizing template: {e}")
            return template
    
    def _get_urgent_template(self) -> str:
        return """Dear Valued Customer,

Thank you for contacting us. We understand that your inquiry requires immediate attention, and we are prioritizing your request.

We have received your message and our team is working to resolve your issue as quickly as possible. You can expect a detailed response within the next 2-4 hours.

If this is a critical issue affecting your service, please don't hesitate to call our emergency support line at (555) 123-4567.

We appreciate your patience and will update you shortly."""
    
    def _get_support_template(self) -> str:
        return """Dear Customer,

Thank you for reaching out to our technical support team. We have received your inquiry and are here to help resolve your technical issue.

Our support team will review your request and provide you with a detailed solution within 24 hours. In the meantime, you may find our knowledge base helpful at www.company.com/support.

If you have any additional information that might help us resolve your issue faster, please feel free to reply to this email."""
    
    def _get_sales_template(self) -> str:
        return """Dear Prospective Customer,

Thank you for your interest in our products/services. We're excited to help you find the perfect solution for your needs.

Our sales team will review your inquiry and provide you with detailed information, pricing, and next steps within 24 hours. 

In the meantime, feel free to explore our product catalog at www.company.com/products or schedule a demo at your convenience."""
    
    def _get_general_template(self) -> str:
        return """Dear Customer,

Thank you for contacting us. We have received your inquiry and appreciate you taking the time to reach out.

Our team will review your message and provide you with a comprehensive response within 24-48 hours. 

If you have any urgent concerns in the meantime, please don't hesitate to contact us directly."""
    
    async def suggest_improvements(self, original_reply: str, 
                                 email_content: str) -> Dict:
        """Suggest improvements to a draft reply"""
        try:
            # 기존 self.client 대신 call_llm_api 사용
            analysis_content = call_llm_api(
                prompt=f"""
Please analyze this draft reply and suggest improvements:

Original Customer Email:
{email_content}

Draft Reply:
{original_reply}

Please provide:
1. Overall assessment (score 1-10)
2. Specific suggestions for improvement
3. Tone assessment
4. Missing elements (if any)
5. Improved version (if needed)
""",
                model_name=self.model, # Config.OPENAI_MODEL_NAME
                max_tokens_to_generate=600,
                temperature=0.3
            )
            
            return {
                "analysis": analysis_content,
                "suggestions": self._parse_suggestions(analysis_content)
            }
            
        except Exception as e:
            print(f"Error analyzing reply: {e}")
            return {"analysis": "Unable to analyze reply", "suggestions": []}
    
    def _parse_suggestions(self, analysis: str) -> list:
        """Parse suggestions from analysis text"""
        # Simple parsing - in production, you might want more sophisticated parsing
        suggestions = []
        lines = analysis.split('\n')
        
        for line in lines:
            if line.strip().startswith(('•', '-', '*', '1.', '2.', '3.')):
                suggestions.append(line.strip())
        
        return suggestions


