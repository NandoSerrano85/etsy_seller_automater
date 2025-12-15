import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { API_BASE_URL } from '../config';

const CraftFlowTemplateCreator = () => {
  const navigate = useNavigate();
  const api = useApi();

  const [templateData, setTemplateData] = useState({
    name: '',
    template_title: '',
    description: '',
    short_description: '',
    product_type: 'physical',
    print_method: 'uvdtf',
    category: 'cup_wraps',
    price: '',
    compare_at_price: '',
    cost: '',
    track_inventory: false,
    inventory_quantity: 0,
    allow_backorder: false,
    digital_file_url: '',
    download_limit: 3,
    meta_title: '',
    meta_description: '',
    is_active: true,
    is_featured: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const productTypes = [
    { value: 'physical', label: 'Physical Product' },
    { value: 'digital', label: 'Digital Product' },
  ];

  const printMethods = [
    { value: 'uvdtf', label: 'UV DTF' },
    { value: 'dtf', label: 'DTF' },
    { value: 'sublimation', label: 'Sublimation' },
    { value: 'vinyl', label: 'Vinyl' },
    { value: 'other', label: 'Other' },
    { value: 'digital', label: 'Digital' },
  ];

  const categories = [
    { value: 'cup_wraps', label: 'Cup Wraps' },
    { value: 'single_square', label: 'Single Square' },
    { value: 'single_rectangle', label: 'Single Rectangle' },
    { value: 'other_custom', label: 'Other Custom' },
  ];

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    setTemplateData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      // Convert string prices to floats
      const payload = {
        ...templateData,
        price: parseFloat(templateData.price),
        compare_at_price: templateData.compare_at_price ? parseFloat(templateData.compare_at_price) : null,
        cost: templateData.cost ? parseFloat(templateData.cost) : null,
      };

      await api.post('/settings/craftflow-commerce-template', payload);
      setSuccess('Template created successfully!');
      setTimeout(() => {
        navigate('/account?tab=templates');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <button
            onClick={() => navigate('/templates/create')}
            className="text-sage-600 hover:text-sage-700 font-medium mb-4"
          >
            ← Back to Platform Selection
          </button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Create CraftFlow Commerce Template</h1>
          <p className="text-gray-600">Create a reusable template for your CraftFlow Commerce products</p>
        </div>

        {error && <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">{error}</div>}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">{success}</div>
        )}

        <form onSubmit={handleSubmit} className="bg-white shadow-lg rounded-lg p-8 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Basic Information</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template Name *</label>
              <input
                type="text"
                name="name"
                value={templateData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                placeholder="e.g., 16oz Cup Wrap Template"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Product Title Template *</label>
              <input
                type="text"
                name="template_title"
                value={templateData.template_title}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                placeholder="e.g., {design_name} - 16oz Cup Wrap"
              />
              <p className="text-sm text-gray-500 mt-1">Use {'{design_name}'} as a placeholder for the design name</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                name="description"
                value={templateData.description}
                onChange={handleChange}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                placeholder="Full product description"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Short Description</label>
              <textarea
                name="short_description"
                value={templateData.short_description}
                onChange={handleChange}
                rows={2}
                maxLength={500}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                placeholder="Brief product description (max 500 characters)"
              />
            </div>
          </div>

          {/* Product Categorization */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Product Categorization</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Type *</label>
                <select
                  name="product_type"
                  value={templateData.product_type}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                >
                  {productTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Print Method *</label>
                <select
                  name="print_method"
                  value={templateData.print_method}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                >
                  {printMethods.map(method => (
                    <option key={method.value} value={method.value}>
                      {method.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select
                  name="category"
                  value={templateData.category}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Pricing</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
                <input
                  type="number"
                  name="price"
                  value={templateData.price}
                  onChange={handleChange}
                  required
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                  placeholder="24.99"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Compare At Price</label>
                <input
                  type="number"
                  name="compare_at_price"
                  value={templateData.compare_at_price}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                  placeholder="29.99"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cost Per Item</label>
                <input
                  type="number"
                  name="cost"
                  value={templateData.cost}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                  placeholder="5.00"
                />
              </div>
            </div>
          </div>

          {/* Inventory */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Inventory</h2>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                name="track_inventory"
                checked={templateData.track_inventory}
                onChange={handleChange}
                className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
              />
              <label className="text-sm font-medium text-gray-700">Track inventory</label>
            </div>

            {templateData.track_inventory && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Inventory Quantity</label>
                  <input
                    type="number"
                    name="inventory_quantity"
                    value={templateData.inventory_quantity}
                    onChange={handleChange}
                    min="0"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    name="allow_backorder"
                    checked={templateData.allow_backorder}
                    onChange={handleChange}
                    className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                  />
                  <label className="text-sm font-medium text-gray-700">Allow backorder</label>
                </div>
              </div>
            )}
          </div>

          {/* Digital Product Settings */}
          {templateData.product_type === 'digital' && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-gray-900">Digital Product Settings</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Digital File URL</label>
                <input
                  type="url"
                  name="digital_file_url"
                  value={templateData.digital_file_url}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                  placeholder="https://..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Download Limit</label>
                <input
                  type="number"
                  name="download_limit"
                  value={templateData.download_limit}
                  onChange={handleChange}
                  min="1"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* SEO */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">SEO</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Meta Title</label>
              <input
                type="text"
                name="meta_title"
                value={templateData.meta_title}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                placeholder="SEO title"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Meta Description</label>
              <textarea
                name="meta_description"
                value={templateData.meta_description}
                onChange={handleChange}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-transparent"
                placeholder="SEO meta description"
              />
            </div>
          </div>

          {/* Status */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Status</h2>

            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={templateData.is_active}
                  onChange={handleChange}
                  className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                />
                <label className="text-sm font-medium text-gray-700">Active</label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_featured"
                  checked={templateData.is_featured}
                  onChange={handleChange}
                  className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                />
                <label className="text-sm font-medium text-gray-700">Featured</label>
              </div>
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-4 pt-6">
            <button
              type="button"
              onClick={() => navigate('/templates/create')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Template'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CraftFlowTemplateCreator;
