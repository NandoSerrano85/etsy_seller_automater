"use client";

import React from "react";
import { useBranding } from "@/contexts/BrandingContext";

export function MaintenancePage() {
  const { settings } = useBranding();

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ backgroundColor: settings.background_color }}
    >
      <div className="text-center px-6">
        {settings.logo_url && (
          <img
            src={settings.logo_url}
            alt={settings.store_name}
            className="h-16 w-auto mx-auto mb-8"
          />
        )}
        <h1
          className="text-4xl font-bold mb-4"
          style={{ color: settings.text_color }}
        >
          We&apos;ll be back soon!
        </h1>
        <p
          className="text-lg mb-8 max-w-md mx-auto"
          style={{ color: settings.text_color, opacity: 0.7 }}
        >
          {settings.store_name} is currently undergoing scheduled maintenance.
          We&apos;ll be back shortly.
        </p>
        <div
          className="inline-flex items-center px-6 py-3 rounded-lg"
          style={{ backgroundColor: settings.primary_color }}
        >
          <svg
            className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span className="text-white font-medium">
            Maintenance in progress
          </span>
        </div>
      </div>
    </div>
  );
}
