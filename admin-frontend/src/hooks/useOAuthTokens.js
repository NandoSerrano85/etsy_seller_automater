import { useState, useEffect, useCallback } from 'react';
import { useApi } from './useApi';
import { useNotifications } from '../components/NotificationSystem';

/**
 * Hook for managing OAuth tokens across all platforms
 * Provides automatic token refresh and status monitoring
 */
export const useOAuthTokens = () => {
  const api = useApi();
  const { addNotification } = useNotifications();

  const [tokens, setTokens] = useState({});
  const [loading, setLoading] = useState(false);
  const [serviceStatus, setServiceStatus] = useState(null);

  /**
   * Load all OAuth token information for the current user
   */
  const loadTokens = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.get('/api/oauth/tokens');

      if (data.success) {
        setTokens(data.tokens || {});
      }
    } catch (error) {
      console.error('Error loading OAuth tokens:', error);
      // Don't show error notification for token loading failures
    } finally {
      setLoading(false);
    }
  }, [api]);

  /**
   * Load token information for a specific platform
   */
  const loadPlatformToken = useCallback(
    async platform => {
      try {
        const data = await api.get(`/api/oauth/tokens/${platform.toLowerCase()}`);

        if (data.success && data.token) {
          setTokens(prev => ({
            ...prev,
            [platform.toUpperCase()]: data.token,
          }));
          return data.token;
        }
      } catch (error) {
        console.error(`Error loading ${platform} token:`, error);
        return null;
      }
    },
    [api]
  );

  /**
   * Manually refresh token for a specific platform
   */
  const refreshPlatformToken = useCallback(
    async platform => {
      try {
        const data = await api.post(`/api/oauth/tokens/${platform.toLowerCase()}/refresh`);

        if (data.success) {
          addNotification(`${platform} token refreshed successfully`, 'success');
          // Reload tokens to get updated info
          await loadTokens();
          return true;
        }
        return false;
      } catch (error) {
        console.error(`Error refreshing ${platform} token:`, error);
        addNotification(`Failed to refresh ${platform} token`, 'error');
        return false;
      }
    },
    [api, addNotification, loadTokens]
  );

  /**
   * Refresh all OAuth tokens for the current user
   */
  const refreshAllTokens = useCallback(async () => {
    try {
      const data = await api.post('/api/oauth/service/refresh-all');

      if (data.success) {
        addNotification(data.message || 'Tokens refreshed successfully', 'success');
        // Reload tokens to get updated info
        await loadTokens();
        return data.results;
      }
      return null;
    } catch (error) {
      console.error('Error refreshing all tokens:', error);
      addNotification('Failed to refresh tokens', 'error');
      return null;
    }
  }, [api, addNotification, loadTokens]);

  /**
   * Get the OAuth refresh service status
   */
  const loadServiceStatus = useCallback(async () => {
    try {
      const data = await api.get('/api/oauth/service/status');

      if (data.success) {
        setServiceStatus(data.service);
        return data.service;
      }
    } catch (error) {
      console.error('Error loading service status:', error);
      return null;
    }
  }, [api]);

  /**
   * Check if a platform token is expired
   */
  const isTokenExpired = useCallback(
    platform => {
      const token = tokens[platform.toUpperCase()];
      return token ? token.is_expired : false;
    },
    [tokens]
  );

  /**
   * Check if a platform token needs refresh
   */
  const needsRefresh = useCallback(
    platform => {
      const token = tokens[platform.toUpperCase()];
      return token ? token.needs_refresh : false;
    },
    [tokens]
  );

  /**
   * Get time until token expiry
   */
  const getTimeUntilExpiry = useCallback(
    platform => {
      const token = tokens[platform.toUpperCase()];
      return token ? token.time_until_expiry : null;
    },
    [tokens]
  );

  /**
   * Get token expiration date
   */
  const getExpiresAt = useCallback(
    platform => {
      const token = tokens[platform.toUpperCase()];
      return token ? token.expires_at : null;
    },
    [tokens]
  );

  /**
   * Check if user has an active token for a platform
   */
  const hasToken = useCallback(
    platform => {
      return !!tokens[platform.toUpperCase()];
    },
    [tokens]
  );

  /**
   * Get all platforms with active tokens
   */
  const getActivePlatforms = useCallback(() => {
    return Object.keys(tokens);
  }, [tokens]);

  // Auto-load tokens on mount
  useEffect(() => {
    loadTokens();
  }, [loadTokens]);

  return {
    // State
    tokens,
    loading,
    serviceStatus,

    // Actions
    loadTokens,
    loadPlatformToken,
    refreshPlatformToken,
    refreshAllTokens,
    loadServiceStatus,

    // Helpers
    isTokenExpired,
    needsRefresh,
    getTimeUntilExpiry,
    getExpiresAt,
    hasToken,
    getActivePlatforms,
  };
};

export default useOAuthTokens;
