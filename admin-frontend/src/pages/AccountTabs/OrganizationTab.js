import React, { useState, useEffect } from 'react';
import useOrganizationStore from '../../stores/organizationStore';
import useAuthStore from '../../stores/authStore';
import organizationService from '../../services/organizationService';
import { useNotifications } from '../../components/NotificationSystem';
import OrganizationList from '../../components/OrganizationList';
import OrganizationDetails from '../../components/OrganizationDetails';
import CreateOrganizationModal from '../../components/CreateOrganizationModal';
import OrganizationSelector from '../../components/OrganizationSelector';

const OrganizationTab = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedOrgId, setSelectedOrgId] = useState(null);

  const { addNotification } = useNotifications();
  const { isUserAuthenticated } = useAuthStore();
  const {
    organizations,
    currentOrganization,
    organizationLoading,
    organizationError,
    setOrganizations,
    setCurrentOrganization,
    setOrganizationLoading,
    setOrganizationError,
    addOrganization,
  } = useOrganizationStore();

  // Load organizations on mount
  useEffect(() => {
    if (isUserAuthenticated) {
      loadOrganizations();
    }
  }, [isUserAuthenticated]);

  const loadOrganizations = async () => {
    setOrganizationLoading(true);
    setOrganizationError(null);

    try {
      const result = await organizationService.getUserOrganizations();
      if (result.success) {
        setOrganizations(result.data);

        // Set current organization if none selected
        if (result.data.length > 0 && !currentOrganization) {
          setCurrentOrganization(result.data[0]);
          setSelectedOrgId(result.data[0].id);
        }
      } else {
        setOrganizationError(result.error);
        addNotification({
          type: 'error',
          message: `Failed to load organizations: ${result.error}`,
        });
      }
    } catch (error) {
      setOrganizationError('Failed to load organizations');
      addNotification({
        type: 'error',
        message: 'Failed to load organizations',
      });
    } finally {
      setOrganizationLoading(false);
    }
  };

  const handleCreateOrganization = async orgData => {
    try {
      const result = await organizationService.createOrganization(orgData);
      if (result.success) {
        addOrganization(result.data);
        setShowCreateModal(false);
        addNotification({
          type: 'success',
          message: 'Organization created successfully!',
        });
      } else {
        addNotification({
          type: 'error',
          message: `Failed to create organization: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to create organization',
      });
    }
  };

  const handleOrganizationSelect = orgId => {
    setSelectedOrgId(orgId);
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      setCurrentOrganization(org);
    }
  };

  const selectedOrganization = selectedOrgId ? organizations.find(org => org.id === selectedOrgId) : null;

  if (organizationLoading && organizations.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
          <p className="text-sage-600">Loading organizations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-sage-900">Organizations</h2>
          <p className="text-sage-600 mt-1">Manage your organizations and team members</p>
        </div>

        <div className="flex items-center space-x-4">
          <OrganizationSelector onOrganizationChange={handleOrganizationSelect} selectedOrgId={selectedOrgId} />

          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Create Organization
          </button>
        </div>
      </div>

      {organizationError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Error:</p>
          <p>{organizationError}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Organization List */}
        <div className="lg:col-span-1">
          <OrganizationList
            organizations={organizations}
            selectedOrgId={selectedOrgId}
            onOrganizationSelect={handleOrganizationSelect}
            onRefresh={loadOrganizations}
          />
        </div>

        {/* Organization Details */}
        <div className="lg:col-span-2">
          {selectedOrganization ? (
            <OrganizationDetails organization={selectedOrganization} onOrganizationUpdate={loadOrganizations} />
          ) : (
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
              <h3 className="text-xl font-medium text-sage-900 mb-2">Select an Organization</h3>
              <p className="text-sage-600">
                Choose an organization from the list to view its details and manage members.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create Organization Modal */}
      {showCreateModal && (
        <CreateOrganizationModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateOrganization}
        />
      )}
    </div>
  );
};

export default OrganizationTab;
