import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('etsy_access_token');
    setIsConnected(!!token);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('etsy_access_token');
    setIsConnected(false);
    window.location.reload();
  };

  return (
    <header className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-gray-900">Etsy Seller Automaker</h1>
          </Link>
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
            {isConnected && (
              <button 
                onClick={handleLogout} 
                className="text-gray-700 hover:text-red-600 transition-colors duration-200 font-medium bg-transparent border-none cursor-pointer"
              >
                Disconnect
              </button>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header; 