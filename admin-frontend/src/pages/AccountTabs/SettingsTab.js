import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useApi } from '../../hooks/useApi';
import { useSubscription } from '../../hooks/useSubscription';
import { TierBadge } from '../../components/subscription';

// Settings Tab Component
const SettingsTab = () => {
  const { user, etsyUserInfo, etsyShopInfo } = useAuth();
  const api = useApi();
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
                        user?.role === 'admin' || user?.role === 'super_admin'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {(user?.role || 'user').charAt(0).toUpperCase() + (user?.role || 'user').slice(1)}
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
