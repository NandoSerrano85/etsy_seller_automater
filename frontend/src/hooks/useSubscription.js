import { useMemo } from 'react';
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
    hasFeature,
    canUseFeature,
    getFeatureLimit,
    getRemainingUsage,
    getTierConfig,
    getUpgradeRecommendation,
    incrementMockupUsage,
    setCurrentUsage,
  } = useSubscriptionStore();

  const tierConfig = useMemo(() => getTierConfig(), [currentTier, getTierConfig]);

  const isFreeTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.FREE, [currentTier]);
  const isProTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.PRO, [currentTier]);
  const isPrintProTier = useMemo(() => currentTier === SUBSCRIPTION_TIERS.PRINT_PRO, [currentTier]);

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
  const trackMockupCreation = () => {
    incrementMockupUsage();
  };

  const updateUsage = usageData => {
    setCurrentUsage(usageData);
  };

  return {
    // Subscription state
    currentTier,
    tierConfig,
    subscriptionActive,
    subscriptionExpiresAt,
    loading,
    error,

    // Tier checks
    isFreeTier,
    isProTier,
    isPrintProTier,

    // Usage state
    currentUsage,
    remainingMockups,
    mockupLimit,

    // Feature access
    hasFeature,
    canUseFeature,
    canCreateMockups,
    isFeatureLocked,

    // Upgrade helpers
    getUpgradeForFeature,

    // Usage tracking
    trackMockupCreation,
    updateUsage,

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
