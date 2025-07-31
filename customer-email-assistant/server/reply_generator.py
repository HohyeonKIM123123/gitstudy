import os
import google.generativeai as genai
from typing import Dict, Optional
import json

# OpenAI 라이브러리를 안전하게 import (0.28.1 버전)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI 라이브러리가 설치되지 않았습니다. pip install openai로 설치하세요.")
    OPENAI_AVAILABLE = False

class ReplyGenerator:
    def __init__(self):
        # Gemini API 설정
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(os.getenv("REPLY_MODEL", "gemini-pro"))
        
        # OpenAI API 설정 (0.28.1 버전)
        if OPENAI_AVAILABLE:
            try:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if openai_api_key:
                    openai.api_key = openai_api_key
                    print("✅ OpenAI API 키 설정 성공")
                else:
                    print("⚠️ OpenAI API 키가 없습니다. Fallback만 사용됩니다.")
            except Exception as e:
                print(f"❌ OpenAI API 키 설정 실패: {e}")
        else:
            print("⚠️ OpenAI 라이브러리가 설치되지 않았습니다. Gemini와 Fallback만 사용됩니다.")
        
    async def generate_reply(self, email_content: str, subject: str, 
                           sender: str, context: Dict = {}) -> str:
        """Generate an AI reply to an email"""
        try:
            # 응답 설정 가져오기
            response_settings = context.get('response_settings', {})
            
            # Build comprehensive prompt with both pension info and response settings
            full_prompt = self._build_comprehensive_prompt(email_content, subject, sender, context, response_settings)
            
            print(f"🤖 AI 프롬프트 (처음 500자): {full_prompt[:500]}...")
            
            # Generate reply using Gemini
            response = self.model.generate_content(full_prompt)
            reply = response.text.strip()
            
            print(f"🤖 AI 원본 응답: {reply}")
            
            # 응답 설정에 따라 후처리
            reply = self._apply_response_settings(reply, response_settings)
            
            print(f"🤖 최종 응답: {reply}")
            
            return reply
            
        except Exception as e:
            print(f"❌ Gemini API 오류: {e}")
            print(f"🔄 OpenAI API로 전환 시도...")
            
            # OpenAI API로 재시도
            try:
                response_settings = context.get('response_settings', {})
                full_prompt = self._build_comprehensive_prompt(email_content, subject, sender, context, response_settings)
                
                print(f"🤖 OpenAI API 호출 중...")
                
                if OPENAI_AVAILABLE and openai.api_key:
                    openai_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "당신은 RPA펜션의 전문 고객 서비스 담당자입니다. 한국어로 친절하고 정확한 답변을 제공하세요."},
                            {"role": "user", "content": full_prompt}
                        ],
                        max_tokens=800,
                        temperature=0.7
                    )
                    
                    reply = openai_response.choices[0].message.content.strip()
                    print(f"✅ OpenAI 응답 생성 성공: {reply[:100]}...")
                else:
                    raise Exception("OpenAI API 키가 설정되지 않았습니다.")
                
                # 응답 설정에 따라 후처리
                reply = self._apply_response_settings(reply, response_settings)
                
                return reply
                
            except Exception as openai_error:
                print(f"❌ OpenAI API도 실패: {openai_error}")
                print(f"🔄 Fallback 응답으로 전환...")
                # 모든 AI API가 실패한 경우 fallback 응답 생성
                return self._generate_fallback_response(email_content, subject, sender, context)
    
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
    
    def _build_comprehensive_prompt(self, email_content: str, subject: str, 
                                  sender: str, context: Dict, response_settings: Dict) -> str:
        """Build comprehensive prompt with both pension info and response settings"""
        
        # 펜션 정보 가져오기
        pension_info = context.get('pension_info', {})
        
        # 응답 설정 가져오기 (새로운 구조 지원)
        tone = response_settings.get('tone', 'friendly')
        structure = response_settings.get('structure', ['greeting', 'answer', 'additional', 'closing'])
        include_emoji = response_settings.get('includeEmoji', True)
        personal_touch = response_settings.get('personalTouch', True)
        custom_instructions = response_settings.get('customInstructions', '')
        greeting = response_settings.get('greeting', '안녕하세요! RPA펜션입니다 😊')
        closing = response_settings.get('closing', '감사합니다. 좋은 하루 되세요!')
        
        # 톤 커스터마이징 설정
        tone_customization = response_settings.get('toneCustomization', {})
        formality = tone_customization.get('formality', 50)  # 0-100
        length_level = tone_customization.get('length', 50)  # 0-100
        emoji_freq = tone_customization.get('emojiFreq', 70)  # 0-100
        
        # 펜션 정보 컨텍스트 구성
        pension_context = ""
        if pension_info:
            # 펜션 정보를 더 자세히 파싱
            location_info = pension_info.get('location', {})
            checkin_info = pension_info.get('checkin_checkout', {})
            capacity_info = pension_info.get('capacity', {})
            parking_info = pension_info.get('parking', {})
            meal_info = pension_info.get('meal', {})
            facilities_info = pension_info.get('wifi_facilities', {})
            
            pension_context = f"""
=== RPA펜션 상세 정보 ===
📍 위치 및 접근:
- 주소: {location_info.get('address', '경기도 가평군 설악면 RPA로 42-1')}
- 대중교통: {location_info.get('public_transport', '가평역에서 택시로 약 15분')}

🕐 체크인/체크아웃:
- 체크인: {checkin_info.get('checkin_time', '오후 3시부터 체크인 가능')}
- 체크아웃: {checkin_info.get('checkout_time', '오전 11시까지 체크아웃')}
- 정책: {checkin_info.get('early_late_policy', '얼리 체크인 불가, 레이트 체크아웃 최대 1시간 가능')}

👥 수용 인원 및 요금:
- 기준 인원: {capacity_info.get('base_capacity', '2인')}
- 최대 인원: {capacity_info.get('max_capacity', '4인')}
- 추가 인원 요금: {capacity_info.get('extra_charge', '1인당 20,000원')}

🚗 주차 안내:
- 주차 가능: {parking_info.get('is_free', '무료 주차 제공')}
- 주차 대수: {parking_info.get('car_limit', '1객실당 최대 2대')}
- 등록 필요: {parking_info.get('registration_required', '차량 등록 불필요')}

🍽️ 식사 안내:
- 조식 제공: {meal_info.get('breakfast_provided', '조식 제공되지 않음')}
- 조식 시간: {meal_info.get('breakfast_time', '오전 8시-9시 30분')}
- 조식 요금: {meal_info.get('extra_fee', '1인당 8,000원')}

🏢 시설 및 편의사항:
- 와이파이: {facilities_info.get('wifi_info', '전 객실 무료 Wi-Fi')}
- 주요 시설: {facilities_info.get('facilities', '바베큐장, 야외 수영장, 개별 테라스')}
- 운영 시간: {facilities_info.get('facility_hours', '바베큐장 18:00-21:00, 수영장 10:00-18:00')}

🚭 정책:
- 금연 정책: {pension_info.get('smoking_pets', {}).get('non_smoking_policy', '전 객실 금연')}
- 반려동물: {pension_info.get('smoking_pets', {}).get('pets_allowed', '반려동물 동반 불가')}

💰 취소/환불 정책:
- 취소 규정: {pension_info.get('refund_policy', {}).get('cancellation_deadline', '3일 전 전액환불, 2일 전 50%, 1일 전 환불불가')}
"""
        
        # 말투 설정
        tone_instructions = {
            'friendly': "친근하고 따뜻한 말투로 답변하세요. 고객이 편안함을 느낄 수 있도록 친구처럼 대화하되 예의는 지켜주세요.",
            'formal': "정중하고 격식있는 말투로 답변하세요. 존댓말을 사용하고 전문적인 어조를 유지해주세요.",
            'casual': "편안하고 자연스러운 말투로 답변하세요. 부담스럽지 않게 대화하되 도움이 되는 정보를 제공해주세요."
        }
        
        # 새로운 응답 구조 설정 (배열 기반)
        structure_map = {
            'greeting': '인사말',
            'answer': '핵심답변', 
            'additional': '추가안내',
            'closing': '마무리'
        }
        
        if isinstance(structure, list):
            structure_text = " → ".join([structure_map.get(block, block) for block in structure])
            structure_instruction = f"다음 순서로 답변을 구성하세요: {structure_text}"
        else:
            # 기존 문자열 구조 지원 (하위 호환성)
            structure_instructions = {
                'greeting_answer_additional_closing': "1) 설정된 인사말로 시작 2) 고객 질문에 대한 구체적 답변 3) 추가 도움이 될 정보나 팁 제공 4) 설정된 마무리 인사로 끝",
                'greeting_answer_closing': "1) 설정된 인사말로 시작 2) 고객 질문에 대한 구체적 답변 3) 설정된 마무리 인사로 끝",
                'answer_additional_closing': "1) 고객 질문에 대한 구체적 답변 2) 추가 도움이 될 정보나 팁 제공 3) 설정된 마무리 인사로 끝"
            }
            structure_instruction = structure_instructions.get(structure, structure_instructions['greeting_answer_additional_closing'])
        
        # 톤 커스터마이징을 반영한 길이 설정
        if length_level <= 30:
            length_instruction = "간결하게 1-2문장으로 핵심만 답변하세요."
        elif length_level <= 70:
            length_instruction = "적당한 길이로 3-4문장 정도로 답변하세요."
        else:
            length_instruction = "자세하게 5문장 이상으로 상세한 설명과 함께 답변하세요."
        
        # 공손함 레벨 반영
        if formality <= 30:
            formality_instruction = "편안하고 캐주얼한 말투를 사용하세요. 반말은 사용하지 말되 친근하게 대화하세요."
        elif formality <= 70:
            formality_instruction = "적당히 정중하면서도 친근한 말투를 사용하세요."
        else:
            formality_instruction = "매우 정중하고 격식있는 말투를 사용하세요. 높임말을 철저히 지켜주세요."
        
        # 이모지 빈도 반영
        if emoji_freq <= 30:
            emoji_instruction = "이모지는 거의 사용하지 마세요."
        elif emoji_freq <= 70:
            emoji_instruction = "적절한 이모지를 1-2개 정도 사용하세요."
        else:
            emoji_instruction = "다양한 이모지를 활용하여 친근하고 생동감 있게 표현하세요."
        
        # 추가 옵션
        additional_instructions = []
        if include_emoji:
            additional_instructions.append("적절한 이모지를 사용하여 답변을 더 친근하게 만드세요.")
        if personal_touch:
            additional_instructions.append("고객의 상황에 맞는 개인적인 멘트나 조언을 추가하세요.")
        
        # 추가 옵션
        additional_instructions = []
        if include_emoji:
            additional_instructions.append(emoji_instruction)
        if personal_touch:
            additional_instructions.append("고객의 상황에 맞는 개인적인 멘트나 조언을 추가하세요.")
        
        # 통합 프롬프트 구성
        comprehensive_prompt = f"""당신은 RPA펜션의 전문 고객 서비스 담당자입니다. 아래 펜션 정보를 정확히 활용하여 고객 문의에 답변해주세요.

{pension_context}

=== 고객 문의 ===
제목: {subject}
발신자: {sender}
문의 내용: {email_content}

=== 응답 지침 ===
말투: {tone_instructions.get(tone, tone_instructions['friendly'])}
공손함 레벨: {formality_instruction}
구조: {structure_instruction}
길이: {length_instruction}

추가 지침:
{chr(10).join(additional_instructions)}

사용자 정의 지시사항:
{custom_instructions}

설정된 인사말: "{greeting}"
설정된 마무리 인사: "{closing}"

=== 중요 사항 ===
1. 위의 펜션 정보를 정확히 활용하여 구체적으로 답변하세요
2. 고객의 질문에 직접적으로 답변하되, 관련된 추가 정보도 제공하세요
3. 예약이나 추가 문의가 필요한 경우 연락 방법을 안내하세요
4. RPA펜션의 매력적인 특징을 자연스럽게 언급하세요
5. 설정된 인사말과 마무리 인사를 적절히 활용하세요

지금 답변을 생성해주세요:"""
        
        return comprehensive_prompt
    
    def _get_system_prompt_with_settings(self, response_settings: Dict) -> str:
        """Get the system prompt with response settings applied"""
        tone = response_settings.get('tone', 'friendly')
        structure = response_settings.get('structure', 'greeting_answer_additional_closing')
        response_length = response_settings.get('responseLength', 'medium')
        include_emoji = response_settings.get('includeEmoji', True)
        personal_touch = response_settings.get('personalTouch', True)
        custom_instructions = response_settings.get('customInstructions', '')
        
        base_prompt = """당신은 RPA펜션의 고객 서비스 담당자입니다. 고객 문의에 대해 정확하고 도움이 되는 답변을 생성해주세요."""
        
        # 말투 설정
        tone_instructions = {
            'friendly': "친근하고 따뜻한 말투로 답변하세요. 고객이 편안함을 느낄 수 있도록 친구처럼 대화하되 예의는 지켜주세요.",
            'formal': "정중하고 격식있는 말투로 답변하세요. 존댓말을 사용하고 전문적인 어조를 유지해주세요.",
            'casual': "편안하고 자연스러운 말투로 답변하세요. 부담스럽지 않게 대화하되 도움이 되는 정보를 제공해주세요."
        }
        
        # 응답 구조 설정
        structure_instructions = {
            'greeting_answer_additional_closing': "다음 구조로 답변하세요: 1) 인사말 2) 질문에 대한 답변 3) 추가 도움이 될 정보 4) 마무리 인사",
            'greeting_answer_closing': "다음 구조로 답변하세요: 1) 인사말 2) 질문에 대한 답변 3) 마무리 인사",
            'answer_additional_closing': "다음 구조로 답변하세요: 1) 질문에 대한 답변 2) 추가 도움이 될 정보 3) 마무리 인사",
            'custom': f"사용자 정의 지시사항을 따라 답변하세요: {custom_instructions}"
        }
        
        # 응답 길이 설정
        length_instructions = {
            'short': "간결하게 1-2문장으로 핵심만 답변하세요.",
            'medium': "적당한 길이로 3-4문장 정도로 답변하세요.",
            'long': "자세하게 5문장 이상으로 상세한 설명과 함께 답변하세요."
        }
        
        # 추가 옵션
        additional_instructions = []
        if include_emoji:
            additional_instructions.append("적절한 이모지를 사용하여 답변을 더 친근하게 만드세요.")
        if personal_touch:
            additional_instructions.append("고객의 상황에 맞는 개인적인 멘트나 조언을 추가하세요.")
        
        # 전체 프롬프트 구성
        full_prompt = f"""{base_prompt}

말투: {tone_instructions.get(tone, tone_instructions['friendly'])}

구조: {structure_instructions.get(structure, structure_instructions['greeting_answer_additional_closing'])}

길이: {length_instructions.get(response_length, length_instructions['medium'])}

추가 지침:
{chr(10).join(additional_instructions)}

사용자 정의 지시사항:
{custom_instructions}
"""
        
        return full_prompt
    
    def _apply_response_settings(self, reply: str, response_settings: Dict) -> str:
        """Apply response settings to the generated reply"""
        greeting = response_settings.get('greeting', '')
        closing = response_settings.get('closing', '')
        
        # 인사말과 마무리 인사가 설정되어 있고, 응답에 포함되지 않은 경우 추가
        if greeting and not any(greet in reply for greet in [greeting[:10], "안녕하세요"]):
            reply = f"{greeting}\n\n{reply}"
        
        if closing and not any(close in reply for close in [closing[:10], "감사합니다", "좋은 하루"]):
            reply = f"{reply}\n\n{closing}"
        
        return reply
    
    def _get_system_prompt(self, tone: str) -> str:
        """Get the system prompt based on tone (legacy method)"""
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
    
    def _generate_fallback_response(self, email_content: str, subject: str, 
                                  sender: str, context: Dict) -> str:
        """Generate fallback response when Gemini API is unavailable"""
        print(f"🔄 Fallback 응답 생성 중...")
        
        # 응답 설정과 펜션 정보 가져오기
        response_settings = context.get('response_settings', {})
        pension_info = context.get('pension_info', {})
        
        greeting = response_settings.get('greeting', '안녕하세요! RPA펜션입니다 😊')
        closing = response_settings.get('closing', '감사합니다. 좋은 하루 되세요!')
        
        # 이메일 내용을 분석하여 키워드 기반 응답 생성
        email_lower = email_content.lower()
        subject_lower = subject.lower()
        
        response_parts = [greeting]
        
        # 주차 관련 문의
        if any(keyword in email_lower or keyword in subject_lower for keyword in ['주차', '차', '자동차', '주차장']):
            if pension_info.get('parking'):
                parking_info = pension_info['parking']
                response_parts.append(f"주차 관련 문의해 주셔서 감사합니다. {parking_info.get('is_free', '무료 주차가 제공됩니다.')} {parking_info.get('car_limit', '1객실당 최대 2대까지 주차 가능합니다.')} {parking_info.get('registration_required', '차량 등록은 필요하지 않습니다.')}")
            else:
                response_parts.append("주차 관련 문의해 주셔서 감사합니다. 저희 RPA펜션은 무료 주차가 가능하며, 자세한 사항은 별도로 안내드리겠습니다.")
        
        # 체크인/체크아웃 관련 문의
        elif any(keyword in email_lower or keyword in subject_lower for keyword in ['체크인', '체크아웃', '입실', '퇴실', '시간']):
            if pension_info.get('checkin_checkout'):
                checkin_info = pension_info['checkin_checkout']
                response_parts.append(f"체크인/체크아웃 관련 문의해 주셔서 감사합니다. {checkin_info.get('checkin_time', '체크인은 오후 3시부터 가능합니다.')} {checkin_info.get('checkout_time', '체크아웃은 오전 11시까지 완료해 주시면 됩니다.')}")
            else:
                response_parts.append("체크인/체크아웃 관련 문의해 주셔서 감사합니다. 체크인은 오후 3시, 체크아웃은 오전 11시입니다.")
        
        # 인원/요금 관련 문의
        elif any(keyword in email_lower or keyword in subject_lower for keyword in ['인원', '사람', '요금', '가격', '비용']):
            if pension_info.get('extra_guests'):
                capacity_info = pension_info['extra_guests']
                response_parts.append(f"인원 및 요금 관련 문의해 주셔서 감사합니다. {capacity_info.get('base_capacity', '기준 인원은 2인입니다.')} {capacity_info.get('max_capacity', '최대 인원은 4인까지 가능합니다.')} {capacity_info.get('extra_charge', '추가 인원 1인당 20,000원의 요금이 발생합니다.')}")
            else:
                response_parts.append("인원 및 요금 관련 문의해 주셔서 감사합니다. 기준 2인, 최대 4인까지 가능하며 추가 인원 시 별도 요금이 발생합니다.")
        
        # 시설 관련 문의
        elif any(keyword in email_lower or keyword in subject_lower for keyword in ['시설', '바베큐', '수영장', '와이파이', 'wifi']):
            if pension_info.get('wifi_facilities'):
                facilities_info = pension_info['wifi_facilities']
                response_parts.append(f"시설 관련 문의해 주셔서 감사합니다. {facilities_info.get('wifi_info', '모든 객실에서 무료 Wi-Fi를 사용하실 수 있습니다.')} {facilities_info.get('facilities', '바베큐장, 야외 수영장, 개별 테라스가 마련되어 있습니다.')} {facilities_info.get('facility_hours', '시설 운영 시간은 별도로 안내드리겠습니다.')}")
            else:
                response_parts.append("시설 관련 문의해 주셔서 감사합니다. 저희 펜션에는 바베큐장, 수영장 등 다양한 시설이 준비되어 있습니다.")
        
        # 조식/식사 관련 문의
        elif any(keyword in email_lower or keyword in subject_lower for keyword in ['조식', '아침', '식사', '밥']):
            if pension_info.get('meal'):
                meal_info = pension_info['meal']
                response_parts.append(f"식사 관련 문의해 주셔서 감사합니다. {meal_info.get('breakfast_provided', '조식 제공 여부를 안내드리겠습니다.')} {meal_info.get('breakfast_time', '')} {meal_info.get('extra_fee', '')}")
            else:
                response_parts.append("식사 관련 문의해 주셔서 감사합니다. 조식 및 식사 관련 자세한 사항은 별도로 안내드리겠습니다.")
        
        # 취소/환불 관련 문의
        elif any(keyword in email_lower or keyword in subject_lower for keyword in ['취소', '환불', '변경', '캔슬']):
            if pension_info.get('refund_policy'):
                refund_info = pension_info['refund_policy']
                response_parts.append(f"취소/환불 관련 문의해 주셔서 감사합니다. {refund_info.get('cancellation_deadline', '취소 정책을 안내드리겠습니다.')} {refund_info.get('refund_rate', '')}")
            else:
                response_parts.append("취소/환불 관련 문의해 주셔서 감사합니다. 취소 정책에 대해 자세히 안내드리겠습니다.")
        
        # 일반적인 문의
        else:
            response_parts.append("문의해 주셔서 감사합니다. 고객님의 문의사항에 대해 정확한 정보를 확인하여 빠른 시일 내에 답변드리겠습니다.")
            
            # 펜션 기본 정보 추가
            if pension_info.get('location', {}).get('address'):
                response_parts.append(f"저희 RPA펜션은 {pension_info['location']['address']}에 위치해 있습니다.")
        
        # 추가 안내 메시지
        response_parts.append("추가 문의사항이 있으시거나 더 자세한 정보가 필요하시면 언제든 연락 주세요.")
        response_parts.append(closing)
        
        fallback_response = "\n\n".join(response_parts)
        
        print(f"✅ Fallback 응답 생성 완료: {fallback_response[:100]}...")
        
        return fallback_response