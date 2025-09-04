import useAuthStore from '../stores/authStore';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

class AuthService {
  
  // User Authentication Methods
  async loginUser(email, password) {
    const { setUserLoading, setUserError, setUserAuth } = useAuthStore.getState();
    
    try {
      setUserLoading(true);
      setUserError(null);
      
      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,
          password: password
        })
      });
      
      if (!response.ok) {
        throw new Error('Login failed');
      }
      
      const data = await response.json();
      
      // Check if the response includes user data (new format)
      if (data.user) {
        // New format includes user data in the auth response
        setUserAuth(data.user, data.access_token);
      } else {
        // Fallback: get user info from /users/me endpoint
        const userResponse = await fetch(`${API_BASE_URL}/users/me`, {
          headers: { 'Authorization': `Bearer ${data.access_token}` }
        });
        
        if (!userResponse.ok) {
          throw new Error('Failed to get user information');
        }
        
        const userData = await userResponse.json();
        setUserAuth(userData, data.access_token);
      }
      
      return { success: true };
    } catch (error) {
      setUserError(error.message);
      return { success: false, error: error.message };
    } finally {
      setUserLoading(false);
    }
  }
  
  async registerUser(email, password, shopName) {
    const { setUserLoading, setUserError } = useAuthStore.getState();
    
    try {
      setUserLoading(true);
      setUserError(null);
      
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          shop_name: shopName
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }
      
      const data = await response.json();
      
      // Check if the response includes user data (new format)
      if (data.user && data.access_token) {
        // New format includes user data in the registration response
        const { setUserAuth } = useAuthStore.getState();
        setUserAuth(data.user, data.access_token);
        return { success: true };
      } else {
        // Fallback: log them in to get user data
        return await this.loginUser(email, password);
      }
    } catch (error) {
      setUserError(error.message);
      return { success: false, error: error.message };
    } finally {
      setUserLoading(false);
    }
  }
  
  async refreshUserData() {
    const { userToken, setUserAuth, setUserError } = useAuthStore.getState();
    
    if (!userToken) {
      return { success: false, error: 'No token available' };
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh user data');
      }
      
      const userData = await response.json();
      setUserAuth(userData, userToken);
      
      return { success: true, user: userData };
    } catch (error) {
      setUserError(error.message);
      return { success: false, error: error.message };
    }
  }

  logoutUser() {
    const { clearUserAuth, clearEtsyAuth } = useAuthStore.getState();
    clearUserAuth();
    clearEtsyAuth(); // Also clear Etsy connection when user logs out
  }
  
  // Etsy Authentication Methods
  async checkEtsyConnection() {
    const { 
      userToken, 
      isUserAuthenticated, 
      setEtsyLoading, 
      setEtsyError, 
      setEtsyConnection, 
      clearEtsyAuth,
      isEtsyTokenValid,
      etsyTokens
    } = useAuthStore.getState();
    
    try {
      setEtsyLoading(true);
      setEtsyError(null);
      
      // Check if we have valid Etsy tokens first
      if (!etsyTokens.accessToken || !isEtsyTokenValid()) {
        clearEtsyAuth();
        return false;
      }
      
      // If user is not logged in to our app, we can't verify with backend
      // but we can still return true if we have valid Etsy tokens
      if (!isUserAuthenticated || !userToken) {
        console.log('User not authenticated to our app, but Etsy tokens exist');
        // Don't clear auth, just return false for backend verification
        return false;
      }
      
      // Verify connection with backend
      
      const response = await fetch(`${API_BASE_URL}/third-party/verify-connection`, {
        headers: { 'Authorization': `Bearer ${userToken}` }
      });
      
      if (!response.ok) {
        throw new Error('Connection verification failed');
      }
      
      const data = await response.json();
      
      if (data.connected) {
        setEtsyConnection(data.user_info, data.shop_info);
        return true;
      } else {
        clearEtsyAuth();
        return false;
      }
      
    } catch (error) {
      console.error('Etsy connection check failed:', error);
      setEtsyError(error.message);
      clearEtsyAuth();
      return false;
    } finally {
      setEtsyLoading(false);
    }
  }
  
  async handleEtsyOAuthCallback(code, state) {
    const { setEtsyLoading, setEtsyError, setEtsyTokens, etsyTokens } = useAuthStore.getState();
    
    // Add check for existing tokens to prevent duplicate processing
    if (etsyTokens.accessToken) {
        console.log('🔄 OAuth callback already processed, skipping...');
        return { success: true };
    }

    console.log('🚀 AuthService: Processing new OAuth callback with:', { 
        codePreview: code?.substring(0, 20) + '...', 
        state 
    });
    
    try {
        setEtsyLoading(true);
        setEtsyError(null);
        
        // Add user token to request if available
        const { userToken } = useAuthStore.getState();
        const headers = userToken ? { 'Authorization': `Bearer ${userToken}` } : {};
        
        const url = `${API_BASE_URL}/third-party/oauth-redirect?code=${code}`;
        console.log('📡 Making request to:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Response error:', errorText);
            throw new Error(`OAuth callback failed: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.access_token) {
            // Store tokens in sessionStorage to prevent loss on re-renders
            sessionStorage.setItem('etsy_oauth_completed', 'true');
            
            console.log('✅ Success! Setting Etsy tokens...');
            setEtsyTokens(data);
            
            // Only check connection status if user is logged in
            const { isUserAuthenticated } = useAuthStore.getState();
            if (isUserAuthenticated && etsyTokens) {
                await this.checkEtsyConnection();
            }
            
            return { success: true };
        } else {
            throw new Error(data.message || 'OAuth failed');
        }
        
    } catch (error) {
        console.error('💥 handleEtsyOAuthCallback error:', error);
        setEtsyError(error.message);
        return { success: false, error: error.message };
    } finally {
        setEtsyLoading(false);
    }
  }
  
  async refreshEtsyToken(refreshToken) {
    const { userToken } = useAuthStore.getState();
    
    try {
      console.log('🔄 AuthService: Refreshing Etsy token...');
      
      const headers = {
        'Content-Type': 'application/json',
        ...(userToken && { 'Authorization': `Bearer ${userToken}` })
      };
      
      const response = await fetch(`${API_BASE_URL}/third-party/refresh-token`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ refresh_token: refreshToken })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Token refresh failed:', errorText);
        throw new Error(`Token refresh failed: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.access_token) {
        console.log('✅ AuthService: Etsy token refreshed successfully');
        return {
          success: true,
          access_token: data.access_token,
          refresh_token: data.refresh_token || refreshToken, // Use new refresh token if provided
          expires_in: data.expires_in,
          expires_at: data.expires_at,
          token_type: data.token_type || 'Bearer'
        };
      } else {
        throw new Error(data.message || 'Token refresh failed');
      }
      
    } catch (error) {
      console.error('💥 AuthService: refreshEtsyToken error:', error);
      return { 
        success: false, 
        error: error.message || 'Token refresh failed' 
      };
    }
  }

  async disconnectEtsy() {
    const { userToken, setEtsyLoading, setEtsyError, clearEtsyAuth } = useAuthStore.getState();
    
    try {
      setEtsyLoading(true);
      setEtsyError(null);
      
      // Try to revoke on backend (optional)
      if (userToken) {
        try {
          await fetch(`${API_BASE_URL}/third-party/revoke-token`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${userToken}` }
          });
        } catch (error) {
          console.warn('Failed to revoke token on backend:', error);
        }
      }
      
      clearEtsyAuth();
      return { success: true };
      
    } catch (error) {
      setEtsyError(error.message);
      return { success: false, error: error.message };
    } finally {
      setEtsyLoading(false);
    }
  }
  
  // API Helper Methods
  async makeAuthenticatedRequest(endpoint, options = {}) {
    const { userToken, getValidEtsyToken } = useAuthStore.getState();
    
    if (!userToken) {
      throw new Error('User not authenticated');
    }
    
    // Check if this is an Etsy-related request that needs a token refresh
    const needsEtsyToken = endpoint.includes('access_token=') || endpoint.includes('/dashboard/') || endpoint.includes('/orders/');
    
    let finalEndpoint = endpoint;
    
    // If the request needs an Etsy token, ensure we have a valid one
    if (needsEtsyToken) {
      try {
        const validEtsyToken = await getValidEtsyToken();
        if (!validEtsyToken) {
          throw new Error('No valid Etsy access token available');
        }
        
        // Replace any existing access token in the endpoint with the current valid one
        if (endpoint.includes('access_token=')) {
          finalEndpoint = endpoint.replace(/access_token=[^&]*/, `access_token=${encodeURIComponent(validEtsyToken)}`);
        } else if (endpoint.includes('?')) {
          finalEndpoint = `${endpoint}&access_token=${encodeURIComponent(validEtsyToken)}`;
        } else {
          finalEndpoint = `${endpoint}?access_token=${encodeURIComponent(validEtsyToken)}`;
        }
      } catch (error) {
        console.error('❌ Failed to get valid Etsy token:', error);
        throw new Error('Etsy authentication required. Please reconnect your Etsy account.');
      }
    }
    
    const headers = {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    const response = await fetch(`${API_BASE_URL}${finalEndpoint}`, {
      ...options,
      headers
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Check if this is an Etsy token issue vs user token issue
        const errorText = await response.text();
        if (errorText.includes('etsy') || errorText.includes('Etsy') || needsEtsyToken) {
          // This is likely an Etsy token issue
          throw new Error('Etsy session expired. Please reconnect your Etsy account.');
        } else {
          // User session expired
          this.logoutUser();
          throw new Error('Session expired. Please log in again.');
        }
      }
      throw new Error(`Request failed: ${response.status}`);
    }
    
    return response.json();
  }
}

export default new AuthService();