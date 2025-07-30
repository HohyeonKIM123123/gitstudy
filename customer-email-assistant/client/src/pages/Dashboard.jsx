import React, { useState, useEffect } from 'react';
import { RefreshCw, Mail, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import EmailCard from '../components/EmailCard';
import StatsCard from '../components/StatsCard';
import { emailApi } from '../api/emailApi';

const Dashboard = () => {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [emailsData, statsData] = await Promise.all([
        emailApi.fetchEmails(),
        emailApi.getStats()
      ]);
      setEmails(emailsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
    setLoading(false);
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await emailApi.syncEmails();
      await loadData();
    } catch (error) {
      console.error('Failed to sync emails:', error);
    }
    setSyncing(false);
  };

  const filteredEmails = emails.filter(email => {
    if (filter === 'all') return true;
    if (filter === 'unread') return email.status === 'unread';
    if (filter === 'urgent') return email.priority === 'urgent';
    return email.status === filter;
  });

  const filters = [
    { key: 'all', label: 'All Emails', count: emails.length },
    { key: 'unread', label: 'Unread', count: emails.filter(e => e.status === 'unread').length },
    { key: 'urgent', label: 'Urgent', count: emails.filter(e => e.priority === 'urgent').length },
    { key: 'replied', label: 'Replied', count: emails.filter(e => e.status === 'replied').length },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Email Dashboard</h1>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-primary disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'Sync Emails'}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Emails"
          value={stats.total || 0}
          icon={Mail}
          color="blue"
          change={stats.totalChange}
        />
        <StatsCard
          title="Unread"
          value={stats.unread || 0}
          icon={AlertTriangle}
          color="red"
          change={stats.unreadChange}
        />
        <StatsCard
          title="Replied"
          value={stats.replied || 0}
          icon={CheckCircle}
          color="green"
          change={stats.repliedChange}
        />
        <StatsCard
          title="Avg Response Time"
          value={stats.avgResponseTime || '0h'}
          icon={Clock}
          color="purple"
        />
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        {filters.map((filterOption) => (
          <button
            key={filterOption.key}
            onClick={() => setFilter(filterOption.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === filterOption.key
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {filterOption.label} ({filterOption.count})
          </button>
        ))}
      </div>

      {/* Email List */}
      <div className="space-y-4">
        {filteredEmails.length === 0 ? (
          <div className="text-center py-12">
            <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No emails found</h3>
            <p className="text-gray-600">
              {filter === 'all' 
                ? 'Try syncing your emails or check your Gmail connection.'
                : `No emails match the "${filter}" filter.`
              }
            </p>
          </div>
        ) : (
          filteredEmails.map((email) => (
            <EmailCard key={email.id} email={email} />
          ))
        )}
      </div>
    </div>
  );
};

export default Dashboard;