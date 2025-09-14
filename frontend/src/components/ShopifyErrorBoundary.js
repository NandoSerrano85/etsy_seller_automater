import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ExclamationTriangleIcon, LinkIcon, ArrowPathIcon, BuildingStorefrontIcon } from '@heroicons/react/24/outline';

const ShopifyErrorBoundary = ({ children, fallback: Fallback }) => {
  const [hasError, setHasError] = React.useState(false);
  const [error, setError] = React.useState(null);
  const navigate = useNavigate();

  React.useEffect(() => {
    const handleError = error => {
      setHasError(true);
      setError(error);
    };

    // Listen for unhandled promise rejections
    const handleUnhandledRejection = event => {
      if (
        event.reason?.message?.includes('shopify') ||
        event.reason?.message?.includes('store') ||
        event.reason?.message?.includes('authentication')
      ) {
        handleError(event.reason);
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  const retry = () => {
    setHasError(false);
    setError(null);
    window.location.reload();
  };

  const getErrorMessage = () => {
    if (!error) return 'An unexpected error occurred';

    const message = error.message || error.toString();

    if (message.includes('authentication') || message.includes('401')) {
      return {
        title: 'Authentication Error',
        description: 'Your Shopify store connection has expired. Please reconnect your store to continue.',
        action: 'reconnect',
      };
    }

    if (message.includes('store') || message.includes('404')) {
      return {
        title: 'Store Not Connected',
        description: 'No Shopify store is currently connected to your account.',
        action: 'connect',
      };
    }

    if (message.includes('rate limit') || message.includes('429')) {
      return {
        title: 'Rate Limit Exceeded',
        description: 'Too many requests to Shopify. Please wait a moment and try again.',
        action: 'retry',
      };
    }

    if (message.includes('network') || message.includes('fetch')) {
      return {
        title: 'Network Error',
        description: 'Unable to connect to Shopify. Please check your internet connection and try again.',
        action: 'retry',
      };
    }

    return {
      title: 'Shopify Error',
      description: message,
      action: 'retry',
    };
  };

  if (hasError) {
    if (Fallback) {
      return <Fallback error={error} retry={retry} />;
    }

    const errorInfo = getErrorMessage();

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />

          <h2 className="text-xl font-semibold text-gray-900 mb-2">{errorInfo.title}</h2>

          <p className="text-gray-600 mb-6">{errorInfo.description}</p>

          <div className="space-y-3">
            {errorInfo.action === 'connect' && (
              <button
                onClick={() => navigate('/shopify/connect')}
                className="w-full flex items-center justify-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
              >
                <LinkIcon className="w-4 h-4 mr-2" />
                Connect Shopify Store
              </button>
            )}

            {errorInfo.action === 'reconnect' && (
              <button
                onClick={() => navigate('/shopify/connect')}
                className="w-full flex items-center justify-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
              >
                <LinkIcon className="w-4 h-4 mr-2" />
                Reconnect Store
              </button>
            )}

            <button
              onClick={retry}
              className="w-full flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              <ArrowPathIcon className="w-4 h-4 mr-2" />
              Try Again
            </button>

            <button
              onClick={() => navigate('/shopify')}
              className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              <BuildingStorefrontIcon className="w-4 h-4 mr-2" />
              Go to Shopify Dashboard
            </button>
          </div>

          {error && process.env.NODE_ENV === 'development' && (
            <details className="mt-4 text-left">
              <summary className="text-sm text-gray-500 cursor-pointer">Technical Details (Development)</summary>
              <pre className="mt-2 text-xs text-gray-600 bg-gray-100 p-2 rounded overflow-auto">
                {error.stack || error.toString()}
              </pre>
            </details>
          )}
        </div>
      </div>
    );
  }

  return children;
};

// Higher-order component for wrapping individual components
export const withShopifyErrorBoundary = (Component, fallback) => {
  return function WrappedComponent(props) {
    return (
      <ShopifyErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ShopifyErrorBoundary>
    );
  };
};

// Hook for handling Shopify API errors consistently
export const useShopifyErrorHandler = () => {
  const navigate = useNavigate();

  const handleError = React.useCallback(
    (error, context = '') => {
      console.error(`Shopify error in ${context}:`, error);

      const message = error.message || error.toString();

      if (message.includes('authentication') || message.includes('401')) {
        navigate('/shopify/connect', {
          state: {
            message: 'Your store connection has expired. Please reconnect.',
            from: context,
          },
        });
        return;
      }

      if (message.includes('store') || message.includes('404')) {
        navigate('/shopify/connect', {
          state: {
            message: 'Please connect your Shopify store to continue.',
            from: context,
          },
        });
        return;
      }

      // For other errors, throw to be caught by error boundary
      throw error;
    },
    [navigate]
  );

  return { handleError };
};

export default ShopifyErrorBoundary;
