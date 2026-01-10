import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { useNotifications } from '../../../components/NotificationSystem';
import axios from 'axios';
import {
  EnvelopeIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';

const EmailTemplates = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [filterActive, setFilterActive] = useState('all');
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadTemplates();
  }, [filterType, filterActive]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterType !== 'all') params.email_type = filterType;
      if (filterActive !== 'all') params.is_active = filterActive === 'active';

      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/emails/templates`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });

      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      addNotification('error', 'Failed to load email templates');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async templateId => {
    if (deleteConfirm !== templateId) {
      setDeleteConfirm(templateId);
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/ecommerce/admin/emails/templates/${templateId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      addNotification('success', 'Template deleted successfully');
      loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to delete template');
    } finally {
      setDeleteConfirm(null);
    }
  };

  const getTypeBadgeColor = type => {
    const colors = {
      order_confirmation: 'bg-blue-100 text-blue-800',
      shipping_notification: 'bg-green-100 text-green-800',
      marketing: 'bg-purple-100 text-purple-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const formatEmailType = type => {
    return type
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading templates...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Email Templates</h1>
          <p className="text-gray-600 mt-1">Manage your transactional and marketing email templates</p>
        </div>
        <button
          onClick={() => navigate('/craftflow/emails/templates/new')}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          Create Template
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="w-5 h-5 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-700">Filters</h3>
        </div>
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Type</label>
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Types</option>
              <option value="order_confirmation">Order Confirmation</option>
              <option value="shipping_notification">Shipping Notification</option>
              <option value="marketing">Marketing</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filterActive}
              onChange={e => setFilterActive(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      {templates.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <EnvelopeIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No templates found</h3>
          <p className="text-gray-600 mb-6">Get started by creating your first email template</p>
          <button
            onClick={() => navigate('/craftflow/emails/templates/new')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <PlusIcon className="w-5 h-5" />
            Create Template
          </button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {templates.map(template => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{template.name}</h3>
                    <p className="text-sm text-gray-600 truncate">{template.subject}</p>
                  </div>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTypeBadgeColor(template.email_type)}`}>
                    {formatEmailType(template.email_type)}
                  </span>
                  {template.is_default && (
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">Default</span>
                  )}
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      template.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {template.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-indigo-100 text-indigo-800">
                    {template.template_type === 'transactional' ? 'Transactional' : 'Marketing'}
                  </span>
                </div>

                {/* Meta Info */}
                <div className="text-xs text-gray-500 mb-4">
                  <p>Blocks: {template.blocks?.length || 0}</p>
                  <p className="mt-1">Updated: {new Date(template.updated_at).toLocaleDateString()}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate(`/craftflow/emails/templates/edit/${template.id}`)}
                    className="flex-1 inline-flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                  >
                    <PencilIcon className="w-4 h-4" />
                    Edit
                  </button>
                  {!template.is_default && (
                    <button
                      onClick={() => handleDelete(template.id)}
                      className={`px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                        deleteConfirm === template.id
                          ? 'bg-red-600 text-white hover:bg-red-700'
                          : 'bg-gray-100 text-red-600 hover:bg-red-50'
                      }`}
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EmailTemplates;
