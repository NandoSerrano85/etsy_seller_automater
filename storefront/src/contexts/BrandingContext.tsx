"use client";

import React, { createContext, useContext } from "react";
import { useStore, StoreConfig } from "./StoreContext";

// Legacy interface for backwards compatibility
interface BrandingSettings {
  store_name: string;
  store_description: string;
  logo_url: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  text_color: string;
  background_color: string;
}

const defaultSettings: BrandingSettings = {
  store_name: "CraftFlow Store",
  store_description: "Custom designs and prints",
  logo_url: "",
  primary_color: "#10b981",
  secondary_color: "#059669",
  accent_color: "#34d399",
  text_color: "#111827",
  background_color: "#ffffff",
};

interface BrandingContextType {
  settings: BrandingSettings;
  loading: boolean;
}

const BrandingContext = createContext<BrandingContextType>({
  settings: defaultSettings,
  loading: true,
});

export function useBranding() {
  return useContext(BrandingContext);
}

/**
 * BrandingProvider now uses StoreContext for multi-tenant support
 * This maintains backwards compatibility with existing components
 */
export function BrandingProvider({ children }: { children: React.ReactNode }) {
  const { config, loading } = useStore();

  // Convert StoreConfig to BrandingSettings for backwards compatibility
  const settings: BrandingSettings = config
    ? {
        store_name: config.store_name,
        store_description:
          config.store_description || defaultSettings.store_description,
        logo_url: config.logo_url || defaultSettings.logo_url,
        primary_color: config.primary_color,
        secondary_color: config.secondary_color,
        accent_color: config.accent_color,
        text_color: config.text_color,
        background_color: config.background_color,
      }
    : defaultSettings;

  return (
    <BrandingContext.Provider value={{ settings, loading }}>
      {children}
    </BrandingContext.Provider>
  );
}
