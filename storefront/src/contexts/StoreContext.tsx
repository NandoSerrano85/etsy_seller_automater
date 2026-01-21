"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

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
  domain: string | null;
  isMultiTenant: boolean;
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
  domain: null,
  isMultiTenant: false,
});

export function useStore() {
  return useContext(StoreContext);
}

/**
 * Get the current domain from the browser
 */
function getCurrentDomain(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const hostname = window.location.hostname;

  // Skip localhost and development domains
  if (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname.includes("vercel.app") ||
    hostname.includes("railway.app")
  ) {
    return null;
  }

  return hostname;
}

/**
 * Check if we're running in multi-tenant mode
 */
function isMultiTenantMode(): boolean {
  // Check for env var to enable/disable multi-tenant
  if (process.env.NEXT_PUBLIC_MULTI_TENANT === "false") {
    return false;
  }

  const domain = getCurrentDomain();

  // If we have a custom domain or craftflow.store subdomain, it's multi-tenant
  if (domain) {
    // Check if it's a craftflow.store subdomain
    if (domain.endsWith(".craftflow.store")) {
      return true;
    }

    // Check if it's a custom domain (not development)
    if (
      !domain.includes("localhost") &&
      !domain.includes("vercel") &&
      !domain.includes("railway")
    ) {
      return true;
    }
  }

  return false;
}

/**
 * Get the store identifier from the domain
 */
function getStoreIdentifier(): string | null {
  const domain = getCurrentDomain();

  if (!domain) {
    return null;
  }

  // For craftflow.store subdomains, extract the subdomain
  if (domain.endsWith(".craftflow.store")) {
    return domain.replace(".craftflow.store", "");
  }

  // For custom domains, use the full domain
  return domain;
}

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<StoreConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domain, setDomain] = useState<string | null>(null);
  const [isMultiTenant, setIsMultiTenant] = useState(false);

  useEffect(() => {
    const fetchStoreConfig = async () => {
      try {
        setLoading(true);
        setError(null);

        const isMulti = isMultiTenantMode();
        setIsMultiTenant(isMulti);

        const API_URL =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:3003";

        if (isMulti) {
          // Multi-tenant mode: fetch config by domain
          const storeId = getStoreIdentifier();
          setDomain(storeId);

          if (!storeId) {
            // No domain detected, use fallback
            setConfig(defaultConfig);
            return;
          }

          // Fetch store config from public API
          const response = await fetch(`${API_URL}/api/store/${storeId}/config`);

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
          // Single-tenant mode: fetch from existing endpoint
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
  }, []);

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

      // Add Facebook Pixel if configured
      if (config.facebook_pixel_id) {
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
  }, [config, loading]);

  return (
    <StoreContext.Provider
      value={{ config, loading, error, domain, isMultiTenant }}
    >
      {children}
    </StoreContext.Provider>
  );
}
