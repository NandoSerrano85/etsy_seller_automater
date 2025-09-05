import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useApi } from '../../hooks/useApi';
import IntegrationCard from '../../components/IntegrationCard';

const IntegrationsTab = () => {
  const navigate = useNavigate();
  const {
    user,
    isEtsyConnected,
    etsyUserInfo,
    etsyShopInfo,
    etsyLoading,
    etsyError,
    checkEtsyConnection,
    disconnectEtsy,
  } = useAuth();

  const api = useApi();
  const [oauthData, setOauthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch OAuth configuration only when needed
  const fetchOAuthData = useCallback(async () => {
    if (oauthData) return;

    try {
      setLoading(true);
      const response = await api.get('/third-party/oauth-data');
      setOauthData(response);
    } catch (err) {
      setError('Failed to load OAuth configuration');
      console.error('Error fetching OAuth data:', err);
    } finally {
      setLoading(false);
    }
  }, [api, oauthData]);

  const handleEtsyConnect = async () => {
    await fetchOAuthData();

    if (!oauthData) {
      setError('OAuth configuration not loaded');
      return;
    }

    // Build and redirect to OAuth URL
    const authUrl =
      `${oauthData.oauthConnectUrl}?` +
      new URLSearchParams({
        response_type: oauthData.responseType,
        redirect_uri: oauthData.redirectUri,
        scope: oauthData.scopes,
        client_id: oauthData.clientId,
        state: oauthData.state,
        code_challenge: oauthData.codeChallenge,
        code_challenge_method: oauthData.codeChallengeMethod,
      });

    window.location.href = authUrl;
  };

  const handleEtsyDisconnect = async () => {
    if (window.confirm('Are you sure you want to disconnect your Etsy account?')) {
      const result = await disconnectEtsy();
      if (result.success) {
        setError(null);
      }
    }
  };

  // Available integrations configuration
  const integrations = [
    {
      name: 'Etsy',
      icon: 'E',
      description: 'Connect your Etsy shop to access sales analytics, order management, and automated features.',
      isConnected: isEtsyConnected,
      userInfo: etsyUserInfo,
      shopInfo: etsyShopInfo,
      isLoading: etsyLoading,
      onConnect: handleEtsyConnect,
      onDisconnect: handleEtsyDisconnect,
      features: [
        { icon: '📊', label: 'Sales Analytics' },
        { icon: '📦', label: 'Order Management' },
        { icon: '🎨', label: 'Design Automation' },
        { icon: '🔄', label: 'Auto-sync Data' },
      ],
    },
    // Add more integrations here as they become available
    {
      name: 'Shopify',
      icon: '🛍️',
      description: 'Coming soon - Connect your Shopify store for seamless integration.',
      isConnected: false,
      isComingSoon: true,
      features: [],
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-xl shadow-sm border border-sage-200 p-6">
        <h1 className="text-2xl font-bold text-sage-900 mb-2">Integrations</h1>
        <p className="text-sage-600">Connect your accounts to enable powerful automation features</p>
      </div>

      {/* Error Messages */}
      {(error || etsyError) && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-4">
          <p className="text-rose-700">{error || etsyError}</p>
        </div>
      )}

      {/* Integration Cards */}
      <div className="space-y-6">
        {integrations.map((integration, index) => (
          <IntegrationCard key={index} {...integration} />
        ))}
      </div>
    </div>
  );
};

export default IntegrationsTab;
