import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';
import { TierBadge } from './subscription';
import OrganizationSelector from './OrganizationSelector';
import useOrganizationStore from '../stores/organizationStore';

const SidebarNavigation = ({ isOpen, onToggle }) => {
  const { user, isUserAuthenticated, logout } = useAuth();
  const { hasAdminAccess } = useOrganizationStore();
  const { currentTier } = useSubscription();
  const location = useLocation();
  const navigate = useNavigate();
  const [expandedSections, setExpandedSections] = useState({});

  console.log('user', user);
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSection = sectionId => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  };

  const mainNavItems = [
    {
      id: 'etsy',
      label: 'Etsy',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
          />
        </svg>
      ),
      hasSubmenu: true,
      gradient: 'from-orange-100 to-orange-200',
      submenu: [
        { label: 'Dashboard', path: '/?tab=overview' },
        { label: 'Orders', path: '/?tab=orders' },
        { label: 'Analytics', path: '/?tab=analytics' },
        { label: 'Listings', path: '/?tab=listings' },
        { label: 'Product', path: '/?tab=products' },
      ],
    },
    {
      id: 'mockups',
      label: 'Mockup Creator',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
      path: '/mockup-creator',
      gradient: 'from-purple-100 to-purple-200',
    },
    {
      id: 'shopify',
      label: 'Shopify',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      hasSubmenu: true,
      gradient: 'from-green-100 to-green-200',
      submenu: [
        { label: 'Connect Store', path: '/shopify/connect' },
        { label: 'Dashboard', path: '/shopify/dashboard' },
        { label: 'Products', path: '/shopify/products' },
        { label: 'Orders', path: '/shopify/orders' },
        { label: 'Analytics', path: '/shopify/analytics' },
      ],
    },
    {
      id: 'craftflow-commerce',
      label: 'CraftFlow Commerce',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
      ),
      hasSubmenu: true,
      gradient: 'from-emerald-100 to-emerald-200',
      submenu: [
        { label: 'Dashboard', path: '/craftflow/dashboard' },
        { label: 'Products', path: '/craftflow/products' },
        { label: 'Orders', path: '/craftflow/orders' },
        { label: 'Customers', path: '/craftflow/customers' },
        { label: 'Email Management', path: '/craftflow/emails/templates' },
        { label: 'Storefront Settings', path: '/craftflow/settings' },
      ],
    },
    {
      id: 'account',
      label: 'Settings',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
      ),
      hasSubmenu: true,
      gradient: 'from-sage-100 to-sage-200',
      submenu: [
        { label: 'Profile', path: '/account?tab=profile' },
        { label: 'Subscription', path: '/subscription' },
        { label: 'Integrations', path: '/account?tab=integrations' },
        { label: 'Preferences', path: '/account?tab=preferences' },
        { label: 'Printer Management', path: '/account?tab=printers' },
        { label: 'Organizations', path: '/account?tab=organizations' },
      ],
    },
  ];

  const isActiveLink = path => {
    // Handle tab-based routes like /?tab=overview
    if (path.includes('?')) {
      const [pathPart, queryPart] = path.split('?');
      if (location.pathname !== pathPart) return false;

      const urlParams = new URLSearchParams(location.search);
      const pathParams = new URLSearchParams(queryPart);

      // Check if all params in the nav path match current URL
      for (const [key, value] of pathParams.entries()) {
        if (urlParams.get(key) !== value) return false;
      }
      return true;
    }

    // Handle regular routes
    if (path === '/') {
      return location.pathname === '/' && !location.search;
    }
    return location.pathname.startsWith(path);
  };

  const NavItem = ({ item, isSubmenuItem = false }) => {
    const isActive = isActiveLink(item.path || '/');
    const hasSubmenu = item.hasSubmenu && !isSubmenuItem;
    const isExpanded = expandedSections[item.id];

    const baseClasses = `
      flex items-center w-full px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
      ${isSubmenuItem ? 'ml-4 pl-8' : ''}
    `;

    const activeClasses = isActive
      ? `bg-gradient-to-r ${item.gradient || 'from-lavender-100 to-lavender-200'} text-lavender-800 shadow-sm`
      : 'text-sage-600 hover:text-sage-800 hover:bg-sage-50';

    const content = (
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center space-x-3">
          <div className={`${isActive ? 'text-lavender-600' : 'text-sage-500'}`}>{item.icon}</div>
          <span className="truncate">{item.label}</span>
        </div>

        {hasSubmenu && (
          <svg
            className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        )}
      </div>
    );

    if (hasSubmenu) {
      return (
        <div>
          <button onClick={() => toggleSection(item.id)} className={`${baseClasses} ${activeClasses}`}>
            {content}
          </button>

          {isExpanded && (
            <div className="mt-1 space-y-1">
              {item.submenu.map((subItem, index) => (
                <NavItem key={index} item={subItem} isSubmenuItem={true} />
              ))}
            </div>
          )}
        </div>
      );
    }

    return (
      <Link to={item.path} className={`${baseClasses} ${activeClasses}`} onClick={() => onToggle && onToggle(false)}>
        {content}
      </Link>
    );
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-25 z-40 lg:hidden" onClick={() => onToggle(false)} />
      )}

      {/* Sidebar */}
      <div
        className={`
        absolute left-0 top-0 h-full bg-gradient-to-b from-white to-sage-50 border-r border-sage-200 z-50 transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:absolute lg:z-auto
        w-64 shadow-lg lg:shadow-none
      `}
      >
        {/* Header */}
        <div className="p-6 border-b border-sage-200">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-lavender-400 to-lavender-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
              <div>
                <h1 className="font-bold text-sage-900 text-lg leading-none">CraftFlow</h1>
                <p className="text-sage-600 text-xs">Etsy Automation</p>
              </div>
            </Link>

            <button
              onClick={() => onToggle(false)}
              className="lg:hidden p-1.5 rounded-lg text-sage-500 hover:text-sage-700 hover:bg-sage-100"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {isUserAuthenticated ? (
            <>
              {mainNavItems.map(item => (
                <NavItem key={item.id} item={item} />
              ))}

              {/* Admin Dashboard - Only show if user has admin access */}
              {(hasAdminAccess() || user?.role === 'admin' || user?.role === 'super_admin') && (
                <div className="pt-4 mt-4 border-t border-sage-200">
                  <p className="px-3 text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">
                    Administration
                  </p>
                  <NavItem
                    item={{
                      id: 'admin',
                      label: 'Admin Dashboard',
                      icon: (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      ),
                      path: '/admin',
                      gradient: 'from-red-100 to-red-200',
                    }}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-sage-600 text-sm mb-4">Please log in to access navigation</p>
              <Link
                to="/login"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-lavender-400 to-lavender-500 text-white rounded-lg hover:from-lavender-500 hover:to-lavender-600 transition-all duration-200"
              >
                Sign In
              </Link>
            </div>
          )}
        </nav>

        {/* User Profile Section */}
        {isUserAuthenticated && (
          <div className="p-4 border-t border-sage-200 space-y-4">
            {/* Organization Selector */}
            <div className="px-1">
              <p className="text-xs font-semibold text-sage-500 uppercase tracking-wider mb-2">Organization</p>
              <OrganizationSelector className="w-full" />
            </div>

            {/* User Profile */}
            <div className="flex items-center space-x-3 p-3 rounded-xl bg-gradient-to-r from-sage-50 to-mint-50">
              <div className="w-8 h-8 bg-gradient-to-br from-mint-400 to-mint-500 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold text-sm">
                  {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sage-900 font-medium text-sm truncate">{user?.shop_name || 'User'}</p>
                <div className="flex items-center space-x-2">
                  <p className="text-sage-600 text-xs truncate">{user.email || 'user@example.com'}</p>
                  <TierBadge size="small" />
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 text-sage-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all duration-200"
                title="Sign out"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                  />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default SidebarNavigation;
