import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Subscription tier definitions
export const SUBSCRIPTION_TIERS = {
  FREE: 'free',
  PRO: 'pro',
  PRINT_PRO: 'print_pro',
};

// Feature definitions with tier requirements
export const FEATURES = {
  // Dashboard & Analytics
  ETSY_DASHBOARD: 'etsy_dashboard',
  BASIC_ANALYTICS: 'basic_analytics',

  // Mockup Features
  MOCKUP_GENERATOR: 'mockup_generator',
  UNLIMITED_MOCKUPS: 'unlimited_mockups',

  // File Management
  FILE_CLEANER: 'file_cleaner',
  FILE_RESIZING: 'file_resizing',
  BULK_FILE_OPERATIONS: 'bulk_file_operations',

  // Listing Management
  LISTING_TEMPLATES: 'listing_templates',
  AUTO_NAMING: 'auto_naming',
  BATCH_UPLOADS: 'batch_uploads',

  // Print Shop Features
  PRINT_FILE_GENERATOR: 'print_file_generator',
  ADVANCED_RESIZING: 'advanced_resizing',
  CSV_EXPORT: 'csv_export',
  MULTI_SHOP_SUPPORT: 'multi_shop_support',

  // Limits
  MONTHLY_MOCKUP_LIMIT: 'monthly_mockup_limit',
};

// Tier configurations
export const TIER_CONFIGS = {
  [SUBSCRIPTION_TIERS.FREE]: {
    name: 'Free Plan',
    price: 0,
    description: 'Perfect for trying out our tools',
    features: {
      [FEATURES.ETSY_DASHBOARD]: true,
      [FEATURES.BASIC_ANALYTICS]: true,
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.FILE_CLEANER]: true,
      [FEATURES.MONTHLY_MOCKUP_LIMIT]: 50, // 50 mockups per month
    },
    limits: {
      mockupsPerMonth: 50,
      maxShops: 1,
      maxUsers: 1,
    },
    color: 'emerald',
  },
  [SUBSCRIPTION_TIERS.PRO]: {
    name: 'Pro Plan',
    price: 29,
    description: 'For serious Etsy sellers who want to scale',
    features: {
      [FEATURES.ETSY_DASHBOARD]: true,
      [FEATURES.BASIC_ANALYTICS]: true,
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.UNLIMITED_MOCKUPS]: true,
      [FEATURES.FILE_CLEANER]: true,
      [FEATURES.FILE_RESIZING]: true,
      [FEATURES.BULK_FILE_OPERATIONS]: true,
      [FEATURES.LISTING_TEMPLATES]: true,
      [FEATURES.AUTO_NAMING]: true,
      [FEATURES.BATCH_UPLOADS]: true,
    },
    limits: {
      mockupsPerMonth: Infinity,
      maxShops: 1,
      maxUsers: 1,
    },
    color: 'blue',
  },
  [SUBSCRIPTION_TIERS.PRINT_PRO]: {
    name: 'Print Shop Pro',
    price: 99,
    description: 'For print shops & businesses processing bulk orders',
    features: {
      [FEATURES.ETSY_DASHBOARD]: true,
      [FEATURES.BASIC_ANALYTICS]: true,
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.UNLIMITED_MOCKUPS]: true,
      [FEATURES.FILE_CLEANER]: true,
      [FEATURES.FILE_RESIZING]: true,
      [FEATURES.BULK_FILE_OPERATIONS]: true,
      [FEATURES.LISTING_TEMPLATES]: true,
      [FEATURES.AUTO_NAMING]: true,
      [FEATURES.BATCH_UPLOADS]: true,
      [FEATURES.PRINT_FILE_GENERATOR]: true,
      [FEATURES.ADVANCED_RESIZING]: true,
      [FEATURES.CSV_EXPORT]: true,
      [FEATURES.MULTI_SHOP_SUPPORT]: true,
    },
    limits: {
      mockupsPerMonth: Infinity,
      maxShops: Infinity,
      maxUsers: 10,
    },
    color: 'purple',
  },
};

const useSubscriptionStore = create(
  persist(
    (set, get) => ({
      // Current subscription state
      currentTier: SUBSCRIPTION_TIERS.FREE,
      subscriptionActive: true,
      subscriptionExpiresAt: null,

      // Usage tracking
      currentUsage: {
        mockupsThisMonth: 0,
        shopsConnected: 0,
        usersInOrg: 1,
      },

      // Loading states
      loading: false,
      error: null,

      // Actions
      setSubscriptionTier: tier =>
        set({
          currentTier: tier,
          error: null,
        }),

      setSubscriptionStatus: (active, expiresAt = null) =>
        set({
          subscriptionActive: active,
          subscriptionExpiresAt: expiresAt,
          error: null,
        }),

      setCurrentUsage: usage =>
        set({
          currentUsage: { ...get().currentUsage, ...usage },
        }),

      incrementMockupUsage: () =>
        set(state => ({
          currentUsage: {
            ...state.currentUsage,
            mockupsThisMonth: state.currentUsage.mockupsThisMonth + 1,
          },
        })),

      setLoading: loading => set({ loading }),
      setError: error => set({ error }),

      // Feature access methods
      hasFeature: featureName => {
        const { currentTier, subscriptionActive } = get();

        if (!subscriptionActive) {
          // If subscription expired, only allow free tier features
          return TIER_CONFIGS[SUBSCRIPTION_TIERS.FREE].features[featureName] || false;
        }

        const tierConfig = TIER_CONFIGS[currentTier];
        return tierConfig?.features[featureName] || false;
      },

      canUseFeature: (featureName, requiredAmount = 1) => {
        const { currentTier, subscriptionActive, currentUsage } = get();

        if (!subscriptionActive) {
          return false;
        }

        const tierConfig = TIER_CONFIGS[currentTier];

        // Check if feature is enabled for tier
        if (!tierConfig?.features[featureName]) {
          return false;
        }

        // Check usage limits
        switch (featureName) {
          case FEATURES.MOCKUP_GENERATOR:
            if (currentTier === SUBSCRIPTION_TIERS.FREE) {
              return currentUsage.mockupsThisMonth < tierConfig.limits.mockupsPerMonth;
            }
            return true;

          case FEATURES.MULTI_SHOP_SUPPORT:
            return currentUsage.shopsConnected < tierConfig.limits.maxShops;

          default:
            return true;
        }
      },

      getFeatureLimit: featureName => {
        const { currentTier } = get();
        const tierConfig = TIER_CONFIGS[currentTier];

        switch (featureName) {
          case FEATURES.MONTHLY_MOCKUP_LIMIT:
            return tierConfig?.limits.mockupsPerMonth || 0;
          default:
            return null;
        }
      },

      getRemainingUsage: featureName => {
        const { currentTier, currentUsage } = get();
        const tierConfig = TIER_CONFIGS[currentTier];

        switch (featureName) {
          case FEATURES.MOCKUP_GENERATOR:
            if (currentTier === SUBSCRIPTION_TIERS.FREE) {
              return Math.max(0, tierConfig.limits.mockupsPerMonth - currentUsage.mockupsThisMonth);
            }
            return Infinity;
          default:
            return null;
        }
      },

      getTierConfig: (tier = null) => {
        const targetTier = tier || get().currentTier;
        return TIER_CONFIGS[targetTier];
      },

      getAllTierConfigs: () => TIER_CONFIGS,

      getUpgradeRecommendation: feature => {
        const { currentTier } = get();

        // Find the lowest tier that supports this feature
        for (const [tier, config] of Object.entries(TIER_CONFIGS)) {
          if (config.features[feature] && tier !== currentTier) {
            return {
              recommendedTier: tier,
              config: config,
            };
          }
        }

        return null;
      },

      // Debug method
      getDebugInfo: () => {
        const state = get();
        return {
          subscription: {
            tier: state.currentTier,
            active: state.subscriptionActive,
            expiresAt: state.subscriptionExpiresAt,
          },
          usage: state.currentUsage,
          tierConfig: state.getTierConfig(),
          availableFeatures: Object.keys(FEATURES).filter(feature => state.hasFeature(FEATURES[feature])),
        };
      },
    }),
    {
      name: 'subscription-store',
      partialize: state => ({
        currentTier: state.currentTier,
        subscriptionActive: state.subscriptionActive,
        subscriptionExpiresAt: state.subscriptionExpiresAt,
        currentUsage: state.currentUsage,
      }),
    }
  )
);

export default useSubscriptionStore;
