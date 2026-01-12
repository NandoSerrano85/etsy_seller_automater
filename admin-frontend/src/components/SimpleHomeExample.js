import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

const SimpleHome = () => {
  const {
    // User auth
    user,
    isUserAuthenticated,
    userLoading,

    // Etsy auth
    isEtsyConnected,
    etsyUserInfo,
    etsyShopInfo,
    etsyLoading,
    getValidEtsyToken,

    // Methods
    makeAuthenticatedRequest,
    getDebugInfo,
  } = useAuth();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    if (!isEtsyConnected) return;

    try {
      setLoading(true);
      setError(null);

      // Get Etsy token for API calls that need it
      const etsyToken = await getValidEtsyToken();
      if (!etsyToken) {
        throw new Error('No valid Etsy token');
      }

      // Make authenticated requests
      const [designs, analytics, orders] = await Promise.all([
        makeAuthenticatedRequest('/designs/'),
        makeAuthenticatedRequest(`/dashboard/analytics?access_token=${encodeURIComponent(etsyToken)}`),
        makeAuthenticatedRequest(`/orders/?access_token=${encodeURIComponent(etsyToken)}`),
      ]);

      setDashboardData({ designs, analytics, orders });
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isEtsyConnected) {
      fetchDashboardData();
    }
  }, [isEtsyConnected]);

  const handleDebug = () => {
    console.log('🔍 Debug Info:', getDebugInfo());
  };

  if (userLoading || etsyLoading) {
    return <div>Loading...</div>;
  }

  if (!isUserAuthenticated) {
    return <div>Please log in to your account first</div>;
  }

  return (
    <div className="p-6">
      <h1>Dashboard</h1>

      {/* Debug Panel */}
      <div className="bg-gray-100 p-4 rounded mb-4">
        <button onClick={handleDebug} className="px-4 py-2 bg-blue-500 text-white rounded">
          Debug Auth State
        </button>
      </div>

      {/* Etsy Connection Status */}
      {isEtsyConnected ? (
        <div className="bg-green-100 p-4 rounded mb-4">
          <p>✅ Connected to Etsy as {etsyUserInfo?.first_name}</p>
          {etsyShopInfo && <p>Shop: {etsyShopInfo.shop_name}</p>}
        </div>
      ) : (
        <div className="bg-yellow-100 p-4 rounded mb-4">
          <p>❌ Not connected to Etsy</p>
          <a href="/connect-etsy" className="text-blue-500">
            Connect your Etsy shop
          </a>
        </div>
      )}

      {/* Dashboard Content */}
      {loading && <p>Loading dashboard data...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded shadow">
            <h3>Designs</h3>
            <p>{dashboardData.designs?.length || 0} designs</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h3>Analytics</h3>
            <p>Revenue: ${dashboardData.analytics?.total_revenue || 0}</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h3>Orders</h3>
            <p>{dashboardData.orders?.length || 0} orders</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleHome;
