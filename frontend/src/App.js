import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import Home from './pages/Home';
import OAuthRedirect from './pages/OAuthRedirect';
import MockupCreator from './pages/MockupCreator';
import LoginRegister from './pages/LoginRegister';
import ApiTest from './components/ApiTest';
import ConnectEtsy from './pages/ConnectEtsy';
import Account from './pages/Account';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main className="flex-1">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginRegister />} />
              <Route path="/welcome" element={<Navigate to="/" replace />} />
              <Route path="/oauth/redirect" element={<OAuthRedirect />} />
              <Route path="/test-api" element={<ApiTest />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              } />
              <Route path="/account" element={
                <ProtectedRoute>
                  <Account />
                </ProtectedRoute>
              } />
              <Route path="/mockup-creator" element={
                <ProtectedRoute>
                  <MockupCreator />
                </ProtectedRoute>
              } />
              <Route path="/connect-etsy" element={
                <ProtectedRoute>
                  <ConnectEtsy />
                </ProtectedRoute>
              } />
              
              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App; 