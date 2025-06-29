import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  const [oauthData, setOauthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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

  if (loading) {
    return (
      <div className="auth-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="alert alert-error">
            {error}
          </div>
        </div>
      </div>
    );
  }

  const authUrl = oauthData ? 
    `${oauthData.oauthConnectUrl || 'https://www.etsy.com/oauth/connect'}?response_type=${oauthData.responseType || 'code'}&redirect_uri=${oauthData.redirectUri}&scope=${oauthData.scopes || 'listings_w%20listings_r%20shops_r%20shops_w%20transactions_r'}&client_id=${oauthData.clientId}&state=${oauthData.state}&code_challenge=${oauthData.codeChallenge}&code_challenge_method=${oauthData.codeChallengeMethod || 'S256'}` : 
    '#';

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>Welcome to Our Etsy App</h1>
        <p>
          This application uses Etsy's OAuth 2.0 authentication to access your shop data. 
          Click the button below to start the authentication process and connect your Etsy shop.
        </p>
        
        <a href={authUrl} className="auth-button">
          Authenticate with Etsy
        </a>
        
        <div className="auth-footer">
          <p>
            If you have any questions, please refer to the{' '}
            <a 
              href="https://developer.etsy.com/documentation/essentials/authentication" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Etsy Authentication Essentials
            </a>{' '}
            page.
          </p>
        </div>
      </div>

      <div className="tools-section">
        <h2>Tools</h2>
        <div className="tools-grid">
          <div className="tool-card">
            <h3>Mask Creator</h3>
            <p>Create masks for mockup images by drawing polygons or rectangles. This tool helps you define areas where designs will be placed on mockup templates.</p>
            <Link to="/mask-creator" className="tool-button">
              Open Mask Creator
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home; 