import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import './Welcome.css';

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
      <div className="welcome-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="welcome-container">
        <div className="welcome-card">
          <div className="alert alert-error">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <h1>Welcome, {userData?.first_name || 'User'}!</h1>
        <p>Authentication was successful. Your Etsy shop is now connected!</p>
        
        {shopInfo && (
          <div className="shop-info">
            <h3>Shop Information</h3>
            <p><strong>Shop Name:</strong> {shopInfo.shop_name || 'Not available'}</p>
            {shopInfo.shop_url && (
              <p>
                <strong>Shop URL:</strong>{' '}
                <a href={shopInfo.shop_url} target="_blank" rel="noopener noreferrer">
                  {shopInfo.shop_url}
                </a>
              </p>
            )}
          </div>
        )}
        
        <div className="welcome-actions">
          <a href="/" className="btn btn-primary">
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
};

export default Welcome; 