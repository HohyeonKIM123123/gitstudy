#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import google.generativeai as genai
import json
from typing import Dict, Optional

class PensionAnalyzer:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # 사용 가능한 모델들을 시도
        try:
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        except:
            try:
                self.model = genai.GenerativeModel("gemini-1.5-pro")
            except:
                self.model = genai.GenerativeModel("models/gemini-1.5-flash")
    
    async def analyze_pension_info(self, raw_text: str) -> Dict:
        """펜션 정보 텍스트를 AI로 분석하여 구조화된 데이터로 변환"""
        try:
            prompt = f"""
다음 RPA펜션 정보를 분석하여 룰북 목차에 맞춰 JSON 형태로 구조화해주세요.

펜션 정보:
{raw_text}

🏡 RPA펜션 룰북 목차에 맞춰 다음 형식으로 분석해주세요:

{{
    "basic_info": {{
        "name": "펜션 이름",
        "description": "간단한 설명"
    }},
    "checkin_checkout": {{
        "checkin_time": "체크인 시간",
        "checkout_time": "체크아웃 시간",
        "early_checkin": "얼리 체크인 가능 여부 및 비용",
        "late_checkout": "레이트 체크아웃 가능 여부 및 비용"
    }},
    "parking": {{
        "available": true/false,
        "free": true/false,
        "capacity": "주차 가능 대수",
        "registration_required": "차량 등록 필요 여부",
        "description": "주차 관련 상세 설명"
    }},
    "meal": {{
        "breakfast_provided": "조식 제공 여부",
        "breakfast_time": "조식 시간",
        "breakfast_fee": "조식 요금",
        "reservation_required": "사전 예약 필요 여부"
    }},
    "room_service": {{
        "amenities_provided": "수건/세면도구 제공 여부",
        "cleaning_schedule": "청소 주기",
        "extra_request": "추가 요청 가능 여부"
    }},
    "extra_guests": {{
        "base_capacity": "기준 인원수",
        "max_capacity": "최대 인원수",
        "extra_charge": "1인당 추가 요금"
    }},
    "smoking_pets": {{
        "non_smoking_policy": "금연 정책",
        "smoking_area": "흡연 구역 유무",
        "pets_allowed": "반려동물 동반 가능 여부"
    }},
    "wifi_facilities": {{
        "wifi_info": "와이파이 제공 여부 및 비밀번호",
        "facilities": "바베큐장/수영장 등 부대시설",
        "facility_hours": "부대시설 운영 시간"
    }},
    "entrance": {{
        "access_method": "출입 방식 (비밀번호/카드키 등)",
        "password_timing": "비밀번호 발송 시점",
        "access_restriction": "출입 통제 시간"
    }},
    "location": {{
        "address": "주소",
        "public_transport": "대중교통 접근 방법",
        "car_access": "자가용 접근 방법",
        "pickup_service": "픽업 서비스 여부"
    }},
    "refund_policy": {{
        "cancellation_deadline": "취소 가능 기한",
        "refund_rate": "환불 비율/조건",
        "change_policy": "변경 정책"
    }},
    "safety": {{
        "emergency_equipment": "소화기/비상등 위치",
        "emergency_contact": "응급연락처",
        "hospital_info": "병원 정보"
    }},
    "payment": {{
        "payment_methods": "결제 수단",
        "onsite_payment": "현장 결제 여부",
        "receipt_available": "세금계산서/영수증 발급 가능 여부"
    }},
    "luggage": {{
        "storage_available": "체크인 전후 짐 보관 가능 여부",
        "delivery_service": "택배 수령 가능 여부"
    }},
    "photography": {{
        "photo_zones": "포토존 위치",
        "drone_allowed": "드론 촬영 가능 여부"
    }},
    "noise_party": {{
        "party_allowed": "파티 가능 여부",
        "quiet_hours": "고성방가 금지 시간대"
    }},
    "cleaning": {{
        "mid_cleaning": "중간 청소 가능 여부",
        "extra_supplies": "수건/이불 추가 요청 가능 여부"
    }},
    "children": {{
        "baby_bed": "아기 침대/보조 침대 여부",
        "child_fee": "유아 요금 정책",
        "safety_facilities": "안전 시설"
    }},
    "seasonal": {{
        "heating_cooling": "난방/냉방 관련",
        "seasonal_notes": "계절별 운영 특이사항"
    }},
    "maintenance": {{
        "repair_contact": "고장 시 연락처",
        "response_time": "처리 예상 시간"
    }},
    "nearby": {{
        "attractions": "주변 관광지",
        "restaurants": "추천 식당",
        "convenience": "편의시설 (마트 등)",
        "distances": "거리 안내"
    }}
}}

정보가 없는 항목은 null로 설정하고, 반드시 유효한 JSON 형식으로만 응답해주세요.
"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].strip()
                
                analyzed_data = json.loads(result_text)
                return analyzed_data
                
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 텍스트: {result_text}")
                
                # 간단한 fallback 분석
                return self._simple_analysis(raw_text)
                
        except Exception as e:
            print(f"펜션 정보 분석 오류: {e}")
            return self._simple_analysis(raw_text)
    
    def _simple_analysis(self, raw_text: str) -> Dict:
        """간단한 키워드 기반 분석 (fallback)"""
        analysis = {
            "basic_info": {
                "name": "RPA펜션",
                "description": "펜션 정보"
            },
            "location": {"address": None, "description": None, "transport": None},
            "checkin_checkout": {"checkin": None, "checkout": None, "policy": None},
            "capacity": {"base": None, "max": None, "extra_charge": None},
            "parking": {"available": None, "free": None, "capacity": None, "description": None},
            "facilities": [],
            "meal": {"breakfast": None, "description": None},
            "policies": [],
            "amenities": [],
            "cancellation": {"policy": None},
            "contact": {"phone": None, "email": None}
        }
        
        text_lower = raw_text.lower()
        
        # 체크인/아웃 시간 추출
        if "체크인" in text_lower:
            if "3시" in text_lower or "15시" in text_lower:
                analysis["checkin_checkout"]["checkin"] = "오후 3시"
        if "체크아웃" in text_lower:
            if "11시" in text_lower:
                analysis["checkin_checkout"]["checkout"] = "오전 11시"
        
        # 인원 정보 추출
        if "기준" in text_lower and "인" in text_lower:
            if "2인" in text_lower:
                analysis["capacity"]["base"] = 2
        if "최대" in text_lower and "인" in text_lower:
            if "4인" in text_lower:
                analysis["capacity"]["max"] = 4
        
        # 주차 정보
        if "주차" in text_lower:
            analysis["parking"]["available"] = True
            if "무료" in text_lower:
                analysis["parking"]["free"] = True
        
        # 시설 정보
        facilities = []
        if "바베큐" in text_lower:
            facilities.append("바베큐장")
        if "수영장" in text_lower:
            facilities.append("수영장")
        if "테라스" in text_lower:
            facilities.append("테라스")
        analysis["facilities"] = facilities
        
        # 정책 정보
        policies = []
        if "금연" in text_lower:
            policies.append("전 객실 금연")
        if "반려동물" in text_lower and "불가" in text_lower:
            policies.append("반려동물 동반 불가")
        analysis["policies"] = policies
        
        return analysis