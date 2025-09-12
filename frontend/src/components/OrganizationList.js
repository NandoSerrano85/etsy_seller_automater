import React from 'react';
import useOrganizationStore from '../stores/organizationStore';

const OrganizationList = ({ organizations, selectedOrgId, onOrganizationSelect, onRefresh }) => {
  const { organizationLoading } = useOrganizationStore();

  const getRoleBadgeColor = role => {
    switch (role) {
      case 'owner':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'admin':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'member':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatRole = role => {
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  if (organizationLoading && organizations.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-sage-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-sage-100 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-sage-200">
      <div className="p-6 border-b border-sage-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-sage-900">Organizations</h2>
          <button
            onClick={onRefresh}
            disabled={organizationLoading}
            className="p-2 text-sage-500 hover:text-sage-700 hover:bg-sage-50 rounded-lg transition-colors disabled:opacity-50"
            title="Refresh organizations"
          >
            <svg
              className={`w-5 h-5 ${organizationLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      <div className="p-6">
        {organizations.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-sage-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 8h5a2 2 0 002-2V9a2 2 0 00-2-2H9a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-sage-900 mb-2">No Organizations</h3>
            <p className="text-sage-600 mb-4">You haven't been added to any organizations yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {organizations.map(org => (
              <div
                key={org.id}
                onClick={() => onOrganizationSelect(org.id)}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedOrgId === org.id
                    ? 'border-sage-500 bg-sage-50 shadow-sm'
                    : 'border-sage-200 hover:border-sage-300'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-sage-900 truncate">{org.name}</h3>
                    {org.description && <p className="text-sm text-sage-600 mt-1 line-clamp-2">{org.description}</p>}
                    <div className="flex items-center mt-3 space-x-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleBadgeColor(
                          org.user_role
                        )}`}
                      >
                        {formatRole(org.user_role)}
                      </span>
                      {org.member_count && (
                        <span className="text-sm text-sage-500 flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                            />
                          </svg>
                          {org.member_count} members
                        </span>
                      )}
                    </div>
                  </div>

                  {org.settings?.is_active === false && (
                    <div className="ml-3">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
                        Inactive
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrganizationList;
