"use client";

import Link from "next/link";
import { useBranding } from "@/contexts/BrandingContext";
import { useState } from "react";

interface CategoryCardProps {
  href: string;
  gradient: string;
  title: string;
  description: string;
  primaryColor: string;
}

function CategoryCard({
  href,
  gradient,
  title,
  description,
  primaryColor,
}: CategoryCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Link
      href={href}
      className="group relative overflow-hidden rounded-lg bg-white shadow-lg hover:shadow-xl transition-shadow"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`aspect-square bg-gradient-to-br ${gradient}`} />
      <div className="p-6">
        <h3
          className="text-xl font-bold transition-colors"
          style={{ color: isHovered ? primaryColor : "#111827" }}
        >
          {title}
        </h3>
        <p className="text-gray-600 mt-2">{description}</p>
      </div>
    </Link>
  );
}

export function CategoriesSection() {
  const { settings } = useBranding();

  const categories = [
    {
      href: "/products?print_method=uvdtf",
      gradient: "from-blue-500 to-purple-600",
      title: "UVDTF Transfers",
      description: "High-quality UV DTF transfers for all surfaces",
    },
    {
      href: "/products?print_method=dtf",
      gradient: "from-pink-500 to-orange-500",
      title: "DTF Transfers",
      description: "Direct-to-film transfers for fabric and more",
    },
    {
      href: "/products?print_method=sublimation",
      gradient: "from-green-500 to-teal-500",
      title: "Sublimation",
      description: "Vibrant sublimation designs for your projects",
    },
  ];

  return (
    <section className="bg-gray-50 py-16">
      <div className="container">
        <h2 className="text-3xl font-bold text-center mb-12">
          Shop by Category
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {categories.map((category, index) => (
            <CategoryCard
              key={index}
              {...category}
              primaryColor={settings.primary_color}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
