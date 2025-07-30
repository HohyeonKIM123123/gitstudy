import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const emailApi = {
  // Fetch emails from Gmail
  fetchEmails: async (limit = 50) => {
    const response = await api.get(`/emails?limit=${limit}`);
    return response.data;
  },

  // Get email by ID
  getEmail: async (emailId) => {
    const response = await api.get(`/emails/${emailId}`);
    return response.data;
  },

  // Classify email
  classifyEmail: async (emailId) => {
    const response = await api.post(`/emails/${emailId}/classify`);
    return response.data;
  },

  // Generate reply
  generateReply: async (emailId, context = {}) => {
    const response = await api.post(`/emails/${emailId}/generate-reply`, context);
    return response.data;
  },

  // Update email status
  updateEmailStatus: async (emailId, status) => {
    const response = await api.put(`/emails/${emailId}`, { status });
    return response.data;
  },

  // Send reply
  sendReply: async (emailId, replyContent) => {
    const response = await api.post(`/emails/${emailId}/send-reply`, {
      content: replyContent
    });
    return response.data;
  },

  // Get email statistics
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  // Sync emails (manual refresh)
  syncEmails: async () => {
    const response = await api.post('/sync');
    return response.data;
  }
};

export default emailApi;