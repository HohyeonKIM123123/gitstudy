import React, { useState } from 'react';
import { Save, Mail, Key, Database, Zap } from 'lucide-react';

const Settings = () => {
  const [settings, setSettings] = useState({
    gmail: {
      enabled: true,
      syncInterval: 5,
      maxEmails: 100,
    },
    ai: {
      model: 'gpt-4',
      tone: 'professional',
      includeSignature: true,
      autoClassify: true,
    },
    notifications: {
      emailAlerts: true,
      urgentOnly: false,
      soundEnabled: true,
    },
    database: {
      retentionDays: 90,
      autoArchive: true,
    }
  });

  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Save settings to backend
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      console.log('Settings saved:', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
    setSaving(false);
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary disabled:opacity-50"
        >
          <Save className="h-4 w-4 mr-2" />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Gmail Settings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Mail className="h-5 w-5 text-gray-400 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">Gmail Integration</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">Enable Gmail Sync</label>
              <p className="text-sm text-gray-500">Automatically fetch emails from Gmail</p>
            </div>
            <input
              type="checkbox"
              checked={settings.gmail.enabled}
              onChange={(e) => updateSetting('gmail', 'enabled', e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sync Interval (minutes)
            </label>
            <select
              value={settings.gmail.syncInterval}
              onChange={(e) => updateSetting('gmail', 'syncInterval', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value={1}>1 minute</option>
              <option value={5}>5 minutes</option>
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
              <option value={60}>1 hour</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Emails per Sync
            </label>
            <input
              type="number"
              value={settings.gmail.maxEmails}
              onChange={(e) => updateSetting('gmail', 'maxEmails', parseInt(e.target.value))}
              min="10"
              max="500"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* AI Settings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Zap className="h-5 w-5 text-gray-400 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">AI Configuration</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <select
              value={settings.ai.model}
              onChange={(e) => updateSetting('ai', 'model', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reply Tone
            </label>
            <select
              value={settings.ai.tone}
              onChange={(e) => updateSetting('ai', 'tone', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="professional">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="formal">Formal</option>
              <option value="casual">Casual</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">Include Signature</label>
              <p className="text-sm text-gray-500">Add company signature to AI replies</p>
            </div>
            <input
              type="checkbox"
              checked={settings.ai.includeSignature}
              onChange={(e) => updateSetting('ai', 'includeSignature', e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">Auto-Classify Emails</label>
              <p className="text-sm text-gray-500">Automatically classify incoming emails</p>
            </div>
            <input
              type="checkbox"
              checked={settings.ai.autoClassify}
              onChange={(e) => updateSetting('ai', 'autoClassify', e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* Database Settings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Database className="h-5 w-5 text-gray-400 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">Data Management</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Retention (days)
            </label>
            <input
              type="number"
              value={settings.database.retentionDays}
              onChange={(e) => updateSetting('database', 'retentionDays', parseInt(e.target.value))}
              min="7"
              max="365"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-sm text-gray-500 mt-1">
              Emails older than this will be automatically deleted
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">Auto-Archive</label>
              <p className="text-sm text-gray-500">Automatically archive replied emails after 7 days</p>
            </div>
            <input
              type="checkbox"
              checked={settings.database.autoArchive}
              onChange={(e) => updateSetting('database', 'autoArchive', e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* API Keys Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Key className="h-5 w-5 text-gray-400 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">API Configuration</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key
            </label>
            <input
              type="password"
              placeholder="sk-..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Gmail Client ID
            </label>
            <input
              type="text"
              placeholder="Your Gmail Client ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;