import React from 'react';
import { useNavigate } from 'react-router-dom';

const IntegrationCard = ({
  name,
  icon,
  description,
  isConnected,
  userInfo,
  shopInfo,
  features,
  onConnect,
  onDisconnect,
  isLoading,
}) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white rounded-xl shadow-sm border border-sage-200 overflow-hidden">
      <div className="p-6">
        <div className="flex items-start space-x-4">
          {/* Integration Logo */}
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-orange-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">{icon}</span>
            </div>
          </div>

          {/* Integration Info */}
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-sage-900 mb-2">{name} Integration</h3>
            <p className="text-sage-600 mb-4">{description}</p>

            {/* Connection Status */}
            <div className="mb-4">
              {isConnected ? (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-mint-500 rounded-full"></div>
                    <span className="text-sm font-medium text-mint-700">Connected</span>
                  </div>
                  {userInfo && (
                    <div className="text-sm text-sage-600">
                      <p>
                        Connected as:{' '}
                        <span className="font-medium">
                          {userInfo.first_name} {userInfo.last_name}
                        </span>
                      </p>
                    </div>
                  )}
                  {shopInfo && (
                    <div className="text-sm text-sage-600">
                      <p>
                        Shop: <span className="font-medium">{shopInfo.shop_name}</span>
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-sage-400 rounded-full"></div>
                  <span className="text-sm font-medium text-sage-600">Not connected</span>
                </div>
              )}
            </div>

            {/* Features List */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-sage-900 mb-3">Features enabled:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <span className="text-base">{feature.icon}</span>
                    <span className={`text-sm ${isConnected ? 'text-sage-700' : 'text-sage-400'}`}>
                      {feature.label}
                    </span>
                    {isConnected && (
                      <svg className="w-4 h-4 text-mint-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              {isConnected ? (
                <>
                  <button
                    onClick={() => navigate('/?tab=overview')}
                    className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-lavender-500 to-lavender-600 text-white rounded-lg hover:from-lavender-600 hover:to-lavender-700 transition-all duration-200"
                  >
                    <span className="mr-2">🚀</span>
                    Go to Dashboard
                  </button>
                  <button
                    onClick={onDisconnect}
                    className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-rose-100 to-rose-200 text-rose-700 rounded-lg hover:from-rose-200 hover:to-rose-300 transition-all duration-200"
                  >
                    <span className="mr-2">🔌</span>
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  onClick={onConnect}
                  disabled={isLoading}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg hover:from-orange-600 hover:to-orange-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <span className="mr-2">🔗</span>
                      Connect {name}
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationCard;
