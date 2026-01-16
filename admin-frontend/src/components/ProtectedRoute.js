import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';

const ProtectedRoute = ({ children }) => {
  const { isUserAuthenticated, userLoading } = useAuth();
  const { fetchSubscription, initialized } = useSubscription();
  const location = useLocation();

  // Fetch subscription data when user is authenticated
  useEffect(() => {
    if (isUserAuthenticated && !initialized) {
      fetchSubscription();
    }
  }, [isUserAuthenticated, initialized, fetchSubscription]);

  if (userLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isUserAuthenticated) {
    // Redirect to login page with the return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
