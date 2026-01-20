import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useCachedApi } from '../../hooks/useCachedApi';
import useDataStore from '../../stores/dataStore';
import OnboardingFlow from '../../components/OnboardingFlow';
import { SalesCard, OrdersCard, DesignsCard, MockupsCard } from '../../components/StatusCard';
import QuickActions from '../../components/QuickActions';
import OverviewTab from '../HomeTabs/OverviewTab';

const EtsyDashboard = () => {
  const { user, isUserAuthenticated, isEtsyConnected, etsyUserInfo, etsyShopInfo, etsyError, getDebugInfo } = useAuth();

  const { fetchAllDashboardData, refreshAllData, loading, errors, debugCache } = useCachedApi();

  const [showOnboarding, setShowOnboarding] = useState(false);

  const { data: storeData } = useDataStore();

  const dashboardStats = storeData.dashboardStats || {
    totalSales: 0,
    totalOrders: 0,
    totalDesigns: 0,
    totalMockups: 0,
  };
  const topSellers = storeData.topSellers || [];
  const monthlyAnalytics = storeData.monthlyAnalytics;
  const designs = storeData.designs || { mockups: [], files: [] };

  const isLoading = useMemo(() => Object.values(loading).some(Boolean), [loading]);
  const error = useMemo(() => Object.values(errors).find(Boolean) || null, [errors]);

  const debugTokens = () => {
    console.log('DEBUG: Auth State:', getDebugInfo());
  };

  useEffect(() => {
    const onboardingCompleted = localStorage.getItem('onboarding_completed');
    if (!onboardingCompleted && isUserAuthenticated) {
      setShowOnboarding(true);
    }
  }, [isUserAuthenticated]);

  const handleFetchData = useCallback(
    async (forceRefresh = false) => {
      if (!isEtsyConnected) return;

      try {
        await fetchAllDashboardData(forceRefresh);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
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

  useEffect(() => {
    if (isEtsyConnected) {
      handleFetchData();
    }
  }, [isEtsyConnected]);

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

  return (
    <>
      {showOnboarding && <OnboardingFlow onComplete={() => setShowOnboarding(false)} />}

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

      {process.env.REACT_APP_DEBUG === 'true' && isEtsyConnected && (etsyUserInfo || etsyShopInfo) && (
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

      {process.env.REACT_APP_DEBUG === 'true' && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
          <p className="text-gray-700 text-sm mb-2">Debug Panel:</p>
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
              Connection Status: <strong>{isEtsyConnected ? 'Connected' : 'Disconnected'}</strong>
            </span>
          </div>
        </div>
      )}

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
    </>
  );
};

export default EtsyDashboard;
