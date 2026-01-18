import { useMemo, useEffect } from 'react';
import useSubscriptionStore, { FEATURES, SUBSCRIPTION_TIERS } from '../stores/subscriptionStore';

/**
 * Hook for subscription and feature access management
 */
export const useSubscription = () => {
  const {
    currentTier,
    subscriptionActive,
    subscriptionExpiresAt,
    currentUsage,
    loading,
    error,
    initialized,
    hasFeature,
    canUseFeature,
    getFeatureLimit,
    getRemainingUsage,
    getTierConfig,
    getAllTierConfigs,
    getUpgradeRecommendation,
    incrementMockupUsage,
    incrementMockupImagesUsage,
    setCurrentUsage,
    fetchSubscription,
  } = useSubscriptionStore();

  const tierConfig = useMemo(() => getTierConfig(), [currentTier, getTierConfig]);

  const isFreeTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.FREE, [currentTier]);
  const isStarterTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.STARTER, [currentTier]);
  const isProTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.PRO, [currentTier]);
  const isFullTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.FULL, [currentTier]);

  // Feature access helpers
  const canCreateMockups = useMemo(() => {
    return canUseFeature(FEATURES.MOCKUP_GENERATOR);
  }, [canUseFeature]);

  const remainingMockups = useMemo(() => {
    return getRemainingUsage(FEATURES.MOCKUP_GENERATOR);
  }, [getRemainingUsage, currentUsage]);

  const mockupLimit = useMemo(() => {
    return getFeatureLimit(FEATURES.MONTHLY_MOCKUP_LIMIT);
  }, [getFeatureLimit]);

  // Upgrade helpers
  const getUpgradeForFeature = feature => {
    return getUpgradeRecommendation(feature);
  };

  const isFeatureLocked = feature => {
    return !hasFeature(feature);
  };

  // Usage tracking
  const trackMockupCreation = (imageCount = 0) => {
    // Increment locally for immediate UI feedback
    incrementMockupUsage();
    if (imageCount > 0) {
      incrementMockupImagesUsage(imageCount);
    }
    // Refresh from backend after a short delay to ensure accuracy
    setTimeout(() => {
      fetchSubscription();
    }, 1000);
  };

  const updateUsage = usageData => {
    setCurrentUsage(usageData);
  };

  // Refresh usage from backend (useful after operations that affect counts)
  const refreshUsage = () => {
    fetchSubscription();
  };

  return {
    // Subscription state
    currentTier,
    tierConfig,
    subscriptionActive,
    subscriptionExpiresAt,
    loading,
    error,
    initialized,

    // Tier checks
    isFreeTier,
    isStarterTier,
    isProTier,
    isFullTier,

    // Usage state
    currentUsage,
    remainingMockups,
    mockupLimit,

    // Feature access
    hasFeature,
    canUseFeature,
    canCreateMockups,
    isFeatureLocked,

    // Configuration helpers
    getTierConfig,
    getAllTierConfigs,

    // Upgrade helpers
    getUpgradeForFeature,

    // Usage tracking
    trackMockupCreation,
    updateUsage,
    refreshUsage,

    // Fetch subscription from backend
    fetchSubscription,

    // Constants for components
    FEATURES,
    SUBSCRIPTION_TIERS,
  };
};

/**
 * Hook for checking if a specific feature is available
 */
export const useFeatureAccess = feature => {
  const { hasFeature, canUseFeature, getUpgradeRecommendation } = useSubscriptionStore();

  return {
    hasAccess: hasFeature(feature),
    canUse: canUseFeature(feature),
    upgradeInfo: getUpgradeRecommendation(feature),
  };
};

/**
 * Hook for feature gates - returns props for feature restriction components
 */
export const useFeatureGate = (feature, options = {}) => {
  const { hasFeature, canUseFeature, getUpgradeRecommendation, currentTier } = useSubscriptionStore();

  const hasAccess = hasFeature(feature);
  const canUse = canUseFeature(feature);
  const upgradeInfo = getUpgradeRecommendation(feature);

  const { showUpgradePrompt = true, blockInteraction = true, customMessage } = options;

  return {
    // State
    isLocked: !hasAccess,
    isDisabled: !canUse,
    hasAccess,
    canUse,

    // Upgrade info
    upgradeInfo,
    shouldShowUpgrade: showUpgradePrompt && !hasAccess,

    // Interaction control
    onClick: blockInteraction && !canUse ? e => e.preventDefault() : undefined,
    className: !canUse ? 'opacity-50 cursor-not-allowed' : '',

    // Messages
    lockMessage: customMessage || `This feature requires ${upgradeInfo?.config.name || 'a higher tier'}`,

    // Current tier
    currentTier,
  };
};

export default useSubscription;
