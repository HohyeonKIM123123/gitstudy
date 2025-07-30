import os
import openai
from typing import Dict, List
import json
import re

class EmailClassifier:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("CLASSIFICATION_MODEL", "gpt-3.5-turbo")
        
    async def classify(self, email_content: str, subject: str = "") -> Dict:
        """Classify email priority and extract tags"""
        try:
            # Build classification prompt
            prompt = self._build_classification_prompt(email_content, subject)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_classification_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_classification_result(result)
            
        except Exception as e:
            print(f"Error classifying email: {e}")
            return self._get_default_classification()
    
    def _build_classification_prompt(self, email_content: str, subject: str) -> str:
        """Build the classification prompt"""
        return f"""
Please classify this customer email:

Subject: {subject}

Content:
{email_content}

Classify the email based on:
1. Priority level (urgent, support, general, sales, spam)
2. Relevant tags (billing, technical, complaint, inquiry, etc.)
3. Confidence level (0.0 to 1.0)

Provide your response in this exact JSON format:
{{
    "priority": "priority_level",
    "tags": ["tag1", "tag2"],
    "confidence": 0.85,
    "reasoning": "Brief explanation"
}}
"""
    
    def _get_classification_system_prompt(self) -> str:
        """Get the system prompt for classification"""
        return """You are an expert email classifier for customer service. Your job is to accurately classify incoming emails based on priority and content.

Priority Levels:
- urgent: Issues requiring immediate attention (service outages, security issues, angry customers, legal matters)
- support: Technical support requests, how-to questions, troubleshooting
- general: General inquiries, information requests, feedback
- sales: Sales inquiries, product questions, pricing requests, demos
- spam: Promotional emails, irrelevant content, suspicious emails

Tags should be specific and relevant (e.g., billing, technical, complaint, refund, feature-request, bug-report, etc.)

Always respond with valid JSON format."""
    
    def _parse_classification_result(self, result: str) -> Dict:
        """Parse the classification result from AI response"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                classification = json.loads(json_str)
                
                # Validate the classification
                return self._validate_classification(classification)
            else:
                # Fallback parsing
                return self._fallback_parse(result)
                
        except json.JSONDecodeError:
            print(f"Failed to parse classification result: {result}")
            return self._get_default_classification()
    
    def _validate_classification(self, classification: Dict) -> Dict:
        """Validate and clean classification result"""
        valid_priorities = ['urgent', 'support', 'general', 'sales', 'spam']
        
        # Ensure priority is valid
        priority = classification.get('priority', 'general').lower()
        if priority not in valid_priorities:
            priority = 'general'
        
        # Ensure tags is a list
        tags = classification.get('tags', [])
        if not isinstance(tags, list):
            tags = []
        
        # Ensure confidence is a float between 0 and 1
        confidence = classification.get('confidence', 0.5)
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5
        
        return {
            'priority': priority,
            'tags': tags[:5],  # Limit to 5 tags
            'confidence': confidence,
            'reasoning': classification.get('reasoning', '')
        }
    
    def _fallback_parse(self, result: str) -> Dict:
        """Fallback parsing when JSON parsing fails"""
        result_lower = result.lower()
        
        # Determine priority based on keywords
        if any(word in result_lower for word in ['urgent', 'emergency', 'critical', 'asap']):
            priority = 'urgent'
        elif any(word in result_lower for word in ['support', 'technical', 'help', 'issue']):
            priority = 'support'
        elif any(word in result_lower for word in ['sales', 'buy', 'purchase', 'price']):
            priority = 'sales'
        elif any(word in result_lower for word in ['spam', 'promotional', 'marketing']):
            priority = 'spam'
        else:
            priority = 'general'
        
        # Extract basic tags
        tags = []
        tag_keywords = {
            'billing': ['bill', 'payment', 'invoice', 'charge'],
            'technical': ['technical', 'bug', 'error', 'not working'],
            'complaint': ['complaint', 'unhappy', 'disappointed', 'angry'],
            'refund': ['refund', 'money back', 'return'],
            'account': ['account', 'login', 'password', 'access']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in result_lower for keyword in keywords):
                tags.append(tag)
        
        return {
            'priority': priority,
            'tags': tags,
            'confidence': 0.6,
            'reasoning': 'Fallback classification based on keywords'
        }
    
    def _get_default_classification(self) -> Dict:
        """Get default classification when all else fails"""
        return {
            'priority': 'general',
            'tags': [],
            'confidence': 0.3,
            'reasoning': 'Default classification due to processing error'
        }
    
    async def batch_classify(self, emails: List[Dict]) -> List[Dict]:
        """Classify multiple emails in batch"""
        results = []
        
        for email in emails:
            classification = await self.classify(
                email.get('body', ''), 
                email.get('subject', '')
            )
            results.append({
                'email_id': email.get('id'),
                'classification': classification
            })
        
        return results
    
    async def get_classification_stats(self, classifications: List[Dict]) -> Dict:
        """Get statistics about classifications"""
        if not classifications:
            return {}
        
        priority_counts = {}
        tag_counts = {}
        total_confidence = 0
        
        for classification in classifications:
            # Count priorities
            priority = classification.get('priority', 'general')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Count tags
            tags = classification.get('tags', [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sum confidence
            total_confidence += classification.get('confidence', 0)
        
        return {
            'total_emails': len(classifications),
            'priority_distribution': priority_counts,
            'top_tags': sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'average_confidence': total_confidence / len(classifications) if classifications else 0
        }
    
    def get_priority_rules(self) -> Dict:
        """Get the rules used for priority classification"""
        return {
            'urgent': {
                'keywords': ['urgent', 'emergency', 'critical', 'asap', 'immediately', 'outage', 'down', 'broken'],
                'description': 'Issues requiring immediate attention'
            },
            'support': {
                'keywords': ['help', 'support', 'technical', 'issue', 'problem', 'bug', 'error', 'not working'],
                'description': 'Technical support and troubleshooting requests'
            },
            'sales': {
                'keywords': ['buy', 'purchase', 'price', 'cost', 'demo', 'trial', 'quote', 'sales'],
                'description': 'Sales inquiries and product questions'
            },
            'general': {
                'keywords': ['question', 'inquiry', 'information', 'feedback', 'suggestion'],
                'description': 'General inquiries and information requests'
            },
            'spam': {
                'keywords': ['promotion', 'offer', 'deal', 'discount', 'marketing', 'unsubscribe'],
                'description': 'Promotional or irrelevant emails'
            }
        }