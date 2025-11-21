import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import { useNavigate } from 'react-router-dom';
import { useShopify } from '../hooks/useShopify';
import {
  ArrowLeftIcon,
  PlusCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const ShopifyBulkProductCreator = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();
  const { isConnected, store } = useShopify();

  const [loading, setLoading] = useState(false);
  const [creationResult, setCreationResult] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    quantity: 10,
    name_prefix: 'Product-',
    starting_number: 1,
    name_postfix: '',
    description: '',
    price: 25.0,
    vendor: 'Custom Design Store',
    product_type: '',
    tags: '',
    status: 'draft',
    inventory_quantity: 0,
    track_inventory: true,
  });

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validation
    if (!formData.quantity || formData.quantity <= 0) {
      addNotification('Please enter a valid quantity', 'error');
      return;
    }

    if (!formData.name_prefix && !formData.name_postfix) {
      addNotification('Please enter at least a prefix or postfix for product names', 'error');
      return;
    }

    if (!formData.price || formData.price <= 0) {
      addNotification('Please enter a valid price', 'error');
      return;
    }

    setLoading(true);
    setCreationResult(null);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/shopify/products/bulk-create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          quantity: parseInt(formData.quantity),
          name_prefix: formData.name_prefix,
          starting_number: parseInt(formData.starting_number),
          name_postfix: formData.name_postfix,
          description: formData.description,
          price: parseFloat(formData.price),
          vendor: formData.vendor,
          product_type: formData.product_type,
          tags: formData.tags,
          status: formData.status,
          inventory_quantity: parseInt(formData.inventory_quantity),
          track_inventory: formData.track_inventory,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setCreationResult(data);
        addNotification(data.message, 'success');
      } else {
        throw new Error(data.detail || 'Failed to create products');
      }
    } catch (error) {
      console.error('Error creating products:', error);
      addNotification(error.message || 'Failed to create products', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Generate preview of product names
  const generatePreview = () => {
    const names = [];
    const previewCount = Math.min(formData.quantity, 5);

    for (let i = 0; i < previewCount; i++) {
      const num = parseInt(formData.starting_number) + i;
      names.push(`${formData.name_prefix}${num}${formData.name_postfix}`);
    }

    if (formData.quantity > 5) {
      names.push('...');
    }

    return names;
  };

  if (!isConnected) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Store Connected</h2>
          <p className="text-gray-600 mb-6">Please connect your Shopify store to create products.</p>
          <button
            onClick={() => navigate('/account?tab=integrations')}
            className="bg-sage-600 text-white px-6 py-2 rounded-md hover:bg-sage-700"
          >
            Go to Integrations
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/shopify/products')}
            className="flex items-center text-sage-600 hover:text-sage-700 mb-4"
          >
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            Back to Products
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Bulk Create Products</h1>
          <p className="text-gray-600">Create multiple products with auto-generated names</p>
        </div>

        {/* Success Result */}
        {creationResult && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex items-start">
              <CheckCircleIcon className="w-6 h-6 text-green-500 mr-3 mt-1" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Products Created Successfully</h3>
                <p className="text-gray-600 mb-4">{creationResult.message}</p>

                {creationResult.errors && creationResult.errors.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-yellow-800 mb-2">Some products failed to create:</h4>
                    <ul className="list-disc list-inside text-sm text-yellow-700">
                      {creationResult.errors.map((error, idx) => (
                        <li key={idx}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex space-x-3">
                  <button
                    onClick={() => navigate('/shopify/products')}
                    className="bg-sage-600 text-white px-4 py-2 rounded-md hover:bg-sage-700"
                  >
                    View Products
                  </button>
                  <button
                    onClick={() => setCreationResult(null)}
                    className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
                  >
                    Create More
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex items-center mb-6">
              <SparklesIcon className="w-6 h-6 text-sage-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Name Generation Settings</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quantity <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  min="1"
                  max="100"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
                <p className="text-xs text-gray-500 mt-1">Number of products to create (max 100)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Starting Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="starting_number"
                  value={formData.starting_number}
                  onChange={handleChange}
                  min="0"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
                <p className="text-xs text-gray-500 mt-1">First number in the sequence</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name Prefix</label>
                <input
                  type="text"
                  name="name_prefix"
                  value={formData.name_prefix}
                  onChange={handleChange}
                  placeholder="Product-"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
                <p className="text-xs text-gray-500 mt-1">Fixed text before the number</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name Postfix</label>
                <input
                  type="text"
                  name="name_postfix"
                  value={formData.name_postfix}
                  onChange={handleChange}
                  placeholder=" - Edition"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
                <p className="text-xs text-gray-500 mt-1">Fixed text after the number</p>
              </div>
            </div>

            {/* Name Preview */}
            <div className="bg-sage-50 border border-sage-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-sage-900 mb-2">Preview of Generated Names:</h3>
              <div className="space-y-1">
                {generatePreview().map((name, idx) => (
                  <div key={idx} className="text-sm text-sage-700 font-mono">
                    {name}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Product Details */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Product Details</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Price <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleChange}
                    step="0.01"
                    min="0.01"
                    required
                    className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Vendor</label>
                <input
                  type="text"
                  name="vendor"
                  value={formData.vendor}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Product Type</label>
                <input
                  type="text"
                  name="product_type"
                  value={formData.product_type}
                  onChange={handleChange}
                  placeholder="e.g., T-Shirt, Mug, Print"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                <input
                  type="text"
                  name="tags"
                  value={formData.tags}
                  onChange={handleChange}
                  placeholder="tag1, tag2, tag3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
                <p className="text-xs text-gray-500 mt-1">Comma-separated tags</p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows="4"
                  placeholder="Enter product description..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
              </div>
            </div>
          </div>

          {/* Inventory Settings */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Inventory Settings</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="track_inventory"
                    checked={formData.track_inventory}
                    onChange={handleChange}
                    className="rounded border-gray-300 text-sage-600 focus:ring-sage-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Track inventory quantity</span>
                </label>
              </div>

              {formData.track_inventory && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Initial Inventory Quantity</label>
                  <input
                    type="number"
                    name="inventory_quantity"
                    value={formData.inventory_quantity}
                    onChange={handleChange}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={() => navigate('/shopify/products')}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center px-6 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating Products...
                </>
              ) : (
                <>
                  <PlusCircleIcon className="w-4 h-4 mr-2" />
                  Create {formData.quantity} Products
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ShopifyBulkProductCreator;
