// eslint-disable-next-line no-unused-vars
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const Welcome = () => {
  const [searchParams] = useSearchParams();
  const [userData, setUserData] = useState(null);
  const [shopInfo, setShopInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    
    if (!accessToken) {
      setError('No access token provided');
      setLoading(false);
      return;
    }

    const fetchUserData = async () => {
      try {
        // Fetch user data from the backend
        const response = await axios.get(`/api/user-data?access_token=${accessToken}`);
        setUserData(response.data.userData);
        setShopInfo(response.data.shopInfo);
      } catch (err) {
        setError('Failed to fetch user data');
        console.error('Error fetching user data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [searchParams]);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center py-8">
      <div className="bg-white rounded-xl p-8 shadow-xl max-w-2xl w-full mx-4">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome, {userData?.first_name || 'User'}!
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Authentication was successful. Your Etsy shop is now connected!
          </p>
          
          {shopInfo && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-lg mb-8 text-left">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Shop Information</h3>
              <div className="space-y-2 text-gray-700">
                <p><strong>Shop Name:</strong> {shopInfo.shop_name || 'Not available'}</p>
                {shopInfo.shop_url && (
                  <p>
                    <strong>Shop URL:</strong>{' '}
                    <a 
                      href={shopInfo.shop_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      {shopInfo.shop_url}
                    </a>
                  </p>
                )}
              </div>
            </div>
          )}
          
          <div className="flex justify-center">
            <a href="/" className="btn-primary">
              Back to Home
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome; 