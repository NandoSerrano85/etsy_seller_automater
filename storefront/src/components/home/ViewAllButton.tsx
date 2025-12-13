"use client";

import Link from "next/link";
import { useBranding } from "@/contexts/BrandingContext";

export function ViewAllButton() {
  const { settings } = useBranding();

  return (
    <div className="text-center mt-12">
      <Link
        href="/products"
        className="inline-block text-white px-8 py-3 rounded-lg font-semibold transition-colors"
        style={{ backgroundColor: settings.primary_color }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = settings.secondary_color;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = settings.primary_color;
        }}
      >
        View All Products
      </Link>
    </div>
  );
}
