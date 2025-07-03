import { useAuth } from '../contexts/AuthContext';

// Standalone API call function for use in AuthContext (no circular dependency)
export const apiCall = async (url, options = {}, token = null) => {
  // Debug logging to see where requests are going
  console.log('🚀 API Request:', {
    url,
    method: options.method || 'GET',
    hasToken: !!token,
    fullUrl: url.startsWith('http') ? url : `${window.location.origin}${url}`
  });

  const headers = {
    ...options.headers,
  };

  // Only set Content-Type for JSON requests, not for FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  console.log('📡 API Response:', {
    url,
    status: response.status,
    ok: response.ok
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('❌ API Error:', {
      url,
      status: response.status,
      error: errorData.detail || `HTTP error! status: ${response.status}`
    });
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const useApi = () => {
  const { token } = useAuth();

  const authenticatedApiCall = async (url, options = {}) => {
    return apiCall(url, options, token);
  };

  const get = (url) => authenticatedApiCall(url, { method: 'GET' });
  const post = (url, data) => authenticatedApiCall(url, { 
    method: 'POST', 
    body: JSON.stringify(data) 
  });
  const postFormData = (url, formData) => authenticatedApiCall(url, {
    method: 'POST',
    body: formData
  });
  const put = (url, data) => authenticatedApiCall(url, { 
    method: 'PUT', 
    body: JSON.stringify(data) 
  });
  const del = (url) => authenticatedApiCall(url, { method: 'DELETE' });

  return {
    get,
    post,
    postFormData,
    put,
    delete: del,
  };
}; 