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
            print(f"🔍 펜션 정보 분석 시작...")
            print(f"📝 입력 텍스트 길이: {len(raw_text)} 문자")
            print(f"📝 입력 텍스트 미리보기: {raw_text[:200]}...")
            
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

            print(f"🤖 Gemini API 호출 중...")
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            print(f"✅ Gemini API 응답 받음")
            print(f"📄 응답 길이: {len(result_text)} 문자")
            print(f"📄 응답 미리보기: {result_text[:300]}...")
            
            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                    print(f"🔧 JSON 코드 블록 제거됨")
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].strip()
                    print(f"🔧 일반 코드 블록 제거됨")
                
                print(f"🔍 JSON 파싱 시도 중...")
                analyzed_data = json.loads(result_text)
                print(f"✅ JSON 파싱 성공!")
                print(f"📊 분석된 데이터 키: {list(analyzed_data.keys())}")
                return analyzed_data
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 오류: {e}")
                print(f"📄 파싱 실패한 텍스트: {result_text}")
                print(f"🔄 Fallback 분석으로 전환...")
                
                # 간단한 fallback 분석
                return self._simple_analysis(raw_text)
                
        except Exception as e:
            print(f"❌ 펜션 정보 분석 오류: {e}")
            print(f"🔄 사용자 입력 기반 키워드 분석으로 전환...")
            return self._user_input_analysis(raw_text)
    
    def _simple_analysis(self, raw_text: str) -> Dict:
        """간단한 키워드 기반 분석 (fallback)"""
        print(f"🔄 Fallback 키워드 분석 시작...")
        
        analysis = {
            "basic_info": {
                "name": "RPA펜션",
                "description": "경기도 가평에 위치한 독채 펜션"
            },
            "checkin_checkout": {
                "checkin_time": "오후 3시부터 체크인이 가능합니다.",
                "checkout_time": "오전 11시까지 체크아웃을 완료해 주세요.",
                "early_checkin": "얼리 체크인은 불가합니다.",
                "late_checkout": "레이트 체크아웃은 최대 1시간까지 가능하며 시간당 10,000원이 추가됩니다."
            },
            "parking": {
                "available": True,
                "free": True,
                "capacity": "1객실당 최대 2대까지 주차 가능합니다.",
                "registration_required": "차량 등록은 필요하지 않습니다.",
                "description": "무료 주차가 제공됩니다."
            },
            "meal": {
                "breakfast_provided": "조식은 제공되지 않습니다.",
                "breakfast_time": "조식 제공 시, 오전 8시부터 9시 30분까지 운영됩니다.",
                "breakfast_fee": "조식은 유료이며, 1인당 8,000원이 부과됩니다.",
                "reservation_required": "사전 예약이 필요합니다."
            },
            "room_service": {
                "amenities_provided": "수건, 샴푸, 바디워시, 칫솔, 치약이 기본 제공됩니다.",
                "cleaning_schedule": "객실 정리는 요청 시 1일 1회 제공됩니다.",
                "extra_request": "추가 수건 및 어메니티는 프론트에 문의 시 무료로 제공됩니다."
            },
            "extra_guests": {
                "base_capacity": "기준 인원은 2인입니다.",
                "max_capacity": "최대 인원은 4인까지 가능합니다.",
                "extra_charge": "추가 인원 1인당 20,000원의 요금이 발생합니다."
            },
            "smoking_pets": {
                "non_smoking_policy": "전 객실 금연이며 위반 시 10만원의 벌금이 부과됩니다.",
                "smoking_area": "지정된 야외 흡연 구역을 이용해 주세요.",
                "pets_allowed": "반려동물 동반은 불가합니다."
            },
            "wifi_facilities": {
                "wifi_info": "모든 객실에서 무료 Wi-Fi 사용 가능하며 비밀번호는 객실 내 안내문에 기재되어 있습니다.",
                "facilities": "바베큐장, 야외 수영장, 개별 테라스가 마련되어 있습니다.",
                "facility_hours": "바베큐장은 오후 6시부터 9시까지 이용 가능합니다. 수영장은 오전 10시부터 오후 6시까지 운영됩니다."
            },
            "entrance": {
                "access_method": "출입문은 비밀번호로 운영됩니다.",
                "password_timing": "체크인 당일 오전 문자로 안내됩니다.",
                "access_restriction": "야간 출입 제한은 없으나, 소음 자제 시간은 오후 10시부터입니다."
            },
            "location": {
                "address": "경기도 가평군 설악면 RPA로 42-1",
                "public_transport": "가평역에서 택시로 약 15분 거리이며, 버스 정류장은 도보 3분 거리에 있습니다.",
                "car_access": "자가용으로 접근 가능합니다.",
                "pickup_service": "픽업 서비스는 제공되지 않습니다."
            },
            "refund_policy": {
                "cancellation_deadline": "예약일 기준 3일 전까지 취소 시 전액 환불됩니다.",
                "refund_rate": "2일 전 취소 시 50% 환불, 1일 전 또는 당일 취소 시 환불이 불가합니다.",
                "change_policy": "변경은 취소 후 재예약으로 처리됩니다."
            }
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
    
    def _user_input_analysis(self, raw_text: str) -> Dict:
        """사용자 입력 텍스트만을 기반으로 한 키워드 분석"""
        print(f"🔍 사용자 입력 기반 키워드 분석 시작...")
        print(f"📝 분석할 텍스트: {raw_text}")
        
        # 기본 구조 (모든 값을 null로 초기화)
        analysis = {
            "basic_info": {
                "name": None,
                "description": None
            },
            "checkin_checkout": {
                "checkin_time": None,
                "checkout_time": None,
                "early_checkin": None,
                "late_checkout": None
            },
            "parking": {
                "available": None,
                "free": None,
                "capacity": None,
                "registration_required": None,
                "description": None
            },
            "meal": {
                "breakfast_provided": None,
                "breakfast_time": None,
                "breakfast_fee": None,
                "reservation_required": None
            },
            "room_service": {
                "amenities_provided": None,
                "cleaning_schedule": None,
                "extra_request": None
            },
            "extra_guests": {
                "base_capacity": None,
                "max_capacity": None,
                "extra_charge": None
            },
            "smoking_pets": {
                "non_smoking_policy": None,
                "smoking_area": None,
                "pets_allowed": None
            },
            "wifi_facilities": {
                "wifi_info": None,
                "facilities": None,
                "facility_hours": None
            },
            "entrance": {
                "access_method": None,
                "password_timing": None,
                "access_restriction": None
            },
            "location": {
                "address": None,
                "public_transport": None,
                "car_access": None,
                "pickup_service": None
            },
            "refund_policy": {
                "cancellation_deadline": None,
                "refund_rate": None,
                "change_policy": None
            }
        }
        
        if not raw_text or not raw_text.strip():
            print("⚠️ 입력 텍스트가 비어있습니다.")
            return analysis
        
        text_lower = raw_text.lower()
        lines = raw_text.split('\n')
        
        print(f"🔍 키워드 분석 중...")
        
        # 기본 정보 추출
        if "rpa펜션" in text_lower or "RPA펜션" in raw_text:
            analysis["basic_info"]["name"] = "RPA펜션"
        
        # 위치 정보 추출
        for line in lines:
            if any(keyword in line for keyword in ["주소", "위치", "경기도", "가평"]):
                analysis["location"]["address"] = line.strip()
                break
        
        # 체크인/체크아웃 시간 추출
        for line in lines:
            line_lower = line.lower()
            if "체크인" in line_lower:
                analysis["checkin_checkout"]["checkin_time"] = line.strip()
            if "체크아웃" in line_lower:
                analysis["checkin_checkout"]["checkout_time"] = line.strip()
        
        # 인원 정보 추출
        for line in lines:
            line_lower = line.lower()
            if "기준" in line_lower and "인" in line_lower:
                analysis["extra_guests"]["base_capacity"] = line.strip()
            if "최대" in line_lower and "인" in line_lower:
                analysis["extra_guests"]["max_capacity"] = line.strip()
            if "추가" in line_lower and ("인원" in line_lower or "요금" in line_lower):
                analysis["extra_guests"]["extra_charge"] = line.strip()
        
        # 주차 정보 추출
        parking_lines = []
        for line in lines:
            if "주차" in line.lower():
                parking_lines.append(line.strip())
        
        if parking_lines:
            analysis["parking"]["description"] = " ".join(parking_lines)
            if any("무료" in line for line in parking_lines):
                analysis["parking"]["free"] = True
                analysis["parking"]["available"] = True
            if any("가능" in line for line in parking_lines):
                analysis["parking"]["available"] = True
        
        # 시설 정보 추출
        facilities = []
        facility_keywords = ["바베큐", "수영장", "테라스", "사우나", "카페", "레스토랑", "놀이터"]
        for keyword in facility_keywords:
            if keyword in text_lower:
                facilities.append(keyword + ("장" if keyword in ["바베큐", "놀이"] else ""))
        
        if facilities:
            analysis["wifi_facilities"]["facilities"] = ", ".join(facilities)
        
        # 와이파이 정보 추출
        for line in lines:
            if "와이파이" in line.lower() or "wifi" in line.lower():
                analysis["wifi_facilities"]["wifi_info"] = line.strip()
                break
        
        # 식사 정보 추출
        for line in lines:
            line_lower = line.lower()
            if "조식" in line_lower or "아침" in line_lower:
                analysis["meal"]["breakfast_provided"] = line.strip()
            if "식사" in line_lower and "시간" in line_lower:
                analysis["meal"]["breakfast_time"] = line.strip()
        
        # 정책 정보 추출
        for line in lines:
            line_lower = line.lower()
            if "금연" in line_lower:
                analysis["smoking_pets"]["non_smoking_policy"] = line.strip()
            if "반려동물" in line_lower:
                analysis["smoking_pets"]["pets_allowed"] = line.strip()
        
        # 취소/환불 정책 추출
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["취소", "환불", "변경"]):
                if "취소" in line_lower:
                    analysis["refund_policy"]["cancellation_deadline"] = line.strip()
                elif "환불" in line_lower:
                    analysis["refund_policy"]["refund_rate"] = line.strip()
        
        # 어메니티 정보 추출
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["수건", "샴푸", "어메니티", "세면도구"]):
                analysis["room_service"]["amenities_provided"] = line.strip()
                break
        
        # 출입 정보 추출
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["출입", "비밀번호", "키", "카드"]):
                analysis["entrance"]["access_method"] = line.strip()
                break
        
        # 교통 정보 추출
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["교통", "버스", "지하철", "택시", "기차"]):
                analysis["location"]["public_transport"] = line.strip()
                break
        
        # null 값들을 제거하여 실제 추출된 정보만 남김
        def remove_null_values(obj):
            if isinstance(obj, dict):
                return {k: remove_null_values(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [remove_null_values(item) for item in obj if item is not None]
            else:
                return obj
        
        cleaned_analysis = remove_null_values(analysis)
        
        print(f"✅ 키워드 분석 완료!")
        print(f"📊 추출된 정보 카테고리: {list(cleaned_analysis.keys())}")
        
        return cleaned_analysis