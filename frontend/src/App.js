import React, { useState, Suspense, memo, useMemo, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useSearchParams } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import SidebarNavigation from './components/SidebarNavigation';
import TopNavigation from './components/TopNavigation';
import NotificationSystem, { useNotifications } from './components/NotificationSystem';

// Critical components (loaded immediately)
import LoginRegister from './pages/LoginRegister';
import OAuthRedirect from './pages/OAuthRedirect';
import OrganizationSelection from './pages/OrganizationSelection';

// Lazy loaded components for better performance
const Home = React.lazy(() => import('./pages/SimpleHome'));
const MockupCreator = React.lazy(() => import('./pages/MockupCreator'));
const ConnectEtsy = React.lazy(() => import('./pages/ConnectEtsy'));
const Account = React.lazy(() => import('./pages/Account'));
const OrganizationManagement = React.lazy(() => import('./pages/OrganizationManagement'));
const PrinterManagement = React.lazy(() => import('./pages/PrinterManagement'));
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'));
const SubscriptionPage = React.lazy(() => import('./pages/SubscriptionPage'));
const DesignsTab = React.lazy(() => import('./pages/HomeTabs/DesignsTab'));
const AnalyticsTab = React.lazy(() => import('./pages/HomeTabs/AnalyticsTab'));
const OrdersTab = React.lazy(() => import('./pages/HomeTabs/OrdersTab'));
const ToolsTab = React.lazy(() => import('./pages/HomeTabs/ToolsTab'));

// Shopify components (lazy loaded)
const ShopifyConnect = React.lazy(() => import('./pages/ShopifyConnect'));
const ShopifySuccess = React.lazy(() => import('./pages/ShopifySuccess'));
const ShopifyProducts = React.lazy(() => import('./pages/ShopifyProducts'));
const ShopifyOrders = React.lazy(() => import('./pages/ShopifyOrders'));
const ShopifyDashboard = React.lazy(() => import('./pages/ShopifyDashboard'));
const ShopifyProductCreator = React.lazy(() => import('./pages/ShopifyProductCreator'));

// Loading component for suspense fallback
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    <span className="ml-3 text-gray-600">Loading...</span>
  </div>
);

const AppLayout = memo(({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { notifications, removeNotification } = useNotifications();

  // Hide sidebar and top nav on login and public pages
  const isPublicPage = useMemo(
    () => ['/login', '/oauth/redirect', '/welcome', '/organization-select'].includes(location.pathname),
    [location.pathname]
  );

  // Memoize handlers to prevent unnecessary re-renders
  const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), []);

  const handleTabChange = useCallback(
    tabId => {
      const newParams = new URLSearchParams(searchParams);
      const currentMainTab = searchParams.get('tab');

      if (currentMainTab === 'orders') {
        newParams.set('subtab', tabId);
      } else {
        newParams.set('tab', tabId);
        newParams.delete('subtab'); // Clear subtab when changing main tab
      }

      setSearchParams(newParams);
    },
    [searchParams, setSearchParams]
  );

  // Memoize current tab values
  const { currentTab, currentSubTab } = useMemo(
    () => ({
      currentTab: searchParams.get('tab') || 'overview',
      currentSubTab: searchParams.get('subtab'),
    }),
    [searchParams]
  );

  if (isPublicPage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-lavender-100 via-mint-50 to-peach-50">
        {children}
        <NotificationSystem notifications={notifications} onDismiss={removeNotification} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50">
      {/* Sidebar Navigation */}
      <SidebarNavigation isOpen={sidebarOpen} onToggle={toggleSidebar} />

      {/* Main Content Area */}
      <div className="lg:ml-64">
        {/* Top Navigation */}
        <TopNavigation
          activeTab={currentSubTab || currentTab}
          onTabChange={handleTabChange}
          onMenuToggle={toggleSidebar}
        />

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>

      {/* Notification System */}
      <NotificationSystem notifications={notifications} onDismiss={removeNotification} />
    </div>
  );
});

function App() {
  return (
    <Router>
      <AppLayout>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginRegister />} />
            <Route path="/welcome" element={<Navigate to="/" replace />} />
            <Route path="/oauth/redirect" element={<OAuthRedirect />} />
            <Route path="/organization-select" element={<OrganizationSelection />} />

            {/* Protected routes */}
            {/* Main Dashboard */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />

            {/* Design Studio Routes */}
            <Route
              path="/designs"
              element={
                <ProtectedRoute>
                  <DesignsTab />
                </ProtectedRoute>
              }
            >
              <Route path="upload" element={<DesignsTab defaultTab="upload" />} />
              <Route path="gallery" element={<DesignsTab defaultTab="gallery" />} />
              <Route path="templates" element={<DesignsTab defaultTab="templates" />} />
            </Route>

            {/* Mockup Creator */}
            <Route
              path="/mockup-creator"
              element={
                <ProtectedRoute>
                  <MockupCreator />
                </ProtectedRoute>
              }
            />

            {/* Shop Management Routes */}
            <Route
              path="/orders"
              element={
                <ProtectedRoute>
                  <OrdersTab />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <AnalyticsTab />
                </ProtectedRoute>
              }
            />
            <Route path="/listings" element={<ProtectedRoute>{/* <ListingsTab /> */}</ProtectedRoute>} />

            {/* Tools & Settings */}
            <Route
              path="/tools"
              element={
                <ProtectedRoute>
                  <ToolsTab />
                </ProtectedRoute>
              }
            />
            <Route
              path="/account"
              element={
                <ProtectedRoute>
                  <Account />
                </ProtectedRoute>
              }
            />

            {/* Etsy Connection */}
            <Route
              path="/connect-etsy"
              element={
                <ProtectedRoute>
                  <ConnectEtsy />
                </ProtectedRoute>
              }
            />

            {/* Shopify Routes */}
            <Route
              path="/shopify/connect"
              element={
                <ProtectedRoute>
                  <ShopifyConnect />
                </ProtectedRoute>
              }
            />
            <Route
              path="/shopify/success"
              element={
                <ProtectedRoute>
                  <ShopifySuccess />
                </ProtectedRoute>
              }
            />
            <Route
              path="/shopify/dashboard"
              element={
                <ProtectedRoute>
                  <ShopifyDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/shopify/products"
              element={
                <ProtectedRoute>
                  <ShopifyProducts />
                </ProtectedRoute>
              }
            />
            <Route
              path="/shopify/products/create"
              element={
                <ProtectedRoute>
                  <ShopifyProductCreator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/shopify/orders"
              element={
                <ProtectedRoute>
                  <ShopifyOrders />
                </ProtectedRoute>
              }
            />
            <Route
              path="/shopify/analytics"
              element={
                <ProtectedRoute>
                  <ShopifyDashboard />
                </ProtectedRoute>
              }
            />

            {/* Organization Management */}
            <Route
              path="/organizations"
              element={
                <ProtectedRoute>
                  <OrganizationManagement />
                </ProtectedRoute>
              }
            />

            {/* Printer Management */}
            <Route
              path="/printers"
              element={
                <ProtectedRoute>
                  <PrinterManagement />
                </ProtectedRoute>
              }
            />

            {/* Admin Dashboard */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* Subscription Management */}
            <Route
              path="/subscription"
              element={
                <ProtectedRoute>
                  <SubscriptionPage />
                </ProtectedRoute>
              }
            />

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AppLayout>
    </Router>
  );
}

export default App;
