import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BuildingStorefrontIcon,
  ShoppingBagIcon,
  LinkIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import { useShopify } from '../../hooks/useShopify';

const OverviewTab = ({ user, isConnected, designs, topSellers, authUrl }) => {
  const navigate = useNavigate();
  const { store: shopifyStore, loading: shopifyLoading } = useShopify();

  const integrations = [
    {
      id: 'etsy',
      name: 'Etsy',
      description: 'Connect your Etsy shop to sync products and orders',
      icon: BuildingStorefrontIcon,
      color: 'orange',
      isConnected: isConnected,
      connectUrl: authUrl,
      connectLabel: 'Connect Etsy Shop',
      dashboardUrl: '/?tab=orders',
    },
    {
      id: 'shopify',
      name: 'Shopify',
      description: 'Connect your Shopify store to manage products',
      icon: ShoppingBagIcon,
      color: 'green',
      isConnected: !!shopifyStore && !shopifyLoading,
      connectUrl: '/shopify/connect',
      connectLabel: 'Connect Shopify Store',
      dashboardUrl: '/shopify/dashboard',
    },
  ];

  const handleIntegrationAction = integration => {
    if (integration.isConnected) {
      navigate(integration.dashboardUrl);
    } else {
      if (integration.id === 'etsy') {
        window.location.href = integration.connectUrl;
      } else {
        navigate(integration.connectUrl);
      }
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Welcome Section */}
      <div className="card p-6 sm:p-8 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">Welcome to Your Dashboard</h2>
        {user && (
          <p className="text-base sm:text-lg text-gray-600 mb-4">
            Hello, <span className="font-semibold text-blue-600">{user.email}</span>!
          </p>
        )}
        <p className="text-base sm:text-lg text-gray-600 mb-6 sm:mb-8">
          Get insights into your shop performance, manage your designs, and use powerful tools to grow your business.
        </p>

        {isConnected && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mt-6 sm:mt-8">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 sm:p-6 rounded-xl text-center">
              <h3 className="text-base sm:text-lg font-semibold mb-2">Total Designs</h3>
              <p className="text-2xl sm:text-3xl font-bold">{designs.length}</p>
            </div>
            <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-4 sm:p-6 rounded-xl text-center">
              <h3 className="text-base sm:text-lg font-semibold mb-2">Top Seller</h3>
              <p className="text-sm sm:text-lg font-medium">
                {topSellers.length > 0 ? topSellers[0]?.title?.substring(0, 20) + '...' : 'N/A'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Integrations Section */}
      <div className="card p-6 sm:p-8">
        <div className="flex items-center mb-6">
          <LinkIcon className="w-6 h-6 text-sage-600 mr-3" />
          <h3 className="text-xl sm:text-2xl font-bold text-gray-900">E-Commerce Integrations</h3>
        </div>

        <p className="text-gray-600 mb-6">
          Connect your e-commerce platforms to sync products, manage inventory, and streamline your workflow.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {integrations.map(integration => (
            <div
              key={integration.id}
              className={`relative border-2 rounded-xl p-6 transition-all duration-200 ${
                integration.isConnected
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-200 bg-white hover:border-sage-300 hover:shadow-lg'
              }`}
            >
              {/* Connection Status Badge */}
              <div className="absolute top-4 right-4">
                {integration.isConnected ? (
                  <div className="flex items-center text-sm text-green-700 bg-green-100 px-3 py-1 rounded-full">
                    <CheckCircleIcon className="w-4 h-4 mr-1" />
                    Connected
                  </div>
                ) : (
                  <div className="flex items-center text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                    <XCircleIcon className="w-4 h-4 mr-1" />
                    Not Connected
                  </div>
                )}
              </div>

              {/* Integration Icon */}
              <div
                className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
                  integration.color === 'orange'
                    ? 'bg-orange-100'
                    : integration.color === 'green'
                      ? 'bg-green-100'
                      : 'bg-blue-100'
                }`}
              >
                <integration.icon
                  className={`w-8 h-8 ${
                    integration.color === 'orange'
                      ? 'text-orange-600'
                      : integration.color === 'green'
                        ? 'text-green-600'
                        : 'text-blue-600'
                  }`}
                />
              </div>

              {/* Integration Details */}
              <h4 className="text-lg font-bold text-gray-900 mb-2">{integration.name}</h4>
              <p className="text-sm text-gray-600 mb-4">{integration.description}</p>

              {/* Action Button */}
              <button
                onClick={() => handleIntegrationAction(integration)}
                className={`w-full flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-colors ${
                  integration.isConnected
                    ? 'bg-sage-600 hover:bg-sage-700 text-white'
                    : 'bg-gray-900 hover:bg-gray-800 text-white'
                }`}
              >
                {integration.isConnected ? (
                  <>
                    <span>View Dashboard</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2" />
                  </>
                ) : (
                  <>
                    <LinkIcon className="w-4 h-4 mr-2" />
                    <span>{integration.connectLabel}</span>
                  </>
                )}
              </button>
            </div>
          ))}
        </div>

        {/* Help Text */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>💡 Tip:</strong> Connect multiple platforms to manage all your products from one place. Your designs
            will sync automatically across all connected stores.
          </p>
        </div>
      </div>

      {/* Getting Started Guide (only show if no integrations connected) */}
      {!isConnected && !shopifyStore && (
        <div className="card p-6 sm:p-8">
          <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-6">Getting Started</h3>

          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-sage-100 rounded-full flex items-center justify-center mr-4">
                <span className="text-sm font-bold text-sage-600">1</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Connect Your Store</h4>
                <p className="text-sm text-gray-600">
                  Choose an integration above and connect your Etsy or Shopify store to get started.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-sage-100 rounded-full flex items-center justify-center mr-4">
                <span className="text-sm font-bold text-sage-600">2</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Upload Your Designs</h4>
                <p className="text-sm text-gray-600">
                  Upload your product designs and images to our platform for easy management.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-sage-100 rounded-full flex items-center justify-center mr-4">
                <span className="text-sm font-bold text-sage-600">3</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Create Products</h4>
                <p className="text-sm text-gray-600">
                  Use our tools to create mockups, manage listings, and track your sales performance.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OverviewTab;
