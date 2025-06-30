import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import Home from './pages/Home';
import Welcome from './pages/Welcome';
import OAuthRedirect from './pages/OAuthRedirect';
import MaskCreator from './pages/MaskCreator';
import LoginRegister from './pages/LoginRegister';

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
              <Route path="/welcome" element={<Welcome />} />
              <Route path="/oauth/redirect" element={<OAuthRedirect />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              } />
              <Route path="/mask-creator" element={
                <ProtectedRoute>
                  <MaskCreator />
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