// eslint-disable-next-line no-unused-vars
import React, { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const OAuthRedirect = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const isProcessing = useRef(false);
  const hasSucceeded = useRef(false);

  useEffect(() => {
    const handleOAuthRedirect = async () => {
      // Prevent multiple simultaneous processing
      if (isProcessing.current) {
        console.log('OAuth redirect already processing, skipping...');
        return;
      }
      
      // Prevent processing if we've already succeeded
      if (hasSucceeded.current) {
        console.log('OAuth already succeeded, skipping...');
        return;
      }
      
      console.log('Starting OAuth redirect processing...');
      isProcessing.current = true;
      
      try {
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const accessToken = urlParams.get('access_token');
        const error = urlParams.get('error');

        console.log('URL parameters:', { code: !!code, state: !!state, accessToken: !!accessToken, error });

        // Check for OAuth error first
        if (error) {
          console.log('OAuth error detected:', error);
          setError(`OAuth error: ${error}`);
          setStatus('error');
          return;
        }

        // If we have an access token directly from backend redirect (legacy flow)
        if (accessToken) {
          console.log('Direct access token flow');
          localStorage.setItem('etsy_access_token', accessToken);
          hasSucceeded.current = true;
          setStatus('success');
          setSuccessMessage('Your Etsy shop has been connected successfully!');
          setTimeout(() => {
            navigate('/');
          }, 3000);
          return;
        }

        // If we have a code, exchange it for token via backend
        if (code) {
          console.log('Authorization code flow');
          try {
            // Call the backend oauth_redirect endpoint directly
            const response = await fetch(`/third-party/oauth-redirect-legacy?code=${code}`);
            console.log('Backend response status:', response.status);
            
            if (response.ok) {
              const data = await response.json();
              console.log('Backend response data:', { success: data.success, hasAccessToken: !!data.access_token });
              
              if (data.success) {
                // Store the access token in localStorage
                localStorage.setItem('etsy_access_token', data.access_token);
                
                console.log('Setting success status');
                hasSucceeded.current = true;
                setStatus('success');
                setSuccessMessage(data.message || 'Your Etsy shop has been connected successfully!');
                
                // Redirect to home page after showing success message
                setTimeout(() => {
                  navigate('/');
                }, 3000);
              } else {
                console.log('Backend returned success: false');
                setError(data.error || 'Authentication failed');
                setStatus('error');
              }
            } else {
              const errorData = await response.json();
              console.log('Backend error response:', errorData);
              setError(errorData.error || 'Failed to exchange code for token');
              setStatus('error');
            }
          } catch (err) {
            console.error('Error during OAuth callback:', err);
            setError('Network error during authentication');
            setStatus('error');
          }
        } else {
          console.log('No code or access token found');
          setError('No authorization code or access token received');
          setStatus('error');
        }
      } finally {
        isProcessing.current = false;
        console.log('OAuth redirect processing completed');
      }
    };

    handleOAuthRedirect();
  }, [location, navigate]);

  if (status === 'processing') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col items-center justify-center text-white px-4">
        <div className="animate-spin rounded-full h-10 w-10 sm:h-12 sm:w-12 border-b-2 border-white mb-4"></div>
        <h1 className="text-xl sm:text-2xl font-bold mb-2 text-center">Processing Authentication</h1>
        <p className="text-base sm:text-lg opacity-90 text-center">Please wait while we complete your login...</p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center px-4">
        <div className="bg-white rounded-xl p-6 sm:p-8 shadow-xl max-w-md w-full mx-4">
          <div className="text-center">
            <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded mb-6">
              <p className="text-red-700 font-medium text-sm sm:text-base">Authentication Failed</p>
              <p className="text-red-600 text-xs sm:text-sm mt-1">{error}</p>
            </div>
            <button 
              onClick={() => navigate('/')}
              className="btn-primary"
            >
              Return to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center px-4">
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-xl max-w-md w-full mx-4">
        <div className="text-center">
          <div className="bg-green-50 border-l-4 border-green-400 p-4 rounded mb-6">
            <div className="text-green-600 mb-2">
              <svg className="mx-auto h-8 w-8 sm:h-12 sm:w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-green-700 font-medium text-sm sm:text-base">Authentication Successful!</p>
            <p className="text-green-600 text-xs sm:text-sm mt-1">{successMessage}</p>
          </div>
          <p className="text-gray-600 mb-4 text-sm sm:text-base">Redirecting to dashboard in 3 seconds...</p>
          <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    </div>
  );
};

export default OAuthRedirect; 