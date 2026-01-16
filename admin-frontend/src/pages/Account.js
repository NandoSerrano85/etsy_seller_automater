import React from 'react';
import { useSearchParams } from 'react-router-dom';
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

  // Get active tab from URL params, default to 'profile'
  const activeTab = searchParams.get('tab') || 'profile';

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

  return <div className="space-y-6">{renderTabContent()}</div>;
};

export default Account;
