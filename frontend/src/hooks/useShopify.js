import { useState, useEffect, useCallback } from 'react';
import { useApi } from './useApi';
import { useNotifications } from '../components/NotificationSystem';

export const useShopify = () => {
  const api = useApi();
  const { addNotification } = useNotifications();

  const [store, setStore] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load store information
  const loadStore = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/store');
      setStore(response);
      setIsConnected(true);
    } catch (err) {
      if (err.message.includes('404')) {
        // No store connected
        setStore(null);
        setIsConnected(false);
      } else {
        setError(err.message);
        addNotification('Failed to load store information', 'error');
      }
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Connect to Shopify
  const connectStore = useCallback(
    async shopDomain => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.post('/api/shopify/connect', { shop_domain: shopDomain });

        // Redirect to Shopify OAuth
        if (response.authorization_url) {
          window.location.href = response.authorization_url;
        }
      } catch (err) {
        setError(err.message);
        addNotification(`Failed to connect store: ${err.message}`, 'error');
      } finally {
        setLoading(false);
      }
    },
    [api, addNotification]
  );

  // Disconnect store
  const disconnectStore = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      await api.delete('/api/shopify/disconnect');
      setStore(null);
      setIsConnected(false);
      addNotification('Store disconnected successfully', 'success');
    } catch (err) {
      setError(err.message);
      addNotification(`Failed to disconnect store: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Test connection
  const testConnection = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/test-connection');

      if (response.status === 'connected') {
        addNotification('Connection test successful', 'success');
        return true;
      } else {
        addNotification('Connection test failed - please reconnect your store', 'error');
        return false;
      }
    } catch (err) {
      setError(err.message);
      addNotification('Connection test failed', 'error');
      return false;
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Load store on hook initialization
  useEffect(() => {
    loadStore();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    store,
    isConnected,
    loading,
    error,
    loadStore,
    connectStore,
    disconnectStore,
    testConnection,
  };
};

export const useShopifyProducts = () => {
  const api = useApi();
  const { addNotification } = useNotifications();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load products
  const loadProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/products');
      setProducts(response.products || []);
    } catch (err) {
      setError(err.message);
      addNotification('Failed to load products', 'error');
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Create product
  const createProduct = useCallback(
    async productData => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.post('/api/shopify/products', productData);
        addNotification('Product created successfully', 'success');
        await loadProducts(); // Reload products
        return response;
      } catch (err) {
        setError(err.message);
        addNotification(`Failed to create product: ${err.message}`, 'error');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [api, addNotification, loadProducts]
  );

  // Update product
  const updateProduct = useCallback(
    async (productId, productData) => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.put(`/api/shopify/products/${productId}`, productData);
        addNotification('Product updated successfully', 'success');
        await loadProducts(); // Reload products
        return response;
      } catch (err) {
        setError(err.message);
        addNotification(`Failed to update product: ${err.message}`, 'error');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [api, addNotification, loadProducts]
  );

  // Delete product
  const deleteProduct = useCallback(
    async productId => {
      try {
        setLoading(true);
        setError(null);
        await api.delete(`/api/shopify/products/${productId}`);
        addNotification('Product deleted successfully', 'success');
        await loadProducts(); // Reload products
      } catch (err) {
        setError(err.message);
        addNotification(`Failed to delete product: ${err.message}`, 'error');
      } finally {
        setLoading(false);
      }
    },
    [api, addNotification, loadProducts]
  );

  // Load products on hook initialization (only run once)
  useEffect(() => {
    loadProducts();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    products,
    loading,
    error,
    loadProducts,
    createProduct,
    updateProduct,
    deleteProduct,
  };
};

export const useShopifyOrders = () => {
  const api = useApi();
  const { addNotification } = useNotifications();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load orders
  const loadOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/orders');
      setOrders(response.orders || []);
    } catch (err) {
      setError(err.message);
      addNotification('Failed to load orders', 'error');
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Load orders on hook initialization (only run once)
  useEffect(() => {
    loadOrders();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    orders,
    loading,
    error,
    loadOrders,
  };
};

export const useShopifyAnalytics = () => {
  const api = useApi();
  const { addNotification } = useNotifications();

  const [analytics, setAnalytics] = useState(null);
  const [orderStats, setOrderStats] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load analytics summary
  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/analytics/summary');
      setAnalytics(response);
    } catch (err) {
      setError(err.message);
      addNotification('Failed to load analytics', 'error');
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Load order stats
  const loadOrderStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/orders/stats');
      setOrderStats(response);
    } catch (err) {
      setError(err.message);
      addNotification('Failed to load order stats', 'error');
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Load top products
  const loadTopProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/shopify/orders/top-products');
      setTopProducts(response.products || []);
    } catch (err) {
      setError(err.message);
      addNotification('Failed to load top products', 'error');
    } finally {
      setLoading(false);
    }
  }, [api, addNotification]);

  // Load all analytics data
  const loadAllAnalytics = useCallback(async () => {
    await Promise.all([loadAnalytics(), loadOrderStats(), loadTopProducts()]);
  }, [loadAnalytics, loadOrderStats, loadTopProducts]);

  return {
    analytics,
    orderStats,
    topProducts,
    loading,
    error,
    loadAnalytics,
    loadOrderStats,
    loadTopProducts,
    loadAllAnalytics,
  };
};
