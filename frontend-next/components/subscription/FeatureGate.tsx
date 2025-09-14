'use client';

import React from 'react';

interface FeatureGateProps {
  feature: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function FeatureGate({ feature, fallback, children }: FeatureGateProps) {
  // Placeholder implementation - in real app this would check user's subscription
  const hasAccess = true; // Mock: always allow access for now

  if (!hasAccess) {
    return (
      <div className="text-center p-4 bg-gray-50 border border-gray-200 rounded-lg">
        {fallback || (
          <div>
            <p className="text-sm text-gray-600 mb-2">
              This feature requires a premium subscription
            </p>
            <button className="text-primary text-sm underline hover:text-opacity-80">
              Upgrade Now
            </button>
          </div>
        )}
      </div>
    );
  }

  return <>{children}</>;
}