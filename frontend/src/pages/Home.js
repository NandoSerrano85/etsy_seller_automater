// eslint-disable-next-line no-unused-vars
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import MockupsGallery from '../components/MockupsGallery';
import DesignFilesGallery from '../components/DesignFilesGallery';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const Home = () => {
  const [oauthData, setOauthData] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [topSellers, setTopSellers] = useState([]);
  const [monthlyAnalytics, setMonthlyAnalytics] = useState(null);
  const [designs, setDesigns] = useState([]);
  const [localImages, setLocalImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [topSellersLimit, setTopSellersLimit] = useState(10);
  const [analyticsView, setAnalyticsView] = useState('yearly'); // 'yearly' or 'monthly'
  const [mockupImages, setMockupImages] = useState([]);
  const [designsTab, setDesignsTab] = useState('mockups');
  const [uploading, setUploading] = useState(false);
  const [orders, setOrders] = useState([]);
  const [ordersSummary, setOrdersSummary] = useState({
    totalOrders: 0,
    totalItems: 0
  });
  const [creatingPrintfile, setCreatingPrintfile] = useState(false);
  const [expandedOrders, setExpandedOrders] = useState([]);

  useEffect(() => {
    // Check for access token in localStorage
    const token = localStorage.getItem('etsy_access_token');
    if (token) {
      setAccessToken(token);
    }

    // Fetch OAuth data from the backend
    const fetchOAuthData = async () => {
      try {
        const response = await axios.get('/api/oauth-data');
        setOauthData(response.data);
      } catch (err) {
        setError('Failed to load OAuth configuration');
        console.error('Error fetching OAuth data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchOAuthData();
  }, []);

  const fetchTopSellers = useCallback(async () => {
    try {
      const response = await axios.get(`/api/top-sellers?access_token=${accessToken}&year=${currentYear}`);
      setTopSellers(response.data.top_sellers);
    } catch (err) {
      console.error('Error fetching top sellers:', err);
    }
  }, [accessToken, currentYear]);

  const fetchMonthlyAnalytics = useCallback(async () => {
    try {
      const response = await axios.get(`/api/monthly-analytics?access_token=${accessToken}&year=${currentYear}`);
      setMonthlyAnalytics(response.data);
    } catch (err) {
      console.error('Error fetching monthly analytics:', err);
    }
  }, [accessToken, currentYear]);

  const fetchDesigns = useCallback(async () => {
    try {
      const response = await axios.get(`/api/shop-listings?access_token=${accessToken}&limit=50`);
      setDesigns(response.data.designs);
    } catch (err) {
      console.error('Error fetching designs:', err);
    }
  }, [accessToken]);

  const fetchLocalImages = useCallback(async () => {
    try {
      const response = await axios.get('/api/local-images');
      console.log('Local images response:', response.data);
      setLocalImages(response.data.images || []);
    } catch (err) {
      console.error('Error fetching local images:', err);
      setLocalImages([]);
    }
  }, []);

  const fetchMockupImages = useCallback(async () => {
    try {
      const response = await axios.get('/api/mockup-images');
      console.log('Mockup images response:', response.data);
      setMockupImages(response.data.images || []);
    } catch (err) {
      console.error('Error fetching mockup images:', err);
      setMockupImages([]);
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    try {
      const response = await axios.get(`/api/orders?access_token=${accessToken}`);
      console.log('Orders response:', response.data);
      setOrders(response.data.orders || []);
      
      // Calculate summary
      const totalOrders = response.data.orders?.length || 0;
      const totalItems = response.data.orders?.reduce((sum, order) => 
        sum + (order.items?.reduce((itemSum, item) => itemSum + (item.quantity || 0), 0) || 0), 0
      ) || 0;
      
      setOrdersSummary({ totalOrders, totalItems });
    } catch (err) {
      console.error('Error fetching orders:', err);
      setOrders([]);
      setOrdersSummary({ totalOrders: 0, totalItems: 0 });
    }
  }, [accessToken]);

  const createPrintfile = async () => {
    setCreatingPrintfile(true);
    try {
      const response = await axios.get('/api/create-gang-sheets');
      alert('Printfile created successfully!');
    } catch (err) {
      console.error('Error creating printfile:', err);
      alert('Error creating printfile. Please try again.');
    }
    setCreatingPrintfile(false);
  };

  useEffect(() => {
    if (accessToken && activeTab === 'analytics') {
      fetchTopSellers();
      fetchMonthlyAnalytics();
    }
  }, [accessToken, activeTab, currentYear, fetchTopSellers, fetchMonthlyAnalytics]);

  useEffect(() => {
    if (accessToken && activeTab === 'designs') {
      fetchDesigns();
      fetchLocalImages();
      fetchMockupImages();
    }
  }, [accessToken, activeTab, fetchDesigns, fetchLocalImages, fetchMockupImages]);

  useEffect(() => {
    if (accessToken && activeTab === 'orders') {
      fetchOrders();
    }
  }, [accessToken, activeTab, fetchOrders]);

  const formatCurrency = (amount, divisor = 100) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount / divisor);
  };

  const openImageModal = (imageUrl) => {
    setSelectedImage(imageUrl);
  };

  const closeImageModal = () => {
    setSelectedImage(null);
  };

  // Prepare pie chart data
  const getPieChartData = () => {
    if (!topSellers || topSellers.length === 0) return null;
    
    const displayItems = topSellers.slice(0, topSellersLimit);
    const colors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
      '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
    ];
    
    return {
      labels: displayItems.map(item => item.title.substring(0, 30) + (item.title.length > 30 ? '...' : '')),
      datasets: [{
        data: displayItems.map(item => item.net_amount),
        backgroundColor: colors.slice(0, displayItems.length),
        borderColor: colors.slice(0, displayItems.length).map(color => color + '80'),
        borderWidth: 2,
      }]
    };
  };

  // Prepare monthly bar chart data
  const getMonthlyBarChartData = () => {
    if (!monthlyAnalytics) return null;
    
    const months = monthlyAnalytics.monthly_breakdown.map(month => month.month_name);
    const netSales = monthlyAnalytics.monthly_breakdown.map(month => month.net_sales);
    
    return {
      labels: months,
      datasets: [{
        label: 'Net Sales',
        data: netSales,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      }]
    };
  };

  const handleUploadClick = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.onchange = async (e) => {
      const files = Array.from(e.target.files);
      if (files.length === 0) return;
      
      // Log available file information
      console.log('Available file information:');
      files.forEach((file, index) => {
        console.log(`File ${index + 1}:`);
        console.log('  - name:', file.name);
        console.log('  - size:', file.size, 'bytes');
        console.log('  - type:', file.type);
        console.log('  - lastModified:', new Date(file.lastModified).toLocaleString());
        console.log('  - webkitRelativePath:', file.webkitRelativePath || 'N/A');
        console.log('  - Full path: NOT AVAILABLE (browser security restriction)');
      });
      
      setUploading(true);
      try {
        // Create FormData to send actual files
        const formData = new FormData();
        files.forEach((file, index) => {
          formData.append('files', file);
          // Note: We can only send the file object, not the full path
          console.log(`Sending file ${index + 1}: ${file.name}`);
        });
        
        const res = await fetch('/api/upload-mockup', {
          method: 'POST',
          body: formData, // Send FormData instead of JSON
        });
        
        if (res.ok) {
          const result = await res.json();
          alert(`Files uploaded successfully! ${result.result?.message || ''}`);
          
          // Refresh both local images and mockup images after upload
          await fetchLocalImages();
          await fetchMockupImages();
        } else {
          const errorData = await res.json();
          alert(`Upload failed: ${errorData.error || 'Unknown error'}`);
        }
      } catch (err) {
        console.error('Upload error:', err);
        alert('Error uploading files');
      }
      setUploading(false);
    };
    input.click();
  };

  // Toggle expand/collapse for an order
  const toggleOrderExpand = (orderId) => {
    setExpandedOrders((prev) =>
      prev.includes(orderId)
        ? prev.filter((id) => id !== orderId)
        : [...prev, orderId]
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col items-center justify-center text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
        <p className="text-lg">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 shadow-xl max-w-md w-full mx-4">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const authUrl = oauthData ? 
    `${oauthData.oauthConnectUrl || 'https://www.etsy.com/oauth/connect'}?response_type=${oauthData.responseType || 'code'}&redirect_uri=${oauthData.redirectUri}&scope=${oauthData.scopes || 'listings_w%20listings_r%20shops_r%20shops_w%20transactions_r'}&client_id=${oauthData.clientId}&state=${oauthData.state}&code_challenge=${oauthData.codeChallenge}&code_challenge_method=${oauthData.codeChallengeMethod || 'S256'}` : 
    '#';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
      {/* Hero Section */}
      <div className="bg-white/10 backdrop-blur-sm py-16 px-4 text-center text-white">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-shadow-lg">
            Etsy Seller Dashboard
          </h1>
          <p className="text-xl mb-8 opacity-90">
            Manage your shop, analyze sales, and create amazing designs
          </p>
          {!accessToken && (
            <div className="space-y-4">
              <a href={authUrl} className="btn-primary">
                Connect Your Etsy Shop
              </a>
              <div className="text-center">
                <button 
                  onClick={async () => {
                    try {
                      const response = await axios.get('/api/oauth-data-legacy');
                      const legacyAuthUrl = `${response.data.oauthConnectUrl}?response_type=${response.data.responseType}&redirect_uri=${response.data.redirectUri}&scope=${response.data.scopes}&client_id=${response.data.clientId}&state=${response.data.state}&code_challenge=${response.data.codeChallenge}&code_challenge_method=${response.data.codeChallengeMethod}`;
                      window.open(legacyAuthUrl, '_blank');
                    } catch (err) {
                      console.error('Error getting legacy OAuth data:', err);
                    }
                  }}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Test with Legacy Redirect URI
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center space-x-1">
            {['overview', 'analytics', 'designs', 'tools', 'orders'].map((tab) => (
              <button 
                key={tab}
                className={`tab-button capitalize ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-gray-50 min-h-screen py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-8">
              <div className="card p-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  Welcome to Your Dashboard
                </h2>
                <p className="text-lg text-gray-600 mb-8">
                  Get insights into your shop performance, manage your designs, and use powerful tools to grow your business.
                </p>
                
                {!accessToken ? (
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-lg">
                    <p className="text-blue-700 mb-4">Connect your Etsy shop to get started</p>
                    <a href={authUrl} className="btn-primary">
                      Connect Shop
                    </a>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                    <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-xl text-center">
                      <h3 className="text-lg font-semibold mb-2">Total Designs</h3>
                      <p className="text-3xl font-bold">{designs.length}</p>
                    </div>
                    <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-6 rounded-xl text-center">
                      <h3 className="text-lg font-semibold mb-2">Top Seller</h3>
                      <p className="text-lg font-medium">
                        {topSellers.length > 0 ? topSellers[0]?.title?.substring(0, 20) + '...' : 'N/A'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="space-y-8">
              {!accessToken ? (
                <div className="card p-8 text-center">
                  <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view analytics</p>
                  <a href={authUrl} className="btn-primary">Connect Shop</a>
                </div>
              ) : (
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
                      
                      {/* Big Total Display */}
                      <div className="text-center mb-8">
                        <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-8 rounded-xl inline-block">
                          <h3 className="text-2xl font-semibold mb-2">Total Net Sales</h3>
                          <p className="text-6xl font-bold">{formatCurrency(monthlyAnalytics.summary.net_sales)}</p>
                        </div>
                      </div>
                      
                      {/* Summary Stats */}
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
                    {/* Pie Chart */}
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
                                    font: {
                                      size: 12
                                    }
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

                    {/* Totals Card */}
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
                              legend: {
                                display: false
                              },
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
              )}
            </div>
          )}

          {/* Designs Tab */}
          {activeTab === 'designs' && (
            <div className="space-y-8">
              {!accessToken ? (
                <div className="card p-8 text-center">
                  <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view designs</p>
                  <a href={authUrl} className="btn-primary">Connect Shop</a>
                </div>
              ) : (
                <div>
                  <div className="flex justify-end mb-4">
                    <button
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        uploading 
                          ? 'bg-gray-400 text-white cursor-not-allowed' 
                          : 'bg-green-500 text-white hover:bg-green-600'
                      }`}
                      onClick={handleUploadClick}
                      disabled={uploading}
                    >
                      {uploading ? (
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Uploading...</span>
                        </div>
                      ) : (
                        'Upload Image'
                      )}
                    </button>
                  </div>
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Designs Gallery</h2>
                    <p className="text-gray-600">Your Etsy listings, local design files, and mockups</p>
                  </div>
                  {/* Sub-tabs for Mockups and Design Files */}
                  <div className="flex space-x-2 mb-6">
                    <button
                      className={`tab-button ${designsTab === 'mockups' ? 'active' : ''}`}
                      onClick={() => setDesignsTab('mockups')}
                    >
                      Mockups
                    </button>
                    <button
                      className={`tab-button ${designsTab === 'designFiles' ? 'active' : ''}`}
                      onClick={() => setDesignsTab('designFiles')}
                    >
                      Design Files
                    </button>
                  </div>
                  {/* Mockups Tab */}
                  {designsTab === 'mockups' && (
                    <MockupsGallery mockupImages={mockupImages} openImageModal={openImageModal} />
                  )}
                  {/* Design Files Tab */}
                  {designsTab === 'designFiles' && (
                    <DesignFilesGallery designFiles={localImages} openImageModal={openImageModal} />
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tools Tab */}
          {activeTab === 'tools' && (
            <div className="space-y-8">
              <h2 className="text-2xl font-bold text-gray-900">Tools</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="card p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">Mask Creator</h3>
                  <p className="text-gray-600 mb-4">
                    Create masks for mockup images by drawing polygons or rectangles. This tool helps you define areas where designs will be placed on mockup templates.
                  </p>
                  <Link to="/mask-creator" className="btn-primary">
                    Open Mask Creator
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Orders Tab */}
          {activeTab === 'orders' && (
            <div className="space-y-8">
              {!accessToken ? (
                <div className="card p-8 text-center">
                  <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view orders</p>
                  <a href={authUrl} className="btn-primary">Connect Shop</a>
                </div>
              ) : (
                <div className="space-y-8">
                  {/* Orders Summary Card */}
                  <div className="card p-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                      <div className="text-center">
                        <h3 className="text-2xl font-bold text-gray-900">{ordersSummary.totalOrders}</h3>
                        <p className="text-gray-600">Total Orders</p>
                      </div>
                      <div className="text-center">
                        <h3 className="text-2xl font-bold text-gray-900">{ordersSummary.totalItems}</h3>
                        <p className="text-gray-600">Total Items Sold</p>
                      </div>
                      <div className="text-center">
                        <button
                          onClick={createPrintfile}
                          disabled={creatingPrintfile}
                          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                            creatingPrintfile 
                              ? 'bg-gray-400 text-white cursor-not-allowed' 
                              : 'bg-blue-500 text-white hover:bg-blue-600'
                          }`}
                        >
                          {creatingPrintfile ? (
                            <div className="flex items-center justify-center space-x-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              <span>Creating...</span>
                            </div>
                          ) : (
                            'Create Printfile'
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Orders Table */}
                  <div className="card p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">Active Orders</h2>
                    <div className="overflow-x-auto rounded-lg shadow">
                      <table className="w-full bg-white">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-4 text-left font-semibold text-gray-700"></th>
                            <th className="px-6 py-4 text-left font-semibold text-gray-700">Order ID</th>
                            <th className="px-6 py-4 text-left font-semibold text-gray-700">Customer Name</th>
                            <th className="px-6 py-4 text-left font-semibold text-gray-700">Shipping Method</th>
                            <th className="px-6 py-4 text-left font-semibold text-gray-700">Shipping Cost</th>
                            <th className="px-6 py-4 text-left font-semibold text-gray-700">Order Date</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {orders.map((order) => (
                            <React.Fragment key={order.order_id}>
                              <tr className="hover:bg-gray-50">
                                <td className="px-2 py-4 text-center">
                                  <button
                                    onClick={() => toggleOrderExpand(order.order_id)}
                                    className="focus:outline-none"
                                    aria-label={expandedOrders.includes(order.order_id) ? 'Collapse' : 'Expand'}
                                  >
                                    {expandedOrders.includes(order.order_id) ? (
                                      <span>&#9660;</span> // Down chevron
                                    ) : (
                                      <span>&#9654;</span> // Right chevron
                                    )}
                                  </button>
                                </td>
                                <td className="px-6 py-4 font-medium text-gray-900">{order.order_id}</td>
                                <td className="px-6 py-4 text-gray-700">{order.customer_name || 'N/A'}</td>
                                <td className="px-6 py-4 text-gray-700">{order.shipping_method || 'N/A'}</td>
                                <td className="px-6 py-4 text-gray-700">{formatCurrency(order.shipping_cost || 0)}</td>
                                <td className="px-6 py-4 text-gray-700">{new Date(order.order_date * 1000).toLocaleDateString()}</td>
                              </tr>
                              {/* Transactions Dropdown */}
                              {expandedOrders.includes(order.order_id) && (
                                <tr>
                                  <td colSpan={6} className="bg-gray-50 px-6 py-4">
                                    <div className="overflow-x-auto">
                                      <table className="w-full">
                                        <thead>
                                          <tr>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700">Item Name</th>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700">Quantity</th>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700">Price</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {order.items.map((item, idx) => (
                                            <tr key={idx}>
                                              <td className="px-4 py-2 text-gray-700">{item.title || 'N/A'}</td>
                                              <td className="px-4 py-2 text-gray-700">{item.quantity || 0}</td>
                                              <td className="px-4 py-2 text-gray-700">{formatCurrency(item.price || 0)}</td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  </td>
                                </tr>
                              )}
                            </React.Fragment>
                          ))}
                        </tbody>
                      </table>
                      {orders.length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          No active orders found
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4"
          onClick={closeImageModal}
        >
          <div className="relative max-w-4xl max-h-full" onClick={(e) => e.stopPropagation()}>
            <button 
              className="absolute -top-12 right-0 text-white text-3xl hover:text-gray-300 transition-colors"
              onClick={closeImageModal}
            >
              ×
            </button>
            <img 
              src={selectedImage} 
              alt="Full size" 
              className="max-w-full max-h-full object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Home; 