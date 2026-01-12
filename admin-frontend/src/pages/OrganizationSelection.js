import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useOrganizationStore from '../stores/organizationStore';
import organizationService from '../services/organizationService';
import { useNotifications } from '../components/NotificationSystem';

const OrganizationSelection = () => {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { setCurrentOrganization, setOrganizations: setStoreOrganizations } = useOrganizationStore();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  useEffect(() => {
    loadUserOrganizations();
  }, []);

  const loadUserOrganizations = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await organizationService.getUserOrganizations();
      if (result.success) {
        setOrganizations(result.data);
        setStoreOrganizations(result.data);

        // If user has only one organization, auto-select it
        if (result.data.length === 1) {
          handleOrganizationSelect(result.data[0]);
          return;
        }
      } else {
        setError(result.error);
      }
    } catch (error) {
      setError('Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  const handleOrganizationSelect = organization => {
    setCurrentOrganization(organization);
    addNotification({
      type: 'success',
      message: `Switched to ${organization.name}`,
    });
    navigate('/', { replace: true });
  };

  const handleCreateOrganization = () => {
    navigate('/organizations/new');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
          <p className="text-sage-600">Loading your organizations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50">
        <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-sage-900 mb-2">Error Loading Organizations</h2>
            <p className="text-sage-600 mb-4">{error}</p>
            <button
              onClick={loadUserOrganizations}
              className="bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-sage-900 mb-2">Select Your Organization</h1>
            <p className="text-sage-600">Choose which organization you'd like to work with today.</p>
          </div>

          {organizations.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-8 text-center">
              <div className="text-sage-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 8h5a2 2 0 002-2V9a2 2 0 00-2-2H9a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-sage-900 mb-2">No Organizations Found</h3>
              <p className="text-sage-600 mb-6">
                You don't belong to any organizations yet. Create your first organization to get started.
              </p>
              <button
                onClick={handleCreateOrganization}
                className="bg-sage-600 hover:bg-sage-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Create Organization
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {organizations.map(org => (
                <div
                  key={org.id}
                  onClick={() => handleOrganizationSelect(org)}
                  className="bg-white rounded-lg shadow-sm border border-sage-200 p-6 cursor-pointer transition-all hover:shadow-md hover:border-sage-300"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-xl font-semibold text-sage-900">{org.name}</h3>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            org.user_role === 'owner'
                              ? 'bg-purple-100 text-purple-800'
                              : org.user_role === 'admin'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {org.user_role.charAt(0).toUpperCase() + org.user_role.slice(1)}
                        </span>
                      </div>

                      {org.description && <p className="text-sage-600 text-sm mb-3">{org.description}</p>}

                      <div className="flex items-center text-sm text-sage-500 space-x-4">
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                            />
                          </svg>
                          {org.member_count || 0} members
                        </span>

                        {org.created_at && (
                          <span className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6v10a2 2 0 01-2 2h-4a2 2 0 01-2-2V7z"
                              />
                            </svg>
                            Created {new Date(org.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="text-sage-400">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))}

              <div className="text-center pt-6">
                <button
                  onClick={handleCreateOrganization}
                  className="text-sage-600 hover:text-sage-700 font-medium transition-colors"
                >
                  + Create New Organization
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrganizationSelection;
