"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";

// Extended store configuration interface
export interface StoreConfig {
  store_name: string;
  store_description: string | null;
  logo_url: string | null;
  favicon_url: string | null;

  // Theme
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  text_color: string;
  background_color: string;
  font_family: string;

  // Settings
  currency: string;
  timezone: string;

  // Contact
  contact_email: string | null;
  support_phone: string | null;

  // Social
  social_links: Record<string, string>;

  // SEO
  meta_title: string | null;
  meta_description: string | null;
  google_analytics_id: string | null;
  facebook_pixel_id: string | null;

  // Status
  is_published: boolean;
  maintenance_mode: boolean;

  // Identifiers
  user_id: string;
  subdomain: string | null;
  custom_domain: string | null;
}

interface StoreContextType {
  config: StoreConfig | null;
  loading: boolean;
  error: string | null;
  storeSlug: string | null;
  isMultiTenant: boolean;
  getStoreUrl: (path?: string) => string;
}

const defaultConfig: StoreConfig = {
  store_name: "CraftFlow Store",
  store_description: "Custom designs and prints",
  logo_url: null,
  favicon_url: null,
  primary_color: "#10b981",
  secondary_color: "#059669",
  accent_color: "#34d399",
  text_color: "#111827",
  background_color: "#ffffff",
  font_family: "Inter",
  currency: "USD",
  timezone: "America/New_York",
  contact_email: null,
  support_phone: null,
  social_links: {},
  meta_title: null,
  meta_description: null,
  google_analytics_id: null,
  facebook_pixel_id: null,
  is_published: true,
  maintenance_mode: false,
  user_id: "",
  subdomain: null,
  custom_domain: null,
};

const StoreContext = createContext<StoreContextType>({
  config: null,
  loading: true,
  error: null,
  storeSlug: null,
  isMultiTenant: false,
  getStoreUrl: () => "/",
});

export function useStore() {
  return useContext(StoreContext);
}

/**
 * Extract store slug from URL path
 * Handles paths like /store/myshop, /store/myshop/products, etc.
 */
function getStoreSlugFromPath(pathname: string): string | null {
  // Match /store/[slug] pattern
  const match = pathname.match(/^\/store\/([^\/]+)/);
  return match ? match[1] : null;
}

/**
 * Check if we're in multi-tenant mode (path-based)
 */
function isPathBasedMultiTenant(pathname: string): boolean {
  return pathname.startsWith("/store/");
}

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [config, setConfig] = useState<StoreConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [storeSlug, setStoreSlug] = useState<string | null>(null);
  const [isMultiTenant, setIsMultiTenant] = useState(false);

  // Helper to generate store-relative URLs
  const getStoreUrl = (path: string = ""): string => {
    if (isMultiTenant && storeSlug) {
      const cleanPath = path.startsWith("/") ? path : `/${path}`;
      return `/store/${storeSlug}${cleanPath}`;
    }
    return path.startsWith("/") ? path : `/${path}`;
  };

  useEffect(() => {
    const fetchStoreConfig = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_URL =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";

        // Check for path-based multi-tenant mode
        const slug = getStoreSlugFromPath(pathname);
        const isMulti = isPathBasedMultiTenant(pathname);

        setStoreSlug(slug);
        setIsMultiTenant(isMulti);

        if (isMulti && slug) {
          // Multi-tenant mode: fetch config by store slug
          // The slug is the same as the subdomain field in the database
          const response = await fetch(
            `${API_URL}/api/store/${slug}/config`
          );

          if (response.ok) {
            const data = await response.json();

            // Check if store is published
            if (!data.is_published) {
              setError("Store is not published");
              setConfig(null);
              return;
            }

            // Check maintenance mode
            if (data.maintenance_mode) {
              setError("Store is under maintenance");
              setConfig(data);
              return;
            }

            setConfig(data);
          } else if (response.status === 404) {
            setError("Store not found");
            setConfig(null);
          } else {
            throw new Error("Failed to fetch store config");
          }
        } else {
          // Single-tenant mode or root path: fetch from existing endpoint
          const response = await fetch(
            `${API_URL}/api/ecommerce/admin/storefront-settings/public/1`
          );

          if (response.ok) {
            const data = await response.json();
            setConfig({
              ...defaultConfig,
              store_name: data.store_name || defaultConfig.store_name,
              store_description:
                data.store_description || defaultConfig.store_description,
              logo_url: data.logo_url || defaultConfig.logo_url,
              primary_color: data.primary_color || defaultConfig.primary_color,
              secondary_color:
                data.secondary_color || defaultConfig.secondary_color,
              accent_color: data.accent_color || defaultConfig.accent_color,
              text_color: data.text_color || defaultConfig.text_color,
              background_color:
                data.background_color || defaultConfig.background_color,
            });
          } else {
            // Use defaults if no settings found
            setConfig(defaultConfig);
          }
        }
      } catch (err) {
        console.error("Error fetching store config:", err);
        setError("Failed to load store configuration");
        setConfig(defaultConfig);
      } finally {
        setLoading(false);
      }
    };

    fetchStoreConfig();
  }, [pathname]);

  // Apply CSS custom properties when config changes
  useEffect(() => {
    if (config && !loading) {
      document.documentElement.style.setProperty(
        "--color-primary",
        config.primary_color
      );
      document.documentElement.style.setProperty(
        "--color-secondary",
        config.secondary_color
      );
      document.documentElement.style.setProperty(
        "--color-accent",
        config.accent_color
      );
      document.documentElement.style.setProperty(
        "--color-text",
        config.text_color
      );
      document.documentElement.style.setProperty(
        "--color-background",
        config.background_color
      );

      // Update document title
      if (config.meta_title || config.store_name) {
        document.title = config.meta_title || config.store_name;
      }

      // Update favicon if available
      if (config.favicon_url) {
        const link: HTMLLinkElement =
          document.querySelector("link[rel~='icon']") ||
          document.createElement("link");
        link.rel = "icon";
        link.href = config.favicon_url;
        document.head.appendChild(link);
      }

      // Add Google Analytics if configured
      if (config.google_analytics_id) {
        const existingScript = document.querySelector(
          `script[src*="googletagmanager.com/gtag/js?id=${config.google_analytics_id}"]`
        );
        if (!existingScript) {
          const script = document.createElement("script");
          script.async = true;
          script.src = `https://www.googletagmanager.com/gtag/js?id=${config.google_analytics_id}`;
          document.head.appendChild(script);

          const inlineScript = document.createElement("script");
          inlineScript.innerHTML = `
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${config.google_analytics_id}');
          `;
          document.head.appendChild(inlineScript);
        }
      }

      // Add Facebook Pixel if configured
      if (config.facebook_pixel_id) {
        const existingFb = document.querySelector(
          'script[src*="connect.facebook.net"]'
        );
        if (!existingFb) {
          const fbScript = document.createElement("script");
          fbScript.innerHTML = `
            !function(f,b,e,v,n,t,s)
            {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', '${config.facebook_pixel_id}');
            fbq('track', 'PageView');
          `;
          document.head.appendChild(fbScript);
        }
      }
    }
  }, [config, loading]);

  return (
    <StoreContext.Provider
      value={{ config, loading, error, storeSlug, isMultiTenant, getStoreUrl }}
    >
      {children}
    </StoreContext.Provider>
  );
}
