"use client";

import Link from "next/link";
import { useBranding } from "@/contexts/BrandingContext";

export function HeroSection() {
  const { settings } = useBranding();

  return (
    <section
      className="text-white"
      style={{
        background: `linear-gradient(to right, ${settings.primary_color}, ${settings.secondary_color})`,
      }}
    >
      <div className="container py-20">
        <div className="max-w-3xl">
          <h1 className="text-5xl font-bold mb-6">
            Premium Transfers for Your Crafting Needs
          </h1>
          <p className="text-xl mb-8 opacity-90">
            Shop high-quality UVDTF, DTF, and sublimation transfers. Perfect for
            cups, tumblers, and more!
          </p>
          <div className="flex gap-4">
            <Link
              href="/products"
              className="bg-white px-8 py-3 rounded-lg font-semibold transition-colors"
              style={{ color: settings.primary_color }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "#f3f4f6";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "white";
              }}
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
  );
}
