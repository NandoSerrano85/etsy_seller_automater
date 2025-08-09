import { useCallback } from 'react';
import apiCache from '../utils/apiCache';
import { useAuth } from '../hooks/useAuth';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

export const useEnhancedApi = () => {
  const { userToken: userJwtToken } = useAuth(); // Get user JWT token for backend auth
  
  const makeRequest = useCallback(async (endpoint, options = {}) => {
    const {
      method = 'GET',
      headers = {},
      body = null,
      useCache = true,
      cacheTTL = null,
      requireAuth = false,
      params = {}
    } = options;

    const url = `${API_BASE_URL}${endpoint}`;
    
    // Check cache for GET requests
    if (method === 'GET' && useCache) {
      const cachedData = apiCache.get(endpoint, params);
      if (cachedData) {
        return cachedData;
      }
    }

    // Prepare headers
    const requestHeaders = {
      'Content-Type': 'application/json',
      ...headers
    };

    // Add authentication if required
    if (requireAuth) {
      if (userJwtToken) {
        requestHeaders.Authorization = `Bearer ${userJwtToken}`;
      } else {
        throw new Error('Authentication required but no valid user token available');
      }
    }

    // Prepare request options
    const requestOptions = {
      method,
      headers: requestHeaders
    };

    if (body) {
      if (body instanceof FormData) {
        // Remove Content-Type for FormData (browser sets it automatically)
        delete requestHeaders['Content-Type'];
        requestOptions.body = body;
      } else {
        requestOptions.body = JSON.stringify(body);
      }
    }

    try {
      const response = await fetch(url, requestOptions);
      
      // Handle authentication errors
      if (response.status === 401 && requireAuth) {
        throw new Error('Authentication failed. Please log in again.');
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Cache successful GET responses
      if (method === 'GET' && useCache) {
        apiCache.set(endpoint, params, data);
      }
      
      // Clear related cache for mutating operations
      if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        // Clear cache for related endpoints
        const endpointBase = endpoint.split('/')[1];
        apiCache.clearEndpoint(`/${endpointBase}/`);
      }

      return data;
    } catch (error) {
      console.error(`API request failed: ${method} ${endpoint}`, error);
      throw error;
    }
  }, [userJwtToken]);

  const get = useCallback(async (endpoint, options = {}) => {
    return makeRequest(endpoint, { ...options, method: 'GET' });
  }, [makeRequest]);

  const post = useCallback(async (endpoint, data, options = {}) => {
    return makeRequest(endpoint, { 
      ...options, 
      method: 'POST', 
      body: data,
      useCache: false 
    });
  }, [makeRequest]);

  const put = useCallback(async (endpoint, data, options = {}) => {
    return makeRequest(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: data,
      useCache: false 
    });
  }, [makeRequest]);

  const del = useCallback(async (endpoint, options = {}) => {
    return makeRequest(endpoint, { 
      ...options, 
      method: 'DELETE',
      useCache: false 
    });
  }, [makeRequest]);

  const postFormData = useCallback(async (endpoint, formData, options = {}) => {
    return makeRequest(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
      useCache: false
    });
  }, [makeRequest]);

  // Utility methods
  const clearCache = useCallback((endpointPattern = null) => {
    if (endpointPattern) {
      apiCache.clearEndpoint(endpointPattern);
    } else {
      apiCache.clear();
    }
  }, []);

  const getCacheStats = useCallback(() => {
    return apiCache.getStats();
  }, []);

  return {
    get,
    post,
    put,
    delete: del,
    postFormData,
    clearCache,
    getCacheStats
  };
};

export default useEnhancedApi;