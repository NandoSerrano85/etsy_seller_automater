import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import { useNavigate } from 'react-router-dom';
import ShopifyStoreManager from '../components/ShopifyStoreManager';
import ShopifyAnalytics from '../components/ShopifyAnalytics';
import apiCache, { CACHE_KEYS } from '../utils/apiCache';
import {
  BuildingStorefrontIcon,
  ChartBarIcon,
  ShoppingBagIcon,
  CogIcon,
  PlusIcon,
  EyeIcon,
  ArrowTrendingUpIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

const ShopifyDashboard = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [storeConnected, setStoreConnected] = useState(false);
  const [loadingStore, setLoadingStore] = useState(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Show cached data immediately if available
      const cachedStore = apiCache.getValid(CACHE_KEYS.SHOPIFY_STORE, 30);
      const cachedAnalytics = apiCache.getValid(CACHE_KEYS.SHOPIFY_ANALYTICS, 60);

      if (cachedStore) {
        setStoreConnected(true);
        setLoadingStore(false);
      }

      if (cachedAnalytics) {
        setDashboardData(cachedAnalytics);
        setLoadingAnalytics(false);
      }

      // If we have all cached data, show it immediately
      if (cachedStore && cachedAnalytics) {
        setLoading(false);
      }

      const headers = {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      const fetchWithTimeout = (url, options, timeout = 5000) => {
        return Promise.race([
          fetch(url, options),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeout)
          )
        ]);
      };

      // Make parallel API calls for better performance
      const requests = [];

      // Only fetch store data if not cached
      if (!cachedStore) {
        requests.push({ key: 'store', promise: fetchWithTimeout('/api/shopify/store', { headers }) });
      }

      // Only fetch analytics if not cached
      if (!cachedAnalytics) {
        requests.push({ key: 'analytics', promise: fetchWithTimeout('/api/shopify/analytics/summary', { headers }) });
      }

      if (requests.length > 0) {
        const results = await Promise.allSettled(requests.map(req => req.promise));

        requests.forEach((request, index) => {
          const result = results[index];

          if (request.key === 'store') {
            setLoadingStore(false);
            if (result.status === 'fulfilled' && result.value.ok) {
              setStoreConnected(true);
              // Cache store connection status
              apiCache.set(CACHE_KEYS.SHOPIFY_STORE, { connected: true }, 30);
            } else {
              setStoreConnected(false);
              if (result.status === 'rejected') {
                console.warn('Store API timeout or error:', result.reason);
              }
            }
          }

          if (request.key === 'analytics') {
            setLoadingAnalytics(false);
            if (result.status === 'fulfilled' && result.value.ok) {
              result.value.json().then(analyticsData => {
                setDashboardData(analyticsData);
                // Cache analytics data for 1 minute
                apiCache.set(CACHE_KEYS.SHOPIFY_ANALYTICS, analyticsData, 60);
              }).catch(jsonError => {
                console.error('Error parsing analytics data:', jsonError);
                setDashboardData(null);
              });
            } else {
              if (result.status === 'rejected') {
                console.warn('Analytics API timeout or error:', result.reason);
              }
              setDashboardData(null);
            }
          }
        });
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      addNotification('Failed to load dashboard data', 'error');
    } finally {
      setLoading(false);
      setLoadingStore(false);
      setLoadingAnalytics(false);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'analytics', name: 'Analytics', icon: ArrowTrendingUpIcon },
    { id: 'store', name: 'Store Settings', icon: CogIcon },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading Shopify dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <BuildingStorefrontIcon className="w-8 h-8 mr-3 text-sage-600" />
              Shopify Integration
            </h1>
            <p className="text-gray-600">Manage your Shopify store and track performance</p>
          </div>

          {storeConnected && (
            <div className="flex items-center space-x-3">
              <button
                onClick={() => navigate('/shopify/create')}
                className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Create Product
              </button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-sage-500 text-sage-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            {storeConnected && (loadingAnalytics ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg shadow-lg p-6">
                    <div className="flex items-center">
                      <div className="p-3 rounded-lg bg-gray-100">
                        <div className="w-6 h-6 bg-gray-200 rounded animate-pulse"></div>
                      </div>
                      <div className="ml-4 flex-1">
                        <div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
                        <div className="h-8 bg-gray-200 rounded animate-pulse mb-1"></div>
                        <div className="h-3 bg-gray-200 rounded animate-pulse w-3/4"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : dashboardData && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-lg bg-blue-100">
                      <ShoppingBagIcon className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Orders (30d)</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {dashboardData.last_30_days?.total_orders || 0}
                      </p>
                      {dashboardData.last_30_days?.orders_growth !== undefined && (
                        <p
                          className={`text-sm ${
                            dashboardData.last_30_days.orders_growth >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {dashboardData.last_30_days.orders_growth >= 0 ? '+' : ''}
                          {dashboardData.last_30_days.orders_growth}% vs last period
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-lg bg-green-100">
                      <CurrencyDollarIcon className="w-6 h-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Revenue (30d)</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${dashboardData.last_30_days?.total_revenue || 0}
                      </p>
                      {dashboardData.last_30_days?.revenue_growth !== undefined && (
                        <p
                          className={`text-sm ${
                            dashboardData.last_30_days.revenue_growth >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {dashboardData.last_30_days.revenue_growth >= 0 ? '+' : ''}
                          {dashboardData.last_30_days.revenue_growth}% vs last period
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-lg bg-purple-100">
                      <ChartBarIcon className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Avg Order Value</p>
                      <p className="text-2xl font-bold text-gray-900">
                        ${dashboardData.last_30_days?.average_order_value || 0}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-lg bg-amber-100">
                      <ClockIcon className="w-6 h-6 text-amber-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Orders (7d)</p>
                      <p className="text-2xl font-bold text-gray-900">{dashboardData.last_7_days?.total_orders || 0}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Store Connection Status */}
            {loadingStore ? (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-200 rounded animate-pulse mr-4"></div>
                    <div>
                      <div className="h-5 bg-gray-200 rounded animate-pulse mb-2 w-32"></div>
                      <div className="h-4 bg-gray-200 rounded animate-pulse w-48"></div>
                    </div>
                  </div>
                  <div className="flex space-x-3">
                    <div className="h-8 bg-gray-200 rounded animate-pulse w-24"></div>
                    <div className="h-8 bg-gray-200 rounded animate-pulse w-20"></div>
                  </div>
                </div>
              </div>
            ) : (
              <ShopifyStoreManager />
            )}

            {/* Recent Activity */}
            {storeConnected && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Quick Actions */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                  <div className="space-y-3">
                    <button
                      onClick={() => navigate('/shopify/products')}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center">
                        <BuildingStorefrontIcon className="w-5 h-5 text-sage-600 mr-3" />
                        <span className="font-medium">Manage Products</span>
                      </div>
                      <EyeIcon className="w-4 h-4 text-gray-400" />
                    </button>

                    <button
                      onClick={() => navigate('/shopify/orders')}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center">
                        <ShoppingBagIcon className="w-5 h-5 text-sage-600 mr-3" />
                        <span className="font-medium">View Orders</span>
                      </div>
                      <EyeIcon className="w-4 h-4 text-gray-400" />
                    </button>

                    <button
                      onClick={() => navigate('/shopify/create')}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center">
                        <PlusIcon className="w-5 h-5 text-sage-600 mr-3" />
                        <span className="font-medium">Create New Product</span>
                      </div>
                      <EyeIcon className="w-4 h-4 text-gray-400" />
                    </button>

                    <button
                      onClick={() => setActiveTab('analytics')}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center">
                        <ChartBarIcon className="w-5 h-5 text-sage-600 mr-3" />
                        <span className="font-medium">View Analytics</span>
                      </div>
                      <EyeIcon className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                </div>

                {/* Top Products */}
                {dashboardData?.top_products && dashboardData.top_products.length > 0 && (
                  <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Products (30d)</h3>
                    <div className="space-y-3">
                      {dashboardData.top_products.slice(0, 5).map((product, index) => (
                        <div key={product.product_id || index} className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="text-sm font-medium text-gray-900 truncate">{product.title}</div>
                            <div className="text-xs text-gray-500">{product.quantity_sold} sold</div>
                          </div>
                          <div className="text-sm font-medium text-gray-900">${product.total_revenue}</div>
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={() => navigate('/shopify/products')}
                      className="mt-4 w-full text-center text-sm text-sage-600 hover:text-sage-700"
                    >
                      View all products →
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Getting Started */}
            {!storeConnected && (
              <div className="bg-white rounded-lg shadow-lg p-8 text-center">
                <BuildingStorefrontIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Connect Your Shopify Store</h3>
                <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
                  Get started by connecting your Shopify store to sync products, track orders, and access powerful
                  analytics to grow your business.
                </p>
                <button
                  onClick={() => navigate('/shopify/connect')}
                  className="bg-sage-600 text-white px-6 py-3 rounded-lg hover:bg-sage-700"
                >
                  Connect Shopify Store
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div>
            {storeConnected ? (
              <ShopifyAnalytics />
            ) : (
              <div className="bg-white rounded-lg shadow-lg p-8 text-center">
                <ChartBarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Analytics Unavailable</h3>
                <p className="text-gray-600 mb-6">
                  Please connect your Shopify store to access analytics and insights.
                </p>
                <button
                  onClick={() => navigate('/shopify/connect')}
                  className="bg-sage-600 text-white px-6 py-3 rounded-lg hover:bg-sage-700"
                >
                  Connect Store
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'store' && (
          <div>
            <ShopifyStoreManager />
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopifyDashboard;
