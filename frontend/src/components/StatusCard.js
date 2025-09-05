import React from 'react';

const StatusCard = ({
  title,
  value,
  subValue,
  icon,
  color = 'blue',
  trend,
  loading = false,
  onClick,
  className = '',
  size = 'md',
}) => {
  const colorClasses = {
    lavender: 'bg-gradient-to-br from-lavender-50 to-lavender-100 text-lavender-700 border-lavender-200',
    mint: 'bg-gradient-to-br from-mint-50 to-mint-100 text-mint-700 border-mint-200',
    peach: 'bg-gradient-to-br from-peach-50 to-peach-100 text-peach-700 border-peach-200',
    rose: 'bg-gradient-to-br from-rose-50 to-rose-100 text-rose-700 border-rose-200',
    sky: 'bg-gradient-to-br from-sky-50 to-sky-100 text-sky-700 border-sky-200',
    sage: 'bg-gradient-to-br from-sage-50 to-sage-100 text-sage-700 border-sage-200',
    // Legacy support
    blue: 'bg-gradient-to-br from-sky-50 to-sky-100 text-sky-700 border-sky-200',
    green: 'bg-gradient-to-br from-mint-50 to-mint-100 text-mint-700 border-mint-200',
    purple: 'bg-gradient-to-br from-lavender-50 to-lavender-100 text-lavender-700 border-lavender-200',
    orange: 'bg-gradient-to-br from-peach-50 to-peach-100 text-peach-700 border-peach-200',
    red: 'bg-gradient-to-br from-rose-50 to-rose-100 text-rose-700 border-rose-200',
    gray: 'bg-gradient-to-br from-sage-50 to-sage-100 text-sage-700 border-sage-200',
  };

  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  const iconSizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  };

  const textSizeClasses = {
    sm: {
      title: 'text-sm',
      value: 'text-lg',
      subValue: 'text-xs',
    },
    md: {
      title: 'text-sm sm:text-base',
      value: 'text-xl sm:text-2xl',
      subValue: 'text-xs sm:text-sm',
    },
    lg: {
      title: 'text-base sm:text-lg',
      value: 'text-2xl sm:text-3xl',
      subValue: 'text-sm',
    },
  };

  const handleClick = () => {
    if (onClick && !loading) {
      onClick();
    }
  };

  return (
    <div
      className={`
        bg-white rounded-xl shadow-sm border-2 transition-all duration-200
        ${colorClasses[color]}
        ${sizeClasses[size]}
        ${onClick ? 'cursor-pointer hover:shadow-md hover:scale-[1.02]' : ''}
        ${loading ? 'animate-pulse' : ''}
        ${className}
      `}
      onClick={handleClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h3 className={`font-medium text-gray-900 truncate ${textSizeClasses[size].title}`}>
            {loading ? <div className="bg-gray-200 h-4 w-24 rounded animate-pulse" /> : title}
          </h3>

          <div className="mt-2">
            {loading ? (
              <div className="bg-gray-300 h-8 w-16 rounded animate-pulse" />
            ) : (
              <p className={`font-bold text-gray-900 ${textSizeClasses[size].value}`}>{value}</p>
            )}

            {subValue && (
              <p className={`text-gray-500 mt-1 ${textSizeClasses[size].subValue}`}>
                {loading ? <div className="bg-gray-200 h-3 w-20 rounded animate-pulse" /> : subValue}
              </p>
            )}
          </div>

          {/* Trend Indicator */}
          {trend && !loading && (
            <div
              className={`flex items-center mt-2 text-xs ${
                trend.direction === 'up'
                  ? 'text-green-600'
                  : trend.direction === 'down'
                    ? 'text-red-600'
                    : 'text-gray-500'
              }`}
            >
              {trend.direction === 'up' && (
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {trend.direction === 'down' && (
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              <span>
                {trend.value} {trend.period}
              </span>
            </div>
          )}
        </div>

        {/* Icon */}
        {icon && (
          <div className={`ml-4 ${iconSizeClasses[size]} flex-shrink-0`}>
            {loading ? (
              <div className={`bg-gray-200 ${iconSizeClasses[size]} rounded animate-pulse`} />
            ) : (
              <div className={`${iconSizeClasses[size]} text-${color}-500`}>
                {typeof icon === 'string' ? <div className="text-2xl">{icon}</div> : icon}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Preset status cards for common use cases
export const SalesCard = ({ value, loading, trend, onClick }) => (
  <StatusCard
    title="Total Sales"
    value={value}
    icon="💰"
    color="mint"
    trend={trend}
    loading={loading}
    onClick={onClick}
  />
);

export const OrdersCard = ({ value, loading, trend, onClick }) => (
  <StatusCard title="Orders" value={value} icon="📦" color="sky" trend={trend} loading={loading} onClick={onClick} />
);

export const DesignsCard = ({ value, loading, onClick }) => (
  <StatusCard title="Designs" value={value} icon="🎨" color="lavender" loading={loading} onClick={onClick} />
);

export const MockupsCard = ({ value, loading, onClick }) => (
  <StatusCard title="Mockups" value={value} icon="🖼️" color="peach" loading={loading} onClick={onClick} />
);

export default StatusCard;
