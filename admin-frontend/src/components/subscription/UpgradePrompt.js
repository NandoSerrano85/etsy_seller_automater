import React, { useState } from 'react';
import { useSubscription } from '../../hooks/useSubscription';

const UpgradePrompt = ({
  feature,
  recommendedTier,
  message,
  className = '',
  size = 'default', // 'small', 'default', 'large'
  variant = 'card', // 'card', 'banner', 'modal'
}) => {
  const { getTierConfig, currentTier } = useSubscription();
  const [isExpanded, setIsExpanded] = useState(false);

  const recommendedConfig = getTierConfig(recommendedTier);
  const currentConfig = getTierConfig(currentTier);

  const handleUpgrade = () => {
    // TODO: Integrate with payment system
    console.log(`Initiating upgrade to ${recommendedTier}`);
    // For now, just expand to show more info
    setIsExpanded(!isExpanded);
  };

  if (variant === 'banner') {
    return (
      <div
        className={`bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-4 ${className}`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                <span className="text-amber-600">🚀</span>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-amber-800">
                {message || `Upgrade to ${recommendedConfig?.name} to unlock this feature`}
              </p>
            </div>
          </div>
          <button
            onClick={handleUpgrade}
            className="bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-700 transition-colors"
          >
            Upgrade Now
          </button>
        </div>
      </div>
    );
  }

  if (size === 'small') {
    return (
      <div className={`bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center ${className}`}>
        <div className="text-gray-400 mb-2">🔒</div>
        <p className="text-xs text-gray-600 mb-3">{message || `Requires ${recommendedConfig?.name}`}</p>
        <button
          onClick={handleUpgrade}
          className="text-xs bg-blue-600 text-white px-3 py-1 rounded font-medium hover:bg-blue-700 transition-colors"
        >
          Upgrade
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white border-2 border-dashed border-gray-300 rounded-xl p-6 text-center ${className}`}>
      <div className="mb-4">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">🎯</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Premium Feature</h3>
        <p className="text-gray-600 mb-4">{message || `This feature is available with ${recommendedConfig?.name}`}</p>
      </div>

      <div className="space-y-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Current Plan</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium bg-${currentConfig?.color}-100 text-${currentConfig?.color}-700`}
            >
              {currentConfig?.name}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Recommended</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium bg-${recommendedConfig?.color}-100 text-${recommendedConfig?.color}-700`}
            >
              {recommendedConfig?.name} - ${recommendedConfig?.price}/mo
            </span>
          </div>
        </div>

        {isExpanded && (
          <div className="bg-blue-50 rounded-lg p-4 text-left">
            <h4 className="font-medium text-blue-900 mb-3">What you'll get with {recommendedConfig?.name}:</h4>
            <ul className="space-y-2 text-sm text-blue-800">
              {recommendedTier === 'pro' && (
                <>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Unlimited mockups
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Etsy listing templates + auto-naming
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    File cleaning + resizing
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Batch product uploads to Etsy
                  </li>
                </>
              )}
              {recommendedTier === 'print_pro' && (
                <>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    All Pro features
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Print file generator (batch all orders)
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Advanced resizing for DTF/sublimation/vinyl
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    CSV/Excel export for production teams
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Multi-shop support
                  </li>
                </>
              )}
            </ul>
          </div>
        )}

        <div className="flex space-x-3">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            {isExpanded ? 'Less Info' : 'Learn More'}
          </button>
          <button
            onClick={handleUpgrade}
            className={`flex-1 bg-${recommendedConfig?.color}-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-${recommendedConfig?.color}-700 transition-colors`}
          >
            Upgrade Now
          </button>
        </div>
      </div>
    </div>
  );
};

export default UpgradePrompt;
