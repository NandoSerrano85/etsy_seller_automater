import { useEffect } from 'react';
import useAuthStore from '../stores/authStore';
import authService from '../services/authService';

export const useAuth = () => {
  const {
    // User state
    user,
    userToken,
    isUserAuthenticated,
    userLoading,
    userError,

    // Etsy state
    etsyTokens,
    etsyUserInfo,
    etsyShopInfo,
    isEtsyConnected,
    etsyLoading,
    etsyError,

    // Helper methods
    isEtsyTokenValid,
    getValidEtsyToken,
    getDebugInfo,
  } = useAuthStore();

  // Auto-check Etsy connection when user logs in or tokens change
  useEffect(() => {
    if (isUserAuthenticated && userToken) {
      authService.checkEtsyConnection();
    }
  }, [isUserAuthenticated, userToken, etsyTokens.accessToken]);

  return {
    // User authentication
    user,
    userToken,
    isUserAuthenticated,
    userLoading,
    userError,
    login: authService.loginUser.bind(authService),
    register: authService.registerUser.bind(authService),
    logout: authService.logoutUser.bind(authService),
    refreshUserData: authService.refreshUserData.bind(authService),

    // Etsy authentication
    etsyUserInfo,
    etsyShopInfo,
    isEtsyConnected,
    etsyLoading,
    etsyError,
    isEtsyTokenValid: isEtsyTokenValid(),
    getValidEtsyToken,
    handleEtsyOAuth: authService.handleEtsyOAuthCallback.bind(authService),
    disconnectEtsy: authService.disconnectEtsy.bind(authService),
    checkEtsyConnection: authService.checkEtsyConnection.bind(authService),

    // API helpers
    makeAuthenticatedRequest: authService.makeAuthenticatedRequest.bind(authService),

    // Debug
    getDebugInfo,
  };
};

export default useAuth;
