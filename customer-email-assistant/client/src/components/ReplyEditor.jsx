import React, { useState, useEffect } from 'react';
import { Send, Wand2, Save, X } from 'lucide-react';

const ReplyEditor = ({ email, onSend, onCancel, onSave }) => {
  const [replyContent, setReplyContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const generateReply = async () => {
    console.log('🔍 AI Generate 버튼 클릭됨');
    console.log('📧 이메일 ID:', email.id);
    console.log('📝 이메일 내용:', email.subject, email.body?.substring(0, 100));
    
    setIsGenerating(true);
    try {
      // 먼저 응답 설정을 가져옵니다
      console.log('⚙️ 응답 설정 가져오는 중...');
      const settingsResponse = await fetch('http://localhost:8000/response-settings');
      let responseSettings = {};
      
      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json();
        responseSettings = settingsData.settings || {};
        console.log('✅ 응답 설정 로드됨:', responseSettings);
      } else {
        console.log('❌ 응답 설정 로드 실패');
      }

      // 요청 데이터 구성
      const requestData = {
        context: {
          response_settings: responseSettings,
          include_signature: true
        }
      };
      
      console.log('📦 서버로 전송할 데이터:', requestData);

      // 응답 설정을 포함하여 답장 생성 요청
      console.log('🚀 서버로 답장 생성 요청 전송 중...');
      const response = await fetch(`http://localhost:8000/emails/${email.id}/generate-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });
      
      console.log('📡 서버 응답 상태:', response.status);
      
      if (!response.ok) {
        throw new Error(`서버 응답 오류: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('✅ 서버 응답 데이터:', data);
      console.log('🤖 생성된 답장:', data.reply);
      
      setReplyContent(data.reply);
    } catch (error) {
      console.error('❌ AI 답장 생성 실패:', error);
      alert('AI 답장 생성에 실패했습니다: ' + error.message);
    }
    setIsGenerating(false);
  };

  const handleSend = async () => {
    if (!replyContent.trim()) return;
    
    setIsSending(true);
    try {
      await onSend(replyContent);
    } catch (error) {
      console.error('Failed to send reply:', error);
    }
    setIsSending(false);
  };

  const handleSave = () => {
    onSave(replyContent);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Reply to Email</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={generateReply}
            disabled={isGenerating}
            className="flex items-center px-3 py-2 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors disabled:opacity-50"
          >
            <Wand2 className="h-4 w-4 mr-2" />
            {isGenerating ? 'Generating...' : 'AI Generate'}
          </button>
        </div>
      </div>

      {/* Original email context */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg border-l-4 border-gray-300">
        <p className="text-sm text-gray-600 mb-1">
          <strong>From:</strong> {email.sender_email}
        </p>
        <p className="text-sm text-gray-600 mb-1">
          <strong>Subject:</strong> {email.subject}
        </p>
        <div className="text-sm text-gray-700 mt-2 max-h-32 overflow-y-auto">
          {email.body?.substring(0, 300)}...
        </div>
      </div>

      {/* Reply editor */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Your Reply
        </label>
        <textarea
          value={replyContent}
          onChange={(e) => setReplyContent(e.target.value)}
          placeholder="Type your reply here..."
          rows={8}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleSave}
            className="flex items-center px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Save className="h-4 w-4 mr-2" />
            Save Draft
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={onCancel}
            className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            <X className="h-4 w-4 mr-2" />
            Cancel
          </button>
          <button
            onClick={handleSend}
            disabled={!replyContent.trim() || isSending}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4 mr-2" />
            {isSending ? 'Sending...' : 'Send Reply'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReplyEditor;