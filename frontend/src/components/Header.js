import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-gray-900">Etsy Seller Automaker</h1>
          </Link>
          
          {isAuthenticated() ? (
            <nav className="flex items-center space-x-8">
              <Link to="/" className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium">
                Home
              </Link>
              <Link to="/mask-creator" className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium">
                Mask Creator
              </Link>
              <a 
                href="https://developer.etsy.com/documentation/essentials/authentication" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium"
              >
                Documentation
              </a>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  Welcome, {user?.email}
                </span>
                <button 
                  onClick={handleLogout} 
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors duration-200 font-medium"
                >
                  Logout
                </button>
              </div>
            </nav>
          ) : (
            <nav className="flex items-center space-x-4">
              <Link 
                to="/login" 
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 font-medium"
              >
                Login
              </Link>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header; 