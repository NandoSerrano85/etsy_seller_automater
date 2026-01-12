import React, { useEffect } from 'react';
import { useOAuthTokens } from '../hooks/useOAuthTokens';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ClockIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

const OAuthTokenStatus = () => {
  const {
    tokens,
    loading,
    serviceStatus,
    loadServiceStatus,
    refreshPlatformToken,
    refreshAllTokens,
    isTokenExpired,
    needsRefresh,
    getActivePlatforms,
  } = useOAuthTokens();

  useEffect(() => {
    loadServiceStatus();
  }, [loadServiceStatus]);

  const platformDisplayNames = {
    ETSY: 'Etsy',
    SHOPIFY: 'Shopify',
    AMAZON: 'Amazon',
    EBAY: 'eBay',
  };

  const getStatusColor = token => {
    if (token.is_expired) return 'red';
    if (token.needs_refresh) return 'yellow';
    return 'green';
  };

  const getStatusIcon = token => {
    if (token.is_expired) {
      return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
    }
    if (token.needs_refresh) {
      return <ClockIcon className="w-5 h-5 text-yellow-500" />;
    }
    return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
  };

  const getStatusText = token => {
    if (token.is_expired) return 'Expired';
    if (token.needs_refresh) return 'Needs Refresh';
    return 'Active';
  };

  const formatTimeUntilExpiry = timeString => {
    if (!timeString) return 'N/A';

    // Parse the time string (format: "H:MM:SS" or "D days, H:MM:SS")
    const parts = timeString.split(', ');
    if (parts.length === 2) {
      return parts[0]; // Return "X days" part
    }

    const timeParts = timeString.split(':');
    if (timeParts.length === 3) {
      const hours = parseInt(timeParts[0]);
      if (hours > 24) {
        const days = Math.floor(hours / 24);
        return `${days} day${days > 1 ? 's' : ''}`;
      }
      return `${hours}h ${timeParts[1]}m`;
    }

    return timeString;
  };

  const activePlatforms = getActivePlatforms();

  if (loading && activePlatforms.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center">
          <ArrowPathIcon className="w-5 h-5 text-sage-600 animate-spin mr-2" />
          <span className="text-gray-600">Loading token status...</span>
        </div>
      </div>
    );
  }

  if (activePlatforms.length === 0) {
    return null; // Don't show anything if no tokens
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <ShieldCheckIcon className="w-6 h-6 text-sage-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">OAuth Token Status</h3>
        </div>
        {serviceStatus && (
          <div className="flex items-center text-sm text-gray-600">
            <div className={`w-2 h-2 rounded-full mr-2 ${serviceStatus.is_running ? 'bg-green-500' : 'bg-red-500'}`} />
            Auto-refresh {serviceStatus.is_running ? 'Active' : 'Inactive'}
          </div>
        )}
      </div>

      <div className="space-y-3">
        {activePlatforms.map(platform => {
          const token = tokens[platform];
          const statusColor = getStatusColor(token);

          return (
            <div
              key={platform}
              className={`p-4 rounded-lg border-2 ${
                statusColor === 'red'
                  ? 'border-red-200 bg-red-50'
                  : statusColor === 'yellow'
                    ? 'border-yellow-200 bg-yellow-50'
                    : 'border-green-200 bg-green-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {getStatusIcon(token)}
                  <div className="ml-3">
                    <h4 className="text-sm font-semibold text-gray-900">
                      {platformDisplayNames[platform] || platform}
                    </h4>
                    <p className="text-xs text-gray-600">
                      Status: <span className="font-medium">{getStatusText(token)}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="text-right text-xs text-gray-600">
                    {token.is_expired ? (
                      <span className="text-red-600 font-medium">Token Expired</span>
                    ) : (
                      <>
                        <div>Expires in:</div>
                        <div className="font-medium">{formatTimeUntilExpiry(token.time_until_expiry)}</div>
                      </>
                    )}
                  </div>

                  <button
                    onClick={() => refreshPlatformToken(platform)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      statusColor === 'red'
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : statusColor === 'yellow'
                          ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                          : 'bg-sage-600 hover:bg-sage-700 text-white'
                    }`}
                  >
                    Refresh
                  </button>
                </div>
              </div>

              {token.last_verified_at && (
                <div className="mt-2 text-xs text-gray-500">
                  Last verified: {new Date(token.last_verified_at).toLocaleString()}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {activePlatforms.length > 1 && (
        <div className="mt-4 pt-4 border-t">
          <button
            onClick={refreshAllTokens}
            className="w-full flex items-center justify-center px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 transition-colors"
          >
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Refresh All Tokens
          </button>
        </div>
      )}

      {serviceStatus && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>Auto-refresh enabled:</strong> Tokens are automatically refreshed every{' '}
            {Math.floor(serviceStatus.refresh_interval / 60)} minutes when they expire within{' '}
            {Math.floor(serviceStatus.refresh_threshold / 60)} minutes.
          </p>
        </div>
      )}
    </div>
  );
};

export default OAuthTokenStatus;
