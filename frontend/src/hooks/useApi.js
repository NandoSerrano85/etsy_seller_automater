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
  const { userToken } = useAuth();

  const authenticatedApiCall = async (url, options = {}) => {
    return apiCall(url, options, userToken);
  };

  const get = url => authenticatedApiCall(url, { method: 'GET' });
  const post = (url, data) =>
    authenticatedApiCall(url, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  const postFormData = (url, formData) =>
    authenticatedApiCall(url, {
      method: 'POST',
      body: formData,
    });
  const postFormDataWithRetry = async (url, formData, maxRetries = 3) => {
    let lastError;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await authenticatedApiCall(url, {
          method: 'POST',
          body: formData,
        });
      } catch (error) {
        lastError = error;
        if (attempt < maxRetries) {
          console.warn(`Attempt ${attempt} failed, retrying...`, error.message);
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
      }
    }
    throw lastError;
  };
  const put = (url, data) =>
    authenticatedApiCall(url, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  const del = url => authenticatedApiCall(url, { method: 'DELETE' });

  return {
    get,
    post,
    postFormData,
    postFormDataWithRetry,
    put,
    delete: del,
  };
};
