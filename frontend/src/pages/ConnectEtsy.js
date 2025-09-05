import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

const ConnectEtsy = () => {
  const api = useApi();
  const [oauthData, setOauthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 w-full max-w-md text-center">
          <p className="text-sm sm:text-base">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 w-full max-w-md text-center">
          <p className="text-red-600 text-sm sm:text-base">{error}</p>
        </div>
      </div>
    );
  }

  const authUrl = oauthData
    ? `${oauthData.oauthConnectUrl || 'https://www.etsy.com/oauth/connect'}?response_type=${oauthData.responseType || 'code'}&redirect_uri=${oauthData.redirectUri}&scope=${oauthData.scopes || 'listings_w%20listings_r%20shops_r%20shops_w%20transactions_r'}&client_id=${oauthData.clientId}&state=${oauthData.state}&code_challenge=${oauthData.codeChallenge}&code_challenge_method=${oauthData.codeChallengeMethod || 'S256'}`
    : '#';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 px-4">
      <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 w-full max-w-md text-center">
        <h1 className="text-xl sm:text-2xl font-bold mb-4">Connect Your Etsy Store</h1>
        <p className="mb-6 text-gray-700 text-sm sm:text-base">
          To get started, connect your Etsy store to enable automated product management and order processing.
        </p>
        <a
          href={authUrl}
          className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-2 sm:py-3 px-4 sm:px-6 rounded-lg transition-colors text-sm sm:text-base"
        >
          Connect Etsy Store
        </a>
      </div>
    </div>
  );
};

export default ConnectEtsy;
