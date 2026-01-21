"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { productsApi } from "@/lib/api";
import { Product } from "@/types";
import { ProductGrid } from "@/components/products/ProductGrid";
import { Filter, X } from "lucide-react";

function ProductsContent() {
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filter state
  const [filters, setFilters] = useState({
    print_method: searchParams.get("print_method") || "",
    category: searchParams.get("category") || "",
    search: searchParams.get("search") || "",
    sort: "newest",
  });

  useEffect(() => {
    fetchProducts();
  }, [filters, page]);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const response = await productsApi.getAll({
        page,
        page_size: 12,
        print_method: filters.print_method || undefined,
        category: filters.category || undefined,
        search: filters.search || undefined,
      });

      setProducts(response.items);
      setTotalPages(response.total_pages);
    } catch (error) {
      console.error("Failed to fetch products:", error);
      setProducts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (name: string, value: string) => {
    setFilters((prev) => ({ ...prev, [name]: value }));
    setPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({
      print_method: "",
      category: "",
      search: "",
      sort: "newest",
    });
    setPage(1);
  };

  const hasActiveFilters =
    filters.print_method || filters.category || filters.search;

  return (
    <div className="bg-white">
      <div className="container py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">All Products</h1>
            <p className="mt-2 text-gray-600">
              {isLoading ? "Loading..." : `${products.length} products`}
            </p>
          </div>

          {/* Mobile Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="md:hidden flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
        </div>

        <div className="lg:grid lg:grid-cols-4 lg:gap-8">
          {/* Filters Sidebar */}
          <aside
            className={`${
              showFilters ? "block" : "hidden"
            } md:block mb-8 lg:mb-0`}
          >
            <div className="bg-white border border-gray-200 rounded-lg p-6 sticky top-24">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Filters</h2>
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    Clear all
                  </button>
                )}
              </div>

              {/* Search */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search
                </label>
                <input
                  type="text"
                  placeholder="Search products..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange("search", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              {/* Print Method */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Print Method
                </h3>
                <div className="space-y-2">
                  {[
                    { value: "", label: "All Methods" },
                    { value: "uvdtf", label: "UVDTF" },
                    { value: "dtf", label: "DTF" },
                    { value: "sublimation", label: "Sublimation" },
                    { value: "vinyl", label: "Vinyl" },
                    { value: "digital", label: "Digital Download" },
                  ].map((option) => (
                    <label key={option.value} className="flex items-center">
                      <input
                        type="radio"
                        name="print_method"
                        value={option.value}
                        checked={filters.print_method === option.value}
                        onChange={(e) =>
                          handleFilterChange("print_method", e.target.value)
                        }
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {option.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Category */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Category
                </h3>
                <div className="space-y-2">
                  {[
                    { value: "", label: "All Categories" },
                    { value: "cup_wraps", label: "Cup Wraps" },
                    { value: "single_square", label: "Square Transfers" },
                    { value: "single_rectangle", label: "Rectangle Transfers" },
                    { value: "other", label: "Other" },
                  ].map((option) => (
                    <label key={option.value} className="flex items-center">
                      <input
                        type="radio"
                        name="category"
                        value={option.value}
                        checked={filters.category === option.value}
                        onChange={(e) =>
                          handleFilterChange("category", e.target.value)
                        }
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {option.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Sort */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sort by
                </label>
                <select
                  value={filters.sort}
                  onChange={(e) => handleFilterChange("sort", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="newest">Newest</option>
                  <option value="price_low">Price: Low to High</option>
                  <option value="price_high">Price: High to Low</option>
                  <option value="name">Name: A to Z</option>
                </select>
              </div>
            </div>
          </aside>

          {/* Products Grid */}
          <div className="lg:col-span-3">
            {/* Active Filters */}
            {hasActiveFilters && (
              <div className="mb-6 flex flex-wrap gap-2">
                {filters.print_method && (
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                    Print: {filters.print_method}
                    <button
                      onClick={() => handleFilterChange("print_method", "")}
                      className="hover:text-primary-900"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                {filters.category && (
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                    Category: {filters.category.replace("_", " ")}
                    <button
                      onClick={() => handleFilterChange("category", "")}
                      className="hover:text-primary-900"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                {filters.search && (
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                    Search: "{filters.search}"
                    <button
                      onClick={() => handleFilterChange("search", "")}
                      className="hover:text-primary-900"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Loading State */}
            {isLoading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <>
                {/* Products */}
                <ProductGrid products={products} />

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-12 flex justify-center">
                    <nav className="flex items-center gap-2">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>

                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                        (pageNum) => (
                          <button
                            key={pageNum}
                            onClick={() => setPage(pageNum)}
                            className={`px-4 py-2 border rounded-md ${
                              page === pageNum
                                ? "bg-primary-600 text-white border-primary-600"
                                : "border-gray-300 hover:bg-gray-50"
                            }`}
                          >
                            {pageNum}
                          </button>
                        ),
                      )}

                      <button
                        onClick={() =>
                          setPage((p) => Math.min(totalPages, p + 1))
                        }
                        disabled={page === totalPages}
                        className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="container py-8">Loading...</div>}>
      <ProductsContent />
    </Suspense>
  );
}
