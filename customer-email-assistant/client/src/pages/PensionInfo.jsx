import React, { useState, useEffect } from 'react';
import { Save, Wand2, Building, MapPin, Clock, Car, Utensils, Bed, Edit3, Check, X } from 'lucide-react';

const PensionInfo = () => {
  const [pensionInfo, setPensionInfo] = useState('');
  const [analyzedInfo, setAnalyzedInfo] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editableInfo, setEditableInfo] = useState({});
  const [autoSaveTimeout, setAutoSaveTimeout] = useState(null);

  useEffect(() => {
    loadPensionInfo();
  }, []);

  const loadPensionInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/pension-info');
      if (response.ok) {
        const data = await response.json();
        setPensionInfo(data.raw_text || '');
        setAnalyzedInfo(data.analyzed_info || null);
        setLastSaved(data.updated_at ? new Date(data.updated_at) : null);
      }
    } catch (error) {
      console.error('펜션 정보 로드 실패:', error);
    }
  };

  const analyzePensionInfo = async () => {
    if (!pensionInfo.trim()) {
      alert('펜션 정보를 먼저 입력해주세요.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await fetch('http://localhost:8000/pension-info/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pensionInfo })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalyzedInfo(data.analyzed_info);
        setEditableInfo(data.analyzed_info); // 편집 가능한 복사본 생성
      } else {
        alert('정보 분석에 실패했습니다.');
      }
    } catch (error) {
      console.error('정보 분석 실패:', error);
      alert('정보 분석 중 오류가 발생했습니다.');
    }
    setIsAnalyzing(false);
  };

  const startEditing = () => {
    setEditableInfo(JSON.parse(JSON.stringify(analyzedInfo))); // 깊은 복사
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setEditableInfo({});
    setIsEditing(false);
  };

  const saveEditing = () => {
    setAnalyzedInfo(editableInfo);
    setIsEditing(false);
  };

  const updateEditableField = (path, value) => {
    const newInfo = { ...editableInfo };
    const keys = path.split('.');
    let current = newInfo;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    setEditableInfo(newInfo);
  };

  // 자동 저장 함수
  const autoSavePensionInfo = async (textToSave, analyzedToSave = null) => {
    try {
      const response = await fetch('http://localhost:8000/pension-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: textToSave,
          analyzed_info: analyzedToSave || analyzedInfo
        })
      });

      if (response.ok) {
        setLastSaved(new Date());
      }
    } catch (error) {
      console.error('자동 저장 실패:', error);
    }
  };

  // 텍스트 변경 시 자동 저장 (디바운싱)
  const handleTextChange = (newText) => {
    setPensionInfo(newText);
    
    // 기존 타이머 클리어
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
    }
    
    // 2초 후 자동 저장
    const newTimeout = setTimeout(() => {
      autoSavePensionInfo(newText);
    }, 2000);
    
    setAutoSaveTimeout(newTimeout);
  };

  const savePensionInfo = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('http://localhost:8000/pension-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: pensionInfo,
          analyzed_info: analyzedInfo
        })
      });

      if (response.ok) {
        setLastSaved(new Date());
        alert('펜션 정보가 저장되었습니다!');
      } else {
        alert('저장에 실패했습니다.');
      }
    } catch (error) {
      console.error('저장 실패:', error);
      alert('저장 중 오류가 발생했습니다.');
    }
    setIsSaving(false);
  };

  const InfoCard = ({ icon: Icon, title, content, color = "blue" }) => (
    <div className={`bg-${color}-50 border border-${color}-200 rounded-lg p-4`}>
      <div className="flex items-center mb-2">
        <Icon className={`h-5 w-5 text-${color}-600 mr-2`} />
        <h3 className={`font-semibold text-${color}-800`}>{title}</h3>
      </div>
      <p className={`text-${color}-700 text-sm`}>{content}</p>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🏨 RPA펜션 정보 관리</h1>
          <p className="text-gray-600 mt-1">펜션 정보를 입력하면 AI가 자동으로 분석하여 고객 문의에 맞춤 답변을 생성합니다.</p>
        </div>
        {lastSaved && (
          <div className="text-sm text-gray-500">
            마지막 저장: {lastSaved.toLocaleString()}
          </div>
        )}
      </div>

      {/* 정보 입력 섹션 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">펜션 정보 입력</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              펜션 정보 (자유 형식으로 입력하세요)
            </label>
            <textarea
              value={pensionInfo}
              onChange={(e) => handleTextChange(e.target.value)}
              placeholder="RPA펜션 정보를 자유롭게 입력해주세요.

예시:
RPA펜션은 경기도 가평에 위치한 독채 펜션입니다.
- 체크인: 오후 3시, 체크아웃: 오전 11시
- 기준 2인, 최대 4인 (추가 인원 1인당 2만원)
- 무료 주차 2대 가능
- 바베큐장, 수영장 운영
- 전 객실 금연, 반려동물 불가
- 조식 미제공, 어메니티 기본 제공
- 취소: 3일 전 전액환불, 2일 전 50%, 1일 전 환불불가"
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={analyzePensionInfo}
              disabled={isAnalyzing || !pensionInfo.trim()}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Wand2 className="h-4 w-4 mr-2" />
              {isAnalyzing ? 'AI 분석 중...' : 'AI로 정보 분석'}
            </button>

            <button
              onClick={savePensionInfo}
              disabled={isSaving || !pensionInfo.trim()}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? '저장 중...' : '정보 저장'}
            </button>
          </div>
        </div>
      </div>

      {/* AI 분석 결과 */}
      {analyzedInfo && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">🤖 AI 분석 결과</h2>
            <div className="flex items-center space-x-2">
              {isEditing ? (
                <>
                  <button
                    onClick={saveEditing}
                    className="flex items-center px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                  >
                    <Check className="h-4 w-4 mr-1" />
                    저장
                  </button>
                  <button
                    onClick={cancelEditing}
                    className="flex items-center px-3 py-1 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors text-sm"
                  >
                    <X className="h-4 w-4 mr-1" />
                    취소
                  </button>
                </>
              ) : (
                <button
                  onClick={startEditing}
                  className="flex items-center px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  <Edit3 className="h-4 w-4 mr-1" />
                  편집
                </button>
              )}
            </div>
          </div>
          
          {isEditing ? (
            // 편집 모드
            <div className="space-y-6">
              {/* 기본 정보 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-800 mb-3">🏨 기본 정보</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">펜션 이름</label>
                    <input
                      type="text"
                      value={editableInfo.basic_info?.name || ''}
                      onChange={(e) => updateEditableField('basic_info.name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="RPA펜션"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                    <input
                      type="text"
                      value={editableInfo.basic_info?.description || ''}
                      onChange={(e) => updateEditableField('basic_info.description', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="경기도 가평의 독채 펜션"
                    />
                  </div>
                </div>
              </div>

              {/* 체크인/아웃 */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-800 mb-3">🕐 체크인/아웃</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">체크인 시간</label>
                    <input
                      type="text"
                      value={editableInfo.checkin_checkout?.checkin || ''}
                      onChange={(e) => updateEditableField('checkin_checkout.checkin', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                      placeholder="오후 3시"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">체크아웃 시간</label>
                    <input
                      type="text"
                      value={editableInfo.checkin_checkout?.checkout || ''}
                      onChange={(e) => updateEditableField('checkin_checkout.checkout', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                      placeholder="오전 11시"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">정책</label>
                    <input
                      type="text"
                      value={editableInfo.checkin_checkout?.policy || ''}
                      onChange={(e) => updateEditableField('checkin_checkout.policy', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                      placeholder="얼리 체크인 불가"
                    />
                  </div>
                </div>
              </div>

              {/* 수용 인원 */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="font-semibold text-purple-800 mb-3">👥 수용 인원</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">기준 인원</label>
                    <input
                      type="number"
                      value={editableInfo.capacity?.base || ''}
                      onChange={(e) => updateEditableField('capacity.base', parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      placeholder="2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">최대 인원</label>
                    <input
                      type="number"
                      value={editableInfo.capacity?.max || ''}
                      onChange={(e) => updateEditableField('capacity.max', parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      placeholder="4"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">추가 인원 요금</label>
                    <input
                      type="text"
                      value={editableInfo.capacity?.extra_charge || ''}
                      onChange={(e) => updateEditableField('capacity.extra_charge', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      placeholder="1인당 20,000원"
                    />
                  </div>
                </div>
              </div>

              {/* 위치 정보 */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-semibold text-yellow-800 mb-3">📍 위치 정보</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">주소</label>
                    <input
                      type="text"
                      value={editableInfo.location?.address || ''}
                      onChange={(e) => updateEditableField('location.address', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-sm"
                      placeholder="경기도 가평군 설악면 RPA로 42-1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">교통편</label>
                    <input
                      type="text"
                      value={editableInfo.location?.transport || ''}
                      onChange={(e) => updateEditableField('location.transport', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-sm"
                      placeholder="가평역에서 택시 15분"
                    />
                  </div>
                </div>
              </div>

              {/* 주차 정보 */}
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                <h3 className="font-semibold text-indigo-800 mb-3">🚗 주차 정보</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">주차 가능 여부</label>
                    <select
                      value={editableInfo.parking?.available ? 'true' : 'false'}
                      onChange={(e) => updateEditableField('parking.available', e.target.value === 'true')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                    >
                      <option value="true">가능</option>
                      <option value="false">불가능</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">무료 여부</label>
                    <select
                      value={editableInfo.parking?.free ? 'true' : 'false'}
                      onChange={(e) => updateEditableField('parking.free', e.target.value === 'true')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                    >
                      <option value="true">무료</option>
                      <option value="false">유료</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">주차 대수</label>
                    <input
                      type="text"
                      value={editableInfo.parking?.capacity || ''}
                      onChange={(e) => updateEditableField('parking.capacity', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                      placeholder="2대"
                    />
                  </div>
                </div>
              </div>

              {/* 시설 정보 */}
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="font-semibold text-red-800 mb-3">🏢 시설 정보</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">시설 목록 (쉼표로 구분)</label>
                  <input
                    type="text"
                    value={Array.isArray(editableInfo.facilities) ? editableInfo.facilities.join(', ') : (editableInfo.facilities || '')}
                    onChange={(e) => updateEditableField('facilities', e.target.value.split(',').map(f => f.trim()).filter(f => f))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
                    placeholder="바베큐장, 수영장, 테라스"
                  />
                </div>
              </div>

              {/* 정책 */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3">📋 정책 및 규정</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">정책 목록 (쉼표로 구분)</label>
                  <textarea
                    value={Array.isArray(editableInfo.policies) ? editableInfo.policies.join(', ') : (editableInfo.policies || '')}
                    onChange={(e) => updateEditableField('policies', e.target.value.split(',').map(p => p.trim()).filter(p => p))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent text-sm"
                    placeholder="전 객실 금연, 반려동물 동반 불가, 소음 자제"
                    rows={3}
                  />
                </div>
              </div>
            </div>
          ) : (
            // 보기 모드 - RPA펜션 룰북 목차에 맞춘 카드들
            <div className="space-y-6">
              {/* 기본 정보 */}
              {analyzedInfo.basic_info && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <Building className="h-5 w-5 text-blue-600 mr-2" />
                    <h3 className="font-semibold text-blue-800">🏡 기본 정보</h3>
                  </div>
                  <p className="text-blue-700 text-sm">
                    {analyzedInfo.basic_info.name || 'RPA펜션'} - {analyzedInfo.basic_info.description || '펜션 정보'}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* 체크인/체크아웃 */}
                {analyzedInfo.checkin_checkout && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Clock className="h-5 w-5 text-green-600 mr-2" />
                      <h3 className="font-semibold text-green-800">🕒 체크인/체크아웃</h3>
                    </div>
                    <div className="text-green-700 text-sm space-y-1">
                      <div>체크인: {analyzedInfo.checkin_checkout.checkin_time || 'N/A'}</div>
                      <div>체크아웃: {analyzedInfo.checkin_checkout.checkout_time || 'N/A'}</div>
                      {analyzedInfo.checkin_checkout.early_checkin && (
                        <div>얼리체크인: {analyzedInfo.checkin_checkout.early_checkin}</div>
                      )}
                      {analyzedInfo.checkin_checkout.late_checkout && (
                        <div>레이트체크아웃: {analyzedInfo.checkin_checkout.late_checkout}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* 주차 안내 */}
                {analyzedInfo.parking && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Car className="h-5 w-5 text-yellow-600 mr-2" />
                      <h3 className="font-semibold text-yellow-800">🚗 주차 안내</h3>
                    </div>
                    <div className="text-yellow-700 text-sm space-y-1">
                      <div>가능 여부: {analyzedInfo.parking.available ? '가능' : '불가능'}</div>
                      <div>요금: {analyzedInfo.parking.free ? '무료' : '유료'}</div>
                      {analyzedInfo.parking.capacity && <div>주차 대수: {analyzedInfo.parking.capacity}</div>}
                      {analyzedInfo.parking.registration_required && (
                        <div>등록 필요: {analyzedInfo.parking.registration_required}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* 조식/식사 안내 */}
                {analyzedInfo.meal && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Utensils className="h-5 w-5 text-red-600 mr-2" />
                      <h3 className="font-semibold text-red-800">🍽️ 조식/식사 안내</h3>
                    </div>
                    <div className="text-red-700 text-sm space-y-1">
                      <div>조식 제공: {analyzedInfo.meal.breakfast_provided || 'N/A'}</div>
                      {analyzedInfo.meal.breakfast_time && <div>시간: {analyzedInfo.meal.breakfast_time}</div>}
                      {analyzedInfo.meal.breakfast_fee && <div>요금: {analyzedInfo.meal.breakfast_fee}</div>}
                      {analyzedInfo.meal.reservation_required && (
                        <div>예약 필요: {analyzedInfo.meal.reservation_required}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* 룸서비스/어메니티 */}
                {analyzedInfo.room_service && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Bed className="h-5 w-5 text-purple-600 mr-2" />
                      <h3 className="font-semibold text-purple-800">🧼 룸서비스/어메니티</h3>
                    </div>
                    <div className="text-purple-700 text-sm space-y-1">
                      <div>어메니티: {analyzedInfo.room_service.amenities_provided || 'N/A'}</div>
                      <div>청소 주기: {analyzedInfo.room_service.cleaning_schedule || 'N/A'}</div>
                      <div>추가 요청: {analyzedInfo.room_service.extra_request || 'N/A'}</div>
                    </div>
                  </div>
                )}

                {/* 인원 추가/요금 정책 */}
                {analyzedInfo.extra_guests && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Building className="h-5 w-5 text-indigo-600 mr-2" />
                      <h3 className="font-semibold text-indigo-800">🧑‍💼 인원 추가/요금 정책</h3>
                    </div>
                    <div className="text-indigo-700 text-sm space-y-1">
                      <div>기준 인원: {analyzedInfo.extra_guests.base_capacity || 'N/A'}인</div>
                      <div>최대 인원: {analyzedInfo.extra_guests.max_capacity || 'N/A'}인</div>
                      <div>추가 요금: {analyzedInfo.extra_guests.extra_charge || 'N/A'}</div>
                    </div>
                  </div>
                )}

                {/* 흡연/반려동물 */}
                {analyzedInfo.smoking_pets && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Building className="h-5 w-5 text-gray-600 mr-2" />
                      <h3 className="font-semibold text-gray-800">🚭 흡연/반려동물</h3>
                    </div>
                    <div className="text-gray-700 text-sm space-y-1">
                      <div>금연 정책: {analyzedInfo.smoking_pets.non_smoking_policy || 'N/A'}</div>
                      <div>흡연 구역: {analyzedInfo.smoking_pets.smoking_area || 'N/A'}</div>
                      <div>반려동물: {analyzedInfo.smoking_pets.pets_allowed || 'N/A'}</div>
                    </div>
                  </div>
                )}

                {/* 와이파이/편의시설 */}
                {analyzedInfo.wifi_facilities && (
                  <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Building className="h-5 w-5 text-cyan-600 mr-2" />
                      <h3 className="font-semibold text-cyan-800">📶 와이파이/편의시설</h3>
                    </div>
                    <div className="text-cyan-700 text-sm space-y-1">
                      <div>와이파이: {analyzedInfo.wifi_facilities.wifi_info || 'N/A'}</div>
                      <div>시설: {analyzedInfo.wifi_facilities.facilities || 'N/A'}</div>
                      <div>운영시간: {analyzedInfo.wifi_facilities.facility_hours || 'N/A'}</div>
                    </div>
                  </div>
                )}

                {/* 출입 안내 */}
                {analyzedInfo.entrance && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Building className="h-5 w-5 text-orange-600 mr-2" />
                      <h3 className="font-semibold text-orange-800">🔑 출입 안내</h3>
                    </div>
                    <div className="text-orange-700 text-sm space-y-1">
                      <div>출입 방식: {analyzedInfo.entrance.access_method || 'N/A'}</div>
                      <div>비밀번호 발송: {analyzedInfo.entrance.password_timing || 'N/A'}</div>
                      <div>출입 제한: {analyzedInfo.entrance.access_restriction || 'N/A'}</div>
                    </div>
                  </div>
                )}

                {/* 위치/접근 */}
                {analyzedInfo.location && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <MapPin className="h-5 w-5 text-green-600 mr-2" />
                      <h3 className="font-semibold text-green-800">📍 위치/접근</h3>
                    </div>
                    <div className="text-green-700 text-sm space-y-1">
                      <div>주소: {analyzedInfo.location.address || 'N/A'}</div>
                      <div>대중교통: {analyzedInfo.location.public_transport || 'N/A'}</div>
                      <div>자가용: {analyzedInfo.location.car_access || 'N/A'}</div>
                      <div>픽업서비스: {analyzedInfo.location.pickup_service || 'N/A'}</div>
                    </div>
                  </div>
                )}

                {/* 환불/취소 규정 */}
                {analyzedInfo.refund_policy && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <Building className="h-5 w-5 text-red-600 mr-2" />
                      <h3 className="font-semibold text-red-800">❌ 환불/취소 규정</h3>
                    </div>
                    <div className="text-red-700 text-sm space-y-1">
                      <div>취소 기한: {analyzedInfo.refund_policy.cancellation_deadline || 'N/A'}</div>
                      <div>환불 조건: {analyzedInfo.refund_policy.refund_rate || 'N/A'}</div>
                      <div>변경 정책: {analyzedInfo.refund_policy.change_policy || 'N/A'}</div>
                    </div>
                  </div>
                )}
              </div>

              {/* 추가 정보들 (있는 경우에만 표시) */}
              {(analyzedInfo.safety || analyzedInfo.payment || analyzedInfo.nearby) && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 추가 정보</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* 안전/비상시 대처 */}
                    {analyzedInfo.safety && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <h4 className="font-semibold text-red-800 mb-2">🧯 안전/비상시 대처</h4>
                        <div className="text-red-700 text-sm space-y-1">
                          <div>비상장비: {analyzedInfo.safety.emergency_equipment || 'N/A'}</div>
                          <div>응급연락처: {analyzedInfo.safety.emergency_contact || 'N/A'}</div>
                          <div>병원정보: {analyzedInfo.safety.hospital_info || 'N/A'}</div>
                        </div>
                      </div>
                    )}

                    {/* 결제/영수증 */}
                    {analyzedInfo.payment && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h4 className="font-semibold text-green-800 mb-2">💳 결제/영수증</h4>
                        <div className="text-green-700 text-sm space-y-1">
                          <div>결제수단: {analyzedInfo.payment.payment_methods || 'N/A'}</div>
                          <div>현장결제: {analyzedInfo.payment.onsite_payment || 'N/A'}</div>
                          <div>영수증: {analyzedInfo.payment.receipt_available || 'N/A'}</div>
                        </div>
                      </div>
                    )}

                    {/* 주변 관광지/편의시설 */}
                    {analyzedInfo.nearby && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h4 className="font-semibold text-blue-800 mb-2">🧭 주변 정보</h4>
                        <div className="text-blue-700 text-sm space-y-1">
                          <div>관광지: {analyzedInfo.nearby.attractions || 'N/A'}</div>
                          <div>식당: {analyzedInfo.nearby.restaurants || 'N/A'}</div>
                          <div>편의시설: {analyzedInfo.nearby.convenience || 'N/A'}</div>
                          <div>거리: {analyzedInfo.nearby.distances || 'N/A'}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {analyzedInfo.policies && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-800 mb-2">📋 정책 및 규정</h3>
              <div className="text-sm text-gray-700 space-y-1">
                {Array.isArray(analyzedInfo.policies) ? (
                  analyzedInfo.policies.map((policy, index) => (
                    <div key={index}>• {policy}</div>
                  ))
                ) : (
                  <div>{analyzedInfo.policies}</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 사용 안내 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">💡 사용 안내</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• 펜션 정보를 자유롭게 입력하고 "AI로 정보 분석" 버튼을 클릭하세요</li>
          <li>• AI가 입력된 정보를 체크인/아웃, 주차, 시설 등으로 자동 분류합니다</li>
          <li>• 분석된 정보는 고객 문의 답변 생성 시 자동으로 활용됩니다</li>
          <li>• 정보 변경 시 다시 분석하고 저장해주세요</li>
        </ul>
      </div>
    </div>
  );
};

export default PensionInfo;