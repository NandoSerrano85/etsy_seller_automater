import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [showAccountDropdown, setShowAccountDropdown] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const closeMobileMenu = () => {
    console.log('Closing mobile menu');
    setShowMobileMenu(false);
    setShowAccountDropdown(false);
  };

  return (
    <>
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2" onClick={closeMobileMenu}>
              <h1 className="text-lg sm:text-xl font-bold text-gray-900">Etsy Seller Automaker</h1>
            </Link>
            
            {/* Desktop Navigation */}
            {isAuthenticated() ? (
              <nav className="hidden md:flex items-center space-x-6 lg:space-x-8">
                <Link to="/" className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium">
                  Home
                </Link>
                <Link to="/mockup-creator" className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium">
                  Mockup Creator
                </Link>
                <a 
                  href="http://localhost:3003/docs" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium"
                >
                  Documentation
                </a>
                <div className="relative">
                  <button 
                    onClick={() => setShowAccountDropdown(!showAccountDropdown)}
                    className="flex items-center space-x-2 text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium"
                  >
                    <span>Account</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {showAccountDropdown && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                      <Link
                        to="/account"
                        onClick={() => setShowAccountDropdown(false)}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Account Settings
                      </Link>
                      <hr className="my-1" />
                      <button 
                        onClick={handleLogout} 
                        className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </nav>
            ) : (
              <nav className="hidden md:flex items-center space-x-4">
                <Link 
                  to="/login" 
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 font-medium"
                >
                  Login
                </Link>
              </nav>
            )}

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => {
                  console.log('Mobile menu button clicked, current state:', showMobileMenu);
                  setShowMobileMenu(!showMobileMenu);
                }}
                className="text-gray-700 hover:text-blue-600 transition-colors duration-200 p-2 -mr-2"
                aria-label="Toggle mobile menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {showMobileMenu ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>

          {/* Mobile Navigation - Popover */}
          {showMobileMenu && isAuthenticated() && (
            <div className="md:hidden fixed top-16 left-0 right-0 bg-white shadow-lg border-b border-gray-200 z-50 transform transition-transform duration-200 ease-in-out rounded-b-lg">
              <nav className="flex flex-col space-y-2 p-4">
                <Link 
                  to="/" 
                  className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium px-4 py-3 block rounded-lg hover:bg-gray-50"
                  onClick={closeMobileMenu}
                >
                  Home
                </Link>
                <Link 
                  to="/mockup-creator" 
                  className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium px-4 py-3 block rounded-lg hover:bg-gray-50"
                  onClick={closeMobileMenu}
                >
                  Mockup Creator
                </Link>
                <a 
                  href="http://localhost:3003/docs" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium px-4 py-3 block rounded-lg hover:bg-gray-50"
                  onClick={closeMobileMenu}
                >
                  Documentation
                </a>
                <div className="border-t border-gray-200 pt-4 space-y-2">
                  <Link
                    to="/account"
                    onClick={closeMobileMenu}
                    className="block px-4 py-3 text-gray-700 hover:text-blue-600 transition-colors duration-200 font-medium rounded-lg hover:bg-gray-50"
                  >
                    Account Settings
                  </Link>
                  <button 
                    onClick={() => {
                      handleLogout();
                      closeMobileMenu();
                    }} 
                    className="block w-full text-left px-4 py-3 text-red-600 hover:text-red-700 transition-colors duration-200 font-medium rounded-lg hover:bg-red-50"
                  >
                    Logout
                  </button>
                </div>
              </nav>
            </div>
          )}

          {/* Mobile Login - Popover */}
          {showMobileMenu && !isAuthenticated() && (
            <div className="md:hidden fixed top-16 left-0 right-0 bg-white shadow-lg border-b border-gray-200 z-50 transform transition-transform duration-200 ease-in-out rounded-b-lg">
              <div className="p-4">
                <Link 
                  to="/login" 
                  className="block px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 font-medium text-center"
                  onClick={closeMobileMenu}
                >
                  Login
                </Link>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Click outside to close dropdowns - only for account dropdown */}
      {showAccountDropdown && (
        <div 
          className="fixed inset-0 z-30 bg-black bg-opacity-25" 
          onClick={() => {
            setShowAccountDropdown(false);
          }}
        />
      )}
    </>
  );
};

export default Header; 