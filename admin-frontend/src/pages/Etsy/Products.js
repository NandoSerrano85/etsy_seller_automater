import React, { useCallback, useMemo, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useCachedApi } from '../../hooks/useCachedApi';
import useDataStore from '../../stores/dataStore';
import ProductsTab from '../HomeTabs/ProductsTab';

const EtsyProducts = () => {
  const { isUserAuthenticated, isEtsyConnected, etsyError } = useAuth();

  const { fetchAllDashboardData, loading, errors } = useCachedApi();

  const { data: storeData } = useDataStore();
  const designs = storeData.designs || { mockups: [], files: [] };

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
        <p className="text-rose-700">Please log in to access products.</p>
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
    <ProductsTab
      isConnected={isEtsyConnected}
      authUrl="/connect-etsy"
      designs={designs}
      loading={isLoading}
      error={error}
      onRefresh={() => handleFetchData(true)}
    />
  );
};

export default EtsyProducts;
