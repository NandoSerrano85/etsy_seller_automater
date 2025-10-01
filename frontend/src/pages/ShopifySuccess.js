import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useNotifications } from '../components/NotificationSystem';
import { useShopify } from '../hooks/useShopify';
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const ShopifySuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { addNotification } = useNotifications();
  const { loadStore } = useShopify();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // Check for error parameter from OAuth callback
    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    if (error) {
      setStatus('error');
      setErrorMessage(errorDescription || error);
      addNotification(`Shopify connection failed: ${errorDescription || error}`, 'error');

      // Redirect to connect page after 3 seconds
      setTimeout(() => {
        navigate('/shopify/connect', { replace: true });
      }, 3000);
      return;
    }

    // Success case - load the store information
    const loadStoreInfo = async () => {
      try {
        await loadStore();
        setStatus('success');
        addNotification('Shopify store connected successfully!', 'success');

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate('/shopify/dashboard', { replace: true });
        }, 2000);
      } catch (err) {
        console.error('Error loading store:', err);
        setStatus('error');
        setErrorMessage('Failed to load store information. Please try again.');
        addNotification('Failed to load store information', 'error');

        // Redirect to connect page after 3 seconds
        setTimeout(() => {
          navigate('/shopify/connect', { replace: true });
        }, 3000);
      }
    };

    loadStoreInfo();
  }, [searchParams, navigate, addNotification, loadStore]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {status === 'loading' && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <ArrowPathIcon className="w-16 h-16 text-sage-600 mx-auto mb-4 animate-spin" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Connecting Your Store</h2>
            <p className="text-gray-600 mb-4">Please wait while we complete the connection to your Shopify store...</p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-sage-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        )}

        {status === 'success' && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Connection Successful!</h2>
            <p className="text-gray-600 mb-6">
              Your Shopify store has been successfully connected. You can now sync products, manage inventory, and track
              orders.
            </p>
            <div className="flex items-center justify-center text-sm text-gray-500">
              <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
              Redirecting to dashboard...
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <XCircleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Connection Failed</h2>
            <p className="text-gray-600 mb-4">
              {errorMessage || 'We encountered an error while connecting your Shopify store.'}
            </p>
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
              <p className="text-sm text-red-800">
                Please try connecting again. If the problem persists, contact support.
              </p>
            </div>
            <div className="flex items-center justify-center text-sm text-gray-500">
              <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
              Redirecting back to connect page...
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopifySuccess;
