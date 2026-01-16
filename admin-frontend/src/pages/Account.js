import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import SettingsTab from './AccountTabs/SettingsTab';
import TemplatesWithSubtabs from './AccountTabs/TemplatesWithSubtabs';
import IntegrationsTab from './AccountTabs/IntegrationsTab';
import OrganizationTab from './AccountTabs/OrganizationTab';
import PrinterTab from './AccountTabs/PrinterTab';
import SubscriptionTab from './AccountTabs/SubscriptionTab';

const Account = () => {
  const { isUserAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Get active tab from URL params, default to 'profile'
  const activeTab = searchParams.get('tab') || 'profile';

  const tabs = [
    {
      id: 'profile',
      label: 'Profile',
      icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    },
    {
      id: 'templates',
      label: 'Templates',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    },
    {
      id: 'subscription',
      label: 'Subscription',
      icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z',
    },
    {
      id: 'integrations',
      label: 'Integrations',
      icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1',
    },
    {
      id: 'printers',
      label: 'Printers',
      icon: 'M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z',
    },
    {
      id: 'organizations',
      label: 'Organizations',
      icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
    },
  ];

  const handleTabChange = tabId => {
    navigate(`/account?tab=${tabId}`);
  };

  if (!isUserAuthenticated) {
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

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return <SettingsTab />;
      case 'templates':
        return <TemplatesWithSubtabs />;
      case 'integrations':
        return <IntegrationsTab />;
      case 'organizations':
        return <OrganizationTab />;
      case 'printers':
        return <PrinterTab />;
      case 'subscription':
        return <SubscriptionTab />;
      default:
        return <SettingsTab />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-2">
        <div className="flex flex-wrap gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
              </svg>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div>{renderTabContent()}</div>
    </div>
  );
};

export default Account;
