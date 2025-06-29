import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './OAuthRedirect.css';

const OAuthRedirect = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (!code) {
      setError('No authorization code received from Etsy');
      setStatus('error');
      return;
    }

    const processOAuth = async () => {
      try {
        setStatus('processing');
        
        // Process OAuth redirect through backend
        const response = await axios.get(`/oauth/redirect?code=${code}`);
        
        if (response.status === 200) {
          setStatus('success');
          // Redirect to welcome page after a short delay
          setTimeout(() => {
            navigate('/welcome?access_token=' + response.data.access_token);
          }, 2000);
        } else {
          throw new Error('OAuth processing failed');
        }
      } catch (err) {
        console.error('OAuth redirect error:', err);
        setError('Failed to complete OAuth authentication');
        setStatus('error');
      }
    };

    processOAuth();
  }, [searchParams, navigate]);

  if (status === 'processing') {
    return (
      <div className="oauth-redirect-container">
        <div className="oauth-card">
          <div className="loading">
            <div className="spinner"></div>
          </div>
          <h2>Processing Authentication...</h2>
          <p>Please wait while we complete your Etsy authentication.</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="oauth-redirect-container">
        <div className="oauth-card">
          <div className="alert alert-error">
            <h2>Authentication Failed</h2>
            <p>{error}</p>
          </div>
          <div className="oauth-actions">
            <a href="/" className="btn btn-primary">
              Try Again
            </a>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="oauth-redirect-container">
        <div className="oauth-card">
          <div className="alert alert-success">
            <h2>Authentication Successful!</h2>
            <p>Redirecting you to the welcome page...</p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default OAuthRedirect; 