import React, { useState, useEffect } from 'react';

const SystemLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const loadLogs = async () => {
      await new Promise(resolve => setTimeout(resolve, 700));
      setLogs([
        {
          id: '1',
          level: 'info',
          message: 'User john@example.com logged in',
          timestamp: new Date(),
          component: 'auth',
        },
        {
          id: '2',
          level: 'error',
          message: 'Print job failed for order #12345',
          timestamp: new Date(Date.now() - 60000),
          component: 'print',
        },
        {
          id: '3',
          level: 'warning',
          message: 'High memory usage detected',
          timestamp: new Date(Date.now() - 120000),
          component: 'system',
        },
        {
          id: '4',
          level: 'info',
          message: 'Backup completed successfully',
          timestamp: new Date(Date.now() - 180000),
          component: 'backup',
        },
        {
          id: '5',
          level: 'error',
          message: 'Database connection failed',
          timestamp: new Date(Date.now() - 240000),
          component: 'database',
        },
      ]);
      setLoading(false);
    };
    loadLogs();
  }, []);

  const getLevelColor = level => {
    switch (level) {
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'info':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getLevelIcon = level => {
    switch (level) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '📝';
    }
  };

  const filteredLogs = filter === 'all' ? logs : logs.filter(log => log.level === filter);

  if (loading) return <div className="animate-pulse h-64 bg-slate-200 rounded-lg"></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sage-500"
        >
          <option value="all">All Levels</option>
          <option value="error">Errors</option>
          <option value="warning">Warnings</option>
          <option value="info">Info</option>
        </select>
        <button className="px-4 py-2 bg-sage-600 text-white rounded-lg">Export Logs</button>
      </div>

      <div className="bg-white border rounded-lg">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">System Logs</h3>
        </div>
        <div className="divide-y max-h-96 overflow-y-auto">
          {filteredLogs.map(log => (
            <div key={log.id} className="px-6 py-3 flex items-start space-x-3">
              <span className="text-lg mt-0.5">{getLevelIcon(log.level)}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-900">{log.message}</p>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getLevelColor(log.level)}`}>
                      {log.level}
                    </span>
                    <span className="text-xs text-slate-500">{log.component}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-1">{log.timestamp.toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SystemLogs;
