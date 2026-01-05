import { useCallback } from 'react';
import { useAuth } from './useAuth';
import useDataStore from '../stores/dataStore';

export const useCachedApi = () => {
  const { isEtsyConnected, makeAuthenticatedRequest } = useAuth();

  const {
    // Cache management
    getCacheData,
    setCacheWithTtl,
    isCacheValid,
    clearCache,

    // Loading states
    loading,
    setLoading,

    // Error states
    errors,
    setError,

    // Data getters
    getTopSellers,
    getMonthlyAnalytics,
    getDesigns,
    getOrders,
    getMockups,
    getDashboardStats,

    // Debug
    getCacheStatus,
  } = useDataStore();

  // Generic cached API call method
  const makeCachedApiCall = useCallback(
    async (cacheKey, apiCall, forceRefresh = false) => {
      try {
        // Check cache first
        if (!forceRefresh && isCacheValid(cacheKey)) {
          const cachedData = getCacheData(cacheKey);
          if (cachedData) {
            console.log(`📋 Using cached data for ${cacheKey}`);
            return cachedData;
          }
        }

        console.log(`🌐 Fetching fresh data for ${cacheKey}`);
        setLoading(cacheKey, true);
        setError(cacheKey, null);

        const data = await apiCall();

        // Cache the data with appropriate TTL
        setCacheWithTtl[cacheKey]?.(data);

        return data;
      } catch (error) {
        console.error(`❌ Error fetching ${cacheKey}:`, error);
        setError(cacheKey, error.message || 'Failed to fetch data');
        throw error;
      } finally {
        setLoading(cacheKey, false);
      }
    },
    [getCacheData, isCacheValid, setCacheWithTtl, setLoading, setError]
  );

  // Specific API methods with caching
  const fetchTopSellers = useCallback(
    async (forceRefresh = false, year = new Date().getFullYear()) => {
      if (!isEtsyConnected) {
        throw new Error('Etsy not connected');
      }

      return makeCachedApiCall(
        'topSellers',
        async () => {
          // Auth service will automatically handle token refresh and injection
          const response = await makeAuthenticatedRequest(`/dashboard/top-sellers?year=${year}`);
          return response?.top_sellers || response?.data?.top_sellers || [];
        },
        forceRefresh
      );
    },
    [isEtsyConnected, makeAuthenticatedRequest, makeCachedApiCall]
  );

  const fetchMonthlyAnalytics = useCallback(
    async (forceRefresh = false, year = new Date().getFullYear()) => {
      if (!isEtsyConnected) {
        throw new Error('Etsy not connected');
      }

      return makeCachedApiCall(
        'monthlyAnalytics',
        async () => {
          // Auth service will automatically handle token refresh and injection
          const response = await makeAuthenticatedRequest(`/dashboard/analytics?year=${year}`);

          return (
            response?.data?.analytics ||
            response || {
              monthly_revenue: [],
              monthly_orders: [],
              monthly_views: [],
            }
          );
        },
        forceRefresh
      );
    },
    [isEtsyConnected, makeAuthenticatedRequest, makeCachedApiCall]
  );

  const fetchDesigns = useCallback(
    async (forceRefresh = false) => {
      return makeCachedApiCall(
        'designGallery',
        async () => {
          // Use new gallery endpoint that returns both Etsy mockups and QNAP design files
          console.log('🎨 Fetching designs from /designs/gallery...');
          const response = await makeAuthenticatedRequest('/designs/gallery');
          console.log('🎨 Designs API response:', response);
          return response || { mockups: [], files: [] };
        },
        forceRefresh
      );
    },
    [makeAuthenticatedRequest, makeCachedApiCall]
  );

  const fetchOrders = useCallback(
    async (forceRefresh = false) => {
      if (!isEtsyConnected) {
        throw new Error('Etsy not connected');
      }

      return makeCachedApiCall(
        'orders',
        async () => {
          // Auth service will automatically handle token refresh and injection
          // Fetch only unshipped orders for the pending count (paid, not shipped, not canceled)
          const response = await makeAuthenticatedRequest(
            '/api/orders?was_paid=true&was_shipped=false&was_canceled=false'
          );
          return response?.orders || response?.data?.orders || [];
        },
        forceRefresh
      );
    },
    [isEtsyConnected, makeAuthenticatedRequest, makeCachedApiCall]
  );

  const fetchMockups = useCallback(
    async (forceRefresh = false) => {
      return makeCachedApiCall(
        'mockups',
        async () => {
          const response = await makeAuthenticatedRequest('/mockups/');
          return response?.mockups || response?.data?.mockups || [];
        },
        forceRefresh
      );
    },
    [makeAuthenticatedRequest, makeCachedApiCall]
  );

  // Fetch all dashboard data
  const fetchAllDashboardData = useCallback(
    async (forceRefresh = false) => {
      if (!isEtsyConnected) {
        throw new Error('Etsy not connected');
      }

      try {
        console.log('🚀 Fetching all dashboard data...');

        const [topSellers, monthlyAnalytics, designs, orders, mockups] = await Promise.allSettled([
          fetchTopSellers(forceRefresh),
          fetchMonthlyAnalytics(forceRefresh),
          fetchDesigns(forceRefresh),
          fetchOrders(forceRefresh),
          fetchMockups(forceRefresh),
        ]);

        // Calculate dashboard stats
        const stats = {
          totalSales:
            monthlyAnalytics.status === 'fulfilled'
              ? monthlyAnalytics.value?.total_revenue || monthlyAnalytics.value?.data?.total_revenue || 0
              : 0,
          totalOrders: orders.status === 'fulfilled' ? orders.value?.length || 0 : 0,
          totalDesigns:
            designs.status === 'fulfilled' ? designs.value?.total_files || designs.value?.files?.length || 0 : 0,
          totalMockups: mockups.status === 'fulfilled' ? mockups.value?.length || 0 : 0, // Use /mockups/ endpoint for dashboard
        };

        // Cache dashboard stats
        setCacheWithTtl.dashboardStats(stats);

        console.log('✅ All dashboard data fetched successfully');

        return {
          topSellers: topSellers.status === 'fulfilled' ? topSellers.value : [],
          monthlyAnalytics: monthlyAnalytics.status === 'fulfilled' ? monthlyAnalytics.value : null,
          designs: designs.status === 'fulfilled' ? designs.value : { mockups: [], files: [] },
          orders: orders.status === 'fulfilled' ? orders.value : [],
          mockups: mockups.status === 'fulfilled' ? mockups.value : [],
          dashboardStats: stats,
        };
      } catch (error) {
        console.error('❌ Error fetching dashboard data:', error);
        throw error;
      }
    },
    [isEtsyConnected, fetchTopSellers, fetchMonthlyAnalytics, fetchDesigns, fetchOrders, fetchMockups, setCacheWithTtl]
  );

  // Cache management utilities
  const refreshData = useCallback(
    (dataType = null) => {
      if (dataType) {
        clearCache(dataType);
      } else {
        clearCache();
      }
    },
    [clearCache]
  );

  const refreshAllData = useCallback(() => {
    return fetchAllDashboardData(true);
  }, [fetchAllDashboardData]);

  return {
    // Data fetching methods
    fetchTopSellers,
    fetchMonthlyAnalytics,
    fetchDesigns,
    fetchOrders,
    fetchMockups,
    fetchAllDashboardData,

    // Cached data getters
    getTopSellers,
    getMonthlyAnalytics,
    getDesigns,
    getOrders,
    getMockups,
    getDashboardStats,

    // Loading states
    loading,

    // Error states
    errors,

    // Cache management
    refreshData,
    refreshAllData,
    clearCache,
    getCacheStatus,

    // Cache status helpers
    isDataCached: isCacheValid,

    // Debug helper
    debugCache: () => {
      console.table(getCacheStatus());
    },
  };
};

export default useCachedApi;
