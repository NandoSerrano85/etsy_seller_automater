import React, { useCallback, useMemo, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useCachedApi } from '../../hooks/useCachedApi';
import useDataStore from '../../stores/dataStore';
import OrdersTab from '../HomeTabs/OrdersTab';

const EtsyOrders = () => {
  const { isUserAuthenticated, isEtsyConnected, etsyError } = useAuth();

  const { fetchAllDashboardData, loading, errors } = useCachedApi();

  const { data: storeData } = useDataStore();
  const orders = storeData.orders || [];

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
        <p className="text-rose-700">Please log in to access orders.</p>
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
    <OrdersTab
      isConnected={isEtsyConnected}
      authUrl="/connect-etsy"
      orders={orders}
      loading={isLoading}
      error={error}
      onRefresh={() => handleFetchData(true)}
    />
  );
};

export default EtsyOrders;
