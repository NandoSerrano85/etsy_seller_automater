import { useAuth } from '../contexts/AuthContext';

export const useApi = () => {
  const { token } = useAuth();

  const apiCall = async (url, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  };

  const get = (url) => apiCall(url, { method: 'GET' });
  const post = (url, data) => apiCall(url, { 
    method: 'POST', 
    body: JSON.stringify(data) 
  });
  const put = (url, data) => apiCall(url, { 
    method: 'PUT', 
    body: JSON.stringify(data) 
  });
  const del = (url) => apiCall(url, { method: 'DELETE' });

  return {
    get,
    post,
    put,
    delete: del,
  };
}; 