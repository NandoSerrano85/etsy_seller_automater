import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useApi } from '../../hooks/useApi';

// Settings Tab Component
const SettingsTab = () => {
    const { user } = useAuth();
    const api = useApi();
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
  
    const handlePasswordChange = async (e) => {
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
          new_password: newPassword
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
                    onChange={(e) => setCurrentPassword(e.target.value)}
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
                    onChange={(e) => setNewPassword(e.target.value)}
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
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
  
                {message && (
                  <div className={`p-3 rounded-lg ${
                    message.includes('successfully') 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {message}
                  </div>
                )}
  
                <button
                  type="submit"
                  disabled={loading}
                  className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                    loading 
                      ? 'bg-gray-400 text-white cursor-not-allowed' 
                      : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  {loading ? 'Changing Password...' : 'Change Password'}
                </button>
              </form>
            </div>
  
            {/* Account Information Section */}
            { user && (
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-gray-900">Account Information</h3>
              
              <div className="bg-gray-50 p-6 rounded-lg space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <p className="text-gray-900 font-medium">{user?.email}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Account Created
                  </label>
                  <p className="text-gray-900">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Account Status
                  </label>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
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