import React, { useState, useEffect } from 'react';
import { useNotifications } from '../NotificationSystem';

const SystemOverview = () => {
  const [systemStats, setSystemStats] = useState({
    totalUsers: 0,
    totalOrganizations: 0,
    activePrintJobs: 0,
    totalPrinters: 0,
    systemUptime: '0 days',
    lastBackup: null,
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [systemHealth, setSystemHealth] = useState({
    database: 'healthy',
    storage: 'healthy',
    printQueue: 'healthy',
    api: 'healthy',
  });
  const [loading, setLoading] = useState(true);

  const { addNotification } = useNotifications();

  useEffect(() => {
    loadSystemOverview();
  }, []);

  const loadSystemOverview = async () => {
    setLoading(true);
    try {
      // Simulate loading system data
      // In a real app, this would make API calls to fetch actual system metrics
      await new Promise(resolve => setTimeout(resolve, 1000));

      setSystemStats({
        totalUsers: 127,
        totalOrganizations: 23,
        activePrintJobs: 8,
        totalPrinters: 45,
        systemUptime: '12 days, 4 hours',
        lastBackup: new Date().toISOString(),
      });

      setRecentActivity([
        {
          id: 1,
          type: 'print_job',
          message: 'Print job completed for Order #12345',
          timestamp: new Date(Date.now() - 5 * 60 * 1000),
        },
        {
          id: 2,
          type: 'user_login',
          message: 'New user registration: john@example.com',
          timestamp: new Date(Date.now() - 15 * 60 * 1000),
        },
        {
          id: 3,
          type: 'organization',
          message: 'Organization "Acme Corp" upgraded plan',
          timestamp: new Date(Date.now() - 30 * 60 * 1000),
        },
        {
          id: 4,
          type: 'system',
          message: 'System backup completed successfully',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        },
        {
          id: 5,
          type: 'printer',
          message: 'Printer "HP LaserJet Pro" went offline',
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
        },
      ]);

      setSystemHealth({
        database: 'healthy',
        storage: 'healthy',
        printQueue: 'warning',
        api: 'healthy',
      });
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to load system overview',
      });
    } finally {
      setLoading(false);
    }
  };

  const getHealthStatusColor = status => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getActivityIcon = type => {
    switch (type) {
      case 'print_job':
        return '🖨️';
      case 'user_login':
        return '👤';
      case 'organization':
        return '🏢';
      case 'system':
        return '⚙️';
      case 'printer':
        return '🖨️';
      default:
        return '📝';
    }
  };

  const formatTimeAgo = timestamp => {
    const now = new Date();
    const diff = now - new Date(timestamp);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 bg-slate-200 rounded-lg"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 bg-slate-200 rounded-lg"></div>
          <div className="h-64 bg-slate-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                <span className="text-blue-600">👥</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Total Users</p>
              <p className="text-2xl font-semibold text-slate-900">{systemStats.totalUsers}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                <span className="text-green-600">🏢</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Organizations</p>
              <p className="text-2xl font-semibold text-slate-900">{systemStats.totalOrganizations}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                <span className="text-yellow-600">🖨️</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Active Print Jobs</p>
              <p className="text-2xl font-semibold text-slate-900">{systemStats.activePrintJobs}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                <span className="text-purple-600">🖨️</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-slate-600">Total Printers</p>
              <p className="text-2xl font-semibold text-slate-900">{systemStats.totalPrinters}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <div className="bg-white border border-slate-200 rounded-lg">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900">System Health</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(systemHealth).map(([component, status]) => (
                <div key={component} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div
                      className={`w-3 h-3 rounded-full mr-3 ${
                        status === 'healthy' ? 'bg-green-500' : status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                    ></div>
                    <span className="text-sm font-medium text-slate-700 capitalize">
                      {component.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getHealthStatusColor(status)}`}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t border-slate-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">System Uptime:</span>
                <span className="font-medium text-slate-900">{systemStats.systemUptime}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-slate-600">Last Backup:</span>
                <span className="font-medium text-slate-900">
                  {systemStats.lastBackup ? new Date(systemStats.lastBackup).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white border border-slate-200 rounded-lg">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentActivity.map(activity => (
                <div key={activity.id} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <span className="text-lg">{getActivityIcon(activity.type)}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-900">{activity.message}</p>
                    <p className="text-xs text-slate-500 mt-1">{formatTimeAgo(activity.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="p-6 border-b border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => addNotification({ type: 'info', message: 'System backup initiated' })}
              className="flex items-center justify-center px-4 py-3 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors"
            >
              <span className="mr-2">💾</span>
              Backup System
            </button>

            <button
              onClick={() => addNotification({ type: 'info', message: 'Print queue cleared' })}
              className="flex items-center justify-center px-4 py-3 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-medium transition-colors"
            >
              <span className="mr-2">🗑️</span>
              Clear Print Queue
            </button>

            <button
              onClick={() => addNotification({ type: 'info', message: 'System maintenance mode enabled' })}
              className="flex items-center justify-center px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
            >
              <span className="mr-2">⚠️</span>
              Maintenance Mode
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview;
