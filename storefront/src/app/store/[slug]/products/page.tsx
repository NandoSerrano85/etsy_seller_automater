"use client";

import { useEffect, useState } from "react";
import { useStore } from "@/contexts/StoreContext";
import { ProductGrid } from "@/components/products/ProductGrid";
import { StoreNotFound } from "@/components/StoreNotFound";
import { MaintenancePage } from "@/components/MaintenancePage";

interface Product {
  id: number;
  slug: string;
  name: string;
  description: string;
  base_price: string;
  images: Array<{ image_url: string; is_primary: boolean }>;
  is_active: boolean;
}

export default function StoreProductsPage({
  params,
}: {
  params: { slug: string };
}) {
  const { config, loading, error, storeSlug } = useStore();
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("newest");

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setProductsLoading(true);
        const API_URL =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";
        const response = await fetch(
          `${API_URL}/api/store/${params.slug}/products?page_size=100`,
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

    fetchProducts();
  }, [params.slug]);

  // Filter and sort products
  const filteredProducts = products
    .filter((product) =>
      product.name.toLowerCase().includes(searchQuery.toLowerCase()),
    )
    .sort((a, b) => {
      switch (sortBy) {
        case "price-asc":
          return parseFloat(a.base_price) - parseFloat(b.base_price);
        case "price-desc":
          return parseFloat(b.base_price) - parseFloat(a.base_price);
        case "name":
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error === "Store not found" || error === "Store is not published") {
    return <StoreNotFound />;
  }

  if (error === "Store is under maintenance") {
    return <MaintenancePage />;
  }

  return (
    <div className="py-8">
      <div className="container mx-auto px-4">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Products</h1>
          <p className="text-gray-600">
            Browse our collection of {products.length} products
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="newest">Newest</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="name">Name: A-Z</option>
          </select>
        </div>

        {/* Products Grid */}
        {productsLoading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <ProductGrid products={filteredProducts} storeSlug={params.slug} />
        )}
      </div>
    </div>
  );
}
