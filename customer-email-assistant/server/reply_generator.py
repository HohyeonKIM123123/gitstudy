import os
import openai
from typing import Dict, Optional
import json

class ReplyGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("REPLY_MODEL", "gpt-4")
        
    async def generate_reply(self, email_content: str, subject: str, 
                           sender: str, context: Dict = {}) -> str:
        """Generate an AI reply to an email"""
        try:
            # Build the prompt
            prompt = self._build_prompt(email_content, subject, sender, context)
            
            # Generate reply using OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(context.get('tone', 'professional'))
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Add signature if requested
            if context.get('include_signature', True):
                reply += self._get_signature()
            
            return reply
            
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "Thank you for your email. We have received your message and will respond shortly."
    
    def _build_prompt(self, email_content: str, subject: str, 
                     sender: str, context: Dict) -> str:
        """Build the prompt for reply generation"""
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are customizing an email template. Make it specific to the customer's inquiry while maintaining the template structure."
                    },
                    {
                        "role": "user",
                        "content": f"Customize this template based on the customer email:\n\nTemplate:\n{template}\n\nCustomer Email:\n{email_content}"
                    }
                ],
                max_tokens=300,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in customer service communication. Analyze the draft reply and suggest improvements."
                    },
                    {
                        "role": "user",
                        "content": f"""
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
                    }
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content.strip()
            
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