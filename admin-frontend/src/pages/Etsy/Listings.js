import React, { useCallback, useMemo, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useCachedApi } from '../../hooks/useCachedApi';
import ListingsTab from '../HomeTabs/ListingsTab';

const EtsyListings = () => {
  const { isUserAuthenticated, isEtsyConnected, etsyError } = useAuth();

  const { fetchAllDashboardData, loading, errors } = useCachedApi();

  const isLoading = useMemo(() => Object.values(loading).some(Boolean), [loading]);
  const error = useMemo(() => Object.values(errors).find(Boolean) || null, [errors]);

  const handleFetchData = useCallback(
    async (forceRefresh = false) => {
      if (!isEtsyConnected) return;

      try {
        await fetchAllDashboardData(forceRefresh);
      } catch (err) {
        console.error('Error fetching data:', err);
      }
    },
    [isEtsyConnected, fetchAllDashboardData]
  );

  useEffect(() => {
    if (isEtsyConnected) {
      handleFetchData();
    }
  }, [isEtsyConnected]);

  if (!isUserAuthenticated) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">Please log in to access listings.</p>
      </div>
    );
  }

  if (etsyError) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{etsyError}</p>
      </div>
    );
  }

  return (
    <ListingsTab
      isConnected={isEtsyConnected}
      authUrl="/connect-etsy"
      loading={isLoading}
      error={error}
      onRefresh={() => handleFetchData(true)}
    />
  );
};

export default EtsyListings;
