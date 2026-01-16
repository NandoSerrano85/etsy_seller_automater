import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import subscriptionService from '../services/subscriptionService';

// Subscription tier definitions - must match backend
export const SUBSCRIPTION_TIERS = {
  FREE: 'free',
  STARTER: 'starter',
  PRO: 'pro',
  FULL: 'full',
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

  // Platform integrations
  ETSY_INTEGRATION: 'etsy_integration',
  SHOPIFY_INTEGRATION: 'shopify_integration',
  CRAFTFLOW_COMMERCE: 'craftflow_commerce',

  // Limits
  MONTHLY_MOCKUP_LIMIT: 'monthly_mockup_limit',
};

// Tier configurations - matches backend SUBSCRIPTION_TIERS
export const TIER_CONFIGS = {
  [SUBSCRIPTION_TIERS.FREE]: {
    name: 'Free',
    price: 0,
    description: 'Get started with basic mockup creation',
    features: {
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.ETSY_INTEGRATION]: true,
      [FEATURES.MONTHLY_MOCKUP_LIMIT]: 15,
    },
    limits: {
      mockupsPerMonth: 15,
      mockupsPerBatch: 1,
      templates: 1,
      canvas: 1,
      sizes: 1,
    },
    color: 'emerald',
  },
  [SUBSCRIPTION_TIERS.STARTER]: {
    name: 'Starter',
    price: 19.99,
    description: 'Perfect for growing sellers',
    features: {
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.ETSY_INTEGRATION]: true,
      [FEATURES.FILE_CLEANER]: true,
      [FEATURES.AUTO_NAMING]: true,
      [FEATURES.BATCH_UPLOADS]: true,
      [FEATURES.MONTHLY_MOCKUP_LIMIT]: 100,
    },
    limits: {
      mockupsPerMonth: 100,
      mockupsPerBatch: 10,
      templates: 10,
      canvas: 5,
      sizes: 10,
    },
    color: 'blue',
  },
  [SUBSCRIPTION_TIERS.PRO]: {
    name: 'Pro',
    price: 39.99,
    description: 'For serious sellers who want more',
    features: {
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.UNLIMITED_MOCKUPS]: true,
      [FEATURES.ETSY_INTEGRATION]: true,
      [FEATURES.SHOPIFY_INTEGRATION]: true,
      [FEATURES.FILE_CLEANER]: true,
      [FEATURES.AUTO_NAMING]: true,
      [FEATURES.BATCH_UPLOADS]: true,
      [FEATURES.ADVANCED_RESIZING]: true,
      [FEATURES.PRINT_FILE_GENERATOR]: true,
      [FEATURES.CSV_EXPORT]: true,
    },
    limits: {
      mockupsPerMonth: -1, // Unlimited
      mockupsPerBatch: 50,
      templates: -1,
      canvas: -1,
      sizes: -1,
    },
    color: 'purple',
  },
  [SUBSCRIPTION_TIERS.FULL]: {
    name: 'Full',
    price: 99.99,
    description: 'Everything you need to scale',
    features: {
      [FEATURES.MOCKUP_GENERATOR]: true,
      [FEATURES.UNLIMITED_MOCKUPS]: true,
      [FEATURES.ETSY_INTEGRATION]: true,
      [FEATURES.SHOPIFY_INTEGRATION]: true,
      [FEATURES.CRAFTFLOW_COMMERCE]: true,
      [FEATURES.FILE_CLEANER]: true,
      [FEATURES.AUTO_NAMING]: true,
      [FEATURES.BATCH_UPLOADS]: true,
      [FEATURES.ADVANCED_RESIZING]: true,
      [FEATURES.PRINT_FILE_GENERATOR]: true,
      [FEATURES.CSV_EXPORT]: true,
      [FEATURES.MULTI_SHOP_SUPPORT]: true,
    },
    limits: {
      mockupsPerMonth: -1,
      mockupsPerBatch: -1,
      templates: -1,
      canvas: -1,
      sizes: -1,
    },
    color: 'amber',
  },
};

const useSubscriptionStore = create(
  persist(
    (set, get) => ({
      // Current subscription state
      currentTier: SUBSCRIPTION_TIERS.FREE,
      subscriptionActive: true,
      subscriptionExpiresAt: null,
      subscriptionStatus: 'active',

      // Usage tracking
      currentUsage: {
        mockupsThisMonth: 0,
        designsThisMonth: 0,
        shopsConnected: 0,
        usersInOrg: 1,
      },

      // Loading states
      loading: false,
      error: null,
      initialized: false,

      // Actions
      setSubscriptionTier: tier =>
        set({
          currentTier: tier,
          error: null,
        }),

      setSubscriptionStatus: (active, expiresAt = null, status = 'active') =>
        set({
          subscriptionActive: active,
          subscriptionExpiresAt: expiresAt,
          subscriptionStatus: status,
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

      // Fetch subscription from backend
      fetchSubscription: async () => {
        try {
          set({ loading: true, error: null });

          const [subscription, usage] = await Promise.all([
            subscriptionService.getCurrentSubscription().catch(() => null),
            subscriptionService.getUsageStats().catch(() => null),
          ]);

          if (subscription) {
            set({
              currentTier: subscription.tier || SUBSCRIPTION_TIERS.FREE,
              subscriptionActive: subscription.status === 'active',
              subscriptionStatus: subscription.status || 'active',
              subscriptionExpiresAt: subscription.current_period_end || null,
            });
          }

          if (usage) {
            set({
              currentUsage: {
                ...get().currentUsage,
                mockupsThisMonth: usage.mockups_created || 0,
                designsThisMonth: usage.designs_uploaded || 0,
              },
            });
          }

          set({ initialized: true, loading: false });
        } catch (error) {
          console.error('Error fetching subscription:', error);
          set({ error: error.message, loading: false, initialized: true });
        }
      },

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

      canUseFeature: (featureName, _requiredAmount = 1) => {
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
            if (tierConfig.limits.mockupsPerMonth !== -1) {
              return currentUsage.mockupsThisMonth < tierConfig.limits.mockupsPerMonth;
            }
            return true;

          case FEATURES.MULTI_SHOP_SUPPORT:
            if (tierConfig.limits.maxShops && tierConfig.limits.maxShops !== -1) {
              return currentUsage.shopsConnected < tierConfig.limits.maxShops;
            }
            return true;

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
            if (tierConfig.limits.mockupsPerMonth === -1) {
              return Infinity;
            }
            return Math.max(0, tierConfig.limits.mockupsPerMonth - currentUsage.mockupsThisMonth);
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
        const tierOrder = [
          SUBSCRIPTION_TIERS.FREE,
          SUBSCRIPTION_TIERS.STARTER,
          SUBSCRIPTION_TIERS.PRO,
          SUBSCRIPTION_TIERS.FULL,
        ];
        const currentIndex = tierOrder.indexOf(currentTier);

        // Find the lowest tier that supports this feature that's higher than current
        for (let i = currentIndex + 1; i < tierOrder.length; i++) {
          const tier = tierOrder[i];
          const config = TIER_CONFIGS[tier];
          if (config.features[feature]) {
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
            status: state.subscriptionStatus,
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
        subscriptionStatus: state.subscriptionStatus,
        subscriptionExpiresAt: state.subscriptionExpiresAt,
        currentUsage: state.currentUsage,
        initialized: state.initialized,
      }),
    }
  )
);

export default useSubscriptionStore;
