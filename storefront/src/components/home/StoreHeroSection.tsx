"use client";

import { useStore } from "@/contexts/StoreContext";
import Link from "next/link";

export function StoreHeroSection() {
  const { config, getStoreUrl } = useStore();

  if (!config) return null;

  return (
    <section
      className="relative py-20 md:py-32"
      style={{
        background: `linear-gradient(135deg, ${config.primary_color}15 0%, ${config.secondary_color}15 100%)`,
      }}
    >
      <div className="container mx-auto px-4 text-center">
        {config.logo_url && (
          <img
            src={config.logo_url}
            alt={config.store_name}
            className="h-20 w-auto mx-auto mb-8"
          />
        )}

        <h1
          className="text-4xl md:text-5xl font-bold mb-6"
          style={{ color: config.text_color }}
        >
          Welcome to {config.store_name}
        </h1>

        {config.store_description && (
          <p
            className="text-xl md:text-2xl mb-8 max-w-2xl mx-auto"
            style={{ color: config.text_color, opacity: 0.8 }}
          >
            {config.store_description}
          </p>
        )}

        <Link
          href={getStoreUrl("/products")}
          className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white rounded-lg transition-all hover:scale-105"
          style={{ backgroundColor: config.primary_color }}
        >
          Shop Now
          <svg
            className="ml-2 w-5 h-5"
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
    </section>
  );
}
