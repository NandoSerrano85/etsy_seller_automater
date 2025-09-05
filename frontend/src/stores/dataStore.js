import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const DEFAULT_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const ANALYTICS_CACHE_DURATION = 10 * 60 * 1000; // 10 minutes for analytics
const DESIGNS_CACHE_DURATION = 15 * 60 * 1000; // 15 minutes for designs

const useDataStore = create(
  persist(
    (set, get) => ({
      // Cache storage
      cache: {},

      // Loading states for different data types
      loading: {
        topSellers: false,
        monthlyAnalytics: false,
        designs: false,
        orders: false,
        mockups: false,
      },

      // Error states
      errors: {
        topSellers: null,
        monthlyAnalytics: null,
        designs: null,
        orders: null,
        mockups: null,
      },

      // Data storage with timestamps
      data: {
        topSellers: null,
        monthlyAnalytics: null,
        designs: null,
        orders: null,
        mockups: null,
        dashboardStats: null,
      },

      timestamps: {
        topSellers: null,
        monthlyAnalytics: null,
        designs: null,
        orders: null,
        mockups: null,
        dashboardStats: null,
      },

      // Cache management methods
      setCacheData: (key, data, customTtl = null) => {
        const ttl = customTtl || DEFAULT_CACHE_DURATION;
        const expiresAt = Date.now() + ttl;

        console.log(`🗄️ Caching data for ${key}, expires at:`, new Date(expiresAt));

        set(state => ({
          data: {
            ...state.data,
            [key]: data,
          },
          timestamps: {
            ...state.timestamps,
            [key]: expiresAt,
          },
          errors: {
            ...state.errors,
            [key]: null,
          },
        }));
      },

      getCacheData: key => {
        const { data, timestamps } = get();
        const now = Date.now();

        if (!data[key] || !timestamps[key]) {
          console.log(`❌ No cached data for ${key}`);
          return null;
        }

        if (now > timestamps[key]) {
          console.log(`⏰ Cached data for ${key} expired`);
          // Clear expired data
          set(state => ({
            data: {
              ...state.data,
              [key]: null,
            },
            timestamps: {
              ...state.timestamps,
              [key]: null,
            },
          }));
          return null;
        }

        console.log(
          `✅ Using cached data for ${key}, expires in:`,
          Math.floor((timestamps[key] - now) / 1000 / 60),
          'minutes'
        );
        return data[key];
      },

      isCacheValid: key => {
        const { timestamps } = get();
        return timestamps[key] && Date.now() < timestamps[key];
      },

      clearCache: (key = null) => {
        if (key) {
          console.log(`🗑️ Clearing cache for ${key}`);
          set(state => ({
            data: {
              ...state.data,
              [key]: null,
            },
            timestamps: {
              ...state.timestamps,
              [key]: null,
            },
          }));
        } else {
          console.log('🗑️ Clearing all cache');
          set(state => ({
            data: {
              topSellers: null,
              monthlyAnalytics: null,
              designs: null,
              orders: null,
              mockups: null,
              dashboardStats: null,
            },
            timestamps: {
              topSellers: null,
              monthlyAnalytics: null,
              designs: null,
              orders: null,
              mockups: null,
              dashboardStats: null,
            },
          }));
        }
      },

      // Loading state management
      setLoading: (key, loading) => {
        set(state => ({
          loading: {
            ...state.loading,
            [key]: loading,
          },
        }));
      },

      // Error state management
      setError: (key, error) => {
        set(state => ({
          errors: {
            ...state.errors,
            [key]: error,
          },
        }));
      },

      // Specific data getters - return stable references from store data
      getTopSellers: () => {
        const { data } = get();
        return data.topSellers || [];
      },

      getMonthlyAnalytics: () => {
        const { data } = get();
        return data.monthlyAnalytics;
      },

      getDesigns: () => {
        const { data } = get();
        return data.designs || [];
      },

      getOrders: () => {
        const { data } = get();
        return data.orders || [];
      },

      getMockups: () => {
        const { data } = get();
        return data.mockups || [];
      },

      getDashboardStats: () => {
        const { data } = get();
        return (
          data.dashboardStats || {
            totalSales: 0,
            totalOrders: 0,
            totalDesigns: 0,
            totalMockups: 0,
          }
        );
      },

      // Helper methods for different TTL requirements
      setCacheWithTtl: {
        topSellers: data => get().setCacheData('topSellers', data, ANALYTICS_CACHE_DURATION),
        monthlyAnalytics: data => get().setCacheData('monthlyAnalytics', data, ANALYTICS_CACHE_DURATION),
        designs: data => get().setCacheData('designs', data, DESIGNS_CACHE_DURATION),
        orders: data => get().setCacheData('orders', data, DEFAULT_CACHE_DURATION),
        mockups: data => get().setCacheData('mockups', data, DESIGNS_CACHE_DURATION),
        dashboardStats: data => get().setCacheData('dashboardStats', data, DEFAULT_CACHE_DURATION),
      },

      // Debug method
      getCacheStatus: () => {
        const { data, timestamps, loading, errors } = get();
        const now = Date.now();

        const status = {};
        Object.keys(data).forEach(key => {
          status[key] = {
            hasData: !!data[key],
            isValid: timestamps[key] && now < timestamps[key],
            expiresIn: timestamps[key]
              ? Math.max(0, Math.floor((timestamps[key] - now) / 1000 / 60)) + ' minutes'
              : 'N/A',
            loading: loading[key] || false,
            error: errors[key] || null,
            lastUpdate: timestamps[key] ? new Date(timestamps[key] - DEFAULT_CACHE_DURATION).toLocaleString() : 'Never',
          };
        });

        return status;
      },
    }),
    {
      name: 'data-store',
      partialize: state => ({
        // Persist cache data and timestamps but not loading/error states
        data: state.data,
        timestamps: state.timestamps,
      }),
    }
  )
);

export default useDataStore;
