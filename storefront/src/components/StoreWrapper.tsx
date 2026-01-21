"use client";

import React from "react";
import { useStore } from "@/contexts/StoreContext";
import { MaintenancePage } from "./MaintenancePage";
import { StoreNotFound } from "./StoreNotFound";

interface StoreWrapperProps {
  children: React.ReactNode;
}

/**
 * Wrapper component that handles store states:
 * - Loading: Shows loading spinner
 * - Not Found: Shows store not found page
 * - Maintenance: Shows maintenance page
 * - Active: Shows children
 */
export function StoreWrapper({ children }: StoreWrapperProps) {
  const { config, loading, error, isMultiTenant } = useStore();

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading store...</p>
        </div>
      </div>
    );
  }

  // Handle errors in multi-tenant mode
  if (isMultiTenant) {
    // Store not found
    if (error === "Store not found" || !config) {
      return <StoreNotFound />;
    }

    // Maintenance mode
    if (config.maintenance_mode) {
      return <MaintenancePage />;
    }

    // Store not published
    if (!config.is_published) {
      return <StoreNotFound />;
    }
  }

  // Render children normally
  return <>{children}</>;
}
