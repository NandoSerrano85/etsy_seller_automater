import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useSearchParams } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import SidebarNavigation from './components/SidebarNavigation';
import TopNavigation from './components/TopNavigation';
import Home from './pages/SimpleHome';
import OAuthRedirect from './pages/OAuthRedirect';
import MockupCreator from './pages/MockupCreator';
import LoginRegister from './pages/LoginRegister';
// import ApiTest from './components/ApiTest';
import ConnectEtsy from './pages/ConnectEtsy';
import Account from './pages/Account';
import OrganizationManagement from './pages/OrganizationManagement';
import PrinterManagement from './pages/PrinterManagement';
import AdminDashboard from './pages/AdminDashboard';
import OrganizationSelection from './pages/OrganizationSelection';
import NotificationSystem, { useNotifications } from './components/NotificationSystem';
import DesignsTab from './pages/HomeTabs/DesignsTab';
import AnalyticsTab from './pages/HomeTabs/AnalyticsTab';
// import ListingsTab from './pages/HomeTabs/ListingsTab';
import OrdersTab from './pages/HomeTabs/OrdersTab';
import ToolsTab from './pages/HomeTabs/ToolsTab';

const AppLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { notifications, removeNotification } = useNotifications();

  // Hide sidebar and top nav on login and public pages
  const isPublicPage = ['/login', '/oauth/redirect', '/welcome', '/organization-select'].includes(location.pathname);

  if (isPublicPage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-lavender-100 via-mint-50 to-peach-50">
        {children}
        <NotificationSystem notifications={notifications} onDismiss={removeNotification} />
      </div>
    );
  }

  const currentTab = searchParams.get('tab') || 'overview';
  const currentSubTab = searchParams.get('subtab');

  const handleTabChange = tabId => {
    const newParams = new URLSearchParams(searchParams);
    const currentMainTab = searchParams.get('tab');

    if (currentMainTab === 'orders') {
      newParams.set('subtab', tabId);
    } else {
      newParams.set('tab', tabId);
      newParams.delete('subtab'); // Clear subtab when changing main tab
    }

    setSearchParams(newParams);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50">
      {/* Sidebar Navigation */}
      <SidebarNavigation isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main Content Area */}
      <div className="lg:ml-64">
        {/* Top Navigation */}
        <TopNavigation
          activeTab={currentSubTab || currentTab}
          onTabChange={handleTabChange}
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
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
};

function App() {
  return (
    <Router>
      <AppLayout>
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

          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
