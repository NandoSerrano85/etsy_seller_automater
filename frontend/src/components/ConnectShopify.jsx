import React, { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useNotifications } from './NotificationSystem';

const ConnectShopify = () => {
  const api = useApi();
  const { addNotification } = useNotifications();
  const [shopDomain, setShopDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleConnect = async e => {
    e.preventDefault();

    if (!shopDomain.trim()) {
      setError('Please enter your shop domain');
      return;
    }

    // Clean the shop domain (remove .myshopify.com if included)
    const cleanDomain = shopDomain.replace('.myshopify.com', '').toLowerCase().trim();

    if (!cleanDomain) {
      setError('Please enter a valid shop domain');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/shopify/connect', {
        shop_domain: `${cleanDomain}.myshopify.com`,
      });

      if (response.authorization_url) {
        addNotification({
          type: 'info',
          message: 'Redirecting to Shopify for authorization...',
        });

        // Redirect to Shopify OAuth
        window.location.href = response.authorization_url;
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err) {
      console.error('Error connecting to Shopify:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to connect to Shopify. Please try again.';
      setError(errorMessage);
      addNotification({
        type: 'error',
        message: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleShopDomainChange = e => {
    const value = e.target.value;
    setShopDomain(value);
    if (error) setError(null);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M15.337 2.367c-.302-.12-.65-.12-.952 0l-3.17 1.26a.6.6 0 0 0-.375.555v15.656c0 .276.188.516.455.587l3.17 1.056a.6.6 0 0 0 .19.031c.122 0 .243-.037.348-.11a.6.6 0 0 0 .252-.489V2.977a.6.6 0 0 0-.375-.555l-3.17-1.26a.6.6 0 0 0-.19-.031zM8.663 2.367c-.302-.12-.65-.12-.952 0l-3.17 1.26a.6.6 0 0 0-.375.555v15.656c0 .276.188.516.455.587l3.17 1.056a.6.6 0 0 0 .19.031c.122 0 .243-.037.348-.11a.6.6 0 0 0 .252-.489V2.977a.6.6 0 0 0-.375-.555l-3.17-1.26a.6.6 0 0 0-.19-.031z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-sage-900">Connect Shopify Store</h3>
          <p className="text-sage-600 text-sm">Connect your Shopify store to sync products and orders</p>
        </div>
      </div>

      <form onSubmit={handleConnect} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-sage-700 mb-2">Shopify Store Domain</label>
          <div className="relative">
            <input
              type="text"
              value={shopDomain}
              onChange={handleShopDomainChange}
              placeholder="your-store-name"
              className="w-full px-3 py-2 border border-sage-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 pr-32"
              disabled={loading}
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <span className="text-sage-500 text-sm">.myshopify.com</span>
            </div>
          </div>
          <p className="text-xs text-sage-500 mt-1">Enter your shop domain without the ".myshopify.com" part</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">{error}</div>
        )}

        <button
          type="submit"
          disabled={loading || !shopDomain.trim()}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-sage-300 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          {loading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Connecting...</span>
            </div>
          ) : (
            'Connect Shopify Store'
          )}
        </button>
      </form>

      <div className="mt-6 p-4 bg-sage-50 rounded-lg border border-sage-200">
        <h4 className="text-sm font-medium text-sage-900 mb-2">What happens next?</h4>
        <ul className="text-xs text-sage-600 space-y-1">
          <li>• You'll be redirected to Shopify to authorize the connection</li>
          <li>• We'll sync your products and orders automatically</li>
          <li>• You can manage your Shopify integration from this dashboard</li>
          <li>• All data is securely encrypted and stored</li>
        </ul>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-start space-x-2">
          <svg
            className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <p className="text-xs text-blue-700 font-medium">Required Permissions</p>
            <p className="text-xs text-blue-600">
              This integration requires read/write access to products and read access to orders to function properly.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectShopify;
