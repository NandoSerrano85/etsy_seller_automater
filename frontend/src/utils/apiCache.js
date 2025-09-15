/**
 * Simple API response cache for faster loading
 */

class APICache {
  constructor() {
    this.cache = new Map();
    this.timeouts = new Map();
  }

  // Get cached data
  get(key) {
    return this.cache.get(key);
  }

  // Set data with TTL (time to live)
  set(key, data, ttlSeconds = 60) {
    // Store data
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });

    // Clear any existing timeout
    if (this.timeouts.has(key)) {
      clearTimeout(this.timeouts.get(key));
    }

    // Set expiration timeout
    const timeout = setTimeout(() => {
      this.cache.delete(key);
      this.timeouts.delete(key);
    }, ttlSeconds * 1000);

    this.timeouts.set(key, timeout);
  }

  // Check if cached data is still valid
  isValid(key, maxAgeSeconds = 60) {
    const cached = this.cache.get(key);
    if (!cached) return false;

    const age = (Date.now() - cached.timestamp) / 1000;
    return age < maxAgeSeconds;
  }

  // Get data if valid, null if expired or missing
  getValid(key, maxAgeSeconds = 60) {
    if (this.isValid(key, maxAgeSeconds)) {
      return this.cache.get(key).data;
    }
    return null;
  }

  // Clear specific cache entry
  clear(key) {
    this.cache.delete(key);
    if (this.timeouts.has(key)) {
      clearTimeout(this.timeouts.get(key));
      this.timeouts.delete(key);
    }
  }

  // Clear all cache
  clearAll() {
    this.cache.clear();
    this.timeouts.forEach(timeout => clearTimeout(timeout));
    this.timeouts.clear();
  }
}

// Global cache instance
const apiCache = new APICache();

// Cache keys
export const CACHE_KEYS = {
  SHOPIFY_STORE: 'shopify_store',
  SHOPIFY_ANALYTICS: 'shopify_analytics',
  SHOPIFY_PRODUCTS: 'shopify_products',
  SHOPIFY_ORDERS: 'shopify_orders',
};

export default apiCache;
