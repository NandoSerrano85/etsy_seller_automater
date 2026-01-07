import axios, { AxiosError } from "axios";
import type {
  Product,
  PaginatedResponse,
  Cart,
  CartItem,
  Customer,
  CustomerAddress,
  AuthResponse,
  Order,
  CheckoutInit,
  CheckoutResponse,
  PaymentIntentResponse,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add session ID for cart
    const sessionId = getSessionId();
    if (sessionId) {
      config.headers["X-Session-ID"] = sessionId;
    }
  }

  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      // Clear auth token on unauthorized
      localStorage.removeItem("auth_token");
      localStorage.removeItem("customer");
    }
    return Promise.reject(error);
  },
);

// Session management
function getSessionId(): string {
  if (typeof window === "undefined") {
    return "";
  }
  let sessionId = localStorage.getItem("session_id");
  if (!sessionId) {
    sessionId = `guest-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("session_id", sessionId);
  }
  return sessionId;
}

// Products API
export const productsApi = {
  getAll: async (params?: {
    page?: number;
    page_size?: number;
    print_method?: string;
    category?: string;
    search?: string;
  }): Promise<PaginatedResponse<Product>> => {
    const { data } = await api.get("/api/storefront/products/", { params });
    return data;
  },

  getBySlug: async (slug: string): Promise<Product> => {
    const { data } = await api.get(`/api/storefront/products/${slug}`);
    return data;
  },

  getById: async (id: string): Promise<Product> => {
    const { data } = await api.get(`/api/storefront/products/id/${id}`);
    return data;
  },

  getFeatured: async (): Promise<Product[]> => {
    const { data } = await api.get("/api/storefront/products", {
      params: { page_size: 8, featured: true },
    });
    return data.items || [];
  },

  getByPrintMethod: async (
    printMethod: string,
  ): Promise<PaginatedResponse<Product>> => {
    const { data } = await api.get(
      `/api/storefront/products/print-method/${printMethod}`,
    );
    return data;
  },

  getByCategory: async (
    category: string,
  ): Promise<PaginatedResponse<Product>> => {
    const { data } = await api.get(
      `/api/storefront/products/category/${category}`,
    );
    return data;
  },

  search: async (query: string): Promise<Product[]> => {
    const { data } = await api.get("/api/storefront/products/search", {
      params: { q: query },
    });
    return data;
  },
};

// Cart API
export const cartApi = {
  get: async (): Promise<Cart> => {
    const { data } = await api.get("/api/storefront/cart/");
    return data;
  },

  add: async (
    productId: string,
    quantity: number,
    variantId?: string,
  ): Promise<Cart> => {
    const { data } = await api.post("/api/storefront/cart/add", {
      product_id: productId,
      quantity,
      variant_id: variantId,
    });
    return data;
  },

  update: async (itemId: string, quantity: number): Promise<Cart> => {
    const { data } = await api.put(`/api/storefront/cart/update/${itemId}`, {
      quantity,
    });
    return data;
  },

  remove: async (itemId: string): Promise<void> => {
    await api.delete(`/api/storefront/cart/remove/${itemId}`);
  },

  clear: async (): Promise<void> => {
    await api.delete("/api/storefront/cart/clear");
  },
};

// Customer API
export const customerApi = {
  register: async (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone?: string;
  }): Promise<AuthResponse> => {
    const response = await api.post("/api/storefront/customers/register", data);
    return response.data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const { data } = await api.post("/api/storefront/customers/login", {
      username: email,
      password,
    });

    // Store auth token and customer data
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("customer", JSON.stringify(data.customer));

    return data;
  },

  logout: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("customer");
  },

  getProfile: async (): Promise<Customer> => {
    const { data } = await api.get("/api/storefront/customers/me");
    return data;
  },

  updateProfile: async (updates: Partial<Customer>): Promise<Customer> => {
    const { data } = await api.put("/api/storefront/customers/me", updates);
    return data;
  },

  changePassword: async (
    currentPassword: string,
    newPassword: string,
  ): Promise<void> => {
    await api.post("/api/storefront/customers/me/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  getAddresses: async (): Promise<CustomerAddress[]> => {
    const { data } = await api.get("/api/storefront/customers/me/addresses");
    return data;
  },

  addAddress: async (
    address: Omit<CustomerAddress, "id" | "customer_id">,
  ): Promise<CustomerAddress> => {
    const { data } = await api.post(
      "/api/storefront/customers/me/addresses",
      address,
    );
    return data;
  },

  updateAddress: async (
    id: string,
    address: Partial<CustomerAddress>,
  ): Promise<CustomerAddress> => {
    const { data } = await api.put(
      `/api/storefront/customers/me/addresses/${id}`,
      address,
    );
    return data;
  },

  deleteAddress: async (id: string): Promise<void> => {
    await api.delete(`/api/storefront/customers/me/addresses/${id}`);
  },

  getCurrentCustomer: (): Customer | null => {
    const customerStr = localStorage.getItem("customer");
    return customerStr ? JSON.parse(customerStr) : null;
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem("auth_token");
  },
};

// Orders API
export const ordersApi = {
  getAll: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<PaginatedResponse<Order>> => {
    const { data } = await api.get("/api/storefront/orders", { params });
    return data;
  },

  getById: async (id: string): Promise<Order> => {
    const { data } = await api.get(`/api/storefront/orders/${id}`);
    return data;
  },

  getByNumber: async (orderNumber: string): Promise<Order> => {
    const { data } = await api.get(
      `/api/storefront/orders/number/${orderNumber}`,
    );
    return data;
  },

  guestLookup: async (orderNumber: string, email: string): Promise<Order> => {
    const { data } = await api.get("/api/storefront/orders/guest/lookup", {
      params: { order_number: orderNumber, email },
    });
    return data;
  },

  downloadDigital: async (orderId: string, itemId: string): Promise<Blob> => {
    const { data } = await api.get(
      `/api/storefront/orders/${orderId}/items/${itemId}/download`,
      {
        responseType: "blob",
      },
    );
    return data;
  },
};

// Checkout API
export const checkoutApi = {
  getStripeConfig: async (): Promise<{ stripe_public_key: string }> => {
    const { data } = await api.get("/api/storefront/checkout/config");
    return data;
  },

  initialize: async (checkoutData: CheckoutInit): Promise<CheckoutResponse> => {
    const { data } = await api.post(
      "/api/storefront/checkout/init",
      checkoutData,
    );
    return data;
  },

  getShippingRates: async (shippingAddress: {
    first_name: string;
    last_name: string;
    address1: string;
    address2?: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
  }): Promise<
    {
      carrier: string;
      service: string;
      service_level: string;
      amount: number;
      currency: string;
      estimated_days: number | null;
      duration_terms: string;
      rate_id: string;
      is_fallback?: boolean;
    }[]
  > => {
    const { data } = await api.post("/api/storefront/checkout/shipping-rates", {
      shipping_address: shippingAddress,
    });
    return data;
  },

  createPaymentIntent: async (
    amount: number,
    currency = "usd",
  ): Promise<PaymentIntentResponse> => {
    const { data } = await api.post(
      "/api/storefront/checkout/create-payment-intent",
      {
        amount,
        currency,
      },
    );
    return data;
  },

  complete: async (params: {
    session_id: string;
    payment_intent_id: string;
    shipping_address: any;
    billing_address?: any;
    customer_note?: string;
    guest_email?: string;
  }): Promise<Order> => {
    const { data } = await api.post(
      "/api/storefront/checkout/complete",
      params,
    );
    return data;
  },
};

export default api;
