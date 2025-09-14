'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface Listing {
  id: string;
  title: string;
  price: string;
  status: string;
  views: number;
  favorites: number;
}

export default function ShopPage() {
  const [syncLoading, setSyncLoading] = useState<boolean>(false);
  const [syncMessage, setSyncMessage] = useState<string>('');

  const {
    data: listings,
    isLoading,
    refetch,
  } = useQuery<Listing[]>({
    queryKey: ['shopListings'],
    queryFn: async () => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/shop-listings`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch listings');
      }
      return response.json();
    },
  });

  const handleSync = async () => {
    setSyncLoading(true);
    setSyncMessage('');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/shop-sync`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        setSyncMessage(
          `Shop sync completed! ${result.updated || 0} listings updated.`
        );
        refetch();
      } else {
        setSyncMessage('Failed to sync shop. Please try again.');
      }
    } catch (error) {
      console.error('Error syncing shop:', error);
      setSyncMessage('Error syncing shop. Please check your connection.');
    } finally {
      setSyncLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading shop listings...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Shop Listings</h1>
        <button
          onClick={handleSync}
          disabled={syncLoading}
          className="bg-accent text-white px-4 py-2 rounded-md font-medium hover:bg-opacity-90 disabled:opacity-50"
        >
          {syncLoading ? 'Syncing...' : 'Sync'}
        </button>
      </div>

      {syncMessage && (
        <div
          className={`mb-4 p-3 rounded-md ${
            syncMessage.includes('completed')
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {syncMessage}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Views
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Favorites
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {listings?.map((listing) => (
                <tr key={listing.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {listing.title}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{listing.price}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        listing.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {listing.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {listing.views}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {listing.favorites}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!listings || listings.length === 0) && (
          <div className="text-center py-12">
            <p className="text-gray-500">
              No listings found. Try syncing your shop.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
