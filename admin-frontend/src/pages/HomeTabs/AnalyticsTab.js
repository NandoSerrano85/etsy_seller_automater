import React, { useState, useMemo, useEffect } from 'react';
import { Pie, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const AnalyticsTab = ({ isConnected, authUrl, monthlyAnalytics, topSellers, loading, error, onRefresh }) => {
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [analyticsView, setAnalyticsView] = useState('revenue');
  const [topSellersLimit, setTopSellersLimit] = useState(10);

  // Cleanup Chart.js instances on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      // Destroy any chart instances when component unmounts
      ChartJS.getChart('analytics-pie-chart')?.destroy();
      ChartJS.getChart('analytics-bar-chart')?.destroy();
    };
  }, []);

  const formatCurrency = (amount, divisor = 100) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount / divisor);
  };

  // Memoize chart data to prevent unnecessary re-renders
  const pieChartData = useMemo(() => {
    console.log('🟡 Pie Chart Data - topSellers:', topSellers);
    if (!topSellers || topSellers.length === 0) return null;

    const colors = [
      '#FF6384',
      '#36A2EB',
      '#FFCE56',
      '#4BC0C0',
      '#9966FF',
      '#FF9F40',
      '#FF6384',
      '#C9CBCF',
      '#4BC0C0',
      '#FF6384',
    ];

    const filteredData = topSellers.slice(0, topSellersLimit).filter(item => (item.net_amount || 0) > 0);

    if (filteredData.length === 0) return null;

    const chartData = {
      labels: filteredData.map(item => {
        const title = item.title || item.name || 'Unknown';
        return title.length > 25 ? title.substring(0, 25) + '...' : title;
      }),
      datasets: [
        {
          data: filteredData.map(item => item.net_amount || 0),
          backgroundColor: colors.slice(0, filteredData.length),
          borderColor: colors.slice(0, filteredData.length).map(color => color + '80'),
          borderWidth: 2,
        },
      ],
    };

    console.log('🟡 Generated pie chart data:', chartData);
    return chartData;
  }, [topSellers, topSellersLimit]);

  const getPieChartData = () => {
    return pieChartData;
  };

  // Memoize bar chart data
  const barChartData = useMemo(() => {
    console.log('🟠 Bar Chart Data - monthlyAnalytics:', monthlyAnalytics);
    if (!monthlyAnalytics) return null;

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    let monthlyData;

    // Check if we have monthly_breakdown data structure
    if (monthlyAnalytics.monthly_breakdown && Array.isArray(monthlyAnalytics.monthly_breakdown)) {
      // Create array of 12 months with data from monthly_breakdown
      monthlyData = new Array(12).fill(0);
      monthlyAnalytics.monthly_breakdown.forEach(monthData => {
        const monthIndex = monthData.month - 1; // Assuming month is 1-based
        if (monthIndex >= 0 && monthIndex < 12) {
          monthlyData[monthIndex] = monthData.net_sales || 0;
        }
      });
    } else {
      // Fallback to direct monthly arrays
      monthlyData =
        analyticsView === 'revenue'
          ? monthlyAnalytics.monthly_revenue || monthlyAnalytics.monthly_net_sales || new Array(12).fill(0)
          : monthlyAnalytics.monthly_orders || new Array(12).fill(0);
    }

    const chartData = {
      labels: months,
      datasets: [
        {
          label: 'Net Sales ($)',
          data: monthlyData,
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    };

    console.log('🟠 Generated bar chart data:', chartData);
    return chartData;
  }, [monthlyAnalytics, analyticsView]);

  const getMonthlyBarChartData = () => {
    return barChartData;
  };
  if (!isConnected) {
    return (
      <div className="card p-8 text-center">
        <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view analytics</p>
        <a href={authUrl} className="btn-primary">
          Connect Shop
        </a>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lavender-500"></div>
        <span className="ml-2 text-sage-600">Loading analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{error}</p>
        <button
          onClick={onRefresh}
          className="mt-2 text-rose-600 hover:text-rose-700 text-sm underline"
          aria-label="Retry loading analytics data"
        >
          Try again
        </button>
      </div>
    );
  }
  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="card p-6">
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <label htmlFor="year-select" className="font-semibold text-gray-700">
              Year:
            </label>
            <select
              id="year-select"
              value={currentYear}
              onChange={e => setCurrentYear(parseInt(e.target.value))}
              className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="view-select" className="font-semibold text-gray-700">
              View:
            </label>
            <select
              id="view-select"
              value={analyticsView}
              onChange={e => setAnalyticsView(e.target.value)}
              className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              <option value="yearly">Yearly Overview</option>
              <option value="monthly">Monthly Breakdown</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="limit-select" className="font-semibold text-gray-700">
              Show Top:
            </label>
            <select
              id="limit-select"
              value={topSellersLimit}
              onChange={e => setTopSellersLimit(parseInt(e.target.value))}
              className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={topSellers?.length || 50}>All</option>
            </select>
          </div>
        </div>
      </div>
      {/* Yearly Summary */}
      {monthlyAnalytics && (
        <div className="card p-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">{currentYear} Sales Summary</h2>
          <div className="text-center mb-8">
            <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-8 rounded-xl inline-block">
              <h3 className="text-2xl font-semibold mb-2">Total Net Sales</h3>
              <p className="text-6xl font-bold">{formatCurrency(monthlyAnalytics?.summary?.net_sales || 0)}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-blue-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-blue-900 mb-2">Total Sales</h4>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(monthlyAnalytics?.summary?.total_sales || 0)}
              </p>
            </div>
            <div className="bg-red-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-red-900 mb-2">Total Discounts</h4>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(monthlyAnalytics?.summary?.total_discounts || 0)}
              </p>
            </div>
            <div className="bg-purple-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-purple-900 mb-2">Items Sold</h4>
              <p className="text-2xl font-bold text-purple-600">{monthlyAnalytics?.summary?.total_quantity || 0}</p>
            </div>
            <div className="bg-orange-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-orange-900 mb-2">Orders</h4>
              <p className="text-2xl font-bold text-orange-600">{monthlyAnalytics?.summary?.total_receipts || 0}</p>
            </div>
          </div>
        </div>
      )}
      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="card p-6 lg:col-span-2">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Top Sellers Distribution</h3>
          {getPieChartData() && (
            <div className="relative">
              <Pie
                key="analytics-pie-chart"
                data={getPieChartData()}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: { size: 11 },
                        boxWidth: 12,
                        maxWidth: 200,
                        generateLabels: function (chart) {
                          const data = chart.data;
                          if (data.labels.length && data.datasets.length) {
                            return data.labels.map((label, i) => {
                              const value = data.datasets[0].data[i];
                              const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                              const percentage = ((value / total) * 100).toFixed(1);
                              return {
                                text: `${label} (${percentage}%)`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: data.datasets[0].borderColor[i],
                                lineWidth: data.datasets[0].borderWidth,
                                hidden: false,
                                index: i,
                              };
                            });
                          }
                          return [];
                        },
                      },
                    },
                    tooltip: {
                      callbacks: {
                        label: function (context) {
                          const label = context.label || '';
                          const value = context.parsed;
                          const total = context.dataset.data.reduce((a, b) => a + b, 0);
                          const percentage = ((value / total) * 100).toFixed(1);
                          return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                        },
                      },
                    },
                  },
                }}
              />
            </div>
          )}
        </div>
        <div className="card p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Item Totals</h3>
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-blue-900 mb-1">Total Quantity</h4>
              <p className="text-2xl font-bold text-blue-600">
                {(topSellers || []).slice(0, topSellersLimit).reduce((sum, item) => sum + (item.quantity_sold || 0), 0)}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-green-900 mb-1">Total Amount</h4>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(
                  (topSellers || []).slice(0, topSellersLimit).reduce((sum, item) => sum + (item.total_amount || 0), 0)
                )}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-red-900 mb-1">Total Discounts</h4>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(
                  (topSellers || [])
                    .slice(0, topSellersLimit)
                    .reduce((sum, item) => sum + (item.total_discounts || 0), 0)
                )}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-purple-900 mb-1">Total Net</h4>
              <p className="text-2xl font-bold text-purple-600">
                {formatCurrency(
                  (topSellers || []).slice(0, topSellersLimit).reduce((sum, item) => sum + (item.net_amount || 0), 0)
                )}
              </p>
            </div>
          </div>
        </div>
      </div>
      {/* Monthly Bar Chart */}
      {analyticsView === 'monthly' && (
        <div className="card p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Monthly Sales Trend</h3>
          {getMonthlyBarChartData() && (
            <Bar
              key="analytics-bar-chart"
              data={getMonthlyBarChartData()}
              options={{
                responsive: true,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    callbacks: {
                      label: function (context) {
                        return `Net Sales: ${formatCurrency(context.parsed.y)}`;
                      },
                    },
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      callback: function (value) {
                        return formatCurrency(value);
                      },
                    },
                  },
                },
              }}
            />
          )}
        </div>
      )}
      {/* Top Sellers Table */}
      <div className="card p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Top Sellers - {currentYear} (Showing Top {topSellersLimit})
        </h2>
        <div className="overflow-x-auto rounded-lg shadow">
          <table className="w-full bg-white">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Rank</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Item Name</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Quantity Sold</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Total Amount</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Discounts</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Net Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {(topSellers || []).slice(0, topSellersLimit).map((item, index) => (
                <tr key={item.listing_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-gray-900">{index + 1}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">{item.title}</td>
                  <td className="px-6 py-4 text-gray-700">{item.quantity_sold}</td>
                  <td className="px-6 py-4 text-gray-700">{formatCurrency(item.total_amount)}</td>
                  <td className="px-6 py-4 text-gray-700">{formatCurrency(item.total_discounts)}</td>
                  <td className="px-6 py-4 font-semibold text-green-600">{formatCurrency(item.net_amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {/* Monthly Breakdown */}
      {analyticsView === 'monthly' && monthlyAnalytics && (
        <div className="card p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Monthly Breakdown - {currentYear}</h2>
          <div className="space-y-6">
            {(monthlyAnalytics?.monthly_breakdown || []).map(month => (
              <div key={month.month} className="border rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-gray-900">{month.month_name}</h3>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(month.net_sales)}</p>
                    <p className="text-sm text-gray-500">{month.receipt_count} orders</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Total Sales</p>
                    <p className="font-semibold">{formatCurrency(month.total_sales)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Items Sold</p>
                    <p className="font-semibold">{month.total_quantity}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Discounts</p>
                    <p className="font-semibold text-red-600">{formatCurrency(month.total_discounts)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">Net Sales</p>
                    <p className="font-semibold text-green-600">{formatCurrency(month.net_sales)}</p>
                  </div>
                </div>
                {month.top_items.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">Top Items:</h4>
                    <div className="space-y-2">
                      {month.top_items.map((item, index) => (
                        <div key={item.listing_id} className="flex justify-between items-center text-sm">
                          <span className="flex-1">
                            {index + 1}. {item.title.substring(0, 50)}...
                          </span>
                          <span className="font-semibold text-green-600">{formatCurrency(item.net_amount)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsTab;
