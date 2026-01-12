import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import { useNotifications } from '../../../components/NotificationSystem';
import axios from 'axios';
import {
  CalendarIcon,
  PlusIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

const EmailCampaigns = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();

  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [showCreateWizard, setShowCreateWizard] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadCampaigns();
  }, [filterStatus]);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterStatus !== 'all') params.status = filterStatus;

      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/emails/scheduled`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });

      setCampaigns(response.data || []);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      addNotification('error', 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelCampaign = async campaignId => {
    try {
      await axios.delete(`${API_BASE_URL}/api/ecommerce/admin/emails/scheduled/${campaignId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      addNotification('success', 'Campaign cancelled successfully');
      loadCampaigns();
    } catch (error) {
      console.error('Error cancelling campaign:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to cancel campaign');
    }
  };

  const getStatusColor = status => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = dateString => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading && campaigns.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading campaigns...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Email Campaigns</h1>
          <p className="text-gray-600 mt-1">Schedule and manage your email marketing campaigns</p>
        </div>
        <button
          onClick={() => setShowCreateWizard(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          Create Campaign
        </button>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Campaigns Table */}
      {campaigns.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <CalendarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No campaigns found</h3>
          <p className="text-gray-600 mb-6">Create your first email campaign to get started</p>
          <button
            onClick={() => setShowCreateWizard(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <PlusIcon className="w-5 h-5" />
            Create Campaign
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Template
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipients
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Scheduled For
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sent/Failed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {campaigns.map(campaign => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.template?.name || `Template ${campaign.template_id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.recipient_emails?.length || 'Filter-based'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDate(campaign.scheduled_for)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(campaign.status)}`}>
                        {campaign.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.sent_count || 0} / {campaign.failed_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {campaign.status === 'pending' && (
                        <button
                          onClick={() => handleCancelCampaign(campaign.id)}
                          className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-xs font-medium"
                        >
                          Cancel
                        </button>
                      )}
                      {campaign.error_message && (
                        <p className="text-xs text-red-600 mt-1" title={campaign.error_message}>
                          Error occurred
                        </p>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Campaign Wizard */}
      {showCreateWizard && (
        <CampaignWizard
          onClose={() => setShowCreateWizard(false)}
          onSuccess={() => {
            setShowCreateWizard(false);
            loadCampaigns();
          }}
          token={token}
          apiBaseUrl={API_BASE_URL}
          addNotification={addNotification}
        />
      )}
    </div>
  );
};

const CampaignWizard = ({ onClose, onSuccess, token, apiBaseUrl, addNotification }) => {
  const [step, setStep] = useState(1);
  const [templates, setTemplates] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [loadingSubscribers, setLoadingSubscribers] = useState(false);

  // Form data
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [recipientMode, setRecipientMode] = useState('all'); // 'all', 'tags', 'manual'
  const [recipientTags, setRecipientTags] = useState('');
  const [manualEmails, setManualEmails] = useState('');
  const [scheduleMode, setScheduleMode] = useState('now'); // 'now', 'schedule'
  const [scheduledDateTime, setScheduledDateTime] = useState('');
  const [recipientCount, setRecipientCount] = useState(0);

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    if (step === 2) {
      loadSubscribers();
    }
  }, [step]);

  useEffect(() => {
    if (step === 2) {
      calculateRecipientCount();
    }
  }, [recipientMode, recipientTags, manualEmails, subscribers]);

  const loadTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const response = await axios.get(`${apiBaseUrl}/api/ecommerce/admin/emails/templates`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { email_type: 'marketing', is_active: true },
      });
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      addNotification('error', 'Failed to load templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const loadSubscribers = async () => {
    try {
      setLoadingSubscribers(true);
      const response = await axios.get(`${apiBaseUrl}/api/ecommerce/admin/emails/subscribers`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { is_subscribed: true },
      });
      setSubscribers(response.data || []);
    } catch (error) {
      console.error('Error loading subscribers:', error);
      addNotification('error', 'Failed to load subscribers');
    } finally {
      setLoadingSubscribers(false);
    }
  };

  const calculateRecipientCount = () => {
    if (recipientMode === 'all') {
      setRecipientCount(subscribers.length);
    } else if (recipientMode === 'tags') {
      if (!recipientTags.trim()) {
        setRecipientCount(0);
        return;
      }
      const tags = recipientTags
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);
      const count = subscribers.filter(sub => tags.some(tag => sub.tags?.includes(tag))).length;
      setRecipientCount(count);
    } else if (recipientMode === 'manual') {
      const emails = manualEmails
        .split('\n')
        .map(e => e.trim())
        .filter(Boolean);
      setRecipientCount(emails.length);
    }
  };

  const handleSubmit = async () => {
    try {
      const campaignData = {
        template_id: parseInt(selectedTemplateId),
        scheduled_for: scheduleMode === 'now' ? new Date().toISOString() : scheduledDateTime,
      };

      if (recipientMode === 'all') {
        campaignData.recipient_filter = {};
      } else if (recipientMode === 'tags') {
        const tags = recipientTags
          .split(',')
          .map(t => t.trim())
          .filter(Boolean);
        campaignData.recipient_filter = { tags };
      } else if (recipientMode === 'manual') {
        const emails = manualEmails
          .split('\n')
          .map(e => e.trim())
          .filter(Boolean);
        campaignData.recipient_emails = emails;
      }

      await axios.post(`${apiBaseUrl}/api/ecommerce/admin/emails/send-marketing`, campaignData, {
        headers: { Authorization: `Bearer ${token}` },
      });

      addNotification(
        'success',
        scheduleMode === 'now' ? 'Campaign sent successfully' : 'Campaign scheduled successfully'
      );
      onSuccess();
    } catch (error) {
      console.error('Error creating campaign:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to create campaign');
    }
  };

  const canProceedFromStep1 = selectedTemplateId !== '';
  const canProceedFromStep2 = recipientCount > 0;
  const canProceedFromStep3 = scheduleMode === 'now' || (scheduleMode === 'schedule' && scheduledDateTime);

  const selectedTemplate = templates.find(t => t.id === parseInt(selectedTemplateId));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Create Email Campaign</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
            <XMarkIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4].map(stepNum => (
              <React.Fragment key={stepNum}>
                <div className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                      step >= stepNum ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {stepNum}
                  </div>
                  <span className="ml-2 text-sm font-medium text-gray-700 hidden sm:inline">
                    {stepNum === 1 && 'Template'}
                    {stepNum === 2 && 'Recipients'}
                    {stepNum === 3 && 'Schedule'}
                    {stepNum === 4 && 'Review'}
                  </span>
                </div>
                {stepNum < 4 && <div className="flex-1 h-0.5 bg-gray-200 mx-2" />}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Select Template */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Email Template</h3>
              {loadingTemplates ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                </div>
              ) : templates.length === 0 ? (
                <div className="text-center py-8 text-gray-600">
                  No marketing templates found. Please create a marketing template first.
                </div>
              ) : (
                <div className="space-y-3">
                  {templates.map(template => (
                    <label
                      key={template.id}
                      className={`block p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                        selectedTemplateId === template.id.toString()
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="template"
                        value={template.id}
                        checked={selectedTemplateId === template.id.toString()}
                        onChange={e => setSelectedTemplateId(e.target.value)}
                        className="sr-only"
                      />
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{template.name}</p>
                          <p className="text-sm text-gray-600 mt-1">{template.subject}</p>
                        </div>
                        {selectedTemplateId === template.id.toString() && (
                          <CheckCircleIcon className="w-6 h-6 text-blue-600 flex-shrink-0" />
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 2: Select Recipients */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Recipients</h3>

              <div className="space-y-3">
                <label className="block p-4 border-2 rounded-lg cursor-pointer hover:border-gray-300">
                  <input
                    type="radio"
                    name="recipients"
                    value="all"
                    checked={recipientMode === 'all'}
                    onChange={e => setRecipientMode(e.target.value)}
                    className="mr-3"
                  />
                  <span className="font-medium">All Subscribers</span>
                  <p className="text-sm text-gray-600 ml-7">Send to all subscribed contacts ({subscribers.length})</p>
                </label>

                <label className="block p-4 border-2 rounded-lg cursor-pointer hover:border-gray-300">
                  <input
                    type="radio"
                    name="recipients"
                    value="tags"
                    checked={recipientMode === 'tags'}
                    onChange={e => setRecipientMode(e.target.value)}
                    className="mr-3"
                  />
                  <span className="font-medium">Filter by Tags</span>
                  <p className="text-sm text-gray-600 ml-7">Send to subscribers with specific tags</p>
                  {recipientMode === 'tags' && (
                    <input
                      type="text"
                      value={recipientTags}
                      onChange={e => setRecipientTags(e.target.value)}
                      placeholder="e.g., vip, customer (comma-separated)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-2 ml-7"
                    />
                  )}
                </label>

                <label className="block p-4 border-2 rounded-lg cursor-pointer hover:border-gray-300">
                  <input
                    type="radio"
                    name="recipients"
                    value="manual"
                    checked={recipientMode === 'manual'}
                    onChange={e => setRecipientMode(e.target.value)}
                    className="mr-3"
                  />
                  <span className="font-medium">Manual Email List</span>
                  <p className="text-sm text-gray-600 ml-7">Enter specific email addresses</p>
                  {recipientMode === 'manual' && (
                    <textarea
                      value={manualEmails}
                      onChange={e => setManualEmails(e.target.value)}
                      placeholder="Enter email addresses (one per line)"
                      rows={5}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-2 ml-7"
                    />
                  )}
                </label>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                <p className="text-sm text-blue-900">
                  <strong>Recipients: {recipientCount}</strong>
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Schedule */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Schedule Campaign</h3>

              <div className="space-y-3">
                <label className="block p-4 border-2 rounded-lg cursor-pointer hover:border-gray-300">
                  <input
                    type="radio"
                    name="schedule"
                    value="now"
                    checked={scheduleMode === 'now'}
                    onChange={e => setScheduleMode(e.target.value)}
                    className="mr-3"
                  />
                  <span className="font-medium">Send Now</span>
                  <p className="text-sm text-gray-600 ml-7">Campaign will be sent immediately</p>
                </label>

                <label className="block p-4 border-2 rounded-lg cursor-pointer hover:border-gray-300">
                  <input
                    type="radio"
                    name="schedule"
                    value="schedule"
                    checked={scheduleMode === 'schedule'}
                    onChange={e => setScheduleMode(e.target.value)}
                    className="mr-3"
                  />
                  <span className="font-medium">Schedule for Later</span>
                  <p className="text-sm text-gray-600 ml-7">Choose a specific date and time</p>
                  {scheduleMode === 'schedule' && (
                    <input
                      type="datetime-local"
                      value={scheduledDateTime}
                      onChange={e => setScheduledDateTime(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-2 ml-7"
                    />
                  )}
                </label>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Campaign</h3>

              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">Template</p>
                  <p className="text-gray-900">{selectedTemplate?.name}</p>
                  <p className="text-sm text-gray-600">{selectedTemplate?.subject}</p>
                </div>

                <div className="border-t border-gray-200 pt-3">
                  <p className="text-sm font-medium text-gray-700">Recipients</p>
                  <p className="text-gray-900">{recipientCount} subscribers</p>
                  <p className="text-sm text-gray-600">
                    {recipientMode === 'all' && 'All subscribers'}
                    {recipientMode === 'tags' && `Filtered by tags: ${recipientTags}`}
                    {recipientMode === 'manual' && 'Manual email list'}
                  </p>
                </div>

                <div className="border-t border-gray-200 pt-3">
                  <p className="text-sm font-medium text-gray-700">Schedule</p>
                  <p className="text-gray-900">
                    {scheduleMode === 'now'
                      ? 'Send immediately'
                      : `Scheduled for ${new Date(scheduledDateTime).toLocaleString()}`}
                  </p>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
                <p className="text-sm text-yellow-900">
                  <strong>Note:</strong> Once sent, this campaign cannot be cancelled. Please review all details
                  carefully.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="p-6 border-t border-gray-200 flex items-center justify-between">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeftIcon className="w-5 h-5" />
            Back
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            {step < 4 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={
                  (step === 1 && !canProceedFromStep1) ||
                  (step === 2 && !canProceedFromStep2) ||
                  (step === 3 && !canProceedFromStep3)
                }
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
                <ChevronRightIcon className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                {scheduleMode === 'now' ? 'Send Campaign' : 'Schedule Campaign'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailCampaigns;
