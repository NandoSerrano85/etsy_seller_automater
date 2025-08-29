import React, { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';
import ListingCard from '../../components/ListingCard';
import EditListingModal from '../../components/EditListingModal';
import BulkEditModal from '../../components/BulkEditModal';

const ListingsTab = ({
  isConnected,
  authUrl,
  loading: parentLoading,
  error: parentError,
  onRefresh
}) => {
  const api = useApi();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedListings, setSelectedListings] = useState([]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showBulkEditModal, setShowBulkEditModal] = useState(false);
  const [editingListing, setEditingListing] = useState(null);

  const fetchListings = async () => {
    if (!isConnected) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/third-party-listings/all');
      setListings(response.listings || []);
    } catch (err) {
      console.error('Error fetching listings:', err);
      setError(err.message || 'Failed to fetch listings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [isConnected]);

  const handleSelectListing = (listingId) => {
    setSelectedListings(prev => {
      if (prev.includes(listingId)) {
        return prev.filter(id => id !== listingId);
      } else {
        return [...prev, listingId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedListings.length === listings.length) {
      setSelectedListings([]);
    } else {
      setSelectedListings(listings.map(listing => listing.listing_id));
    }
  };

  const handleEditListing = (listing) => {
    setEditingListing(listing);
    setShowEditModal(true);
  };

  const handleBulkEdit = () => {
    if (selectedListings.length === 0) {
      alert('Please select at least one listing to edit');
      return;
    }
    setShowBulkEditModal(true);
  };

  const handleEditSuccess = () => {
    fetchListings(); // Refresh listings after successful edit
    setSelectedListings([]); // Clear selections
  };

  const handleModalClose = () => {
    setShowEditModal(false);
    setShowBulkEditModal(false);
    setEditingListing(null);
  };

  if (!isConnected) {
    return (
      <div className="card p-6 sm:p-8 text-center">
        <div className="mb-6">
          <div className="mx-auto w-16 h-16 bg-lavender-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl">🛍️</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Connect Your Etsy Shop</h3>
          <p className="text-gray-600 mb-6">Connect your Etsy shop to view and manage your listings</p>
        </div>
        <a href={authUrl} className="btn-primary">Connect Shop</a>
      </div>
    );
  }

  if (loading || parentLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lavender-500"></div>
        <span className="ml-2 text-sage-600">Loading listings...</span>
      </div>
    );
  }

  if (error || parentError) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{error || parentError}</p>
        <button 
          onClick={() => {
            if (onRefresh) onRefresh();
            fetchListings();
          }}
          className="mt-2 text-rose-600 hover:text-rose-700 text-sm underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Listings Management</h2>
          <p className="text-gray-600">
            Manage your Etsy listings • {listings.length} total listings
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchListings}
            className="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="mr-2">🔄</span>
            Refresh
          </button>
          {selectedListings.length > 0 && (
            <button
              onClick={handleBulkEdit}
              className="px-4 py-2 bg-lavender-500 text-white rounded-lg hover:bg-lavender-600 transition-colors"
            >
              Edit Selected ({selectedListings.length})
            </button>
          )}
        </div>
      </div>

      {listings.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl">📝</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Listings Found</h3>
          <p className="text-gray-600">Your Etsy shop doesn't have any active listings yet.</p>
        </div>
      ) : (
        <>
          {/* Selection Controls */}
          <div className="flex items-center justify-between bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedListings.length === listings.length && listings.length > 0}
                onChange={handleSelectAll}
                className="rounded border-gray-300 text-lavender-500 focus:ring-lavender-500"
              />
              <span className="text-sm text-gray-600">
                {selectedListings.length === 0 
                  ? 'Select listings to bulk edit' 
                  : `${selectedListings.length} of ${listings.length} selected`
                }
              </span>
            </div>
            {selectedListings.length > 0 && (
              <button
                onClick={() => setSelectedListings([])}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear selection
              </button>
            )}
          </div>

          {/* Listings Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {listings.map((listing) => (
              <ListingCard
                key={listing.listing_id}
                listing={listing}
                isSelected={selectedListings.includes(listing.listing_id)}
                onSelect={() => handleSelectListing(listing.listing_id)}
                onEdit={() => handleEditListing(listing)}
              />
            ))}
          </div>
        </>
      )}

      {/* Modals */}
      {showEditModal && editingListing && (
        <EditListingModal
          listing={editingListing}
          onClose={handleModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {showBulkEditModal && (
        <BulkEditModal
          selectedListingIds={selectedListings}
          onClose={handleModalClose}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
};

export default ListingsTab;