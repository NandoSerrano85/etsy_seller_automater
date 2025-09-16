import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useShopify } from '../hooks/useShopify';
import {
  BuildingStorefrontIcon,
  LinkIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  CogIcon,
} from '@heroicons/react/24/outline';

const ShopifyConnect = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Use Shopify hook
  const {
    store: connectedStore,
    isConnected,
    loading,
    error,
    loadStore,
    connectStore,
    disconnectStore,
    testConnection,
  } = useShopify();

  const [connecting, setConnecting] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);

  // Check for OAuth callback parameters
  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      addNotification(`Shopify connection failed: ${error}`, 'error');
      navigate('/shopify/connect', { replace: true });
    } else if (code && state) {
      // OAuth callback received - this is handled by the backend
      addNotification('Store connected successfully!', 'success');
      loadStore();
      navigate('/shopify/connect', { replace: true });
    }
  }, [searchParams, addNotification, navigate, loadStore]);

  const initiateConnection = async () => {
    try {
      setConnecting(true);
      await connectStore(null); // Will prompt for shop domain in OAuth flow
    } catch (error) {
      console.error('Error connecting to Shopify:', error);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnectStore = async () => {
    if (
      !window.confirm(
        'Are you sure you want to disconnect your Shopify store? This will remove access to your products and orders.'
      )
    ) {
      return;
    }

    await disconnectStore();
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    await testConnection();
    setTestingConnection(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading store information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-12 px-6">
        {/* Header */}
        <div className="text-center mb-8">
          <BuildingStorefrontIcon className="w-16 h-16 text-sage-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Shopify Integration</h1>
          <p className="text-lg text-gray-600">Connect your Shopify store to sync products and manage orders</p>
        </div>

        {connectedStore ? (
          /* Connected Store View */
          <div className="space-y-6">
            {/* Store Status Card */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <CheckCircleIcon className="w-8 h-8 text-green-500 mr-3" />
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Store Connected</h2>
                    <p className="text-gray-600">Your Shopify store is successfully connected</p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleTestConnection}
                    disabled={testingConnection}
                    className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {testingConnection ? (
                      <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <ShieldCheckIcon className="w-4 h-4 mr-2" />
                    )}
                    Test Connection
                  </button>
                  <button
                    onClick={handleDisconnectStore}
                    className="flex items-center px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    <XCircleIcon className="w-4 h-4 mr-2" />
                    Disconnect
                  </button>
                </div>
              </div>

              {/* Store Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Store Information</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Store Name:</span>
                      <span className="text-sm font-medium">{connectedStore.shop_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Domain:</span>
                      <span className="text-sm font-medium">{connectedStore.shop_domain}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Email:</span>
                      <span className="text-sm font-medium">{connectedStore.email || 'Not provided'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Currency:</span>
                      <span className="text-sm font-medium">{connectedStore.currency || 'USD'}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Connection Status</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Status:</span>
                      <span
                        className={`text-sm font-medium ${connectedStore.is_active ? 'text-green-600' : 'text-red-600'}`}
                      >
                        {connectedStore.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Connected:</span>
                      <span className="text-sm font-medium">
                        {new Date(connectedStore.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Last Updated:</span>
                      <span className="text-sm font-medium">
                        {new Date(connectedStore.updated_at || connectedStore.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <button
                  onClick={() => navigate('/shopify/products')}
                  className="flex items-center justify-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <BuildingStorefrontIcon className="w-6 h-6 text-sage-600 mr-2" />
                  <span>View Products</span>
                </button>

                <button
                  onClick={() => navigate('/shopify/orders')}
                  className="flex items-center justify-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <CogIcon className="w-6 h-6 text-sage-600 mr-2" />
                  <span>View Orders</span>
                </button>

                <button
                  onClick={() => navigate('/shopify/analytics')}
                  className="flex items-center justify-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <CogIcon className="w-6 h-6 text-sage-600 mr-2" />
                  <span>Analytics</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Not Connected View */
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center mb-6">
              <LinkIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Connect Your Shopify Store</h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Connect your Shopify store to automatically sync products, manage inventory, and track orders directly
                from your dashboard.
              </p>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="text-center">
                <BuildingStorefrontIcon className="w-8 h-8 text-sage-600 mx-auto mb-2" />
                <h3 className="font-medium text-gray-900 mb-1">Product Sync</h3>
                <p className="text-sm text-gray-600">Automatically sync your products and inventory</p>
              </div>

              <div className="text-center">
                <CogIcon className="w-8 h-8 text-sage-600 mx-auto mb-2" />
                <h3 className="font-medium text-gray-900 mb-1">Order Management</h3>
                <p className="text-sm text-gray-600">Track and manage orders from one place</p>
              </div>

              <div className="text-center">
                <ShieldCheckIcon className="w-8 h-8 text-sage-600 mx-auto mb-2" />
                <h3 className="font-medium text-gray-900 mb-1">Secure Connection</h3>
                <p className="text-sm text-gray-600">OAuth 2.0 secure authentication</p>
              </div>
            </div>

            {/* Connection Steps */}
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h3 className="font-medium text-gray-900 mb-4">How it works:</h3>
              <div className="space-y-3">
                <div className="flex items-center">
                  <div className="flex-shrink-0 w-6 h-6 bg-sage-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    1
                  </div>
                  <span className="text-sm text-gray-700">Click "Connect Store" to start the process</span>
                </div>
                <div className="flex items-center">
                  <div className="flex-shrink-0 w-6 h-6 bg-sage-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    2
                  </div>
                  <span className="text-sm text-gray-700">
                    You'll be redirected to Shopify to authorize the connection
                  </span>
                </div>
                <div className="flex items-center">
                  <div className="flex-shrink-0 w-6 h-6 bg-sage-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    3
                  </div>
                  <span className="text-sm text-gray-700">
                    Once authorized, you'll be redirected back and your store will be connected
                  </span>
                </div>
              </div>
            </div>

            {/* Security Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <ShieldCheckIcon className="w-5 h-5 text-blue-500 mr-2 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-blue-900 mb-1">Secure Connection</h4>
                  <p className="text-sm text-blue-700">
                    We use OAuth 2.0 to securely connect to your Shopify store. We only request the minimum permissions
                    needed: read/write products and read orders. Your store credentials are never stored.
                  </p>
                </div>
              </div>
            </div>

            {/* Connect Button */}
            <div className="text-center">
              <button
                onClick={initiateConnection}
                disabled={connecting}
                className="flex items-center px-6 py-3 bg-sage-600 text-white rounded-lg hover:bg-sage-700 disabled:opacity-50 disabled:cursor-not-allowed mx-auto"
              >
                {connecting ? (
                  <>
                    <ArrowPathIcon className="w-5 h-5 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <LinkIcon className="w-5 h-5 mr-2" />
                    Connect Shopify Store
                  </>
                )}
              </button>

              {connecting && (
                <p className="text-sm text-gray-600 mt-2">Please wait while we redirect you to Shopify...</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopifyConnect;
