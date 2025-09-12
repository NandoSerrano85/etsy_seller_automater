import React, { useState, useEffect } from 'react';
import { useNotifications } from '../NotificationSystem';

const OrganizationAdmin = () => {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { addNotification } = useNotifications();

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockOrgs = [
        {
          id: '1',
          name: 'Acme Corporation',
          description: 'Manufacturing company specializing in industrial tools',
          member_count: 25,
          created_at: '2024-01-15T10:00:00Z',
          settings: { is_active: true, plan: 'enterprise' },
          usage_stats: {
            print_jobs_this_month: 145,
            storage_used_mb: 2048,
            api_calls_this_month: 15420
          }
        },
        {
          id: '2',
          name: 'Design Studio Plus',
          description: 'Creative design agency for small businesses',
          member_count: 8,
          created_at: '2024-02-20T14:30:00Z',
          settings: { is_active: true, plan: 'professional' },
          usage_stats: {
            print_jobs_this_month: 67,
            storage_used_mb: 1024,
            api_calls_this_month: 8940
          }
        },
        {
          id: '3',
          name: 'Beta Test Co',
          description: 'Test organization for new features',
          member_count: 3,
          created_at: '2024-03-01T09:15:00Z',
          settings: { is_active: false, plan: 'starter' },
          usage_stats: {
            print_jobs_this_month: 12,
            storage_used_mb: 256,
            api_calls_this_month: 1250
          }
        }
      ];
      
      setOrganizations(mockOrgs);
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to load organizations',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStatusToggle = async (orgId, currentStatus) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setOrganizations(prev => prev.map(org => 
        org.id === orgId 
          ? { ...org, settings: { ...org.settings, is_active: !currentStatus } }
          : org
      ));
      
      addNotification({
        type: 'success',
        message: `Organization ${currentStatus ? 'deactivated' : 'activated'} successfully`,
      });
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to update organization status',
      });
    }
  };

  const filteredOrganizations = organizations.filter(org => {
    const matchesSearch = org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         org.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && org.settings.is_active) ||
                         (statusFilter === 'inactive' && !org.settings.is_active);
    
    return matchesSearch && matchesStatus;
  });

  const getPlanBadgeColor = (plan) => {
    switch (plan) {
      case 'enterprise':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'professional':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'starter':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-slate-200 rounded-lg w-1/3"></div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-slate-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0 sm:space-x-4">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
              placeholder="Search organizations..."
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          
          <button
            onClick={loadOrganizations}
            className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Organizations List */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900">
            Organizations ({filteredOrganizations.length})
          </h3>
        </div>

        {filteredOrganizations.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <div className="text-slate-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 8h5a2 2 0 002-2V9a2 2 0 00-2-2H9a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-slate-900 mb-2">No Organizations Found</h4>
            <p className="text-slate-600">
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filter criteria.'
                : 'No organizations have been created yet.'
              }
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {filteredOrganizations.map((org) => (
              <div key={org.id} className="px-6 py-4 hover:bg-slate-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-semibold text-slate-900">{org.name}</h4>
                      
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPlanBadgeColor(org.settings.plan)}`}
                      >
                        {org.settings.plan.charAt(0).toUpperCase() + org.settings.plan.slice(1)}
                      </span>
                      
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          org.settings.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {org.settings.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    
                    <p className="text-slate-600 text-sm mb-3">{org.description}</p>
                    
                    <div className="flex items-center text-sm text-slate-500 space-x-6">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                        </svg>
                        {org.member_count} members
                      </span>
                      
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6v10a2 2 0 01-2 2h-4a2 2 0 01-2-2V7z" />
                        </svg>
                        Created {new Date(org.created_at).toLocaleDateString()}
                      </span>
                      
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-9a2 2 0 00-2-2H9a2 2 0 00-2 2v9a2 2 0 002 2z" />
                        </svg>
                        {org.usage_stats.print_jobs_this_month} prints this month
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setSelectedOrg(selectedOrg === org.id ? null : org.id)}
                      className="px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-sage-500"
                    >
                      {selectedOrg === org.id ? 'Hide Details' : 'View Details'}
                    </button>
                    
                    <button
                      onClick={() => handleStatusToggle(org.id, org.settings.is_active)}
                      className={`px-3 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
                        org.settings.is_active
                          ? 'text-red-700 bg-red-100 hover:bg-red-200 focus:ring-red-500'
                          : 'text-green-700 bg-green-100 hover:bg-green-200 focus:ring-green-500'
                      }`}
                    >
                      {org.settings.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedOrg === org.id && (
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <h5 className="font-medium text-slate-900 mb-2">Usage Stats</h5>
                        <div className="space-y-1 text-sm text-slate-600">
                          <div>Print jobs: {org.usage_stats.print_jobs_this_month}</div>
                          <div>Storage: {(org.usage_stats.storage_used_mb / 1024).toFixed(1)} GB</div>
                          <div>API calls: {org.usage_stats.api_calls_this_month.toLocaleString()}</div>
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-slate-900 mb-2">Organization Info</h5>
                        <div className="space-y-1 text-sm text-slate-600">
                          <div>ID: {org.id}</div>
                          <div>Plan: {org.settings.plan}</div>
                          <div>Members: {org.member_count}</div>
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-slate-900 mb-2">Actions</h5>
                        <div className="space-y-2">
                          <button className="block w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded">
                            View Audit Log
                          </button>
                          <button className="block w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded">
                            Export Data
                          </button>
                          <button className="block w-full text-left px-3 py-2 text-sm text-red-700 hover:bg-red-50 rounded">
                            Delete Organization
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrganizationAdmin;