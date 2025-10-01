import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useNotifications } from '../components/NotificationSystem';
import {
  PlusIcon,
  ArrowLeftIcon,
  DocumentTextIcon,
  CurrencyDollarIcon,
  TagIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

const ShopifyTemplateCreator = () => {
  const navigate = useNavigate();
  const api = useApi();
  const { addNotification } = useNotifications();

  const [formData, setFormData] = useState({
    name: '',
    template_title: '',
    description: '',
    price: '',
    template_type: 'physical',
    tags: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Template name is required';
    }

    if (!formData.template_title.trim()) {
      newErrors.template_title = 'Product title is required';
    }

    if (!formData.price || parseFloat(formData.price) <= 0) {
      newErrors.price = 'Valid price is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('name', formData.name);
      formDataToSend.append('template_title', formData.template_title);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('price', formData.price);
      formDataToSend.append('template_type', formData.template_type);
      formDataToSend.append('tags', formData.tags);

      const response = await api.post('/api/shopify/templates', formDataToSend);

      addNotification('Template created successfully!', 'success');
      navigate('/shopify/products/create');
    } catch (error) {
      console.error('Error creating template:', error);
      addNotification(error.message || 'Failed to create template', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/shopify/products/create')}
            className="flex items-center text-sage-600 hover:text-sage-700 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Product Creator
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Create Product Template</h1>
          <p className="mt-2 text-gray-600">
            Create a reusable template for your Shopify products. This template can be used to quickly create products
            with consistent settings.
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Template Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Template Name *
              </label>
              <div className="relative">
                <DocumentTextIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g., UVDTF Standard Template"
                  className={`w-full pl-10 pr-4 py-2 border ${
                    errors.name ? 'border-red-500' : 'border-gray-300'
                  } rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500`}
                />
              </div>
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
              <p className="mt-1 text-xs text-gray-500">Internal name for this template (not shown to customers)</p>
            </div>

            {/* Product Title */}
            <div>
              <label htmlFor="template_title" className="block text-sm font-medium text-gray-700 mb-2">
                Product Title Template *
              </label>
              <input
                type="text"
                id="template_title"
                name="template_title"
                value={formData.template_title}
                onChange={handleChange}
                placeholder="e.g., Custom UVDTF Transfer - {design_name}"
                className={`w-full px-4 py-2 border ${
                  errors.template_title ? 'border-red-500' : 'border-gray-300'
                } rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500`}
              />
              {errors.template_title && <p className="mt-1 text-sm text-red-600">{errors.template_title}</p>}
              <p className="mt-1 text-xs text-gray-500">Use {'{design_name}'} as a placeholder for the design name</p>
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Product Description
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={4}
                placeholder="Enter product description template..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
              />
              <p className="mt-1 text-xs text-gray-500">Default description for products created with this template</p>
            </div>

            {/* Price */}
            <div>
              <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-2">
                Default Price *
              </label>
              <div className="relative">
                <CurrencyDollarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="number"
                  id="price"
                  name="price"
                  value={formData.price}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  className={`w-full pl-10 pr-4 py-2 border ${
                    errors.price ? 'border-red-500' : 'border-gray-300'
                  } rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500`}
                />
              </div>
              {errors.price && <p className="mt-1 text-sm text-red-600">{errors.price}</p>}
            </div>

            {/* Product Type */}
            <div>
              <label htmlFor="template_type" className="block text-sm font-medium text-gray-700 mb-2">
                Product Type
              </label>
              <select
                id="template_type"
                name="template_type"
                value={formData.template_type}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
              >
                <option value="physical">Physical Product</option>
                <option value="digital">Digital Product</option>
              </select>
            </div>

            {/* Tags */}
            <div>
              <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <div className="relative">
                <TagIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  id="tags"
                  name="tags"
                  value={formData.tags}
                  onChange={handleChange}
                  placeholder="e.g., UVDTF, Custom, Transfer"
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">Comma-separated tags for categorization</p>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex">
                <CheckCircleIcon className="w-5 h-5 text-blue-500 mr-3 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <h4 className="font-medium mb-1">Template Benefits</h4>
                  <ul className="list-disc list-inside space-y-1 text-blue-700">
                    <li>Reuse product settings across multiple designs</li>
                    <li>Maintain consistent pricing and descriptions</li>
                    <li>Speed up product creation workflow</li>
                    <li>Easy to update settings for all future products</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4 pt-6 border-t">
              <button
                type="button"
                onClick={() => navigate('/shopify/products/create')}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center px-6 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <PlusIcon className="w-5 h-5 mr-2" />
                    Create Template
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ShopifyTemplateCreator;
