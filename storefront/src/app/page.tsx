import { productsApi } from "@/lib/api";
import { ProductGrid } from "@/components/products/ProductGrid";
import { HeroSection } from "@/components/home/HeroSection";
import { ViewAllButton } from "@/components/home/ViewAllButton";
import { CategoriesSection } from "@/components/home/CategoriesSection";
import { BenefitsSection } from "@/components/home/BenefitsSection";

export default async function HomePage() {
  // Fetch featured products on the server
  const featuredProducts = await productsApi.getFeatured().catch(() => []);

  return (
    <div>
      {/* Hero Section */}
      <HeroSection />

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

          <ViewAllButton />
        </div>
      </section>

      {/* Categories */}
      <CategoriesSection />

      {/* Benefits */}
      <BenefitsSection />
    </div>
  );
}
