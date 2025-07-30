import React from 'react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { Clock, User, Tag } from 'lucide-react';

const EmailCard = ({ email }) => {
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

  const getStatusColor = (status) => {
    const colors = {
      unread: 'bg-red-50 border-red-200',
      read: 'bg-white border-gray-200',
      replied: 'bg-green-50 border-green-200',
      archived: 'bg-gray-50 border-gray-200',
    };
    return colors[status] || colors.unread;
  };

  return (
    <Link to={`/email/${email.id}`}>
      <div className={`email-card ${getStatusColor(email.status)} cursor-pointer`}>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-900 truncate">
                  {email.sender_name || email.sender_email}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {email.priority && (
                  <span className={`priority-badge ${getPriorityColor(email.priority)}`}>
                    {email.priority}
                  </span>
                )}
                <div className="flex items-center text-xs text-gray-500">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatDistanceToNow(new Date(email.received_at), { addSuffix: true })}
                </div>
              </div>
            </div>

            {/* Subject */}
            <h3 className="text-sm font-medium text-gray-900 mb-1 truncate">
              {email.subject}
            </h3>

            {/* Preview */}
            <p className="text-sm text-gray-600 line-clamp-2 mb-2">
              {email.preview || email.body?.substring(0, 150) + '...'}
            </p>

            {/* Tags */}
            {email.tags && email.tags.length > 0 && (
              <div className="flex items-center space-x-1">
                <Tag className="h-3 w-3 text-gray-400" />
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

          {/* Status indicator */}
          <div className="ml-4 flex-shrink-0">
            <div className={`w-3 h-3 rounded-full ${
              email.status === 'unread' ? 'bg-blue-500' :
              email.status === 'replied' ? 'bg-green-500' :
              'bg-gray-300'
            }`} />
          </div>
        </div>
      </div>
    </Link>
  );
};

export default EmailCard;