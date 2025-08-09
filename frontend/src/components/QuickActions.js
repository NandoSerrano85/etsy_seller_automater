import React from 'react';
import { Link } from 'react-router-dom';

const QuickActions = ({ className = '' }) => {
  const actions = [
    {
      id: 'upload-design',
      title: 'Upload Design',
      description: 'Add new designs to your collection',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      ),
      color: 'lavender',
      href: null,
      onClick: () => {
        // This would trigger the design upload modal
        console.log('Upload design clicked');
      }
    },
    {
      id: 'create-mockup',
      title: 'Create Mockup',
      description: 'Generate professional mockups',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
      color: 'peach',
      href: '/mockup-creator'
    },
    {
      id: 'view-orders',
      title: 'Check Orders',
      description: 'View recent Etsy orders',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
      ),
      color: 'mint',
      href: '/?tab=orders'
    },
    {
      id: 'analytics',
      title: 'View Analytics',
      description: 'Check your sales performance',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'sky',
      href: '/?tab=analytics'
    }
  ];

  const colorClasses = {
    lavender: 'bg-gradient-to-br from-lavender-400 to-lavender-500 hover:from-lavender-500 hover:to-lavender-600 text-white shadow-sm hover:shadow-md',
    peach: 'bg-gradient-to-br from-peach-400 to-peach-500 hover:from-peach-500 hover:to-peach-600 text-white shadow-sm hover:shadow-md',
    mint: 'bg-gradient-to-br from-mint-400 to-mint-500 hover:from-mint-500 hover:to-mint-600 text-white shadow-sm hover:shadow-md',
    sky: 'bg-gradient-to-br from-sky-400 to-sky-500 hover:from-sky-500 hover:to-sky-600 text-white shadow-sm hover:shadow-md',
    // Legacy support
    blue: 'bg-gradient-to-br from-sky-400 to-sky-500 hover:from-sky-500 hover:to-sky-600 text-white shadow-sm hover:shadow-md',
    purple: 'bg-gradient-to-br from-lavender-400 to-lavender-500 hover:from-lavender-500 hover:to-lavender-600 text-white shadow-sm hover:shadow-md',
    green: 'bg-gradient-to-br from-mint-400 to-mint-500 hover:from-mint-500 hover:to-mint-600 text-white shadow-sm hover:shadow-md',
    orange: 'bg-gradient-to-br from-peach-400 to-peach-500 hover:from-peach-500 hover:to-peach-600 text-white shadow-sm hover:shadow-md'
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {actions.map((action) => {
          const baseClasses = `
            p-3 sm:p-4 rounded-lg transition-all duration-200 text-center
            hover:scale-[1.02] hover:shadow-md active:scale-[0.98]
            ${colorClasses[action.color]}
          `;

          const content = (
            <>
              <div className="flex justify-center mb-2">
                {action.icon}
              </div>
              <h4 className="font-medium text-sm sm:text-base mb-1">
                {action.title}
              </h4>
              <p className="text-xs opacity-90 hidden sm:block">
                {action.description}
              </p>
            </>
          );

          if (action.href) {
            return (
              <Link
                key={action.id}
                to={action.href}
                className={baseClasses}
              >
                {content}
              </Link>
            );
          }

          return (
            <button
              key={action.id}
              onClick={action.onClick}
              className={baseClasses}
            >
              {content}
            </button>
          );
        })}
      </div>

      {/* Additional Help Section */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Need help getting started?</p>
            <p className="text-xs text-gray-500">Check out our quick tutorial</p>
          </div>
          <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
            View Tutorial
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickActions;