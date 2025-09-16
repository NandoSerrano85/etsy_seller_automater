import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from './NotificationSystem';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ShoppingBagIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CalendarIcon,
  FunnelIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ArcElement);

const ShopifyAnalytics = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();

  // State management
  const [loading, setLoading] = useState(true);
  const [orderStats, setOrderStats] = useState(null);
  const [topProducts, setTopProducts] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  // Filter state
  const [dateRange, setDateRange] = useState('30d');
  const [groupBy, setGroupBy] = useState('day');
  const [customDateRange, setCustomDateRange] = useState({
    start: '',
    end: '',
  });
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Calculate date range based on selection
  const getDateRange = useCallback(() => {
    const end = new Date();
    let start = new Date();

    switch (dateRange) {
      case '7d':
        start.setDate(end.getDate() - 7);
        break;
      case '30d':
        start.setDate(end.getDate() - 30);
        break;
      case '90d':
        start.setDate(end.getDate() - 90);
        break;
      case 'custom':
        if (customDateRange.start && customDateRange.end) {
          return {
            start: new Date(customDateRange.start).toISOString(),
            end: new Date(customDateRange.end).toISOString(),
          };
        }
        start.setDate(end.getDate() - 30);
        break;
      default:
        start.setDate(end.getDate() - 30);
    }

    return {
      start: start.toISOString(),
      end: end.toISOString(),
    };
  }, [dateRange, customDateRange]);

  // Fetch analytics data
  const fetchAnalytics = useCallback(async () => {
    if (!token) return;

    try {
      setLoading(true);
      setError(null);

      const { start, end } = getDateRange();

      // Fetch order statistics
      const statsParams = new URLSearchParams({
        start_date: start,
        end_date: end,
        group_by: groupBy,
      });

      const statsResponse = await fetch(`/api/shopify/orders/stats?${statsParams}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!statsResponse.ok) {
        const errorData = await statsResponse.json();
        throw new Error(errorData.detail || 'Failed to fetch order statistics');
      }

      const statsData = await statsResponse.json();
      setOrderStats(statsData);

      // Fetch top products
      const productsParams = new URLSearchParams({
        start_date: start,
        end_date: end,
        limit: '10',
      });

      const productsResponse = await fetch(`/api/shopify/orders/top-products?${productsParams}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (productsResponse.ok) {
        const productsData = await productsResponse.json();
        setTopProducts(productsData);
      }

      // Fetch summary
      const summaryResponse = await fetch('/api/shopify/analytics/summary', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setSummary(summaryData);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setError(error.message);

      if (error.message.includes('authentication')) {
        addNotification('Please reconnect your Shopify store', 'error');
      } else {
        addNotification(`Analytics error: ${error.message}`, 'error');
      }
    } finally {
      setLoading(false);
    }
  }, [token, getDateRange, groupBy, addNotification]);

  // Initial load (only run once)
  useEffect(() => {
    fetchAnalytics();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAnalytics, 60000); // Refresh every minute
      return () => clearInterval(interval);
    }
  }, [autoRefresh]); // eslint-disable-line react-hooks/exhaustive-deps

  // Chart configurations
  const getLineChartData = () => {
    if (!orderStats || !orderStats.time_series) return null;

    const labels = orderStats.time_series.map(point => {
      const date = new Date(point.date);
      if (groupBy === 'day') {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } else if (groupBy === 'week') {
        return `Week of ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
      } else {
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      }
    });

    return {
      labels,
      datasets: [
        {
          label: 'Orders',
          data: orderStats.time_series.map(point => point.orders),
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          yAxisID: 'y',
        },
        {
          label: 'Revenue ($)',
          data: orderStats.time_series.map(point => point.revenue),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          yAxisID: 'y1',
        },
      ],
    };
  };

  const getBarChartData = () => {
    if (!topProducts || !topProducts.top_by_revenue) return null;

    const products = topProducts.top_by_revenue.slice(0, 8); // Show top 8

    return {
      labels: products.map(product =>
        product.title.length > 20 ? `${product.title.substring(0, 20)}...` : product.title
      ),
      datasets: [
        {
          label: 'Revenue ($)',
          data: products.map(product => product.total_revenue),
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(251, 191, 36, 0.8)',
            'rgba(239, 68, 68, 0.8)',
            'rgba(168, 85, 247, 0.8)',
            'rgba(236, 72, 153, 0.8)',
            'rgba(14, 165, 233, 0.8)',
            'rgba(34, 197, 94, 0.8)',
          ],
          borderColor: [
            'rgba(59, 130, 246, 1)',
            'rgba(34, 197, 94, 1)',
            'rgba(251, 191, 36, 1)',
            'rgba(239, 68, 68, 1)',
            'rgba(168, 85, 247, 1)',
            'rgba(236, 72, 153, 1)',
            'rgba(14, 165, 233, 1)',
            'rgba(34, 197, 94, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Orders & Revenue Over Time',
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Orders',
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Revenue ($)',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const barChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Top Products by Revenue',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Revenue ($)',
        },
      },
    },
  };

  if (error && error.includes('No active Shopify store')) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 text-center">
        <ExclamationTriangleIcon className="w-16 h-16 text-amber-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Shopify Store Connected</h3>
        <p className="text-gray-600 mb-4">Please connect your Shopify store to view analytics data.</p>
        <button
          onClick={() => (window.location.href = '/shopify/connect')}
          className="bg-sage-600 hover:bg-sage-700 text-white px-6 py-2 rounded-md transition-colors"
        >
          Connect Shopify Store
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading analytics data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Shopify Analytics</h2>
          <p className="text-gray-600">
            {orderStats?.store_name ? `Store: ${orderStats.store_name}` : 'Order and revenue insights'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              autoRefresh
                ? 'bg-sage-100 text-sage-700 border border-sage-300'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            <ArrowPathIcon className="w-4 h-4 mr-1 inline" />
            Auto-refresh
          </button>
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <FunnelIcon className="w-5 h-5 mr-2" />
            Filters
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
            <select
              value={dateRange}
              onChange={e => setDateRange(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="custom">Custom range</option>
            </select>
          </div>

          {/* Group By */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Group By</label>
            <select
              value={groupBy}
              onChange={e => setGroupBy(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="day">Daily</option>
              <option value="week">Weekly</option>
              <option value="month">Monthly</option>
            </select>
          </div>

          {/* Custom Date Range */}
          {dateRange === 'custom' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={customDateRange.start}
                  onChange={e => setCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={customDateRange.end}
                  onChange={e => setCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      {orderStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <SummaryCard
            title="Total Orders"
            value={orderStats.summary.total_orders}
            growth={orderStats.summary.orders_growth}
            icon={ShoppingBagIcon}
            color="blue"
          />
          <SummaryCard
            title="Total Revenue"
            value={`$${orderStats.summary.total_revenue}`}
            growth={orderStats.summary.revenue_growth}
            icon={CurrencyDollarIcon}
            color="green"
          />
          <SummaryCard
            title="Avg Order Value"
            value={`$${orderStats.summary.average_order_value}`}
            icon={ChartBarIcon}
            color="purple"
          />
          <SummaryCard
            title="Products Sold"
            value={topProducts?.total_products_sold || 0}
            icon={ChartBarIcon}
            color="amber"
          />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Orders & Revenue Chart */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {getLineChartData() ? (
            <Line data={getLineChartData()} options={lineChartOptions} />
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No order data available for the selected period</p>
            </div>
          )}
        </div>

        {/* Top Products Chart */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {getBarChartData() ? (
            <Bar data={getBarChartData()} options={barChartOptions} />
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No product data available for the selected period</p>
            </div>
          )}
        </div>
      </div>

      {/* Top Products Table */}
      {topProducts && topProducts.top_by_revenue.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Products Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity Sold
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Orders
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {topProducts.top_by_revenue.slice(0, 10).map((product, index) => (
                  <tr key={product.product_id || index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{product.title}</div>
                      <div className="text-sm text-gray-500">ID: {product.product_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${product.total_revenue}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.quantity_sold}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${product.average_price}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.orders_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mr-2" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error Loading Analytics</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Summary Card Component
const SummaryCard = ({ title, value, growth, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-100',
    green: 'text-green-600 bg-green-100',
    purple: 'text-purple-600 bg-purple-100',
    amber: 'text-amber-600 bg-amber-100',
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {growth !== undefined && (
            <div className="flex items-center mt-1">
              {growth >= 0 ? (
                <ArrowTrendingUpIcon className="w-4 h-4 text-green-500 mr-1" />
              ) : (
                <ArrowTrendingDownIcon className="w-4 h-4 text-red-500 mr-1" />
              )}
              <span className={`text-sm font-medium ${growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {growth >= 0 ? '+' : ''}
                {growth}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShopifyAnalytics;
