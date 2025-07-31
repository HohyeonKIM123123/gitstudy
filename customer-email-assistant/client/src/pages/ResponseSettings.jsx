import React, { useState, useEffect } from 'react';
import { Save, MessageSquare, Wand2, Eye, EyeOff } from 'lucide-react';

const ResponseSettings = () => {
  const [settings, setSettings] = useState({
    greeting: '안녕하세요! RPA펜션입니다 😊',
    closing: '감사합니다. 좋은 하루 되세요!',
    tone: 'friendly', // friendly, formal, casual
    structure: 'greeting_answer_additional_closing',
    customInstructions: '',
    responseLength: 'medium', // short, medium, long
    includeEmoji: true,
    personalTouch: true
  });
  
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [previewExample, setPreviewExample] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [autoSaveTimeout, setAutoSaveTimeout] = useState(null);

  useEffect(() => {
    loadResponseSettings();
  }, []);

  const loadResponseSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/response-settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings || settings);
        setLastSaved(data.updated_at ? new Date(data.updated_at) : null);
      }
    } catch (error) {
      console.error('응답 설정 로드 실패:', error);
    }
  };

  // 자동 저장 함수
  const autoSaveSettings = async (newSettings) => {
    try {
      const response = await fetch('http://localhost:8000/response-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: newSettings })
      });

      if (response.ok) {
        setLastSaved(new Date());
      }
    } catch (error) {
      console.error('자동 저장 실패:', error);
    }
  };

  // 설정 변경 시 자동 저장 (디바운싱)
  const handleSettingChange = (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    
    // 기존 타이머 클리어
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
    }
    
    // 2초 후 자동 저장
    const newTimeout = setTimeout(() => {
      autoSaveSettings(newSettings);
    }, 2000);
    
    setAutoSaveTimeout(newTimeout);
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('http://localhost:8000/response-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings })
      });

      if (response.ok) {
        setLastSaved(new Date());
        alert('응답 설정이 저장되었습니다!');
      } else {
        alert('저장에 실패했습니다.');
      }
    } catch (error) {
      console.error('저장 실패:', error);
      alert('저장 중 오류가 발생했습니다.');
    }
    setIsSaving(false);
  };

  const generatePreview = async () => {
    setIsPreviewMode(true);
    try {
      const response = await fetch('http://localhost:8000/response-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          settings,
          sampleQuery: "체크인 시간과 주차 가능 여부를 알고 싶습니다."
        })
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewExample(data.preview);
      } else {
        setPreviewExample('미리보기 생성에 실패했습니다.');
      }
    } catch (error) {
      console.error('미리보기 생성 실패:', error);
      setPreviewExample('미리보기 생성 중 오류가 발생했습니다.');
    }
  };

  const toneOptions = [
    { value: 'friendly', label: '친근하고 따뜻한 톤', description: '😊 친구처럼 편안하고 따뜻한 말투' },
    { value: 'formal', label: '정중하고 격식있는 톤', description: '🎩 예의바르고 전문적인 말투' },
    { value: 'casual', label: '편안하고 자연스러운 톤', description: '😎 부담없고 자연스러운 말투' }
  ];

  const structureOptions = [
    { 
      value: 'greeting_answer_additional_closing', 
      label: '인사 → 답변 → 추가정보 → 마무리',
      description: '가장 일반적인 구조'
    },
    { 
      value: 'greeting_answer_closing', 
      label: '인사 → 답변 → 마무리',
      description: '간결한 구조'
    },
    { 
      value: 'answer_additional_closing', 
      label: '답변 → 추가정보 → 마무리',
      description: '바로 본론으로 들어가는 구조'
    },
    { 
      value: 'custom', 
      label: '사용자 정의',
      description: '아래 사용자 정의 지시사항 사용'
    }
  ];

  const lengthOptions = [
    { value: 'short', label: '간결하게 (1-2문장)', description: '핵심만 간단히' },
    { value: 'medium', label: '적당하게 (3-4문장)', description: '적절한 길이로' },
    { value: 'long', label: '자세하게 (5문장 이상)', description: '상세한 설명과 함께' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🤖 AI 응답 구조 설정</h1>
          <p className="text-gray-600 mt-1">재미나이가 고객 이메일에 응답할 때 사용할 말투와 구조를 설정하세요.</p>
        </div>
        {lastSaved && (
          <div className="text-sm text-gray-500">
            마지막 저장: {lastSaved.toLocaleString()}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 설정 패널 */}
        <div className="space-y-6">
          {/* 기본 인사말 설정 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">👋 인사말 설정</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  첫 인사말
                </label>
                <input
                  type="text"
                  value={settings.greeting}
                  onChange={(e) => handleSettingChange('greeting', e.target.value)}
                  placeholder="안녕하세요! RPA펜션입니다 😊"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  마무리 인사말
                </label>
                <input
                  type="text"
                  value={settings.closing}
                  onChange={(e) => handleSettingChange('closing', e.target.value)}
                  placeholder="감사합니다. 좋은 하루 되세요!"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* 말투 설정 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">🗣️ 말투 설정</h2>
            
            <div className="space-y-3">
              {toneOptions.map((option) => (
                <label key={option.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="tone"
                    value={option.value}
                    checked={settings.tone === option.value}
                    onChange={(e) => handleSettingChange('tone', e.target.value)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 응답 구조 설정 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">📝 응답 구조</h2>
            
            <div className="space-y-3">
              {structureOptions.map((option) => (
                <label key={option.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="structure"
                    value={option.value}
                    checked={settings.structure === option.value}
                    onChange={(e) => handleSettingChange('structure', e.target.value)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 응답 길이 설정 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">📏 응답 길이</h2>
            
            <div className="space-y-3">
              {lengthOptions.map((option) => (
                <label key={option.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="responseLength"
                    value={option.value}
                    checked={settings.responseLength === option.value}
                    onChange={(e) => handleSettingChange('responseLength', e.target.value)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div>
                    <div className="font-medium text-gray-900">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 추가 옵션 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">⚙️ 추가 옵션</h2>
            
            <div className="space-y-4">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.includeEmoji}
                  onChange={(e) => handleSettingChange('includeEmoji', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div>
                  <div className="font-medium text-gray-900">이모지 사용</div>
                  <div className="text-sm text-gray-500">응답에 적절한 이모지 포함</div>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.personalTouch}
                  onChange={(e) => handleSettingChange('personalTouch', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div>
                  <div className="font-medium text-gray-900">개인적인 터치</div>
                  <div className="text-sm text-gray-500">고객의 상황에 맞는 개인적인 멘트 추가</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* 미리보기 및 사용자 정의 */}
        <div className="space-y-6">
          {/* 사용자 정의 지시사항 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">✍️ 사용자 정의 지시사항</h2>
            <p className="text-sm text-gray-600 mb-4">
              재미나이에게 직접 전달할 특별한 지시사항을 입력하세요.
            </p>
            
            <textarea
              value={settings.customInstructions}
              onChange={(e) => handleSettingChange('customInstructions', e.target.value)}
              placeholder="예시:
- 항상 고객의 이름을 언급하며 답변하기
- 예약 관련 질문에는 반드시 전화번호 안내하기
- 날씨가 좋은 날에는 야외 활동 추천하기
- 가족 단위 고객에게는 아이 관련 시설 안내하기"
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          {/* 미리보기 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">👀 응답 미리보기</h2>
              <button
                onClick={generatePreview}
                className="flex items-center px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
              >
                <Wand2 className="h-4 w-4 mr-2" />
                미리보기 생성
              </button>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4 min-h-[200px]">
              <div className="text-sm text-gray-600 mb-2">
                <strong>고객 문의 예시:</strong> "체크인 시간과 주차 가능 여부를 알고 싶습니다."
              </div>
              <div className="border-t pt-3">
                <strong className="text-sm text-gray-600">AI 응답:</strong>
                <div className="mt-2 text-gray-800 whitespace-pre-wrap">
                  {isPreviewMode ? (
                    previewExample || '미리보기를 생성하려면 위의 버튼을 클릭하세요.'
                  ) : (
                    '미리보기를 생성하려면 위의 버튼을 클릭하세요.'
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 저장 버튼 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <button
              onClick={saveSettings}
              disabled={isSaving}
              className="w-full flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="h-5 w-5 mr-2" />
              {isSaving ? '저장 중...' : '설정 저장'}
            </button>
            <p className="text-xs text-gray-500 mt-2 text-center">
              설정은 자동으로 저장되지만, 수동 저장으로 확실히 적용할 수 있습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponseSettings;