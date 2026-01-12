import React from 'react';
import { useSubscription } from '../../hooks/useSubscription';

const UsageIndicator = ({
  feature,
  showDetails = true,
  className = '',
  size = 'default', // 'small', 'default', 'large'
}) => {
  const { currentUsage, remainingMockups, mockupLimit, isFreeTier, getUpgradeForFeature, FEATURES } = useSubscription();

  // Only show usage for features with limits
  if (feature !== FEATURES.MOCKUP_GENERATOR || !isFreeTier) {
    return null;
  }

  const used = currentUsage.mockupsThisMonth;
  const total = mockupLimit;
  const remaining = remainingMockups;
  const percentage = total > 0 ? (used / total) * 100 : 0;

  const getProgressColor = () => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-amber-500';
    return 'bg-green-500';
  };

  const getTextColor = () => {
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 75) return 'text-amber-600';
    return 'text-green-600';
  };

  const upgradeInfo = getUpgradeForFeature(FEATURES.UNLIMITED_MOCKUPS);

  if (size === 'small') {
    return (
      <div className={`text-xs ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="flex-1 bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all duration-300 ${getProgressColor()}`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
          <span className={`font-medium ${getTextColor()}`}>{remaining} left</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">Monthly Mockup Usage</h4>
        <span className={`text-sm font-medium ${getTextColor()}`}>
          {used} / {total}
        </span>
      </div>

      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Used</span>
          <span>Limit</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      </div>

      {showDetails && (
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Remaining this month:</span>
            <span className={`font-medium ${getTextColor()}`}>{remaining} mockups</span>
          </div>

          {percentage >= 80 && upgradeInfo && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-0.5">💡</span>
                <div className="flex-1">
                  <p className="text-sm text-blue-800 mb-2">
                    Running low on mockups? Upgrade to {upgradeInfo.config.name} for unlimited mockups!
                  </p>
                  <button className="text-xs bg-blue-600 text-white px-3 py-1 rounded font-medium hover:bg-blue-700 transition-colors">
                    Upgrade to {upgradeInfo.config.name}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UsageIndicator;
