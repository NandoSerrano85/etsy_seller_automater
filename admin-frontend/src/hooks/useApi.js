import { useAuth } from '../hooks/useAuth';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

// Debug: Log the API base URL to make sure it's correct
console.log('🔧 API_BASE_URL:', API_BASE_URL);

// Standalone API call function for use in AuthContext (no circular dependency)
export const apiCall = async (url, options = {}, token = null) => {
  // Construct the full URL using the API base URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  // Debug logging to see where requests are going
  console.log('🚀 API Request:', {
    url,
    method: options.method || 'GET',
    hasToken: !!token,
    fullUrl,
  });

  const headers = {
    ...options.headers,
  };

  // Only set Content-Type to application/json if not already set, and not for FormData or URLSearchParams
  if (!(options.body instanceof FormData) && !(options.body instanceof URLSearchParams) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(fullUrl, {
      ...options,
      headers,
      // Only add timeout if specifically requested (uploads should have no timeout)
      signal: options.signal || (options.timeout ? AbortSignal.timeout(options.timeout) : undefined),
    });

    console.log('📡 API Response:', {
      url,
      status: response.status,
      ok: response.ok,
    });
  } catch (networkError) {
    console.error('🌐 Network Error:', {
      url,
      fullUrl,
      error: networkError.message,
      type: networkError.name,
    });

    // Special handling for connection reset during uploads
    if (networkError.message.includes('ERR_CONNECTION_RESET') && options.method === 'POST') {
      console.warn('⚠️ Connection reset during POST - request may have succeeded on server');
    }

    throw networkError;
  }

  if (!response.ok) {
    // Get the response as text first to see if it's HTML
    const responseText = await response.text();
    console.error('❌ API Error:', {
      url,
      fullUrl,
      status: response.status,
      responseText: responseText.substring(0, 200) + '...', // First 200 chars
    });

    // Try to parse as JSON, fallback to text error
    try {
      const errorData = JSON.parse(responseText);
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    } catch (jsonError) {
      throw new Error(`HTTP ${response.status}: Received HTML instead of JSON`);
    }
  }

  // Also add error handling for the success case
  const responseText = await response.text();
  try {
    return JSON.parse(responseText);
  } catch (jsonError) {
    console.error('❌ JSON Parse Error:', {
      url,
      fullUrl,
      status: response.status,
      responseText: responseText.substring(0, 200) + '...',
      jsonError: jsonError.message,
    });
    throw new Error('Received HTML instead of JSON from API');
  }
};

export const useApi = () => {
  const { userToken, logout } = useAuth();

  const authenticatedApiCall = async (url, options = {}) => {
    try {
      return await apiCall(url, options, userToken);
    } catch (error) {
      // Check if it's a 401 Unauthorized error
      if (error.message.includes('HTTP 401') || error.message.includes('401')) {
        console.warn('🔒 Session expired - logging out user');
        // Trigger logout and redirect to login
        logout();
        window.location.href = '/login';
        throw new Error('Session expired. Please log in again.');
      }
      throw error;
    }
  };

  const get = url => authenticatedApiCall(url, { method: 'GET' });
  const post = (url, data) =>
    authenticatedApiCall(url, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  const postFormData = (url, formData, options = {}) => {
    // Remove timeout for uploads - let them run as long as needed
    const { timeout, ...restOptions } = options;
    return authenticatedApiCall(url, {
      method: 'POST',
      body: formData,
      // No timeout - uploads can take as long as needed
      ...restOptions,
    });
  };

  // Enhanced form data post with retry logic for connection reset errors
  const postFormDataWithRetry = async (url, formData, maxRetries = 2) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`🔄 Upload attempt ${attempt}/${maxRetries} for ${url}`);
        const result = await postFormData(url, formData);
        console.log(`✅ Upload successful on attempt ${attempt}`);
        return result;
      } catch (error) {
        console.log(`❌ Upload attempt ${attempt} failed:`, error.message);

        // Check if it's a retryable error (network issues, not timeouts since we removed them)
        const isRetryableError =
          error.message.includes('ERR_CONNECTION_RESET') ||
          error.message.includes('Failed to fetch') ||
          error.name === 'TypeError';

        // If it's the last attempt or not a retryable error, throw
        if (attempt === maxRetries || !isRetryableError) {
          throw error;
        }

        // Wait before retrying (exponential backoff)
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`⏳ Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  };
  const put = (url, data) =>
    authenticatedApiCall(url, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  const putFormData = (url, formData) =>
    authenticatedApiCall(url, {
      method: 'PUT',
      body: formData,
    });
  const del = url => authenticatedApiCall(url, { method: 'DELETE' });

  // Raw fetch for downloading files (returns response, not JSON)
  const fetchFile = async (url, options = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

    const headers = {
      ...options.headers,
    };

    if (userToken) {
      headers['Authorization'] = `Bearer ${userToken}`;
    }

    const response = await fetch(fullUrl, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      } else {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
      }
    }

    return response;
  };

  return {
    get,
    post,
    postFormData,
    postFormDataWithRetry,
    put,
    putFormData,
    delete: del,
    fetchFile,
    baseUrl: API_BASE_URL,
  };
};
