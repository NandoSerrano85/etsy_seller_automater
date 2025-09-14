import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useCachedApi } from '../hooks/useCachedApi';
import useDataStore from '../stores/dataStore';
import OnboardingFlow from '../components/OnboardingFlow';
import { SalesCard, OrdersCard, DesignsCard, MockupsCard } from '../components/StatusCard';
import QuickActions from '../components/QuickActions';
import OverviewTab from './HomeTabs/OverviewTab';
import AnalyticsTab from './HomeTabs/AnalyticsTab';
import DesignsTab from './HomeTabs/DesignsTab';
import ToolsTab from './HomeTabs/ToolsTab';
import OrdersTab from './HomeTabs/OrdersTab';
import ListingsTab from './HomeTabs/ListingsTab';

// const LoadingIndicator = () => (
//   <div className="flex items-center justify-center p-4">
//     <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lavender-500"></div>
//     <span className="ml-2 text-sage-600">Loading...</span>
//   </div>
// );

// const TabErrorBoundary = ({ error, onRetry, children }) => {
//   if (error) {
//     return (
//       <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
//         <p className="text-rose-700">{error}</p>
//         {onRetry && (
//           <button onClick={onRetry} className="mt-4 px-4 py-2 bg-rose-100 text-rose-700 rounded-lg hover:bg-rose-200">
//             Try Again
//           </button>
//         )}
//       </div>
//     );
//   }
//   return children;
// };

const Home = () => {
  const {
    // User auth
    user,
    isUserAuthenticated,
    // userLoading,

    // Etsy auth
    isEtsyConnected,
    etsyUserInfo,
    etsyShopInfo,
    // etsyLoading,
    etsyError,

    // Methods
    getDebugInfo,
  } = useAuth();

  // Cached API hook
  const {
    // Data fetchers
    fetchAllDashboardData,
    refreshAllData,

    // Loading and error states
    loading,
    errors,

    // Cache management
    debugCache,
  } = useCachedApi();

  const [searchParams] = useSearchParams();

  // Get active tab from URL params
  const activeTab = searchParams.get('tab') || 'overview';

  // State
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Get cached data directly from store - this will be stable and reactive
  const { data: storeData } = useDataStore();

  // Extract data with fallbacks
  const dashboardStats = storeData.dashboardStats || {
    totalSales: 0,
    totalOrders: 0,
    totalDesigns: 0,
    totalMockups: 0,
  };
  const topSellers = storeData.topSellers || [];
  const monthlyAnalytics = storeData.monthlyAnalytics;
  const designs = storeData.designs || { mockups: [], files: [] };
  const orders = storeData.orders || [];
  // const mockups = storeData.mockups || [];

  // Loading state - check if any data is loading
  const isLoading = useMemo(() => Object.values(loading).some(Boolean), [loading]);

  // Error state - get first error if any
  const error = useMemo(() => Object.values(errors).find(Boolean) || null, [errors]);

  // Debug helper - remove after debugging
  const debugTokens = () => {
    console.log('🔍 DEBUG: Auth State:', getDebugInfo());
  };

  useEffect(() => {
    // Check if user needs onboarding
    const onboardingCompleted = localStorage.getItem('onboarding_completed');
    if (!onboardingCompleted && isUserAuthenticated) {
      setShowOnboarding(true);
    }
  }, [isUserAuthenticated]);

  // Simplified data fetching function
  const handleFetchData = useCallback(
    async (forceRefresh = false) => {
      if (!isEtsyConnected) return;

      console.log('🔄 Fetching dashboard data...', { forceRefresh });

      try {
        await fetchAllDashboardData(forceRefresh);
        console.log('✅ Dashboard data fetch completed');
      } catch (err) {
        console.error('❌ Error fetching dashboard data:', err);
      }
    },
    [isEtsyConnected, fetchAllDashboardData]
  );

  const formatCurrency = (amount, divisor = 100) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount / divisor);
  };

  // Fetch dashboard stats when connected - stable useEffect
  useEffect(() => {
    if (isEtsyConnected) {
      handleFetchData();
    }
  }, [isEtsyConnected]); // Only depend on connection status

  // if (userLoading || etsyLoading) {
  //   return (
  //     <div className="flex items-center justify-center min-h-64">
  //       <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-lavender-500 mb-4"></div>
  //       <p className="text-sage-600 ml-4">Loading your dashboard...</p>
  //     </div>
  //   );
  // }

  if (!isUserAuthenticated) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">Please log in to access your dashboard.</p>
      </div>
    );
  }

  if (etsyError) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{etsyError}</p>
      </div>
    );
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <QuickActions />
            {isEtsyConnected && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <SalesCard value={formatCurrency(dashboardStats.totalSales)} loading={isLoading} />
                <OrdersCard value={dashboardStats.totalOrders} loading={isLoading} />
                <DesignsCard value={dashboardStats.totalDesigns} loading={isLoading} />
                <MockupsCard value={dashboardStats.totalMockups} loading={isLoading} />
              </div>
            )}
            <OverviewTab
              user={user}
              isConnected={isEtsyConnected}
              designs={designs}
              topSellers={topSellers}
              userInfo={etsyUserInfo}
              shopInfo={etsyShopInfo}
              authUrl="/connect-etsy"
              monthlyAnalytics={monthlyAnalytics}
              loading={isLoading}
              error={error}
              onRefresh={() => handleFetchData(true)}
            />
          </div>
        );

      case 'analytics':
        return (
          <AnalyticsTab
            isConnected={isEtsyConnected}
            authUrl="/connect-etsy"
            monthlyAnalytics={monthlyAnalytics}
            topSellers={topSellers}
            loading={isLoading}
            error={error}
            onRefresh={() => handleFetchData(true)}
          />
        );

      case 'designs':
        return (
          <DesignsTab
            isConnected={isEtsyConnected}
            authUrl="/connect-etsy"
            designs={designs}
            loading={isLoading}
            error={error}
            onRefresh={() => handleFetchData(true)}
          />
        );

      case 'tools':
        return <ToolsTab />;

      case 'orders':
        return (
          <OrdersTab
            isConnected={isEtsyConnected}
            authUrl="/connect-etsy"
            orders={orders}
            loading={isLoading}
            error={error}
            onRefresh={() => handleFetchData(true)}
          />
        );

      case 'listings':
        return (
          <ListingsTab
            isConnected={isEtsyConnected}
            authUrl="/connect-etsy"
            loading={isLoading}
            error={error}
            onRefresh={() => handleFetchData(true)}
          />
        );

      default:
        return (
          <div className="text-center py-12">
            <p className="text-sage-600">Select a tab to view content</p>
          </div>
        );
    }
  };

  return (
    <>
      {/* Onboarding Flow */}
      {showOnboarding && <OnboardingFlow onComplete={() => setShowOnboarding(false)} />}

      {/* Welcome Message */}
      {!isEtsyConnected && (
        <div className="bg-gradient-to-r from-lavender-100 to-mint-100 border border-lavender-200 rounded-xl p-6 mb-6">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">👋</div>
            <div>
              <h2 className="text-xl font-semibold text-sage-900 mb-2">Welcome to your Etsy automation center!</h2>
              <p className="text-sage-700 mb-4">
                Get started by connecting your Etsy shop to unlock powerful automation features.
              </p>
              <a
                href="/connect-etsy"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-lavender-500 to-lavender-600 text-white rounded-lg hover:from-lavender-600 hover:to-lavender-700 transition-all duration-200 shadow-sm hover:shadow-md"
              >
                <span className="mr-2">🛍️</span>
                Connect Your Etsy Shop
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Connection Status */}
      {isEtsyConnected && (etsyUserInfo || etsyShopInfo) && (
        <div className="bg-gradient-to-r from-mint-100 to-mint-200 border border-mint-300 rounded-xl p-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-mint-500 rounded-full animate-pulse"></div>
            <div>
              <p className="text-mint-800 font-medium">
                Connected to Etsy as {etsyUserInfo?.first_name || etsyShopInfo?.shop_name || 'User'}
              </p>
              {etsyShopInfo && <p className="text-mint-700 text-sm">Shop: {etsyShopInfo.shop_name}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 mb-6">
          <p className="text-rose-700">{error}</p>
          <button
            onClick={() => handleFetchData(true)}
            className="mt-2 text-rose-600 hover:text-rose-700 text-sm underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Debug Panel - Remove after fixing */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
        <p className="text-gray-700 text-sm mb-2">🐛 Debug Panel:</p>
        <div className="flex gap-2 text-sm">
          <button onClick={debugTokens} className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
            Check Tokens
          </button>
          <button onClick={debugCache} className="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200">
            Check Cache
          </button>
          <button
            onClick={refreshAllData}
            className="px-3 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
          >
            Force Refresh
          </button>
          <span className="text-gray-600">
            Connection Status: <strong>{isEtsyConnected ? '✅ Connected' : '❌ Disconnected'}</strong>
          </span>
        </div>
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </>
  );
};

export default Home;
