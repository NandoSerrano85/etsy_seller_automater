import React from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

const TopNavigation = ({
  sectionTitle,
  breadcrumbs = [],
  actions = [],
  tabs = [],
  activeTab,
  onTabChange,
  onMenuToggle,
  unshippedOrdersCount = 0,
}) => {
  const location = useLocation();
  // const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const handleTabChange = tabId => {
    const pathname = location.pathname;
    const newParams = new URLSearchParams(searchParams);

    // For Etsy and other page-based routes, use subtab parameter
    if (pathname.startsWith('/etsy/') || pathname.startsWith('/craftflow/')) {
      newParams.set('subtab', tabId);
    } else {
      // Legacy: For old tab-based routes
      const currentTab = searchParams.get('tab');
      if (currentTab === 'orders' || currentTab === 'products') {
        newParams.set('subtab', tabId);
      } else {
        newParams.set('tab', tabId);
      }
    }

    // Update URL and trigger callback if provided
    setSearchParams(newParams);
    if (onTabChange) {
      onTabChange(tabId);
    }
  };

  const getSectionConfig = () => {
    const pathname = location.pathname;
    const searchParams = new URLSearchParams(location.search);
    const tab = searchParams.get('tab');

    // Dashboard section
    if (pathname === '/' && !tab) {
      return {
        title: 'Dashboard Overview',
        subtitle: 'Welcome to your Etsy automation center',
        breadcrumbs: [{ label: 'Dashboard', active: true }],
        tabs: [
          { id: 'overview', label: 'Overview', icon: '📊' },
          { id: 'quick-actions', label: 'Quick Actions', icon: '⚡' },
        ],
      };
    }

    // Section-specific configs
    if (pathname === '/' && tab === 'analytics') {
      return {
        title: 'Sales Analytics',
        subtitle: 'Track your shop performance and trends',
        breadcrumbs: [
          { label: 'Dashboard', href: '/' },
          { label: 'Analytics', active: true },
        ],
        tabs: [
          { id: 'overview', label: 'Overview', icon: '📈' },
          { id: 'sales', label: 'Sales', icon: '💰' },
          { id: 'products', label: 'Products', icon: '📦' },
          { id: 'customers', label: 'Customers', icon: '👥' },
        ],
      };
    }

    if (pathname === '/' && tab === 'products') {
      return {
        title: 'Products',
        subtitle: 'Manage your product mockups and designs',
        breadcrumbs: [
          { label: 'Dashboard', href: '/' },
          { label: 'Products', active: true },
        ],
        tabs: [
          { id: 'productMockup', label: 'Product Mockup', icon: '🖼️' },
          { id: 'productDesign', label: 'Product Design', icon: '🎨' },
          { id: 'upload', label: 'Upload Product', icon: '⬆️' },
        ],
      };
    }

    if (pathname === '/' && tab === 'orders') {
      return {
        title: 'Order Management',
        subtitle: 'Process and track your Etsy orders',
        breadcrumbs: [
          { label: 'Dashboard', href: '/' },
          { label: 'Orders', active: true },
        ],
        tabs: [
          { id: 'pending', label: 'Pending', icon: '⏳', badge: unshippedOrdersCount || undefined },
          { id: 'completed', label: 'Completed', icon: '✅' },
          { id: 'all', label: 'All Orders', icon: '📋' },
          { id: 'print', label: 'Send to Print', icon: '🖨️' },
        ],
      };
    }

    if (pathname === '/' && tab === 'tools') {
      return {
        title: 'Automation Tools',
        subtitle: 'Streamline your workflow with powerful automation',
        breadcrumbs: [
          { label: 'Dashboard', href: '/' },
          { label: 'Tools', active: true },
        ],
        tabs: [
          { id: 'batch', label: 'Batch Operations', icon: '📦' },
          { id: 'scheduling', label: 'Scheduling', icon: '📅' },
          { id: 'integrations', label: 'Integrations', icon: '🔗' },
        ],
      };
    }

    if (pathname === '/mockup-creator') {
      return {
        title: 'Mockup Creator',
        subtitle: 'Create professional product mockups',
        breadcrumbs: [
          { label: 'Dashboard', href: '/' },
          { label: 'Mockup Creator', active: true },
        ],
        tabs: [
          { id: 'create', label: 'Create New', icon: '➕' },
          { id: 'library', label: 'My Mockups', icon: '📁' },
          { id: 'templates', label: 'Templates', icon: '🎭' },
        ],
      };
    }

    // Etsy section routes
    if (pathname === '/etsy/dashboard') {
      return {
        title: 'Etsy Dashboard',
        subtitle: 'Your Etsy shop overview',
        breadcrumbs: [
          { label: 'Etsy', href: '/etsy/dashboard' },
          { label: 'Dashboard', active: true },
        ],
        tabs: [],
      };
    }

    if (pathname === '/etsy/orders') {
      return {
        title: 'Etsy Orders',
        subtitle: 'Manage your Etsy orders',
        breadcrumbs: [
          { label: 'Etsy', href: '/etsy/dashboard' },
          { label: 'Orders', active: true },
        ],
        tabs: [
          { id: 'all', label: 'All Orders', icon: '📋' },
          { id: 'print', label: 'Send to Print', icon: '🖨️' },
        ],
      };
    }

    if (pathname === '/etsy/products') {
      return {
        title: 'Etsy Products',
        subtitle: 'Manage your product mockups and designs',
        breadcrumbs: [
          { label: 'Etsy', href: '/etsy/dashboard' },
          { label: 'Products', active: true },
        ],
        tabs: [
          { id: 'productMockup', label: 'Product Mockups', icon: '🖼️' },
          { id: 'productDesign', label: 'Product Designs', icon: '🎨' },
          { id: 'upload', label: 'Upload Product', icon: '⬆️' },
        ],
      };
    }

    if (pathname === '/etsy/analytics') {
      return {
        title: 'Etsy Analytics',
        subtitle: 'Track your shop performance',
        breadcrumbs: [
          { label: 'Etsy', href: '/etsy/dashboard' },
          { label: 'Analytics', active: true },
        ],
        tabs: [],
      };
    }

    if (pathname === '/etsy/listings') {
      return {
        title: 'Etsy Listings',
        subtitle: 'Manage your Etsy listings',
        breadcrumbs: [
          { label: 'Etsy', href: '/etsy/dashboard' },
          { label: 'Listings', active: true },
        ],
        tabs: [],
      };
    }

    if (pathname === '/account') {
      return {
        title: 'Account Settings',
        subtitle: 'Manage your profile and preferences',
        breadcrumbs: [
          { label: 'Dashboard', href: '/' },
          { label: 'Settings', active: true },
        ],
      };
    }

    // Default fallback
    return {
      title: sectionTitle || 'Dashboard',
      subtitle: 'Manage your Etsy business',
      breadcrumbs: breadcrumbs.length ? breadcrumbs : [{ label: 'Dashboard', active: true }],
      tabs: tabs,
    };
  };

  const config = getSectionConfig();
  const currentTabs = tabs.length ? tabs : config.tabs;
  const currentBreadcrumbs = breadcrumbs.length ? breadcrumbs : config.breadcrumbs;

  return (
    <div className="bg-white border-b border-sage-200 shadow-sm">
      {/* Top Bar */}
      <div className="px-4 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          {/* Left side - Menu toggle & Title */}
          <div className="flex items-center space-x-4">
            <button
              onClick={onMenuToggle}
              className="lg:hidden p-2 rounded-lg text-sage-600 hover:text-sage-900 hover:bg-sage-100 transition-all duration-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <div>
              {/* Breadcrumbs */}
              {currentBreadcrumbs.length > 0 && (
                <nav className="flex items-center space-x-2 text-sm mb-1">
                  {currentBreadcrumbs.map((crumb, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      {index > 0 && (
                        <svg className="w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      )}
                      {crumb.href ? (
                        <a
                          href={crumb.href}
                          className="text-sage-600 hover:text-lavender-600 transition-colors duration-200"
                        >
                          {crumb.label}
                        </a>
                      ) : (
                        <span className={crumb.active ? 'text-sage-900 font-medium' : 'text-sage-600'}>
                          {crumb.label}
                        </span>
                      )}
                    </div>
                  ))}
                </nav>
              )}

              {/* Title & Subtitle */}
              <h1 className="text-xl lg:text-2xl font-bold text-sage-900">{sectionTitle || config.title}</h1>
              {config.subtitle && <p className="text-sage-600 text-sm mt-1">{config.subtitle}</p>}
            </div>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center space-x-4">
            {/* Actions */}
            {actions.length > 0 && (
              <div className="flex items-center space-x-3">
                {actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={action.onClick}
                    disabled={action.disabled}
                    className={`
                      px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2
                      ${
                        action.variant === 'primary'
                          ? 'bg-gradient-to-r from-lavender-500 to-lavender-600 text-white hover:from-lavender-600 hover:to-lavender-700 shadow-sm'
                          : action.variant === 'secondary'
                            ? 'bg-gradient-to-r from-mint-100 to-mint-200 text-mint-800 hover:from-mint-200 hover:to-mint-300'
                            : 'bg-sage-100 text-sage-700 hover:bg-sage-200'
                      }
                      ${action.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md active:scale-95'}
                    `}
                  >
                    {action.icon && <span className="text-lg">{action.icon}</span>}
                    <span className="hidden sm:inline">{action.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      {currentTabs && currentTabs.length > 0 && (
        <div className="px-4 lg:px-8">
          <nav className="flex space-x-1 overflow-x-auto pb-px">
            {currentTabs.map(tab => {
              const isActive = tab.id === (searchParams.get('subtab') || activeTab);
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`
                    flex items-center space-x-2 px-4 py-3 font-medium text-sm whitespace-nowrap transition-all duration-200 border-b-2
                    ${
                      isActive
                        ? 'border-lavender-500 text-lavender-700 bg-gradient-to-t from-lavender-50 to-transparent'
                        : 'border-transparent text-sage-600 hover:text-sage-900 hover:border-sage-300'
                    }
                  `}
                >
                  {tab.icon && <span className="text-base">{tab.icon}</span>}
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span
                      className={`
                      px-2 py-0.5 rounded-full text-xs font-semibold
                      ${isActive ? 'bg-lavender-500 text-white' : 'bg-sage-200 text-sage-700'}
                    `}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      )}
    </div>
  );
};

export default TopNavigation;
