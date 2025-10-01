import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useApi } from '../hooks/useApi';
import { useNotifications } from './NotificationSystem';
import { useNavigate } from 'react-router-dom';
import apiCache, { CACHE_KEYS } from '../utils/apiCache';
import {
  BuildingStorefrontIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CogIcon,
  LinkIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  ClockIcon,
  InformationCircleIcon,
  ChartBarIcon,
  ShoppingBagIcon,
} from '@heroicons/react/24/outline';

const ShopifyStoreManager = () => {
  const { token } = useAuth();
  const api = useApi();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [store, setStore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  useEffect(() => {
    loadStoreInfo();
  }, []);

  const loadStoreInfo = async () => {
    try {
      // Show cached data immediately if available
      const cachedStore = apiCache.getValid(CACHE_KEYS.SHOPIFY_STORE, 30);
      if (cachedStore) {
        if (cachedStore.connected && cachedStore.store) {
          setStore(cachedStore.store);
          setConnectionStatus('connected');
          setLoading(false);
          return; // Use cache and skip API call
        }
      }

      setLoading(true);

      const storeData = await api.get('/api/shopify/store');
      setStore(storeData);
      setConnectionStatus('connected');
      // Cache the store data
      apiCache.set(CACHE_KEYS.SHOPIFY_STORE, { connected: true, store: storeData }, 30);
    } catch (error) {
      if (error.status === 404) {
        // No store connected
        setStore(null);
        setConnectionStatus('disconnected');
        apiCache.set(CACHE_KEYS.SHOPIFY_STORE, { connected: false }, 30);
      } else {
        console.error('Error loading store info:', error);
        addNotification('Failed to load store information', 'error');
        setConnectionStatus('error');
      }
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      setTestingConnection(true);

      const data = await api.get('/api/shopify/test-connection');

      if (data.status === 'connected') {
        addNotification('Connection test successful - store is working properly', 'success');
        setConnectionStatus('connected');
      } else {
        addNotification('Connection test failed - please check your store settings', 'error');
        setConnectionStatus('error');
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      addNotification('Connection test failed', 'error');
      setConnectionStatus('error');
    } finally {
      setTestingConnection(false);
    }
  };

  const disconnectStore = async () => {
    if (
      !window.confirm(
        'Are you sure you want to disconnect your Shopify store?\n\n' +
          'This will:\n' +
          '• Remove access to your products and orders\n' +
          '• Stop syncing new data\n' +
          '• Require re-authentication to reconnect\n\n' +
          'You can reconnect at any time.'
      )
    ) {
      return;
    }

    try {
      setDisconnecting(true);

      await api.delete('/api/shopify/disconnect');

      setStore(null);
      setConnectionStatus('disconnected');
      apiCache.set(CACHE_KEYS.SHOPIFY_STORE, { connected: false }, 30);
      addNotification('Store disconnected successfully', 'success');
    } catch (error) {
      console.error('Error disconnecting store:', error);
      addNotification('Failed to disconnect store', 'error');
    } finally {
      setDisconnecting(false);
    }
  };

  const connectStore = () => {
    navigate('/shopify/connect');
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircleIcon className="w-8 h-8 text-green-500" />;
      case 'disconnected':
        return <XCircleIcon className="w-8 h-8 text-gray-400" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />;
      default:
        return <ClockIcon className="w-8 h-8 text-yellow-500" />;
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          title: 'Store Connected',
          description: 'Your Shopify store is successfully connected and operational',
        };
      case 'disconnected':
        return {
          title: 'No Store Connected',
          description: 'Connect your Shopify store to start managing products and orders',
        };
      case 'error':
        return {
          title: 'Connection Error',
          description: 'There seems to be an issue with your store connection',
        };
      default:
        return {
          title: 'Checking Connection',
          description: 'Please wait while we verify your store connection',
        };
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sage-600 mr-3"></div>
          <span className="text-sage-600">Loading store information...</span>
        </div>
      </div>
    );
  }

  const statusInfo = getStatusText();

  return (
    <div className="space-y-6">
      {/* Main Status Card */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {getStatusIcon()}
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-gray-900">{statusInfo.title}</h3>
              <p className="text-gray-600">{statusInfo.description}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {store && (
              <button
                onClick={testConnection}
                disabled={testingConnection}
                className="flex items-center px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 disabled:opacity-50"
              >
                {testingConnection ? (
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ShieldCheckIcon className="w-4 h-4 mr-2" />
                )}
                Test Connection
              </button>
            )}

            {store ? (
              <button
                onClick={disconnectStore}
                disabled={disconnecting}
                className="flex items-center px-3 py-2 text-sm bg-red-50 text-red-600 rounded-md hover:bg-red-100 disabled:opacity-50"
              >
                {disconnecting ? (
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <XCircleIcon className="w-4 h-4 mr-2" />
                )}
                Disconnect
              </button>
            ) : (
              <button
                onClick={connectStore}
                className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
              >
                <LinkIcon className="w-4 h-4 mr-2" />
                Connect Store
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Store Details */}
      {store && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Store Details</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Basic Information</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Store Name:</span>
                  <span className="text-sm font-medium text-gray-900">{store.shop_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Domain:</span>
                  <span className="text-sm font-medium text-gray-900">{store.shop_domain}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Email:</span>
                  <span className="text-sm font-medium text-gray-900">{store.email || 'Not provided'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Currency:</span>
                  <span className="text-sm font-medium text-gray-900">{store.currency || 'USD'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Timezone:</span>
                  <span className="text-sm font-medium text-gray-900">{store.timezone || 'Not specified'}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Connection Status</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Status:</span>
                  <span className={`text-sm font-medium ${store.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {store.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Connected:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {new Date(store.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Updated:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {new Date(store.updated_at || store.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Store ID:</span>
                  <span className="text-sm font-medium text-gray-900">{store.id}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      {store && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => navigate('/shopify/products')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <BuildingStorefrontIcon className="w-8 h-8 text-sage-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Products</span>
              <span className="text-xs text-gray-500">Manage inventory</span>
            </button>

            <button
              onClick={() => navigate('/shopify/orders')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ShoppingBagIcon className="w-8 h-8 text-sage-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Orders</span>
              <span className="text-xs text-gray-500">Track sales</span>
            </button>

            <button
              onClick={() => navigate('/shopify/analytics')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ChartBarIcon className="w-8 h-8 text-sage-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Analytics</span>
              <span className="text-xs text-gray-500">View insights</span>
            </button>

            <button
              onClick={() => navigate('/shopify/create')}
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <CogIcon className="w-8 h-8 text-sage-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Create</span>
              <span className="text-xs text-gray-500">New products</span>
            </button>
          </div>
        </div>
      )}

      {/* Permissions Info */}
      {store && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <InformationCircleIcon className="w-5 h-5 text-blue-500 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">Permissions & Security</h4>
              <p className="text-sm text-blue-700 mb-2">Your store connection uses the following permissions:</p>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>
                  • <strong>Read Products:</strong> View your product catalog and inventory
                </li>
                <li>
                  • <strong>Write Products:</strong> Create and update products
                </li>
                <li>
                  • <strong>Read Orders:</strong> Access order information and customer data
                </li>
              </ul>
              <p className="text-sm text-blue-700 mt-2">
                We use OAuth 2.0 for secure authentication and never store your Shopify credentials.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Getting Started */}
      {!store && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Getting Started</h3>

          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-sage-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-sm font-medium text-sage-600">1</span>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-900">Connect Your Store</h4>
                <p className="text-sm text-gray-600">Click "Connect Store" to authorize access to your Shopify store</p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-sage-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-sm font-medium text-sage-600">2</span>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-900">Sync Your Data</h4>
                <p className="text-sm text-gray-600">
                  Once connected, your products and orders will be automatically synced
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-sage-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-sm font-medium text-sage-600">3</span>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-900">Start Managing</h4>
                <p className="text-sm text-gray-600">
                  Use the dashboard to create products, track orders, and analyze performance
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShopifyStoreManager;
