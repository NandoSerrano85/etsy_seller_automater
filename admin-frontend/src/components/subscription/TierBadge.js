import React from 'react';
import { useSubscription } from '../../hooks/useSubscription';

const TierBadge = ({
  tier = null, // If null, uses current tier
  size = 'default', // 'small', 'default', 'large'
  showPrice = false,
  className = '',
}) => {
  const { currentTier, getTierConfig } = useSubscription();

  const targetTier = tier || currentTier;
  const config = getTierConfig(targetTier);

  if (!config) return null;

  const sizeClasses = {
    small: 'px-2 py-1 text-xs',
    default: 'px-3 py-1 text-sm',
    large: 'px-4 py-2 text-base',
  };

  const colorClasses = {
    emerald: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
    purple: 'bg-purple-100 text-purple-700 border-purple-200',
    amber: 'bg-amber-100 text-amber-700 border-amber-200',
  };

  return (
    <span
      className={`
      inline-flex items-center font-medium rounded-full border
      ${sizeClasses[size]}
      ${colorClasses[config.color]}
      ${className}
    `}
    >
      {config.name}
      {showPrice && config.price > 0 && <span className="ml-1 opacity-75">${config.price}/mo</span>}
    </span>
  );
};

export default TierBadge;
