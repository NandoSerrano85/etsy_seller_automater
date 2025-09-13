import React from 'react';
import { useFeatureGate } from '../../hooks/useSubscription';
import UpgradePrompt from './UpgradePrompt';

/**
 * Feature Gate Component - Controls access to features based on subscription tier
 *
 * @param {string} feature - The feature to check access for
 * @param {React.ReactNode} children - Content to show when feature is accessible
 * @param {React.ReactNode} fallback - Content to show when feature is locked (optional)
 * @param {boolean} showUpgradePrompt - Whether to show upgrade prompt when locked (default: true)
 * @param {boolean} blockInteraction - Whether to block interaction when disabled (default: true)
 * @param {string} customMessage - Custom message for locked features
 */
const FeatureGate = ({
  feature,
  children,
  fallback,
  showUpgradePrompt = true,
  blockInteraction = true,
  customMessage,
  className = '',
}) => {
  const gateProps = useFeatureGate(feature, {
    showUpgradePrompt,
    blockInteraction,
    customMessage,
  });

  const {
    isLocked,
    isDisabled,
    hasAccess,
    canUse,
    shouldShowUpgrade,
    upgradeInfo,
    lockMessage,
    onClick,
    className: gateClassName,
  } = gateProps;

  // If completely locked (no access to feature)
  if (isLocked) {
    if (fallback) {
      return fallback;
    }

    if (shouldShowUpgrade && upgradeInfo) {
      return (
        <UpgradePrompt
          feature={feature}
          recommendedTier={upgradeInfo.recommendedTier}
          message={lockMessage}
          className={className}
        />
      );
    }

    // Default locked state - show children but disabled
    return (
      <div className={`relative ${className}`}>
        <div className="opacity-30 pointer-events-none">{children}</div>
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-lg">
          <div className="text-center p-4">
            <div className="text-gray-600 font-medium mb-2">🔒 Premium Feature</div>
            <div className="text-sm text-gray-500">{lockMessage}</div>
          </div>
        </div>
      </div>
    );
  }

  // Has access but might be disabled due to usage limits
  if (hasAccess && !canUse) {
    return (
      <div className={`${gateClassName} ${className}`} onClick={onClick}>
        <div className="opacity-50">{children}</div>
      </div>
    );
  }

  // Full access
  return <div className={className}>{children}</div>;
};

export default FeatureGate;
