import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const EditListingModal = ({ listing, onClose, onSuccess }) => {
  const api = useApi();
  const [formData, setFormData] = useState({
    description: '',
    price: '',
    quantity: '',
    tags: '',
    materials: '',
    taxonomy_id: '',
    shop_section_id: '',
    shipping_profile_id: '',
    item_weight: '',
    item_weight_unit: 'oz',
    item_length: '',
    item_width: '',
    item_height: '',
    item_dimensions_unit: 'in',
    who_made: 'i_did',
    when_made: 'made_to_order',
    processing_min: '',
    processing_max: '',
    is_taxable: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dropdownOptions, setDropdownOptions] = useState({
    taxonomies: [],
    shippingProfiles: [],
    shopSections: [],
  });
  const [dropdownLoading, setDropdownLoading] = useState(true);

  useEffect(() => {
    if (listing) {
      setFormData({
        description: listing.description || '',
        price: listing.price || '',
        quantity: listing.quantity || '',
        tags: listing.tags ? listing.tags.join(', ') : '',
        materials: listing.materials ? listing.materials.join(', ') : '',
        taxonomy_id: listing.taxonomy_id || '',
        shop_section_id: listing.shop_section_id || '',
        shipping_profile_id: listing.shipping_profile_id || '',
        item_weight: listing.item_weight || '',
        item_weight_unit: listing.item_weight_unit || 'oz',
        item_length: listing.item_length || '',
        item_width: listing.item_width || '',
        item_height: listing.item_height || '',
        item_dimensions_unit: listing.item_dimensions_unit || 'in',
        who_made: listing.who_made || 'i_did',
        when_made: listing.when_made || 'made_to_order',
        processing_min: listing.processing_min || '',
        processing_max: listing.processing_max || '',
        is_taxable: listing.is_taxable || false,
      });
    }

    // Fetch dropdown options
    fetchDropdownOptions();
  }, [listing]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchDropdownOptions = async () => {
    setDropdownLoading(true);
    try {
      const [taxonomiesRes, shippingProfilesRes, shopSectionsRes] = await Promise.all([
        api.get('/third-party-listings/options/taxonomies'),
        api.get('/third-party-listings/options/shipping-profiles'),
        api.get('/third-party-listings/options/shop-sections'),
      ]);

      setDropdownOptions({
        taxonomies: taxonomiesRes.taxonomies || [],
        shippingProfiles: shippingProfilesRes.shipping_profiles || [],
        shopSections: shopSectionsRes.shop_sections || [],
      });
    } catch (err) {
      console.error('Error fetching dropdown options:', err);
    } finally {
      setDropdownLoading(false);
    }
  };

  const handleInputChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Prepare the data for submission
      const updateData = {
        ...formData,
        price: formData.price ? parseFloat(formData.price) : undefined,
        quantity: formData.quantity ? parseInt(formData.quantity) : undefined,
        taxonomy_id: formData.taxonomy_id ? parseInt(formData.taxonomy_id) : undefined,
        shop_section_id: formData.shop_section_id ? parseInt(formData.shop_section_id) : undefined,
        shipping_profile_id: formData.shipping_profile_id ? parseInt(formData.shipping_profile_id) : undefined,
        item_weight: formData.item_weight ? parseFloat(formData.item_weight) : undefined,
        item_length: formData.item_length ? parseFloat(formData.item_length) : undefined,
        item_width: formData.item_width ? parseFloat(formData.item_width) : undefined,
        item_height: formData.item_height ? parseFloat(formData.item_height) : undefined,
        processing_min: formData.processing_min ? parseInt(formData.processing_min) : undefined,
        processing_max: formData.processing_max ? parseInt(formData.processing_max) : undefined,
        tags: formData.tags
          ? formData.tags
              .split(',')
              .map(tag => tag.trim())
              .filter(Boolean)
          : undefined,
        materials: formData.materials
          ? formData.materials
              .split(',')
              .map(material => material.trim())
              .filter(Boolean)
          : undefined,
      };

      // Remove undefined values
      Object.keys(updateData).forEach(key => {
        if (updateData[key] === undefined || updateData[key] === '') {
          delete updateData[key];
        }
      });

      await api.patch(`/third-party-listings/${listing.listing_id}`, updateData);
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error updating listing:', err);
      setError(err.message || 'Failed to update listing');
    } finally {
      setLoading(false);
    }
  };

  if (!listing) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Edit Listing</h2>
              <p className="text-gray-600 mt-1">
                {listing.title} (ID: {listing.listing_id})
              </p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">
              ×
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Basic Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                placeholder="Enter listing description..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Price ($)</label>
                <input
                  type="number"
                  name="price"
                  value={formData.price}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleInputChange}
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="0"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags (comma separated)</label>
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                placeholder="tag1, tag2, tag3"
              />
              <p className="text-xs text-gray-500 mt-1">Maximum 13 tags allowed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Materials (comma separated)</label>
              <input
                type="text"
                name="materials"
                value={formData.materials}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                placeholder="material1, material2, material3"
              />
              <p className="text-xs text-gray-500 mt-1">Maximum 13 materials allowed</p>
            </div>
          </div>

          {/* Shop Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Shop Settings</h3>

            {dropdownLoading && (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-lavender-500 mx-auto"></div>
                <p className="text-gray-500 text-sm mt-2">Loading options...</p>
              </div>
            )}

            {!dropdownLoading && (
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category (Taxonomy)</label>
                  <select
                    name="taxonomy_id"
                    value={formData.taxonomy_id}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  >
                    <option value="">Select a category...</option>
                    {dropdownOptions.taxonomies.map(taxonomy => (
                      <option key={taxonomy.id} value={taxonomy.id}>
                        {taxonomy.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Shop Section</label>
                  <select
                    name="shop_section_id"
                    value={formData.shop_section_id}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  >
                    <option value="">Select a section...</option>
                    {dropdownOptions.shopSections.map(section => (
                      <option key={section.id} value={section.id}>
                        {section.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Shipping Profile</label>
                  <select
                    name="shipping_profile_id"
                    value={formData.shipping_profile_id}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  >
                    <option value="">Select a shipping profile...</option>
                    {dropdownOptions.shippingProfiles.map(profile => (
                      <option key={profile.id} value={profile.id}>
                        {profile.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Physical Properties */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Physical Properties</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Weight</label>
                <input
                  type="number"
                  name="item_weight"
                  value={formData.item_weight}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Weight Unit</label>
                <select
                  name="item_weight_unit"
                  value={formData.item_weight_unit}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                >
                  <option value="oz">oz</option>
                  <option value="lb">lb</option>
                  <option value="g">g</option>
                  <option value="kg">kg</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Length</label>
                <input
                  type="number"
                  name="item_length"
                  value={formData.item_length}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Width</label>
                <input
                  type="number"
                  name="item_width"
                  value={formData.item_width}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Height</label>
                <input
                  type="number"
                  name="item_height"
                  value={formData.item_height}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="0.00"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dimensions Unit</label>
              <select
                name="item_dimensions_unit"
                value={formData.item_dimensions_unit}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
              >
                <option value="in">inches</option>
                <option value="cm">cm</option>
                <option value="mm">mm</option>
              </select>
            </div>
          </div>

          {/* Product Details */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Product Details</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Who Made</label>
                <select
                  name="who_made"
                  value={formData.who_made}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                >
                  <option value="i_did">I did</option>
                  <option value="someone_else">Someone else</option>
                  <option value="collective">A member of my shop</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">When Made</label>
                <select
                  name="when_made"
                  value={formData.when_made}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                >
                  <option value="made_to_order">Made to order</option>
                  <option value="2020_2023">2020-2023</option>
                  <option value="2010_2019">2010-2019</option>
                  <option value="2000_2009">2000-2009</option>
                  <option value="1990s">1990s</option>
                  <option value="1980s">1980s</option>
                  <option value="1970s">1970s</option>
                  <option value="1960s">1960s</option>
                  <option value="1950s">1950s</option>
                  <option value="1940s">1940s</option>
                  <option value="1930s">1930s</option>
                  <option value="1920s">1920s</option>
                  <option value="1910s">1910s</option>
                  <option value="1900s">1900s</option>
                  <option value="1800s">1800s</option>
                  <option value="1700s">1700s</option>
                  <option value="before_1700">Before 1700</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Processing Time Min (days)</label>
                <input
                  type="number"
                  name="processing_min"
                  value={formData.processing_min}
                  onChange={handleInputChange}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Processing Time Max (days)</label>
                <input
                  type="number"
                  name="processing_max"
                  value={formData.processing_max}
                  onChange={handleInputChange}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  placeholder="7"
                />
              </div>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_taxable"
                  checked={formData.is_taxable}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-lavender-500 focus:ring-lavender-500"
                />
                <span className="ml-2 text-sm text-gray-700">This item is taxable</span>
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-lavender-500 text-white rounded-lg hover:bg-lavender-600 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditListingModal;
