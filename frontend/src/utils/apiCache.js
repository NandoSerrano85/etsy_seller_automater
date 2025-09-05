class ApiCache {
  constructor() {
    this.cache = new Map();
    this.timestamps = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes default

    // Configure different TTL for different endpoints
    this.endpointTTLs = {
      '/third-party/oauth-data': 30 * 60 * 1000, // 30 minutes - rarely changes
      '/settings/product-template': 10 * 60 * 1000, // 10 minutes
      '/settings/canvas-config': 10 * 60 * 1000, // 10 minutes
      '/settings/size-config': 10 * 60 * 1000, // 10 minutes
      '/mockups/': 2 * 60 * 1000, // 2 minutes - changes more frequently
      '/designs/': 2 * 60 * 1000, // 2 minutes
      '/orders/': 1 * 60 * 1000, // 1 minute - most dynamic
      '/dashboard/': 2 * 60 * 1000, // 2 minutes
    };
  }

  // Generate cache key from URL and params
  generateKey(url, params = {}) {
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((acc, key) => {
        acc[key] = params[key];
        return acc;
      }, {});

    return `${url}?${JSON.stringify(sortedParams)}`;
  }

  // Get TTL for specific endpoint
  getTTL(endpoint) {
    // Find matching endpoint pattern
    for (const [pattern, ttl] of Object.entries(this.endpointTTLs)) {
      if (endpoint.includes(pattern)) {
        return ttl;
      }
    }
    return this.defaultTTL;
  }

  // Check if cached data is still valid
  isValid(key) {
    if (!this.cache.has(key) || !this.timestamps.has(key)) {
      return false;
    }

    const timestamp = this.timestamps.get(key);
    const ttl = this.getTTL(key);

    return Date.now() - timestamp < ttl;
  }

  // Get cached data if valid
  get(url, params = {}) {
    const key = this.generateKey(url, params);

    if (this.isValid(key)) {
      console.log(`Cache hit for ${url}`);
      return this.cache.get(key);
    }

    // Clean up expired entry
    this.delete(key);
    return null;
  }

  // Set cached data
  set(url, params = {}, data) {
    const key = this.generateKey(url, params);

    this.cache.set(key, data);
    this.timestamps.set(key, Date.now());

    console.log(`Cached data for ${url}`);

    // Cleanup old entries periodically
    if (this.cache.size > 100) {
      this.cleanup();
    }
  }

  // Delete specific cache entry
  delete(key) {
    this.cache.delete(key);
    this.timestamps.delete(key);
  }

  // Clear all cache for a specific endpoint pattern
  clearEndpoint(endpointPattern) {
    const keysToDelete = [];

    for (const key of this.cache.keys()) {
      if (key.includes(endpointPattern)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => {
      this.delete(key);
    });

    console.log(`Cleared cache for ${endpointPattern}`);
  }

  // Clear all cache
  clear() {
    this.cache.clear();
    this.timestamps.clear();
    console.log('Cleared all cache');
  }

  // Clean up expired entries
  cleanup() {
    const now = Date.now();
    const keysToDelete = [];

    for (const [key, timestamp] of this.timestamps.entries()) {
      const ttl = this.getTTL(key);
      if (now - timestamp > ttl) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => {
      this.delete(key);
    });

    if (keysToDelete.length > 0) {
      console.log(`Cleaned up ${keysToDelete.length} expired cache entries`);
    }
  }

  // Get cache statistics
  getStats() {
    return {
      size: this.cache.size,
      entries: Array.from(this.cache.keys()),
    };
  }
}

// Create singleton instance
const apiCache = new ApiCache();

// Clean up expired entries every 5 minutes
setInterval(
  () => {
    apiCache.cleanup();
  },
  5 * 60 * 1000
);

export default apiCache;
