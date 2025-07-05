import React from 'react';
import { Pie, Bar } from 'react-chartjs-2';

const AnalyticsTab = ({
  accessToken,
  authUrl,
  currentYear,
  setCurrentYear,
  analyticsView,
  setAnalyticsView,
  topSellersLimit,
  setTopSellersLimit,
  topSellers,
  monthlyAnalytics,
  getPieChartData,
  getMonthlyBarChartData,
  formatCurrency
}) => {
  if (!accessToken) {
    return (
      <div className="card p-8 text-center">
        <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view analytics</p>
        <a href={authUrl} className="btn-primary">Connect Shop</a>
      </div>
    );
  }
  return (
    <div className="space-y-8">
      {/* Controls */}
      <div className="card p-6">
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <label htmlFor="year-select" className="font-semibold text-gray-700">Year:</label>
            <select 
              id="year-select"
              value={currentYear}
              onChange={(e) => setCurrentYear(parseInt(e.target.value))}
              className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="view-select" className="font-semibold text-gray-700">View:</label>
            <select 
              id="view-select"
              value={analyticsView}
              onChange={(e) => setAnalyticsView(e.target.value)}
              className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              <option value="yearly">Yearly Overview</option>
              <option value="monthly">Monthly Breakdown</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="limit-select" className="font-semibold text-gray-700">Show Top:</label>
            <select 
              id="limit-select"
              value={topSellersLimit}
              onChange={(e) => setTopSellersLimit(parseInt(e.target.value))}
              className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={topSellers.length}>All</option>
            </select>
          </div>
        </div>
      </div>
      {/* Yearly Summary */}
      {monthlyAnalytics && (
        <div className="card p-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
            {currentYear} Sales Summary
          </h2>
          <div className="text-center mb-8">
            <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-8 rounded-xl inline-block">
              <h3 className="text-2xl font-semibold mb-2">Total Net Sales</h3>
              <p className="text-6xl font-bold">{formatCurrency(monthlyAnalytics.summary.net_sales)}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-blue-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-blue-900 mb-2">Total Sales</h4>
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(monthlyAnalytics.summary.total_sales)}</p>
            </div>
            <div className="bg-red-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-red-900 mb-2">Total Discounts</h4>
              <p className="text-2xl font-bold text-red-600">{formatCurrency(monthlyAnalytics.summary.total_discounts)}</p>
            </div>
            <div className="bg-purple-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-purple-900 mb-2">Items Sold</h4>
              <p className="text-2xl font-bold text-purple-600">{monthlyAnalytics.summary.total_quantity}</p>
            </div>
            <div className="bg-orange-50 p-6 rounded-xl text-center">
              <h4 className="text-lg font-semibold text-orange-900 mb-2">Orders</h4>
              <p className="text-2xl font-bold text-orange-600">{monthlyAnalytics.summary.total_receipts}</p>
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
                data={getPieChartData()} 
                options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: { size: 12 }
                      }
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          const label = context.label || '';
                          const value = context.parsed;
                          const total = context.dataset.data.reduce((a, b) => a + b, 0);
                          const percentage = ((value / total) * 100).toFixed(1);
                          return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                        }
                      }
                    }
                  }
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
                {topSellers.slice(0, topSellersLimit).reduce((sum, item) => sum + item.quantity_sold, 0)}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-green-900 mb-1">Total Amount</h4>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(topSellers.slice(0, topSellersLimit).reduce((sum, item) => sum + item.total_amount, 0))}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-red-900 mb-1">Total Discounts</h4>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(topSellers.slice(0, topSellersLimit).reduce((sum, item) => sum + item.total_discounts, 0))}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg text-center">
              <h4 className="text-sm font-semibold text-purple-900 mb-1">Total Net</h4>
              <p className="text-2xl font-bold text-purple-600">
                {formatCurrency(topSellers.slice(0, topSellersLimit).reduce((sum, item) => sum + item.net_amount, 0))}
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
              data={getMonthlyBarChartData()} 
              options={{
                responsive: true,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        return `Net Sales: ${formatCurrency(context.parsed.y)}`;
                      }
                    }
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      callback: function(value) {
                        return formatCurrency(value);
                      }
                    }
                  }
                }
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
              {topSellers.slice(0, topSellersLimit).map((item, index) => (
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
            {monthlyAnalytics.monthly_breakdown.map((month) => (
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
                          <span className="flex-1">{index + 1}. {item.title.substring(0, 50)}...</span>
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