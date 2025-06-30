import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import Welcome from './pages/Welcome';
import OAuthRedirect from './pages/OAuthRedirect';
import MaskCreator from './pages/MaskCreator';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/welcome" element={<Welcome />} />
            <Route path="/oauth/redirect" element={<OAuthRedirect />} />
            <Route path="/mask-creator" element={<MaskCreator />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 