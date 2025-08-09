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
  const [registerError, setRegisterError] = useState('');
  
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
    setError('');
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setError('');
    
    try {
      if (tab === 'login') {
        const result = await login(email, password);
        if (result.success) {
          navigate('/connect-etsy', { replace: true });
        } else {
          setError(result.error);
        }
      } else {
        const result = await register(email, password, confirmPassword, shopName);
        if (result.success) {
          navigate('/', { replace: true });
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
            onClick={() => { setTab('login'); setError(''); }}
          >
            Login
          </button>
          <button
            className={`flex-1 py-2 sm:py-3 font-semibold rounded-r-lg transition-colors text-sm sm:text-base ${tab === 'register' ? 'bg-gradient-to-r from-lavender-500 to-lavender-600 text-white' : 'bg-sage-100 text-sage-700'}`}
            onClick={() => { setTab('register'); setError(''); }}
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
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.403-3.221 1.125-4.575M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm2.121 2.121A9.969 9.969 0 0021 12c0-5.523-4.477-10-10-10S1 6.477 1 12c0 1.657.403 3.221 1.125 4.575M4.222 4.222l15.556 15.556" /></svg>
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
              <div className="mb-4">
                <label htmlFor="shop-name" className="block text-sm font-medium text-gray-700">Shop Name</label>
                <input
                  id="shop-name"
                  type="text"
                  value={shopName}
                  onChange={e => setShopName(e.target.value)}
                  required
                  className="input-field"
                />
              </div>
            </div>
          )}
          {error && (
            <div className="bg-red-100 text-red-700 px-4 py-2 rounded-lg text-sm">{error}</div>
          )}
          <button
            type="submit"
            className="w-full py-2 sm:py-3 bg-gradient-to-r from-lavender-500 to-lavender-600 text-white font-semibold rounded-lg hover:from-lavender-600 hover:to-lavender-700 transition-all duration-200 flex items-center justify-center text-sm sm:text-base shadow-sm hover:shadow-md"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center"><span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>Loading...</span>
            ) : (
              tab === 'login' ? 'Login' : 'Register'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginRegister; 