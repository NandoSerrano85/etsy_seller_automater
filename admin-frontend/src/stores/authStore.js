import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set, get) => ({
      // User Authentication State
      user: null,
      userToken: null,
      isUserAuthenticated: false,

      // Etsy Authentication State
      etsyTokens: {
        accessToken: null,
        refreshToken: null,
        expiresAt: null,
        tokenType: 'Bearer',
      },
      etsyUserInfo: null,
      etsyShopInfo: null,
      isEtsyConnected: false,

      // Loading States
      userLoading: false,
      etsyLoading: false,

      // Error States
      userError: null,
      etsyError: null,

      // User Authentication Actions
      setUserAuth: (user, token) =>
        set({
          user,
          userToken: token,
          isUserAuthenticated: true,
          userError: null,
        }),

      clearUserAuth: () =>
        set({
          user: null,
          userToken: null,
          isUserAuthenticated: false,
          userError: null,
        }),

      setUserLoading: loading => set({ userLoading: loading }),
      setUserError: error => set({ userError: error }),

      // Etsy Authentication Actions
      setEtsyTokens: tokenData => {
        console.log('🏪 setEtsyTokens called with:', tokenData);

        const tokens = {
          accessToken: tokenData.access_token || tokenData.accessToken,
          refreshToken: tokenData.refresh_token || tokenData.refreshToken,
          expiresAt: tokenData.expires_at || Date.now() + (tokenData.expires_in || 3600) * 1000,
          tokenType: tokenData.token_type || 'Bearer',
        };

        console.log('🔧 Processed tokens:', {
          hasAccessToken: !!tokens.accessToken,
          hasRefreshToken: !!tokens.refreshToken,
          expiresAt: new Date(tokens.expiresAt),
          accessTokenPreview: tokens.accessToken?.substring(0, 20) + '...',
        });

        set({
          etsyTokens: tokens,
          etsyError: null,
          // Set as connected if we have access token, even without backend verification
          isEtsyConnected: !!tokens.accessToken,
        });

        console.log('✅ Store updated, isEtsyConnected:', !!tokens.accessToken);
      },

      setEtsyConnection: (userInfo, shopInfo) =>
        set({
          etsyUserInfo: userInfo,
          etsyShopInfo: shopInfo,
          isEtsyConnected: true,
          etsyError: null,
        }),

      clearEtsyAuth: () =>
        set({
          etsyTokens: {
            accessToken: null,
            refreshToken: null,
            expiresAt: null,
            tokenType: 'Bearer',
          },
          etsyUserInfo: null,
          etsyShopInfo: null,
          isEtsyConnected: false,
          etsyError: null,
        }),

      setEtsyLoading: loading => set({ etsyLoading: loading }),
      setEtsyError: error => set({ etsyError: error }),

      // Helper Methods
      isEtsyTokenValid: () => {
        const { etsyTokens } = get();

        if (!etsyTokens.accessToken) {
          return false;
        }

        if (!etsyTokens.expiresAt) {
          return true; // No expiry, assume valid
        }

        // Check if token expires within next 5 minutes (buffer)
        const bufferTime = 5 * 60 * 1000;
        return Date.now() < etsyTokens.expiresAt - bufferTime;
      },

      getValidEtsyToken: async () => {
        const { etsyTokens, isEtsyTokenValid, refreshEtsyToken } = get();

        if (isEtsyTokenValid()) {
          return etsyTokens.accessToken;
        }

        // Token is expired - try to refresh it
        if (etsyTokens.refreshToken) {
          console.log('🔄 Etsy token expired, attempting refresh...');
          const refreshResult = await refreshEtsyToken();
          if (refreshResult.success) {
            return refreshResult.accessToken;
          }
        }

        // If refresh failed or no refresh token, clear auth
        console.log('❌ Unable to refresh Etsy token. Clearing tokens.');
        get().clearEtsyAuth();
        return null;
      },

      refreshEtsyToken: async () => {
        const { etsyTokens, setEtsyTokens, setEtsyError } = get();

        if (!etsyTokens.refreshToken) {
          return { success: false, error: 'No refresh token available' };
        }

        try {
          console.log('🔄 Attempting to refresh Etsy token...');

          // Call auth service to refresh token
          const authService = await import('../services/authService');
          const result = await authService.default.refreshEtsyToken(etsyTokens.refreshToken);

          if (result.success && result.access_token) {
            console.log('✅ Etsy token refreshed successfully');
            setEtsyTokens(result);
            return {
              success: true,
              accessToken: result.access_token,
            };
          } else {
            setEtsyError('Failed to refresh Etsy token');
            return { success: false, error: result.error || 'Refresh failed' };
          }
        } catch (error) {
          console.error('❌ Error refreshing Etsy token:', error);
          setEtsyError(error.message || 'Token refresh failed');
          return { success: false, error: error.message };
        }
      },

      // Debug method
      getDebugInfo: () => {
        const state = get();
        return {
          userAuth: {
            hasUser: !!state.user,
            hasToken: !!state.userToken,
            isAuthenticated: state.isUserAuthenticated,
            userEmail: state.user?.email || 'N/A',
          },
          etsyAuth: {
            hasAccessToken: !!state.etsyTokens.accessToken,
            hasRefreshToken: !!state.etsyTokens.refreshToken,
            isConnected: state.isEtsyConnected,
            tokenValid: state.isEtsyTokenValid(),
            expiresAt: state.etsyTokens.expiresAt ? new Date(state.etsyTokens.expiresAt) : null,
            accessTokenPreview: state.etsyTokens.accessToken
              ? state.etsyTokens.accessToken.substring(0, 20) + '...'
              : 'None',
            refreshTokenPreview: state.etsyTokens.refreshToken
              ? state.etsyTokens.refreshToken.substring(0, 20) + '...'
              : 'None',
            canRefresh: !!state.etsyTokens.refreshToken,
            hasUserInfo: !!state.etsyUserInfo,
            hasShopInfo: !!state.etsyShopInfo,
            loading: state.etsyLoading,
            error: state.etsyError,
          },
          timestamps: {
            currentTime: new Date().toISOString(),
            tokenExpiresIn: state.etsyTokens.expiresAt
              ? Math.max(0, Math.floor((state.etsyTokens.expiresAt - Date.now()) / 1000 / 60)) + ' minutes'
              : 'N/A',
          },
        };
      },
    }),
    {
      name: 'auth-store', // localStorage key
      partialize: state => ({
        // Only persist these fields
        user: state.user,
        userToken: state.userToken,
        isUserAuthenticated: state.isUserAuthenticated,
        etsyTokens: state.etsyTokens,
        etsyUserInfo: state.etsyUserInfo,
        etsyShopInfo: state.etsyShopInfo,
        isEtsyConnected: state.isEtsyConnected,
      }),
    }
  )
);

export default useAuthStore;
