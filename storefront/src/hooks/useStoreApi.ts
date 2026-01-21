"use client";

import { useStore } from "@/contexts/StoreContext";
import type { Product, PaginatedResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";

/**
 * Hook that provides multi-tenant aware API functions
 * Uses path-based endpoints when in multi-tenant mode
 */
export function useStoreApi() {
  const { storeSlug, isMultiTenant, config } = useStore();

  /**
   * Get products for the current store
   */
  const getProducts = async (params?: {
    page?: number;
    page_size?: number;
    category?: string;
    search?: string;
    sort?: string;
    order?: string;
  }): Promise<PaginatedResponse<Product>> => {
    if (isMultiTenant && storeSlug) {
      // Multi-tenant mode: use path-based public API
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.set("page", params.page.toString());
      if (params?.page_size)
        queryParams.set("page_size", params.page_size.toString());
      if (params?.category) queryParams.set("category", params.category);
      if (params?.search) queryParams.set("search", params.search);
      if (params?.sort) queryParams.set("sort", params.sort);
      if (params?.order) queryParams.set("order", params.order);

      const response = await fetch(
        `${API_URL}/api/store/${storeSlug}/products?${queryParams.toString()}`,
      );

      if (!response.ok) {
        throw new Error("Failed to fetch products");
      }

      return response.json();
    } else {
      // Single-tenant mode: use existing API
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.set("page", params.page.toString());
      if (params?.page_size)
        queryParams.set("page_size", params.page_size.toString());
      if (params?.category) queryParams.set("category", params.category);
      if (params?.search) queryParams.set("search", params.search);

      const response = await fetch(
        `${API_URL}/api/storefront/products/?${queryParams.toString()}`,
      );

      if (!response.ok) {
        throw new Error("Failed to fetch products");
      }

      return response.json();
    }
  };

  /**
   * Get a single product by slug
   */
  const getProductBySlug = async (slug: string): Promise<Product> => {
    if (isMultiTenant && storeSlug) {
      const response = await fetch(
        `${API_URL}/api/store/${storeSlug}/products/${slug}`,
      );

      if (!response.ok) {
        throw new Error("Product not found");
      }

      return response.json();
    } else {
      const response = await fetch(
        `${API_URL}/api/storefront/products/${slug}`,
      );

      if (!response.ok) {
        throw new Error("Product not found");
      }

      return response.json();
    }
  };

  /**
   * Get featured products
   */
  const getFeaturedProducts = async (limit = 8): Promise<Product[]> => {
    if (isMultiTenant && storeSlug) {
      const response = await fetch(
        `${API_URL}/api/store/${storeSlug}/featured?limit=${limit}`,
      );

      if (!response.ok) {
        throw new Error("Failed to fetch featured products");
      }

      return response.json();
    } else {
      const response = await fetch(
        `${API_URL}/api/storefront/products/?page_size=${limit}&featured=true`,
      );

      if (!response.ok) {
        throw new Error("Failed to fetch featured products");
      }

      const data = await response.json();
      return data.items || [];
    }
  };

  /**
   * Get product categories
   */
  const getCategories = async (): Promise<
    { id: string; name: string; slug: string; product_count: number }[]
  > => {
    if (isMultiTenant && storeSlug) {
      const response = await fetch(
        `${API_URL}/api/store/${storeSlug}/categories`,
      );

      if (!response.ok) {
        throw new Error("Failed to fetch categories");
      }

      return response.json();
    } else {
      // Single-tenant mode doesn't have a categories endpoint
      // Return empty array or implement if needed
      return [];
    }
  };

  return {
    getProducts,
    getProductBySlug,
    getFeaturedProducts,
    getCategories,
    storeSlug,
    isMultiTenant,
    storeConfig: config,
  };
}
