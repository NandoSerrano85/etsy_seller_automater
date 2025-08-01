// eslint-disable-next-line no-unused-vars
import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import MockupsGallery from '../components/MockupsGallery';
import DesignFilesGallery from '../components/DesignFilesGallery';
import OverviewTab from './HomeTabs/OverviewTab';
import AnalyticsTab from './HomeTabs/AnalyticsTab';
import DesignsTab from './HomeTabs/DesignsTab';
import ToolsTab from './HomeTabs/ToolsTab';
import OrdersTab from './HomeTabs/OrdersTab';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const Home = () => {
  const { user, isAuthenticated } = useAuth();
  const api = useApi();
  const [searchParams] = useSearchParams();
  
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
  
  // Welcome state variables
  const [userData, setUserData] = useState(null);
  const [shopInfo, setShopInfo] = useState(null);
  const [showWelcome, setShowWelcome] = useState(false);

  useEffect(() => {
    // Check for access token in URL parameters (Welcome functionality)
    const urlAccessToken = searchParams.get('access_token');
    if (urlAccessToken) {
      setAccessToken(urlAccessToken);
      localStorage.setItem('etsy_access_token', urlAccessToken);
      
      // Fetch user data for welcome screen
      const fetchUserData = async () => {
        try {
          const response = await api.get(`/api/user-data?access_token=${urlAccessToken}`);
          setUserData(response.userData);
          setShopInfo(response.shopInfo);
          setShowWelcome(true);
        } catch (err) {
          console.error('Error fetching user data:', err);
          setError('Failed to fetch user data');
        }
      };
      
      fetchUserData();
    } else {
      // Check for Etsy access token in localStorage (for backward compatibility)
      const token = localStorage.getItem('etsy_access_token');
      if (token) {
        setAccessToken(token);
      }
    }

    // Fetch OAuth data from the backend
    const fetchOAuthData = async () => {
      try {
        const response = await api.get('/third-party/oauth-data');
        setOauthData(response);
      } catch (err) {
        setError('Failed to load OAuth configuration');
        console.error('Error fetching OAuth data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchOAuthData();
  }, [searchParams]);

  const fetchTopSellers = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      const response = await api.get(`/dashboard/top-sellers?access_token=${accessToken}&year=${currentYear}`);
      setTopSellers(response.top_sellers);
    } catch (err) {
      console.error('Error fetching top sellers:', err);
    }
  }, [accessToken, currentYear, api]);

  const fetchMonthlyAnalytics = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      const response = await api.get(`/dashboard/analytics?access_token=${accessToken}&year=${currentYear}`);
      setMonthlyAnalytics(response);
    } catch (err) {
      console.error('Error fetching monthly analytics:', err);
    }
  }, [accessToken, currentYear, api]);

  const fetchDesigns = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      const response = await api.get(`/dashboard/shop-listings?access_token=${accessToken}&limit=50`);
      setDesigns(response.designs);
    } catch (err) {
      console.error('Error fetching designs:', err);
    }
  }, [accessToken, api]);

  const fetchLocalImages = useCallback(async () => {
    console.log('DEBUG: fetchLocalImages called');
    try {
      const response = await api.get('/mockups');
      console.log('Local images response:', response);
      
      // Extract images from the new API structure
      const images = [];
      if (response.mockups) {
        response.mockups.forEach(mockup => {
          if (mockup.mockup_images) {
            mockup.mockup_images.forEach(image => {
              images.push({
                filename: image.filename,
                path: `/api/mockup-images/${image.id}`,
                full_path: image.file_path,
                template_name: mockup.product_template_id, // This is now a UUID
                template_title: 'Mockup Image'
              });
            });
          }
        });
      }
      
      console.log('Processed images:', images);
      setLocalImages(images);
    } catch (err) {
      console.error('Error fetching local images:', err);
      setLocalImages([]);
    }
  }, [api]);

  const fetchMockupImages = useCallback(async () => {
    console.log('DEBUG: fetchMockupImages called');
    try {
      const response = await api.get('/mockups');
      console.log('Mockup images response:', response);
      
      // Extract images from the new API structure
      const images = [];
      if (response.mockups) {
        response.mockups.forEach(mockup => {
          if (mockup.mockup_images) {
            mockup.mockup_images.forEach(image => {
              images.push({
                filename: image.filename,
                path: `/api/mockup-images/${image.id}`,
                full_path: image.file_path,
                template_name: mockup.product_template_id, // This is now a UUID
                template_title: 'Mockup Image'
              });
            });
          }
        });
      }
      
      console.log('Processed mockup images:', images);
      setMockupImages(images);
    } catch (err) {
      console.error('Error fetching mockup images:', err);
      setMockupImages([]);
    }
  }, [api]);

  const fetchOrders = useCallback(async () => {
    if (!accessToken) return;
    
    try {
      const response = await api.get(`/orders/?access_token=${accessToken}`);
      console.log('Orders response:', response);
      setOrders(response.orders || []);
      
      // Calculate summary
      const totalOrders = response.orders?.length || 0;
      const totalItems = response.orders?.reduce((sum, order) => 
        sum + (order.items?.reduce((itemSum, item) => itemSum + (item.quantity || 0), 0) || 0), 0
      ) || 0;
      
      setOrdersSummary({ totalOrders, totalItems });
    } catch (err) {
      console.error('Error fetching orders:', err);
      setOrders([]);
      setOrdersSummary({ totalOrders: 0, totalItems: 0 });
    }
  }, [accessToken, api]);

  const createPrintfile = async () => {
    setCreatingPrintfile(true);
    try {
      await api.get('/orders/create-print-files');
      alert('Printfile created successfully!');
    } catch (err) {
      console.error('Error creating printfile:', err);
      alert('Error creating printfile. Please try again.');
    }
    setCreatingPrintfile(false);
  };

  useEffect(() => {
    console.log('DEBUG: useEffect triggered', { accessToken: !!accessToken, activeTab, currentYear });
    if (accessToken && activeTab === 'analytics') {
      fetchTopSellers();
      fetchMonthlyAnalytics();
    }
    if (accessToken && activeTab === 'designs') {
      console.log('DEBUG: Fetching designs data');
      fetchDesigns();
      fetchLocalImages();
      fetchMockupImages();
    }
    if (accessToken && activeTab === 'orders') {
      fetchOrders();
    }
  }, [accessToken, activeTab, currentYear]);

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
        
        const result = await api.postFormData('/mockups/upload', formData);
        
        // Handle digital files response
        let successMessage = 'Files uploaded successfully!';
        if (result.result?.digital_message) {
          successMessage += `\n\n${result.result.digital_message}`;
        }
        if (result.result?.message) {
          successMessage += `\n${result.result.message}`;
        }
        
        alert(successMessage);
        
        // Refresh both local images and mockup images after upload
        await fetchLocalImages();
        await fetchMockupImages();
      } catch (err) {
        console.error('Upload error:', err);
        alert(`Upload failed: ${err.message || 'Unknown error'}`);
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

  // Render Welcome screen if access token is provided via URL
  if (showWelcome && userData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center py-4 sm:py-8 px-4">
        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-xl max-w-2xl w-full mx-4">
          <div className="text-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              Welcome, {userData?.first_name || 'User'}!
            </h1>
            <p className="text-base sm:text-lg text-gray-600 mb-6 sm:mb-8">
              Authentication was successful. Your Etsy shop is now connected!
            </p>
            
            {shopInfo && (
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 sm:p-6 rounded-lg mb-6 sm:mb-8 text-left">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Shop Information</h3>
                <div className="space-y-2 text-gray-700 text-sm sm:text-base">
                  <p><strong>Shop Name:</strong> {shopInfo.shop_name || 'Not available'}</p>
                  {shopInfo.shop_url && (
                    <p>
                      <strong>Shop URL:</strong>{' '}
                      <a 
                        href={shopInfo.shop_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline break-all"
                      >
                        {shopInfo.shop_url}
                      </a>
                    </p>
                  )}
                </div>
              </div>
            )}
            
            <div className="flex justify-center">
              <button 
                onClick={() => setShowWelcome(false)}
                className="btn-primary"
              >
                Continue to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
      {/* Hero Section */}
      <div className="bg-white/10 backdrop-blur-sm py-8 sm:py-16 px-4 text-center text-white">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 text-shadow-lg">
            Etsy Seller Dashboard
          </h1>
          <p className="text-base sm:text-lg md:text-xl mb-6 sm:mb-8 opacity-90 px-2">
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
                      const response = await api.get('/third-party/oauth-data');
                      const legacyAuthUrl = `${response.oauthConnectUrl}?response_type=${response.responseType}&redirect_uri=${response.redirectUri}&scope=${response.scopes}&client_id=${response.clientId}&state=${response.state}&code_challenge=${response.codeChallenge}&code_challenge_method=${response.codeChallengeMethod}`;
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
          <div className="flex sm:justify-start md:justify-center space-x-1 overflow-x-auto">
            {['overview', 'analytics', 'designs', 'tools', 'orders'].map((tab) => (
              <button 
                key={tab}
                className={`tab-button capitalize whitespace-nowrap text-sm sm:text-base ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-gray-50 min-h-screen py-4 sm:py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <OverviewTab
              user={user}
              accessToken={accessToken}
              designs={designs}
              topSellers={topSellers}
              oauthData={oauthData}
              authUrl={authUrl}
            />
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <AnalyticsTab
              accessToken={accessToken}
              authUrl={authUrl}
              currentYear={currentYear}
              setCurrentYear={setCurrentYear}
              analyticsView={analyticsView}
              setAnalyticsView={setAnalyticsView}
              topSellersLimit={topSellersLimit}
              setTopSellersLimit={setTopSellersLimit}
              topSellers={topSellers}
              monthlyAnalytics={monthlyAnalytics}
              getPieChartData={getPieChartData}
              getMonthlyBarChartData={getMonthlyBarChartData}
              formatCurrency={formatCurrency}
            />
          )}

          {/* Designs Tab */}
          {activeTab === 'designs' && (
            <DesignsTab
              accessToken={accessToken}
              authUrl={authUrl}
              uploading={uploading}
              handleUploadClick={handleUploadClick}
              designsTab={designsTab}
              setDesignsTab={setDesignsTab}
              mockupImages={mockupImages}
              localImages={localImages}
              openImageModal={openImageModal}
              onUploadComplete={() => {
                fetchLocalImages();
                fetchMockupImages();
              }}
            />
          )}

          {/* Tools Tab */}
          {activeTab === 'tools' && <ToolsTab />}

          {/* Orders Tab */}
          {activeTab === 'orders' && (
            <OrdersTab
              accessToken={accessToken}
              authUrl={authUrl}
              ordersSummary={ordersSummary}
              createPrintfile={createPrintfile}
              creatingPrintfile={creatingPrintfile}
              orders={orders}
              expandedOrders={expandedOrders}
              toggleOrderExpand={toggleOrderExpand}
              formatCurrency={formatCurrency}
            />
          )}
        </div>
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-2 sm:p-4"
          onClick={closeImageModal}
        >
          <div className="relative max-w-full max-h-full" onClick={(e) => e.stopPropagation()}>
            <button 
              className="absolute -top-8 sm:-top-12 right-0 text-white text-2xl sm:text-3xl hover:text-gray-300 transition-colors z-10"
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