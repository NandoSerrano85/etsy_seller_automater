import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import { useNotifications } from '../../../components/NotificationSystem';
import axios from 'axios';
import { ChartBarIcon, EnvelopeIcon, CursorArrowRaysIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

const EmailAnalytics = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('last_30_days');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadAnalytics();
  }, [dateRange, startDate, endDate]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const params = {};

      if (dateRange === 'custom') {
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
      } else if (dateRange === 'last_7_days') {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 7);
        params.start_date = start.toISOString().split('T')[0];
        params.end_date = end.toISOString().split('T')[0];
      } else if (dateRange === 'last_90_days') {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 90);
        params.start_date = start.toISOString().split('T')[0];
        params.end_date = end.toISOString().split('T')[0];
      }

      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/emails/analytics/summary`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });

      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      addNotification('error', 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading analytics...</span>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No analytics data available</p>
      </div>
    );
  }

  const { summary } = analytics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Email Analytics</h1>
          <p className="text-gray-600 mt-1">Track your email performance and engagement metrics</p>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
            <select
              value={dateRange}
              onChange={e => setDateRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="last_7_days">Last 7 Days</option>
              <option value="last_30_days">Last 30 Days</option>
              <option value="last_90_days">Last 90 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>

          {dateRange === 'custom' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Sent */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <EnvelopeIcon className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Total Sent</p>
          <p className="text-3xl font-bold text-gray-900">{summary.total_sent.toLocaleString()}</p>
        </div>

        {/* Delivery Rate */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Delivery Rate</p>
          <p className="text-3xl font-bold text-gray-900">{summary.delivery_rate.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">{summary.total_delivered.toLocaleString()} delivered</p>
        </div>

        {/* Open Rate */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <EnvelopeIcon className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Open Rate</p>
          <p className="text-3xl font-bold text-gray-900">{summary.open_rate.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">{summary.total_opened.toLocaleString()} opened</p>
        </div>

        {/* Click Rate */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <CursorArrowRaysIcon className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Click Rate</p>
          <p className="text-3xl font-bold text-gray-900">{summary.click_rate.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">{summary.total_clicked.toLocaleString()} clicked</p>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Breakdown by Email Type */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Emails by Type</h3>
          <div className="space-y-4">
            {Object.entries(summary.by_email_type || {}).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm text-gray-700 capitalize">{type.replace('_', ' ')}</span>
                <span className="text-sm font-semibold text-gray-900">{count.toLocaleString()}</span>
              </div>
            ))}
            {Object.keys(summary.by_email_type || {}).length === 0 && (
              <p className="text-sm text-gray-500">No data available</p>
            )}
          </div>
        </div>

        {/* Additional Metrics */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Total Bounced</span>
              <span className="text-sm font-semibold text-red-600">{summary.total_bounced.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Total Failed</span>
              <span className="text-sm font-semibold text-red-600">{summary.total_failed.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Success Rate</span>
              <span className="text-sm font-semibold text-green-600">
                {(
                  ((summary.total_sent - summary.total_bounced - summary.total_failed) / summary.total_sent) *
                  100
                ).toFixed(1)}
                %
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Overview</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Count</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Percentage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 text-sm text-gray-900">Sent</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">{summary.total_sent.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">100%</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm text-gray-900">Delivered</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">
                  {summary.total_delivered.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                  {summary.delivery_rate.toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm text-gray-900">Opened</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">{summary.total_opened.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-right text-purple-600 font-medium">
                  {summary.open_rate.toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm text-gray-900">Clicked</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">{summary.total_clicked.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-right text-indigo-600 font-medium">
                  {summary.click_rate.toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm text-gray-900">Bounced</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">{summary.total_bounced.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-right text-red-600 font-medium">
                  {((summary.total_bounced / summary.total_sent) * 100).toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm text-gray-900">Failed</td>
                <td className="px-4 py-3 text-sm text-right text-gray-900">{summary.total_failed.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-right text-red-600 font-medium">
                  {((summary.total_failed / summary.total_sent) * 100).toFixed(1)}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <InformationCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-900">
          <p className="font-medium mb-1">About Email Analytics</p>
          <p>
            Metrics are updated in real-time via SendGrid webhooks. Open and click rates are calculated based on
            delivered emails. Industry average open rate is around 20-25% for transactional emails.
          </p>
        </div>
      </div>
    </div>
  );
};

export default EmailAnalytics;
