'use client';

import React from 'react';
import clsx from 'clsx';

interface UsageIndicatorProps {
  current: number;
  max: number;
  label: string;
  className?: string;
}

export function UsageIndicator({ current, max, label, className }: UsageIndicatorProps) {
  const percentage = Math.min((current / max) * 100, 100);
  const isNearLimit = percentage >= 80;
  const isAtLimit = current >= max;

  return (
    <div className={clsx("space-y-2", className)}>
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className={clsx(
          "font-medium",
          isAtLimit ? "text-red-600" : isNearLimit ? "text-amber-600" : "text-gray-900"
        )}>
          {current} / {max}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={clsx(
            "h-2 rounded-full transition-all duration-300",
            isAtLimit ? "bg-red-500" : isNearLimit ? "bg-amber-500" : "bg-green-500"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {isNearLimit && (
        <p className={clsx(
          "text-xs",
          isAtLimit ? "text-red-600" : "text-amber-600"
        )}>
          {isAtLimit
            ? "Usage limit reached. Upgrade to continue."
            : "Approaching usage limit. Consider upgrading."
          }
        </p>
      )}
    </div>
  );
}