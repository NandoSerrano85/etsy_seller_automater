import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import { useNotifications } from '../../../components/NotificationSystem';
import axios from 'axios';
import {
  UserGroupIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
} from '@heroicons/react/24/outline';

const EmailSubscribers = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();

  const [subscribers, setSubscribers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterTags, setFilterTags] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSubscriber, setEditingSubscriber] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadSubscribers();
  }, [searchQuery, filterStatus, filterTags]);

  const loadSubscribers = async () => {
    try {
      setLoading(true);
      const params = {};
      if (searchQuery) params.search = searchQuery;
      if (filterStatus !== 'all') params.is_subscribed = filterStatus === 'subscribed';
      if (filterTags) params.tags = filterTags;

      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/emails/subscribers`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });

      setSubscribers(response.data || []);
    } catch (error) {
      console.error('Error loading subscribers:', error);
      addNotification('error', 'Failed to load subscribers');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSubscriber = async subscriberData => {
    try {
      if (editingSubscriber) {
        await axios.put(`${API_BASE_URL}/api/ecommerce/admin/emails/subscribers/${editingSubscriber.id}`, subscriberData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        addNotification('success', 'Subscriber updated successfully');
      } else {
        await axios.post(`${API_BASE_URL}/api/ecommerce/admin/emails/subscribers`, subscriberData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        addNotification('success', 'Subscriber added successfully');
      }
      setShowAddModal(false);
      setEditingSubscriber(null);
      loadSubscribers();
    } catch (error) {
      console.error('Error saving subscriber:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to save subscriber');
    }
  };

  const handleDelete = async subscriberId => {
    if (deleteConfirm !== subscriberId) {
      setDeleteConfirm(subscriberId);
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/ecommerce/admin/emails/subscribers/${subscriberId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      addNotification('success', 'Subscriber deleted successfully');
      loadSubscribers();
    } catch (error) {
      console.error('Error deleting subscriber:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to delete subscriber');
    } finally {
      setDeleteConfirm(null);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/emails/subscribers/export`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `subscribers-${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      addNotification('success', 'Subscribers exported successfully');
    } catch (error) {
      console.error('Error exporting subscribers:', error);
      addNotification('error', 'Failed to export subscribers');
    }
  };

  const formatDate = dateString => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  if (loading && subscribers.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading subscribers...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Email Subscribers</h1>
          <p className="text-gray-600 mt-1">Manage your email subscriber list and segments</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            Export CSV
          </button>
          <button
            onClick={() => {
              setEditingSubscriber(null);
              setShowAddModal(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            Add Subscriber
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="w-5 h-5 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-700">Search & Filters</h3>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search by email..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="all">All Status</option>
              <option value="subscribed">Subscribed</option>
              <option value="unsubscribed">Unsubscribed</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
            <input
              type="text"
              value={filterTags}
              onChange={e => setFilterTags(e.target.value)}
              placeholder="Filter by tags..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
        </div>
      </div>

      {/* Subscribers Table */}
      {subscribers.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <UserGroupIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No subscribers found</h3>
          <p className="text-gray-600 mb-6">Add your first subscriber to get started</p>
          <button
            onClick={() => {
              setEditingSubscriber(null);
              setShowAddModal(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <PlusIcon className="w-5 h-5" />
            Add Subscriber
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Sent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Opened
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Sent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {subscribers.map(subscriber => (
                  <tr key={subscriber.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{subscriber.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex flex-wrap gap-1">
                        {subscriber.tags && subscriber.tags.length > 0 ? (
                          subscriber.tags.map((tag, idx) => (
                            <span key={idx} className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="text-gray-400">No tags</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{subscriber.total_sent || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{subscriber.total_opened || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formatDate(subscriber.last_sent_at)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          subscriber.is_subscribed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {subscriber.is_subscribed ? 'Subscribed' : 'Unsubscribed'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setEditingSubscriber(subscriber);
                            setShowAddModal(true);
                          }}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(subscriber.id)}
                          className={`p-2 rounded-lg transition-colors ${
                            deleteConfirm === subscriber.id
                              ? 'bg-red-600 text-white hover:bg-red-700'
                              : 'text-red-600 hover:bg-red-50'
                          }`}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <SubscriberModal
          subscriber={editingSubscriber}
          onSave={handleSaveSubscriber}
          onClose={() => {
            setShowAddModal(false);
            setEditingSubscriber(null);
          }}
        />
      )}
    </div>
  );
};

const SubscriberModal = ({ subscriber, onSave, onClose }) => {
  const [email, setEmail] = useState(subscriber?.email || '');
  const [tags, setTags] = useState(subscriber?.tags?.join(', ') || '');
  const [customerId, setCustomerId] = useState(subscriber?.customer_id || '');
  const [isSubscribed, setIsSubscribed] = useState(subscriber?.is_subscribed ?? true);

  const handleSubmit = e => {
    e.preventDefault();
    const subscriberData = {
      email,
      tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      customer_id: customerId || null,
      is_subscribed: isSubscribed,
    };
    onSave(subscriberData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {subscriber ? 'Edit Subscriber' : 'Add New Subscriber'}
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
            <input
              type="text"
              value={tags}
              onChange={e => setTags(e.target.value)}
              placeholder="vip, customer, newsletter (comma-separated)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">Separate tags with commas</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Customer ID</label>
            <input
              type="text"
              value={customerId}
              onChange={e => setCustomerId(e.target.value)}
              placeholder="Optional"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="isSubscribed"
              checked={isSubscribed}
              onChange={e => setIsSubscribed(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="isSubscribed" className="ml-2 block text-sm text-gray-700">
              Subscribed to emails
            </label>
          </div>

          <div className="flex items-center gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {subscriber ? 'Update' : 'Add'} Subscriber
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmailSubscribers;
