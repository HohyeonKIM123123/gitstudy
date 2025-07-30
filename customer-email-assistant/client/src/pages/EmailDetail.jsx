import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Reply, Archive, Tag, Clock, User } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ReplyEditor from '../components/ReplyEditor';
import { emailApi } from '../api/emailApi';

const EmailDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showReplyEditor, setShowReplyEditor] = useState(false);
  const [classifying, setClassifying] = useState(false);

  useEffect(() => {
    loadEmail();
  }, [id]);

  const loadEmail = async () => {
    try {
      const emailData = await emailApi.getEmail(id);
      setEmail(emailData);
      
      // Mark as read if unread
      if (emailData.status === 'unread') {
        await emailApi.updateEmailStatus(id, 'read');
        setEmail(prev => ({ ...prev, status: 'read' }));
      }
    } catch (error) {
      console.error('Failed to load email:', error);
    }
    setLoading(false);
  };

  const handleClassify = async () => {
    setClassifying(true);
    try {
      const result = await emailApi.classifyEmail(id);
      setEmail(prev => ({ 
        ...prev, 
        priority: result.priority,
        tags: result.tags 
      }));
    } catch (error) {
      console.error('Failed to classify email:', error);
    }
    setClassifying(false);
  };

  const handleSendReply = async (replyContent) => {
    try {
      await emailApi.sendReply(id, replyContent);
      setEmail(prev => ({ ...prev, status: 'replied' }));
      setShowReplyEditor(false);
    } catch (error) {
      console.error('Failed to send reply:', error);
      throw error;
    }
  };

  const handleArchive = async () => {
    try {
      await emailApi.updateEmailStatus(id, 'archived');
      navigate('/');
    } catch (error) {
      console.error('Failed to archive email:', error);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      urgent: 'bg-red-100 text-red-800',
      support: 'bg-yellow-100 text-yellow-800',
      general: 'bg-green-100 text-green-800',
      sales: 'bg-blue-100 text-blue-800',
      spam: 'bg-gray-100 text-gray-800',
    };
    return colors[priority] || colors.general;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!email) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Email not found</h3>
        <button onClick={() => navigate('/')} className="btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </button>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleClassify}
            disabled={classifying}
            className="btn-secondary disabled:opacity-50"
          >
            <Tag className="h-4 w-4 mr-2" />
            {classifying ? 'Classifying...' : 'AI Classify'}
          </button>
          <button onClick={handleArchive} className="btn-secondary">
            <Archive className="h-4 w-4 mr-2" />
            Archive
          </button>
          <button
            onClick={() => setShowReplyEditor(!showReplyEditor)}
            className="btn-primary"
          >
            <Reply className="h-4 w-4 mr-2" />
            Reply
          </button>
        </div>
      </div>

      {/* Email Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Email Header */}
        <div className="border-b border-gray-200 pb-4 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-xl font-semibold text-gray-900 mb-2">
                {email.subject}
              </h1>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center">
                  <User className="h-4 w-4 mr-1" />
                  <span>{email.sender_name || email.sender_email}</span>
                </div>
                <div className="flex items-center">
                  <Clock className="h-4 w-4 mr-1" />
                  <span>
                    {formatDistanceToNow(new Date(email.received_at), { addSuffix: true })}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {email.priority && (
                <span className={`priority-badge ${getPriorityColor(email.priority)}`}>
                  {email.priority}
                </span>
              )}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                email.status === 'unread' ? 'bg-blue-100 text-blue-800' :
                email.status === 'replied' ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {email.status}
              </span>
            </div>
          </div>

          {/* Tags */}
          {email.tags && email.tags.length > 0 && (
            <div className="flex items-center space-x-1">
              <Tag className="h-4 w-4 text-gray-400" />
              <div className="flex flex-wrap gap-1">
                {email.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Email Body */}
        <div className="prose max-w-none">
          <div 
            className="text-gray-900 whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: email.body || email.text_content }}
          />
        </div>
      </div>

      {/* Reply Editor */}
      {showReplyEditor && (
        <ReplyEditor
          email={email}
          onSend={handleSendReply}
          onCancel={() => setShowReplyEditor(false)}
          onSave={(content) => console.log('Saving draft:', content)}
        />
      )}
    </div>
  );
};

export default EmailDetail;