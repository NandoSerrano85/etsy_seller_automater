import Link from "next/link";
import { productsApi } from "@/lib/api";
import { ProductGrid } from "@/components/products/ProductGrid";

export default async function HomePage() {
  // Fetch featured products on the server
  const featuredProducts = await productsApi.getFeatured().catch(() => []);

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white">
        <div className="container py-20">
          <div className="max-w-3xl">
            <h1 className="text-5xl font-bold mb-6">
              Premium Transfers for Your Crafting Needs
            </h1>
            <p className="text-xl mb-8 text-primary-100">
              Shop high-quality UVDTF, DTF, and sublimation transfers. Perfect
              for cups, tumblers, and more!
            </p>
            <div className="flex gap-4">
              <Link
                href="/products"
                className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Shop Now
              </Link>
              <Link
                href="/products?print_method=uvdtf"
                className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
              >
                Browse UVDTF
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Featured Products</h2>
            <p className="text-gray-600">
              Check out our best-selling transfers
            </p>
          </div>

          <ProductGrid products={featuredProducts} />

          <div className="text-center mt-12">
            <Link
              href="/products"
              className="inline-block bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
            >
              View All Products
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="bg-gray-50 py-16">
        <div className="container">
          <h2 className="text-3xl font-bold text-center mb-12">
            Shop by Category
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Link
              href="/products?print_method=uvdtf"
              className="group relative overflow-hidden rounded-lg bg-white shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="aspect-square bg-gradient-to-br from-blue-500 to-purple-600" />
              <div className="p-6">
                <h3 className="text-xl font-bold group-hover:text-primary-600 transition-colors">
                  UVDTF Transfers
                </h3>
                <p className="text-gray-600 mt-2">
                  High-quality UV DTF transfers for all surfaces
                </p>
              </div>
            </Link>

            <Link
              href="/products?print_method=dtf"
              className="group relative overflow-hidden rounded-lg bg-white shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="aspect-square bg-gradient-to-br from-pink-500 to-orange-500" />
              <div className="p-6">
                <h3 className="text-xl font-bold group-hover:text-primary-600 transition-colors">
                  DTF Transfers
                </h3>
                <p className="text-gray-600 mt-2">
                  Direct-to-film transfers for fabric and more
                </p>
              </div>
            </Link>

            <Link
              href="/products?print_method=sublimation"
              className="group relative overflow-hidden rounded-lg bg-white shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="aspect-square bg-gradient-to-br from-green-500 to-teal-500" />
              <div className="p-6">
                <h3 className="text-xl font-bold group-hover:text-primary-600 transition-colors">
                  Sublimation
                </h3>
                <p className="text-gray-600 mt-2">
                  Vibrant sublimation designs for your projects
                </p>
              </div>
            </Link>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h3 className="font-bold mb-2">Premium Quality</h3>
              <p className="text-gray-600 text-sm">
                High-quality materials and printing
              </p>
            </div>

            <div>
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="font-bold mb-2">Fast Shipping</h3>
              <p className="text-gray-600 text-sm">
                Quick processing and delivery
              </p>
            </div>

            <div>
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="font-bold mb-2">Easy to Apply</h3>
              <p className="text-gray-600 text-sm">
                Simple application instructions included
              </p>
            </div>

            <div>
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
                  />
                </svg>
              </div>
              <h3 className="font-bold mb-2">Satisfaction Guaranteed</h3>
              <p className="text-gray-600 text-sm">
                100% satisfaction or your money back
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
