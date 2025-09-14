'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

interface TenantContextType {
  tenant?: any;
  loading: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

interface TenantProviderProps {
  children: React.ReactNode;
}

export function TenantProvider({ children }: TenantProviderProps) {
  const [tenant, setTenant] = useState<any>();
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadTenant = async () => {
      try {
        let tenantId: string | undefined;

        // Try to get tenant ID from window object first
        if (typeof window !== 'undefined') {
          tenantId = (window as any).__EDGE_TENANT_ID;
        }

        // If not found, extract from hostname subdomain
        if (!tenantId && typeof window !== 'undefined') {
          const hostname = window.location.hostname;
          const subdomain = hostname.split('.')[0];
          if (subdomain && subdomain !== 'www' && subdomain !== 'localhost') {
            tenantId = subdomain;
          }
        }

        if (tenantId) {
          const apiClient = axios.create({
            baseURL: process.env.NEXT_PUBLIC_API_URL || '',
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json',
            },
          });

          const response = await apiClient.get(`/api/tenant/${tenantId}`);
          setTenant(response.data);
        }
      } catch (error) {
        console.error('Error loading tenant:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTenant();
  }, []);

  const value: TenantContextType = {
    tenant,
    loading,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
}