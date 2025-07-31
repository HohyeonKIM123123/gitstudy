import React, { useState, useEffect } from 'react';
import { Save, Wand2, Settings, MessageSquare, Shuffle, Copy, Trash2, Plus, GripVertical } from 'lucide-react';

const ResponseSettings = () => {
  const [settings, setSettings] = useState({
    tone: 'friendly',
    greeting: '안녕하세요! RPA펜션입니다 😊',
    closing: '감사합니다. 좋은 하루 되세요!',
    responseLength: 'medium',
    includeEmoji: true,
    personalTouch: true,
    customInstructions: '',
    structure: ['greeting', 'answer', 'additional', 'closing'],
    toneCustomization: {
      formality: 50, // 0: 캐주얼 ~ 100: 격식
      length: 50,    // 0: 짧게 ~ 100: 자세하게
      emojiFreq: 70  // 0: 없음 ~ 100: 많이
    }
  });

  const [activeProfile, setActiveProfile] = useState('default');
  const [savedProfiles, setSavedProfiles] = useState({
    default: '기본 설정',
    formal: '정중형',
    friendly: '친근형',
    night: '밤시간 답변형'
  });

  const [previewQuery, setPreviewQuery] = useState("와이파이 비밀번호 좀 알 수 있을까요?");
  const [previewResponse, setPreviewResponse] = useState('');
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);

  // 톤 옵션들 (카드 형태)
  const toneOptions = [
    {
      id: 'friendly',
      title: '😊 친구처럼 따뜻한',
      description: '편안하고 친근한 말투',
      preview: '안녕하세요~ 따뜻한 펜션지기예요! 😊',
      color: 'bg-orange-50 border-orange-200 text-orange-800'
    },
    {
      id: 'formal',
      title: '🎩 정중하고 격식있는',
      description: '예의바르고 전문적인 말투',
      preview: '안녕하십니까, 고객님. RPA펜션입니다.',
      color: 'bg-blue-50 border-blue-200 text-blue-800'
    },
    {
      id: 'casual',
      title: '😎 자연스럽고 편안한',
      description: '부담없고 자연스러운 말투',
      preview: '네~ 편하게 물어보세요. 알려드릴게요!',
      color: 'bg-green-50 border-green-200 text-green-800'
    }
  ];

  // 응답 구조 블록들
  const structureBlocks = {
    greeting: { name: '인사말', icon: '👋', color: 'bg-blue-100' },
    answer: { name: '핵심답변', icon: '💬', color: 'bg-green-100' },
    additional: { name: '추가안내', icon: '📋', color: 'bg-yellow-100' },
    closing: { name: '마무리', icon: '🙏', color: 'bg-purple-100' }
  };

  // 추천 인사말/마무리말
  const greetingTemplates = [
    '안녕하세요! RPA펜션입니다 😊',
    '안녕하세요~ 따뜻한 펜션지기예요!',
    '안녕하십니까, 고객님. RPA펜션입니다.',
    '네~ RPA펜션입니다! 무엇을 도와드릴까요?',
    '반갑습니다! RPA펜션에 문의해 주셔서 감사해요 ✨'
  ];

  const closingTemplates = [
    '감사합니다. 좋은 하루 되세요!',
    '언제든 편하게 연락 주세요~ 😊',
    '추가 문의사항이 있으시면 언제든 말씀해 주십시오.',
    '즐거운 여행 되시길 바라요! 🌟',
    'RPA펜션에서 뵙겠습니다! 감사합니다 💕'
  ];

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/response-settings');
      if (response.ok) {
        const data = await response.json();
        if (data.settings) {
          // 기존 설정과 새 설정을 병합하되, structure가 배열이 아니면 기본값 사용
          const loadedSettings = { ...data.settings };
          
          // structure가 배열이 아니면 기본 배열로 변환
          if (!Array.isArray(loadedSettings.structure)) {
            loadedSettings.structure = ['greeting', 'answer', 'additional', 'closing'];
          }
          
          // toneCustomization이 없으면 기본값 설정
          if (!loadedSettings.toneCustomization) {
            loadedSettings.toneCustomization = {
              formality: 50,
              length: 50,
              emojiFreq: 70
            };
          }
          
          setSettings(prev => ({ ...prev, ...loadedSettings }));
        }
        setLastSaved(data.updated_at ? new Date(data.updated_at) : null);
      }
    } catch (error) {
      console.error('설정 로드 실패:', error);
    }
  };

  const saveSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/response-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings })
      });

      if (response.ok) {
        setLastSaved(new Date());
        // 성공 알림 (토스트 형태로 개선 가능)
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = '설정이 저장되었습니다! ✅';
        document.body.appendChild(notification);
        setTimeout(() => document.body.removeChild(notification), 3000);
      }
    } catch (error) {
      console.error('저장 실패:', error);
    }
  };

  const generatePreview = async () => {
    setIsGeneratingPreview(true);
    try {
      const response = await fetch('http://localhost:8000/response-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          settings,
          sampleQuery: previewQuery
        })
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewResponse(data.preview);
      } else {
        setPreviewResponse('미리보기 생성에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      console.error('미리보기 생성 실패:', error);
      setPreviewResponse('미리보기 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  const handleToneSelect = (toneId) => {
    setSettings(prev => ({ ...prev, tone: toneId }));
  };

  const handleSliderChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      toneCustomization: {
        ...prev.toneCustomization,
        [key]: value
      }
    }));
  };

  const moveStructureBlock = (fromIndex, toIndex) => {
    const newStructure = [...settings.structure];
    const [moved] = newStructure.splice(fromIndex, 1);
    newStructure.splice(toIndex, 0, moved);
    setSettings(prev => ({ ...prev, structure: newStructure }));
  };

  const removeStructureBlock = (index) => {
    if (settings.structure.length <= 1) return; // 최소 1개는 유지
    
    const newStructure = [...settings.structure];
    newStructure.splice(index, 1);
    setSettings(prev => ({ ...prev, structure: newStructure }));
  };

  const addStructureBlock = (blockId) => {
    if (settings.structure.includes(blockId)) return; // 이미 있으면 추가하지 않음
    
    const newStructure = [...settings.structure, blockId];
    setSettings(prev => ({ ...prev, structure: newStructure }));
  };

  const setStructureTemplate = (template) => {
    setSettings(prev => ({ ...prev, structure: template }));
  };

  const selectTemplate = (type, template) => {
    setSettings(prev => ({ ...prev, [type]: template }));
  };

  const randomizeGreeting = () => {
    const randomTemplate = greetingTemplates[Math.floor(Math.random() * greetingTemplates.length)];
    setSettings(prev => ({ ...prev, greeting: randomTemplate }));
  };

  const randomizeClosing = () => {
    const randomTemplate = closingTemplates[Math.floor(Math.random() * closingTemplates.length)];
    setSettings(prev => ({ ...prev, closing: randomTemplate }));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🧠 AI 응답 스타일 설정 고도화
          </h1>
          <p className="text-gray-600">
            재미나이의 말투와 응답 구조를 세밀하게 커스터마이징하세요
          </p>
          {lastSaved && (
            <p className="text-sm text-gray-500 mt-2">
              마지막 저장: {lastSaved.toLocaleString()}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 왼쪽: 설정 패널 */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* 1. AI 톤 & 스타일 설정 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                🎯 AI 톤 & 스타일 설정
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {toneOptions.map((option) => (
                  <div
                    key={option.id}
                    onClick={() => handleToneSelect(option.id)}
                    className={`cursor-pointer rounded-lg border-2 p-4 transition-all hover:shadow-md ${
                      settings.tone === option.id 
                        ? `${option.color} border-current shadow-md` 
                        : 'bg-white border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <h3 className="font-semibold mb-2">{option.title}</h3>
                    <p className="text-sm text-gray-600 mb-3">{option.description}</p>
                    <div className="bg-gray-50 rounded-lg p-3 text-sm italic">
                      "{option.preview}"
                    </div>
                  </div>
                ))}
              </div>

              {/* 톤 미세 조정 슬라이더 */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">💬 말투 미세 조정</h3>
                
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-sm font-medium text-gray-700">공손함 ↔ 캐주얼함</label>
                      <span className="text-sm text-gray-500">{settings.toneCustomization.formality}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.toneCustomization.formality}
                      onChange={(e) => handleSliderChange('formality', parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>캐주얼</span>
                      <span>공손함</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-sm font-medium text-gray-700">응답 길이</label>
                      <span className="text-sm text-gray-500">{settings.toneCustomization.length}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.toneCustomization.length}
                      onChange={(e) => handleSliderChange('length', parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>간결</span>
                      <span>자세함</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-sm font-medium text-gray-700">이모지 빈도</label>
                      <span className="text-sm text-gray-500">{settings.toneCustomization.emojiFreq}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.toneCustomization.emojiFreq}
                      onChange={(e) => handleSliderChange('emojiFreq', parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>없음</span>
                      <span>많이</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. 응답 구조 설정 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                🏗 응답 구조 설정
              </h2>
              
              <p className="text-gray-600 mb-4">블록을 추가/제거하고 드래그하여 응답 순서를 변경하세요</p>
              
              {/* 현재 구조 블록들 */}
              <div className="space-y-3 mb-6">
                {settings.structure.map((blockId, index) => {
                  const block = structureBlocks[blockId];
                  return (
                    <div
                      key={`${blockId}-${index}`}
                      className={`flex items-center p-4 rounded-lg border-2 border-dashed border-gray-300 ${block.color} hover:shadow-md transition-all`}
                    >
                      <GripVertical className="h-5 w-5 text-gray-400 mr-3 cursor-move" />
                      <span className="text-2xl mr-3">{block.icon}</span>
                      <div className="flex-1">
                        <span className="font-medium">{index + 1}. {block.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {/* 순서 변경 버튼 */}
                        {index > 0 && (
                          <button
                            onClick={() => moveStructureBlock(index, index - 1)}
                            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                            title="위로 이동"
                          >
                            ↑
                          </button>
                        )}
                        {index < settings.structure.length - 1 && (
                          <button
                            onClick={() => moveStructureBlock(index, index + 1)}
                            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                            title="아래로 이동"
                          >
                            ↓
                          </button>
                        )}
                        
                        {/* 제거 버튼 (최소 1개는 유지) */}
                        {settings.structure.length > 1 && (
                          <button
                            onClick={() => removeStructureBlock(index)}
                            className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded transition-colors"
                            title="블록 제거"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* 블록 추가 섹션 */}
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">블록 추가:</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(structureBlocks).map(([blockId, block]) => {
                    const isAlreadyAdded = settings.structure.includes(blockId);
                    return (
                      <button
                        key={blockId}
                        onClick={() => addStructureBlock(blockId)}
                        disabled={isAlreadyAdded}
                        className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          isAlreadyAdded
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : `${block.color} hover:shadow-md cursor-pointer`
                        }`}
                        title={isAlreadyAdded ? '이미 추가된 블록입니다' : `${block.name} 블록 추가`}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        <span className="mr-2">{block.icon}</span>
                        {block.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 미리 정의된 구조 템플릿 */}
              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">빠른 설정:</h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setStructureTemplate(['greeting', 'answer', 'additional', 'closing'])}
                    className="px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                  >
                    📋 완전한 구조
                  </button>
                  <button
                    onClick={() => setStructureTemplate(['greeting', 'answer', 'closing'])}
                    className="px-3 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                  >
                    ⚡ 간결한 구조
                  </button>
                  <button
                    onClick={() => setStructureTemplate(['answer', 'additional'])}
                    className="px-3 py-2 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
                  >
                    🎯 핵심만
                  </button>
                  <button
                    onClick={() => setStructureTemplate(['greeting', 'answer'])}
                    className="px-3 py-2 text-sm bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors"
                  >
                    💬 기본형
                  </button>
                </div>
              </div>
            </div>

            {/* 3. 고정 인사말/마무리말 관리 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                🧾 고정 인사말/마무리말 관리
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 인사말 */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="font-medium text-gray-900">👋 인사말</label>
                    <button
                      onClick={randomizeGreeting}
                      className="flex items-center text-sm text-purple-600 hover:text-purple-700"
                    >
                      <Shuffle className="h-4 w-4 mr-1" />
                      랜덤
                    </button>
                  </div>
                  
                  <textarea
                    value={settings.greeting}
                    onChange={(e) => setSettings(prev => ({ ...prev, greeting: e.target.value }))}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows={3}
                  />
                  
                  <div className="mt-3 space-y-2">
                    <p className="text-sm font-medium text-gray-700">추천 템플릿:</p>
                    <div className="flex flex-wrap gap-2">
                      {greetingTemplates.slice(0, 3).map((template, index) => (
                        <button
                          key={index}
                          onClick={() => selectTemplate('greeting', template)}
                          className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded transition-colors"
                        >
                          {template.length > 20 ? template.substring(0, 20) + '...' : template}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 마무리말 */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="font-medium text-gray-900">🙏 마무리말</label>
                    <button
                      onClick={randomizeClosing}
                      className="flex items-center text-sm text-purple-600 hover:text-purple-700"
                    >
                      <Shuffle className="h-4 w-4 mr-1" />
                      랜덤
                    </button>
                  </div>
                  
                  <textarea
                    value={settings.closing}
                    onChange={(e) => setSettings(prev => ({ ...prev, closing: e.target.value }))}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows={3}
                  />
                  
                  <div className="mt-3 space-y-2">
                    <p className="text-sm font-medium text-gray-700">추천 템플릿:</p>
                    <div className="flex flex-wrap gap-2">
                      {closingTemplates.slice(0, 3).map((template, index) => (
                        <button
                          key={index}
                          onClick={() => selectTemplate('closing', template)}
                          className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded transition-colors"
                        >
                          {template.length > 20 ? template.substring(0, 20) + '...' : template}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 4. 개인화 옵션 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                ✨ 개인화 옵션 강화
              </h2>
              
              <div className="space-y-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.personalTouch}
                    onChange={(e) => setSettings(prev => ({ ...prev, personalTouch: e.target.checked }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div>
                    <div className="font-medium text-gray-900">고객 상황별 개인화</div>
                    <div className="text-sm text-gray-500">고객의 상황에 맞는 개인적인 멘트 추가</div>
                  </div>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.includeEmoji}
                    onChange={(e) => setSettings(prev => ({ ...prev, includeEmoji: e.target.checked }))}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div>
                    <div className="font-medium text-gray-900">이모지 자동 삽입</div>
                    <div className="text-sm text-gray-500">적절한 이모지를 자동으로 추가</div>
                  </div>
                </label>
              </div>

              <div className="mt-6">
                <label className="block font-medium text-gray-900 mb-2">
                  🎯 사용자 정의 지시사항
                </label>
                <textarea
                  value={settings.customInstructions}
                  onChange={(e) => setSettings(prev => ({ ...prev, customInstructions: e.target.value }))}
                  placeholder="예시:
- 항상 고객의 이름을 언급하며 답변하기
- 예약 관련 질문에는 반드시 전화번호 안내하기
- 가족 단위 고객에게는 아이 관련 시설 안내하기"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={6}
                />
              </div>
            </div>
          </div>

          {/* 오른쪽: 실시간 미리보기 */}
          <div className="space-y-6">
            {/* 실시간 응답 미리보기 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                🧪 실시간 응답 미리보기
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block font-medium text-gray-900 mb-2">
                    고객 문의 예시:
                  </label>
                  <input
                    type="text"
                    value={previewQuery}
                    onChange={(e) => setPreviewQuery(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="고객 문의를 입력하세요..."
                  />
                </div>

                <button
                  onClick={generatePreview}
                  disabled={isGeneratingPreview}
                  className="w-full flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Wand2 className={`h-5 w-5 mr-2 ${isGeneratingPreview ? 'animate-spin' : ''}`} />
                  {isGeneratingPreview ? 'AI 응답 생성 중...' : 'AI 응답 미리보기'}
                </button>

                <div className="bg-gray-50 rounded-lg p-4 min-h-[200px]">
                  <div className="text-sm font-medium text-gray-700 mb-2">AI 응답:</div>
                  <div className="text-gray-800 whitespace-pre-wrap">
                    {isGeneratingPreview ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
                          <span className="text-gray-600">AI가 응답을 생성하고 있습니다...</span>
                        </div>
                      </div>
                    ) : previewResponse ? (
                      previewResponse
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        위의 "AI 응답 미리보기" 버튼을 클릭하여 현재 설정으로 생성될 응답을 확인해보세요.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* 저장 버튼 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <button
                onClick={saveSettings}
                className="w-full flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                <Save className="h-5 w-5 mr-2" />
                설정 저장
              </button>
              <p className="text-xs text-gray-500 mt-2 text-center">
                설정이 자동으로 저장되며, 즉시 AI 응답에 반영됩니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponseSettings;