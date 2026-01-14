import { useState, useEffect } from 'react';
import organizationService from '../services/organizationService';
import useOrganizationStore from '../stores/organizationStore';
import { useNotifications } from './NotificationSystem';
import EditOrganizationModal from './EditOrganizationModal';
import InviteMemberModal from './InviteMemberModal';

const OrganizationDetails = ({ organization, onOrganizationUpdate }) => {
  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);

  const { addNotification } = useNotifications();
  const { hasAdminAccess, isOwner } = useOrganizationStore();

  useEffect(() => {
    if (organization?.id) {
      loadMembers();
    }
  }, [organization?.id]);

  const loadMembers = async () => {
    if (!organization?.id) return;

    setMembersLoading(true);
    try {
      const result = await organizationService.getOrganizationMembers(organization.id);
      if (result.success) {
        setMembers(Array.isArray(result.data) ? result.data : []);
      } else {
        setMembers([]);
        addNotification({
          type: 'error',
          message: `Failed to load members: ${result.error}`,
        });
      }
    } catch (error) {
      setMembers([]);
      addNotification({
        type: 'error',
        message: 'Failed to load organization members',
      });
    } finally {
      setMembersLoading(false);
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      const result = await organizationService.updateMemberRole(organization.id, userId, newRole);
      if (result.success) {
        setMembers(prev => prev.map(member => (member.user_id === userId ? { ...member, role: newRole } : member)));
        addNotification({
          type: 'success',
          message: 'Member role updated successfully',
        });
      } else {
        addNotification({
          type: 'error',
          message: `Failed to update role: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to update member role',
      });
    }
  };

  const handleRemoveMember = async userId => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;

    try {
      const result = await organizationService.removeMember(organization.id, userId);
      if (result.success) {
        setMembers(prev => prev.filter(member => member.user_id !== userId));
        addNotification({
          type: 'success',
          message: 'Member removed successfully',
        });
      } else {
        addNotification({
          type: 'error',
          message: `Failed to remove member: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to remove member',
      });
    }
  };

  const handleInviteMember = async inviteData => {
    try {
      const result = await organizationService.inviteUser(organization.id, inviteData);
      if (result.success) {
        setShowInviteModal(false);
        loadMembers(); // Reload members to show new invite
        addNotification({
          type: 'success',
          message: 'Invitation sent successfully',
        });
      } else {
        addNotification({
          type: 'error',
          message: `Failed to send invitation: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to send invitation',
      });
    }
  };

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
    if (!role || typeof role !== 'string') return 'Unknown';
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  if (!organization) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-8 text-center">
        <p className="text-sage-600">No organization selected</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Organization Info */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200">
        <div className="p-6 border-b border-sage-200">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h2 className="text-2xl font-semibold text-sage-900 mb-2">{organization.name}</h2>
              {organization.description && <p className="text-sage-600 mb-4">{organization.description}</p>}
              <div className="flex items-center space-x-4 text-sm text-sage-500">
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6v10a2 2 0 01-2 2h-4a2 2 0 01-2-2V7z"
                    />
                  </svg>
                  Created {new Date(organization.created_at).toLocaleDateString()}
                </span>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleBadgeColor(
                    organization.user_role
                  )}`}
                >
                  Your role: {formatRole(organization.user_role)}
                </span>
              </div>
            </div>

            {hasAdminAccess() && (
              <button
                onClick={() => setShowEditModal(true)}
                className="px-4 py-2 text-sage-600 hover:text-sage-800 hover:bg-sage-50 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Organization Settings */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-sage-900 mb-4">Settings</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-sage-500">Status:</span>
              <span className={`ml-2 ${organization.settings?.is_active ? 'text-green-600' : 'text-yellow-600'}`}>
                {organization.settings?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <span className="text-sage-500">Members:</span>
              <span className="ml-2 text-sage-900">{members.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Members Section */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200">
        <div className="p-6 border-b border-sage-200">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-semibold text-sage-900">Members</h3>
            {hasAdminAccess() && (
              <button
                onClick={() => setShowInviteModal(true)}
                className="bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Invite Member
              </button>
            )}
          </div>
        </div>

        <div className="p-6">
          {membersLoading ? (
            <div className="animate-pulse space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="h-10 w-10 bg-sage-200 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-sage-200 rounded w-1/4 mb-2"></div>
                    <div className="h-3 bg-sage-200 rounded w-1/3"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : members.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-sage-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                  />
                </svg>
              </div>
              <h4 className="text-lg font-medium text-sage-900 mb-2">No Members</h4>
              <p className="text-sage-600">
                {hasAdminAccess()
                  ? 'Start building your team by inviting members.'
                  : 'No members have been added to this organization yet.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {members.map(member => (
                <div
                  key={member.user_id}
                  className="flex items-center justify-between p-4 border border-sage-200 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-sage-300 rounded-full flex items-center justify-center">
                      <span className="text-sage-700 font-medium text-sm">
                        {member.user_name?.charAt(0)?.toUpperCase() || member.email?.charAt(0)?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <h4 className="font-medium text-sage-900">{member.user_name || member.email}</h4>
                      <p className="text-sm text-sage-500">{member.email}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleBadgeColor(
                        member.role
                      )}`}
                    >
                      {formatRole(member.role)}
                    </span>

                    {hasAdminAccess() && member.role !== 'owner' && (
                      <div className="flex items-center space-x-2">
                        <select
                          value={member.role}
                          onChange={e => handleUpdateRole(member.user_id, e.target.value)}
                          className="text-sm border border-sage-300 rounded px-2 py-1"
                        >
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                          {isOwner() && <option value="owner">Owner</option>}
                        </select>

                        <button
                          onClick={() => handleRemoveMember(member.user_id)}
                          className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                          title="Remove member"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showEditModal && (
        <EditOrganizationModal
          isOpen={showEditModal}
          organization={organization}
          onClose={() => setShowEditModal(false)}
          onSubmit={() => {
            setShowEditModal(false);
            onOrganizationUpdate();
          }}
        />
      )}

      {showInviteModal && (
        <InviteMemberModal
          isOpen={showInviteModal}
          organizationId={organization.id}
          onClose={() => setShowInviteModal(false)}
          onSubmit={handleInviteMember}
        />
      )}
    </div>
  );
};

export default OrganizationDetails;
