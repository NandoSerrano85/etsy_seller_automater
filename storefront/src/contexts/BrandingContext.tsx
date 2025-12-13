'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

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
  store_name: 'CraftFlow Store',
  store_description: 'Custom designs and prints',
  logo_url: '',
  primary_color: '#10b981',
  secondary_color: '#059669',
  accent_color: '#34d399',
  text_color: '#111827',
  background_color: '#ffffff',
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

export function BrandingProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<BrandingSettings>(defaultSettings);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch branding settings from API
    const fetchSettings = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3003';
        // For now, use user_id = 1 as default. In production, this should be dynamic based on the store
        const response = await fetch(`${API_URL}/api/ecommerce/storefront-settings/public/1`);

        if (response.ok) {
          const data = await response.json();
          setSettings({
            store_name: data.store_name || defaultSettings.store_name,
            store_description: data.store_description || defaultSettings.store_description,
            logo_url: data.logo_url || defaultSettings.logo_url,
            primary_color: data.primary_color || defaultSettings.primary_color,
            secondary_color: data.secondary_color || defaultSettings.secondary_color,
            accent_color: data.accent_color || defaultSettings.accent_color,
            text_color: data.text_color || defaultSettings.text_color,
            background_color: data.background_color || defaultSettings.background_color,
          });
        } else {
          // If settings not found, use defaults
          setSettings(defaultSettings);
        }
      } catch (error) {
        console.error('Error fetching branding settings:', error);
        setSettings(defaultSettings);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  // Apply CSS custom properties to the document root
  useEffect(() => {
    if (!loading) {
      document.documentElement.style.setProperty('--color-primary', settings.primary_color);
      document.documentElement.style.setProperty('--color-secondary', settings.secondary_color);
      document.documentElement.style.setProperty('--color-accent', settings.accent_color);
      document.documentElement.style.setProperty('--color-text', settings.text_color);
      document.documentElement.style.setProperty('--color-background', settings.background_color);
    }
  }, [settings, loading]);

  return (
    <BrandingContext.Provider value={{ settings, loading }}>
      {children}
    </BrandingContext.Provider>
  );
}
