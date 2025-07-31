import os
import google.generativeai as genai
from typing import Dict, Optional
import json

class ReplyGenerator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(os.getenv("REPLY_MODEL", "gemini-pro"))
        
    async def generate_reply(self, email_content: str, subject: str, 
                           sender: str, context: Dict = {}) -> str:
        """Generate an AI reply to an email"""
        try:
            # Build the prompt with pension info
            system_prompt = self._get_system_prompt(context.get('tone', 'professional'))
            user_prompt = self._build_prompt(email_content, subject, sender, context)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate reply using Gemini
            response = self.model.generate_content(full_prompt)
            reply = response.text.strip()
            
            # Add signature if requested
            if context.get('include_signature', True):
                reply += self._get_signature()
            
            return reply
            
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "안녕하세요. RPA펜션입니다. 문의해 주셔서 감사합니다. 빠른 시일 내에 답변드리겠습니다."
    
    def _build_prompt(self, email_content: str, subject: str, 
                     sender: str, context: Dict) -> str:
        """Build the prompt for reply generation with pension info"""
        
        # 펜션 정보 가져오기
        pension_info = context.get('pension_info', {})
        
        pension_context = ""
        if pension_info:
            pension_context = f"""
펜션 정보 (답변 시 참고):
- 펜션명: RPA펜션
- 위치: {pension_info.get('location', {}).get('address', '경기도 가평군')}
- 체크인: {pension_info.get('checkin_checkout', {}).get('checkin', '오후 3시')}
- 체크아웃: {pension_info.get('checkin_checkout', {}).get('checkout', '오전 11시')}
- 기준인원: {pension_info.get('capacity', {}).get('base', '2')}인, 최대인원: {pension_info.get('capacity', {}).get('max', '4')}인
- 추가인원 요금: {pension_info.get('capacity', {}).get('extra_charge', '1인당 20,000원')}
- 주차: {pension_info.get('parking', {}).get('description', '무료 주차 가능')}
- 시설: {', '.join(pension_info.get('facilities', ['바베큐장', '수영장']))}
- 정책: {', '.join(pension_info.get('policies', ['전 객실 금연', '반려동물 동반 불가']))}
- 취소정책: {pension_info.get('cancellation', {}).get('policy', '3일 전 전액환불, 2일 전 50%, 1일 전 환불불가')}
"""

        prompt = f"""
당신은 RPA펜션의 고객 서비스 담당자입니다. 다음 고객 문의에 대해 친절하고 정확한 답변을 생성해주세요.

고객 문의:
제목: {subject}
발신자: {sender}
내용: {email_content}

{pension_context}

답변 작성 지침:
1. 한국어로 정중하고 친근한 톤으로 답변
2. 고객의 구체적인 질문에 정확한 정보 제공
3. 펜션 정보를 바탕으로 상세하고 도움이 되는 답변 작성
4. 예약이나 추가 문의가 필요한 경우 연락처 안내
5. RPA펜션의 매력적인 특징들을 자연스럽게 언급

답변 형식:
- 인사말로 시작
- 문의 내용에 대한 구체적인 답변
- 추가 정보나 도움이 될 만한 내용
- 마무리 인사 및 연락처 안내
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
        """Generate a reply based on email classification"""
        templates = {
            'urgent': self._get_urgent_template(),
            'support': self._get_support_template(),
            'sales': self._get_sales_template(),
            'general': self._get_general_template(),
            'spam': None  # Don't reply to spam
        }
        
        template = templates.get(classification)
        if not template:
            return await self.generate_reply(email_content, "", "", {})
        
        # Customize template based on email content
        try:
            prompt = f"""You are customizing an email template. Make it specific to the customer's inquiry while maintaining the template structure.

Customize this template based on the customer email:

Template:
{template}

Customer Email:
{email_content}"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
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
            prompt = f"""You are an expert in customer service communication. Analyze the draft reply and suggest improvements.

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
"""
            
            response = self.model.generate_content(prompt)
            analysis = response.text.strip()
            
            return {
                "analysis": analysis,
                "suggestions": self._parse_suggestions(analysis)
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