import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import { useNotifications } from '../components/NotificationSystem';
import SystemOverview from '../components/admin/SystemOverview';
import UserManagement from '../components/admin/UserManagement';
import SystemLogs from '../components/admin/SystemLogs';
import PrintJobMonitor from '../components/admin/PrintJobMonitor';

const AdminDashboard = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'overview');
  const [loading, setLoading] = useState(false);

  const { addNotification } = useNotifications();
  const { isUserAuthenticated, user } = useAuthStore();

  // Update URL when tab changes
  useEffect(() => {
    setSearchParams({ tab: activeTab });
  }, [activeTab, setSearchParams]);

  // Check if user has admin access
  const isAuthorized = user?.role === 'admin' || user?.role === 'super_admin';

  if (!isUserAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-sage-900 mb-2">Authentication Required</h2>
          <p className="text-sage-600">Please log in to access the admin dashboard.</p>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold text-sage-900 mb-2">Access Denied</h2>
          <p className="text-sage-600">You don't have permission to access the admin dashboard.</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'System Overview', icon: '📊' },
    { id: 'users', name: 'User Management', icon: '👥' },
    { id: 'print-jobs', name: 'Print Jobs', icon: '🖨️' },
    { id: 'logs', name: 'System Logs', icon: '📋' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <SystemOverview />;
      case 'users':
        return <UserManagement />;
      case 'print-jobs':
        return <PrintJobMonitor />;
      case 'logs':
        return <SystemLogs />;
      default:
        return <SystemOverview />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-25 to-sage-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Admin Dashboard</h1>
              <p className="text-slate-600 mt-2">System administration and operations management</p>
            </div>

            <div className="flex items-center space-x-4">
              <div className="bg-white rounded-lg px-4 py-2 border border-slate-200">
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-slate-600">System Operational</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 mb-8">
          <div className="border-b border-slate-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-sage-500 text-sage-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="flex flex-col items-center space-y-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
                  <p className="text-slate-600">Loading...</p>
                </div>
              </div>
            ) : (
              renderTabContent()
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
