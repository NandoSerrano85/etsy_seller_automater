import React from 'react';

const ListingCard = ({ listing, isSelected, onSelect, onEdit }) => {
  const formatPrice = (price) => {
    if (!price) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  const getStateColor = (state) => {
    switch (state) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const truncateTitle = (title, maxLength = 50) => {
    if (!title) return 'Untitled Listing';
    return title.length > maxLength ? `${title.substring(0, maxLength)}...` : title;
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border-2 transition-all duration-200 hover:shadow-md ${
      isSelected ? 'border-lavender-500 bg-lavender-50' : 'border-gray-200 hover:border-gray-300'
    }`}>
      {/* Image Section */}
      <div className="relative">
        {listing.default_image_url ? (
          <img 
            src={listing.default_image_url} 
            alt={listing.title || 'Listing image'}
            className="w-full h-48 object-cover rounded-t-lg"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : null}
        
        {/* Fallback when no image or image fails to load */}
        <div 
          className={`w-full h-48 bg-gray-100 rounded-t-lg flex items-center justify-center ${
            listing.default_image_url ? 'hidden' : 'flex'
          }`}
        >
          <div className="text-center text-gray-400">
            <span className="text-4xl mb-2 block">📷</span>
            <span className="text-sm">No Image</span>
          </div>
        </div>

        {/* Selection Checkbox */}
        <div className="absolute top-3 left-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            className="w-5 h-5 rounded border-gray-300 text-lavender-500 focus:ring-lavender-500 bg-white shadow-sm"
          />
        </div>

        {/* State Badge */}
        <div className="absolute top-3 right-3">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStateColor(listing.state)}`}>
            {listing.state || 'unknown'}
          </span>
        </div>
      </div>

      {/* Content Section */}
      <div className="p-4">
        <div className="mb-3">
          <h3 className="font-semibold text-gray-900 text-sm leading-tight mb-1">
            {truncateTitle(listing.title)}
          </h3>
          <div className="flex items-center justify-between text-sm">
            <span className="text-lg font-bold text-gray-900">
              {formatPrice(listing.price)}
            </span>
            <span className="text-gray-500">
              Qty: {listing.quantity || 0}
            </span>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mb-3 text-xs text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>ID:</span>
            <span>{listing.listing_id}</span>
          </div>
          {listing.tags && listing.tags.length > 0 && (
            <div className="flex justify-between">
              <span>Tags:</span>
              <span>{listing.tags.length}</span>
            </div>
          )}
          {listing.taxonomy_id && (
            <div className="flex justify-between">
              <span>Category:</span>
              <span>{listing.taxonomy_id}</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="flex-1 px-3 py-2 bg-lavender-500 text-white text-sm rounded-lg hover:bg-lavender-600 transition-colors"
          >
            Edit
          </button>
          <a
            href={`https://www.etsy.com/listing/${listing.listing_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors"
          >
            <span className="text-xs">🔗</span>
          </a>
        </div>
      </div>
    </div>
  );
};

export default ListingCard;