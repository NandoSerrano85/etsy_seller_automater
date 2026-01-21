"use client";

import { useEffect, useState } from "react";
import { useStore } from "@/contexts/StoreContext";
import { ProductGrid } from "@/components/products/ProductGrid";
import { StoreHeroSection } from "@/components/home/StoreHeroSection";
import { StoreNotFound } from "@/components/StoreNotFound";
import { MaintenancePage } from "@/components/MaintenancePage";
import Link from "next/link";

interface Product {
  id: number;
  slug: string;
  name: string;
  description: string;
  base_price: string;
  images: Array<{ image_url: string; is_primary: boolean }>;
  is_active: boolean;
}

export default function StoreHomePage({
  params,
}: {
  params: { slug: string };
}) {
  const { config, loading, error, getStoreUrl } = useStore();
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      if (!config?.user_id) return;

      try {
        setProductsLoading(true);
        const API_URL =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";
        const response = await fetch(
          `${API_URL}/api/store/${params.slug}/products?page_size=8`,
        );

        if (response.ok) {
          const data = await response.json();
          setProducts(data.items || []);
        }
      } catch (err) {
        console.error("Error fetching products:", err);
      } finally {
        setProductsLoading(false);
      }
    };

    if (config) {
      fetchProducts();
    }
  }, [config, params.slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error === "Store not found") {
    return <StoreNotFound />;
  }

  if (error === "Store is under maintenance") {
    return <MaintenancePage />;
  }

  if (error === "Store is not published") {
    return <StoreNotFound />;
  }

  return (
    <div>
      {/* Hero Section */}
      <StoreHeroSection />

      {/* Featured Products */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Our Products</h2>
            <p className="text-gray-600">
              {config?.store_description || "Check out our latest products"}
            </p>
          </div>

          {productsLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : products.length > 0 ? (
            <>
              <ProductGrid products={products} storeSlug={params.slug} />
              <div className="text-center mt-8">
                <Link
                  href={getStoreUrl("/products")}
                  className="inline-flex items-center px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
                  style={{ backgroundColor: config?.primary_color }}
                >
                  View All Products
                  <svg
                    className="ml-2 w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </Link>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>No products available yet.</p>
            </div>
          )}
        </div>
      </section>

      {/* About Section */}
      {config?.store_description && (
        <section className="py-16 bg-gray-50">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-4">
              About {config.store_name}
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              {config.store_description}
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
