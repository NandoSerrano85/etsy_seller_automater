import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
// import useAuthStore from '../stores/authStore';

const OAuthRedirect = () => {
  const navigate = useNavigate();
  const processed = useRef(false);
  // const { isEtsyConnected } = useAuthStore();

  useEffect(() => {
    const processOAuth = async () => {
      // Check if we've already processed this OAuth callback
      if (processed.current || sessionStorage.getItem('etsy_oauth_completed')) {
        return;
      }

      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');

      if (code) {
        processed.current = true;
        const result = await authService.handleEtsyOAuthCallback(code, state);

        if (result.success) {
          // Clear the completion flag when navigating away
          sessionStorage.removeItem('etsy_oauth_completed');

          navigate('/?tab=overview');
        } else {
          navigate('/connect-etsy?error=oauth_failed');
        }
      } else {
        navigate('/connect-etsy?error=no_code');
      }
    };

    processOAuth();
  }, [navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4 text-gray-600">Connecting to Etsy...</p>
      </div>
    </div>
  );
};

export default OAuthRedirect;
