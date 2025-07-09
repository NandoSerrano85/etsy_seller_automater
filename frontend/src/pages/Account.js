import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import SettingsTab from './AccountTabs/SettingsTab';
import TemplatesTab from './AccountTabs/TemplatesTab';
import ResizingTab from './AccountTabs/ResizingTab';

const Account = () => {
  const { user, isAuthenticated } = useAuth();
  const api = useApi();
  const [activeTab, setActiveTab] = useState('settings');

  if (!isAuthenticated()) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 shadow-xl max-w-md w-full mx-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <p className="text-red-700">Please log in to access your account settings.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
      {/* Hero Section */}
      <div className="bg-white/10 backdrop-blur-sm py-8 sm:py-16 px-4 text-center text-white">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 text-shadow-lg">
            Account Settings
          </h1>
          <p className="text-base sm:text-lg md:text-xl mb-6 sm:mb-8 opacity-90 px-2">
            Manage your account settings, product templates, and resizing configurations
          </p>
          {user && (
            <p className="text-sm sm:text-base lg:text-lg opacity-90">
              Welcome back, <span className="font-semibold">{user.email}</span>!
            </p>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center space-x-1 overflow-x-auto">
            {['settings', 'templates', 'resizing'].map((tab) => (
              <button 
                key={tab}
                className={`tab-button capitalize whitespace-nowrap text-sm sm:text-base ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-gray-50 min-h-screen py-4 sm:py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Settings Tab */}
          {activeTab === 'settings' && <SettingsTab />}
          
          {/* Templates Tab */}
          {activeTab === 'templates' && <TemplatesTab />}
          
          {/* Resizing Tab */}
          {activeTab === 'resizing' && <ResizingTab />}
        </div>
      </div>
    </div>
  );
};

export default Account; 