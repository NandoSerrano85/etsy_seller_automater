import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(price);
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(date));
}

export function formatPrintMethod(method: string): string {
  const methods: Record<string, string> = {
    uvdtf: "UVDTF",
    dtf: "DTF",
    sublimation: "Sublimation",
    vinyl: "Vinyl",
    digital: "Digital Download",
    other: "Other",
  };
  return methods[method] || method;
}

export function formatCategory(category: string): string {
  const categories: Record<string, string> = {
    cup_wraps: "Cup Wraps",
    single_square: "Square Transfers",
    single_rectangle: "Rectangle Transfers",
    other: "Other",
  };
  return categories[category] || category;
}

export function getImageUrl(path?: string): string {
  if (!path) return "/images/placeholder-product.svg";
  if (path.startsWith("http")) return path;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";
  return `${apiUrl}${path}`;
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + "...";
}
