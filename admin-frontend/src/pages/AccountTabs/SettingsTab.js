import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useApi } from '../../hooks/useApi';
import useOrganizationStore from '../../stores/organizationStore';
import { useSubscription } from '../../hooks/useSubscription';
import { TierBadge } from '../../components/subscription';

// Settings Tab Component
const SettingsTab = () => {
  const { user, etsyUserInfo, etsyShopInfo } = useAuth();
  const api = useApi();
  const { currentOrganization, getUserRole } = useOrganizationStore();
  const { tierConfig } = useSubscription();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handlePasswordChange = async e => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage('New passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      setMessage('New password must be at least 6 characters');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setMessage(response.message || 'Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error('Password change error:', error);
      setMessage(error.message || 'Failed to change password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="card p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Account Settings</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Password Change Section */}
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-gray-900">Change Password</h3>

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
                  Current Password
                </label>
                <input
                  type="password"
                  id="currentPassword"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  id="newPassword"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {message && (
                <div
                  className={`p-3 rounded-lg ${
                    message.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {message}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                  loading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {loading ? 'Changing Password...' : 'Change Password'}
              </button>
            </form>
          </div>

          {/* Account Information Section */}
          {user && (
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-900">Account Information</h3>

              <div className="bg-gray-50 p-6 rounded-lg space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                  <p className="text-gray-900 font-medium">{user?.email || 'Not available'}</p>
                </div>

                {/* User Role */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Your Role</label>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        getUserRole() === 'owner'
                          ? 'bg-purple-100 text-purple-800'
                          : getUserRole() === 'admin'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {getUserRole() === 'owner' && (
                        <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      )}
                      {getUserRole().charAt(0).toUpperCase() + getUserRole().slice(1)}
                    </span>
                  </div>
                </div>

                {/* Subscription Plan */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subscription Plan</label>
                  <div className="flex items-center space-x-3">
                    <TierBadge showPrice />
                    {tierConfig && tierConfig.name !== 'Full' && (
                      <a href="/subscription" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                        Upgrade
                      </a>
                    )}
                  </div>
                </div>

                {/* Current Organization */}
                {currentOrganization && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Current Organization</label>
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center">
                          <span className="text-white font-bold text-lg">
                            {currentOrganization.name?.charAt(0).toUpperCase() || 'O'}
                          </span>
                        </div>
                        <div>
                          <p className="text-gray-900 font-semibold">{currentOrganization.name}</p>
                          <p className="text-sm text-gray-500">{currentOrganization.description || 'No description'}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {etsyShopInfo && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Shop Name</label>
                    <p className="text-gray-900 font-medium">{etsyShopInfo.shop_name}</p>
                  </div>
                )}

                {etsyUserInfo && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Etsy Name</label>
                    <p className="text-gray-900 font-medium">
                      {etsyUserInfo.first_name} {etsyUserInfo.last_name}
                    </p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Account Created</label>
                  <p className="text-gray-900">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Connection Status</label>
                  <div className="flex items-center flex-wrap gap-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Account Active
                    </span>
                    {etsyShopInfo && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Etsy Connected
                      </span>
                    )}
                    {currentOrganization && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        Organization: {currentOrganization.name}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsTab;
