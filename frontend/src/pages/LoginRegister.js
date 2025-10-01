import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const LoginRegister = () => {
  const [tab, setTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [shopName, setShopName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [registrationMode, setRegistrationMode] = useState('create'); // 'create' or 'join'

  const { login, register, isUserAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already logged in
  useEffect(() => {
    if (isUserAuthenticated) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isUserAuthenticated, navigate, location]);

  const validate = () => {
    if (!email || !password) {
      setError('Email and password are required.');
      return false;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setError('Please enter a valid email address.');
      return false;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return false;
    }
    if (tab === 'register' && password !== confirmPassword) {
      setError('Passwords do not match.');
      return false;
    }
    if (tab === 'register' && registrationMode === 'create' && !organizationName.trim()) {
      setError('Organization name is required.');
      return false;
    }
    if (tab === 'register' && registrationMode === 'join' && !inviteCode.trim()) {
      setError('Invite code is required to join an organization.');
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setError('');

    try {
      if (tab === 'login') {
        const result = await login(email, password);
        if (result.success) {
          if (result.needsOrganizationSelection) {
            navigate('/organization-select', { replace: true });
          } else {
            // Redirect to dashboard overview after login
            navigate('/?tab=overview', { replace: true });
          }
        } else {
          setError(result.error);
        }
      } else {
        const registrationData = {
          email,
          password,
          shop_name: shopName,
          registration_mode: registrationMode,
          ...(registrationMode === 'create' ? { organization_name: organizationName } : { invite_code: inviteCode }),
        };
        const result = await register(registrationData);
        if (result.success) {
          // Redirect to dashboard overview after registration
          navigate('/?tab=overview', { replace: true });
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      setError('An unexpected error occurred.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-xl border border-lavender-200 p-6 sm:p-8 w-full max-w-md">
        <div className="flex mb-6">
          <button
            className={`flex-1 py-2 sm:py-3 font-semibold rounded-l-lg transition-colors text-sm sm:text-base ${tab === 'login' ? 'bg-gradient-to-r from-lavender-500 to-lavender-600 text-white' : 'bg-sage-100 text-sage-700'}`}
            onClick={() => {
              setTab('login');
              setError('');
            }}
          >
            Login
          </button>
          <button
            className={`flex-1 py-2 sm:py-3 font-semibold rounded-r-lg transition-colors text-sm sm:text-base ${tab === 'register' ? 'bg-gradient-to-r from-lavender-500 to-lavender-600 text-white' : 'bg-sage-100 text-sage-700'}`}
            onClick={() => {
              setTab('register');
              setError('');
              setRegistrationMode('create');
            }}
          >
            Register
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-700 font-medium mb-1 text-sm sm:text-base">Email</label>
            <input
              type="email"
              className="w-full px-3 sm:px-4 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-lavender-500 focus:border-lavender-500 text-sm sm:text-base"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 font-medium mb-1 text-sm sm:text-base">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                className="w-full px-3 sm:px-4 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-lavender-500 focus:border-lavender-500 text-sm sm:text-base"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                required
              />
              <button
                type="button"
                className="absolute right-3 top-2 text-gray-400 hover:text-gray-600"
                onClick={() => setShowPassword(v => !v)}
                tabIndex={-1}
              >
                {showPassword ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.403-3.221 1.125-4.575M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm2.121 2.121A9.969 9.969 0 0021 12c0-5.523-4.477-10-10-10S1 6.477 1 12c0 1.657.403 3.221 1.125 4.575M4.222 4.222l15.556 15.556"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
          {tab === 'register' && (
            <div>
              <div>
                <label className="block text-gray-700 font-medium mb-1 text-sm sm:text-base">Confirm Password</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="w-full px-3 sm:px-4 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-lavender-500 focus:border-lavender-500 text-sm sm:text-base"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
              </div>

              {/* Registration Mode Selection */}
              <div className="mb-4">
                <label className="block text-gray-700 font-medium mb-2 text-sm sm:text-base">Registration Type</label>
                <div className="flex space-x-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="create"
                      checked={registrationMode === 'create'}
                      onChange={e => setRegistrationMode(e.target.value)}
                      className="mr-2"
                    />
                    <span className="text-sm">Create New Organization</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="join"
                      checked={registrationMode === 'join'}
                      onChange={e => setRegistrationMode(e.target.value)}
                      className="mr-2"
                    />
                    <span className="text-sm">Join Existing Organization</span>
                  </label>
                </div>
              </div>

              {registrationMode === 'create' && (
                <div className="mb-4">
                  <label
                    htmlFor="organization-name"
                    className="block text-gray-700 font-medium mb-1 text-sm sm:text-base"
                  >
                    Organization Name
                  </label>
                  <input
                    id="organization-name"
                    type="text"
                    value={organizationName}
                    onChange={e => setOrganizationName(e.target.value)}
                    className="w-full px-3 sm:px-4 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-lavender-500 focus:border-lavender-500 text-sm sm:text-base"
                    placeholder="Enter your organization name"
                    required
                  />
                </div>
              )}

              {registrationMode === 'join' && (
                <div className="mb-4">
                  <label htmlFor="invite-code" className="block text-gray-700 font-medium mb-1 text-sm sm:text-base">
                    Invite Code
                  </label>
                  <input
                    id="invite-code"
                    type="text"
                    value={inviteCode}
                    onChange={e => setInviteCode(e.target.value)}
                    className="w-full px-3 sm:px-4 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-lavender-500 focus:border-lavender-500 text-sm sm:text-base"
                    placeholder="Enter your invite code"
                    required
                  />
                </div>
              )}

              <div className="mb-4">
                <label htmlFor="shop-name" className="block text-gray-700 font-medium mb-1 text-sm sm:text-base">
                  Shop Name
                </label>
                <input
                  id="shop-name"
                  type="text"
                  value={shopName}
                  onChange={e => setShopName(e.target.value)}
                  required
                  className="w-full px-3 sm:px-4 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-lavender-500 focus:border-lavender-500 text-sm sm:text-base"
                  placeholder="Enter your shop name"
                />
              </div>
            </div>
          )}
          {error && <div className="bg-red-100 text-red-700 px-4 py-2 rounded-lg text-sm">{error}</div>}
          <button
            type="submit"
            className="w-full py-2 sm:py-3 bg-gradient-to-r from-lavender-500 to-lavender-600 text-white font-semibold rounded-lg hover:from-lavender-600 hover:to-lavender-700 transition-all duration-200 flex items-center justify-center text-sm sm:text-base shadow-sm hover:shadow-md"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center">
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>Loading...
              </span>
            ) : tab === 'login' ? (
              'Login'
            ) : (
              'Register'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginRegister;
