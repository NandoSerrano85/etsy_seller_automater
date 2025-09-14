'use client';

import { useQuery } from '@tanstack/react-query';
import { getUserData, getTopSellers } from '@/lib/api';

interface User {
  shop: {
    name: string;
  };
}

interface Seller {
  id: string;
  name: string;
  sales: number;
}

export default function DashboardPage() {
  const { data: userData, isLoading: userLoading } = useQuery<User>({
    queryKey: ['userData'],
    queryFn: getUserData,
  });

  const { data: topSellers, isLoading: sellersLoading } = useQuery<Seller[]>({
    queryKey: ['topSellers'],
    queryFn: getTopSellers,
  });

  if (userLoading || sellersLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {userData?.shop?.name && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            Welcome, {userData.shop.name}!
          </h2>
        </div>
      )}

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top Sellers</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {topSellers?.map((seller) => (
            <div
              key={seller.id}
              className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm"
            >
              <h4 className="font-semibold text-gray-900">{seller.name}</h4>
              <p className="text-gray-600 mt-1">Sales: {seller.sales}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
