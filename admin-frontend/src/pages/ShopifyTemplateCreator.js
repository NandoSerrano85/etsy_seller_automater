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
  TruckIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ShoppingBagIcon,
} from '@heroicons/react/24/outline';

const ShopifyTemplateCreator = () => {
  const navigate = useNavigate();
  const api = useApi();
  const { addNotification } = useNotifications();

  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Template metadata
    name: '',
    template_title: '',
    description: '',

    // Pricing
    price: '',
    compare_at_price: '',
    cost_per_item: '',

    // Product details
    vendor: '',
    product_type: '',
    tags: '',

    // Inventory & Shipping
    sku_prefix: '',
    barcode_prefix: '',
    track_inventory: true,
    inventory_quantity: '0',
    inventory_policy: 'deny',
    fulfillment_service: 'manual',
    requires_shipping: true,
    weight: '',
    weight_unit: 'g',

    // Product variants
    has_variants: false,
    option1_name: '',
    option1_values: '',
    option2_name: '',
    option2_values: '',
    option3_name: '',
    option3_values: '',

    // Publishing & SEO
    status: 'draft',
    published_scope: 'web',
    seo_title: '',
    seo_description: '',

    // Tax settings
    is_taxable: true,
    tax_code: '',

    // Additional settings
    gift_card: false,
    template_suffix: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateStep = stepNumber => {
    const newErrors = {};

    if (stepNumber === 1) {
      if (!formData.name.trim()) {
        newErrors.name = 'Template name is required';
      }
      if (!formData.template_title.trim()) {
        newErrors.template_title = 'Product title is required';
      }
    }

    if (stepNumber === 2) {
      if (!formData.price || parseFloat(formData.price) <= 0) {
        newErrors.price = 'Valid price is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 5));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!validateStep(1) || !validateStep(2)) {
      setCurrentStep(1);
      return;
    }

    setLoading(true);

    try {
      const formDataToSend = new FormData();

      // Add all form fields
      Object.keys(formData).forEach(key => {
        const value = formData[key];
        if (value !== '' && value !== null && value !== undefined) {
          formDataToSend.append(key, value);
        }
      });

      await api.post('/api/shopify/templates', formDataToSend);

      addNotification('Shopify template created successfully!', 'success');
      navigate('/shopify/products/create');
    } catch (error) {
      console.error('Error creating template:', error);
      addNotification(error.message || 'Failed to create template', 'error');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { number: 1, name: 'Basic Info', icon: DocumentTextIcon },
    { number: 2, name: 'Pricing', icon: CurrencyDollarIcon },
    { number: 3, name: 'Inventory & Shipping', icon: TruckIcon },
    { number: 4, name: 'Variants & Options', icon: Cog6ToothIcon },
    { number: 5, name: 'SEO & Publishing', icon: ChartBarIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/templates/create')}
            className="flex items-center text-sage-600 hover:text-sage-700 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Platform Selection
          </button>
          <div className="flex items-center mb-4">
            <ShoppingBagIcon className="w-10 h-10 text-green-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Create Shopify Template</h1>
              <p className="text-gray-600">Configure a reusable template for your Shopify products</p>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.number} className="flex-1">
                <div className="flex items-center">
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                      currentStep === step.number
                        ? 'border-sage-600 bg-sage-600 text-white'
                        : currentStep > step.number
                          ? 'border-sage-600 bg-sage-600 text-white'
                          : 'border-gray-300 bg-white text-gray-400'
                    }`}
                  >
                    <step.icon className="w-5 h-5" />
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`flex-1 h-1 mx-2 ${currentStep > step.number ? 'bg-sage-600' : 'bg-gray-300'}`} />
                  )}
                </div>
                <p className="text-xs text-center mt-2 hidden sm:block">{step.name}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit}>
            {/* Step 1: Basic Info */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>

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
                      placeholder="e.g., UVDTF Standard Product"
                      className={`w-full pl-10 pr-4 py-2 border ${
                        errors.name ? 'border-red-500' : 'border-gray-300'
                      } rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500`}
                    />
                  </div>
                  {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
                  <p className="mt-1 text-xs text-gray-500">Internal name for this template</p>
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
                  <p className="mt-1 text-xs text-gray-500">Use {'{design_name}'} as a placeholder</p>
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
                    placeholder="Enter product description..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  />
                </div>

                {/* Vendor */}
                <div>
                  <label htmlFor="vendor" className="block text-sm font-medium text-gray-700 mb-2">
                    Vendor
                  </label>
                  <input
                    type="text"
                    id="vendor"
                    name="vendor"
                    value={formData.vendor}
                    onChange={handleChange}
                    placeholder="e.g., Custom Design Store"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  />
                </div>

                {/* Product Type */}
                <div>
                  <label htmlFor="product_type" className="block text-sm font-medium text-gray-700 mb-2">
                    Product Type
                  </label>
                  <input
                    type="text"
                    id="product_type"
                    name="product_type"
                    value={formData.product_type}
                    onChange={handleChange}
                    placeholder="e.g., Transfer, Decal, Sticker"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  />
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
                  <p className="mt-1 text-xs text-gray-500">Comma-separated tags</p>
                </div>
              </div>
            )}

            {/* Step 2: Pricing */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Pricing</h2>

                {/* Price */}
                <div>
                  <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-2">
                    Price *
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

                {/* Compare At Price */}
                <div>
                  <label htmlFor="compare_at_price" className="block text-sm font-medium text-gray-700 mb-2">
                    Compare At Price
                  </label>
                  <div className="relative">
                    <CurrencyDollarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="number"
                      id="compare_at_price"
                      name="compare_at_price"
                      value={formData.compare_at_price}
                      onChange={handleChange}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Show as "original price" for sales</p>
                </div>

                {/* Cost Per Item */}
                <div>
                  <label htmlFor="cost_per_item" className="block text-sm font-medium text-gray-700 mb-2">
                    Cost Per Item
                  </label>
                  <div className="relative">
                    <CurrencyDollarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="number"
                      id="cost_per_item"
                      name="cost_per_item"
                      value={formData.cost_per_item}
                      onChange={handleChange}
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Your cost for this item (for profit tracking)</p>
                </div>

                {/* Tax Settings */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Tax Settings</h3>

                  <div className="flex items-center mb-4">
                    <input
                      type="checkbox"
                      id="is_taxable"
                      name="is_taxable"
                      checked={formData.is_taxable}
                      onChange={handleChange}
                      className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_taxable" className="ml-2 block text-sm text-gray-700">
                      Charge tax on this product
                    </label>
                  </div>

                  <div>
                    <label htmlFor="tax_code" className="block text-sm font-medium text-gray-700 mb-2">
                      Tax Code
                    </label>
                    <input
                      type="text"
                      id="tax_code"
                      name="tax_code"
                      value={formData.tax_code}
                      onChange={handleChange}
                      placeholder="Optional tax code"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Inventory & Shipping */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Inventory & Shipping</h2>

                {/* SKU Prefix */}
                <div>
                  <label htmlFor="sku_prefix" className="block text-sm font-medium text-gray-700 mb-2">
                    SKU Prefix
                  </label>
                  <input
                    type="text"
                    id="sku_prefix"
                    name="sku_prefix"
                    value={formData.sku_prefix}
                    onChange={handleChange}
                    placeholder="e.g., UVDTF-"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Prefix for auto-generated SKUs</p>
                </div>

                {/* Barcode Prefix */}
                <div>
                  <label htmlFor="barcode_prefix" className="block text-sm font-medium text-gray-700 mb-2">
                    Barcode Prefix
                  </label>
                  <input
                    type="text"
                    id="barcode_prefix"
                    name="barcode_prefix"
                    value={formData.barcode_prefix}
                    onChange={handleChange}
                    placeholder="e.g., UPC-"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  />
                </div>

                {/* Track Inventory */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="track_inventory"
                    name="track_inventory"
                    checked={formData.track_inventory}
                    onChange={handleChange}
                    className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                  />
                  <label htmlFor="track_inventory" className="ml-2 block text-sm text-gray-700">
                    Track inventory for this product
                  </label>
                </div>

                {/* Inventory Quantity */}
                <div>
                  <label htmlFor="inventory_quantity" className="block text-sm font-medium text-gray-700 mb-2">
                    Default Inventory Quantity
                  </label>
                  <input
                    type="number"
                    id="inventory_quantity"
                    name="inventory_quantity"
                    value={formData.inventory_quantity}
                    onChange={handleChange}
                    min="0"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  />
                </div>

                {/* Inventory Policy */}
                <div>
                  <label htmlFor="inventory_policy" className="block text-sm font-medium text-gray-700 mb-2">
                    When Sold Out
                  </label>
                  <select
                    id="inventory_policy"
                    name="inventory_policy"
                    value={formData.inventory_policy}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  >
                    <option value="deny">Stop selling when out of stock</option>
                    <option value="continue">Continue selling when out of stock</option>
                  </select>
                </div>

                {/* Shipping */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Shipping</h3>

                  <div className="flex items-center mb-4">
                    <input
                      type="checkbox"
                      id="requires_shipping"
                      name="requires_shipping"
                      checked={formData.requires_shipping}
                      onChange={handleChange}
                      className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                    />
                    <label htmlFor="requires_shipping" className="ml-2 block text-sm text-gray-700">
                      This product requires shipping
                    </label>
                  </div>

                  {formData.requires_shipping && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-2">
                            Weight
                          </label>
                          <input
                            type="number"
                            id="weight"
                            name="weight"
                            value={formData.weight}
                            onChange={handleChange}
                            step="0.01"
                            min="0"
                            placeholder="0.00"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                        <div>
                          <label htmlFor="weight_unit" className="block text-sm font-medium text-gray-700 mb-2">
                            Unit
                          </label>
                          <select
                            id="weight_unit"
                            name="weight_unit"
                            value={formData.weight_unit}
                            onChange={handleChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          >
                            <option value="g">Grams (g)</option>
                            <option value="kg">Kilograms (kg)</option>
                            <option value="oz">Ounces (oz)</option>
                            <option value="lb">Pounds (lb)</option>
                          </select>
                        </div>
                      </div>

                      <div className="mt-4">
                        <label htmlFor="fulfillment_service" className="block text-sm font-medium text-gray-700 mb-2">
                          Fulfillment Service
                        </label>
                        <select
                          id="fulfillment_service"
                          name="fulfillment_service"
                          value={formData.fulfillment_service}
                          onChange={handleChange}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                        >
                          <option value="manual">Manual</option>
                          <option value="shipstation">ShipStation</option>
                          <option value="amazon">Amazon FBA</option>
                        </select>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Step 4: Variants & Options */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Product Variants & Options</h2>

                <div className="flex items-center mb-6">
                  <input
                    type="checkbox"
                    id="has_variants"
                    name="has_variants"
                    checked={formData.has_variants}
                    onChange={handleChange}
                    className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                  />
                  <label htmlFor="has_variants" className="ml-2 block text-sm text-gray-700">
                    This product has multiple options (e.g., size, color)
                  </label>
                </div>

                {formData.has_variants && (
                  <>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <p className="text-sm text-blue-800">
                        Define up to 3 option types (e.g., Size, Color, Material). Enter values separated by commas.
                      </p>
                    </div>

                    {/* Option 1 */}
                    <div className="border-b pb-6">
                      <h3 className="text-md font-semibold text-gray-900 mb-3">Option 1</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="option1_name" className="block text-sm font-medium text-gray-700 mb-2">
                            Option Name
                          </label>
                          <input
                            type="text"
                            id="option1_name"
                            name="option1_name"
                            value={formData.option1_name}
                            onChange={handleChange}
                            placeholder="e.g., Size"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                        <div>
                          <label htmlFor="option1_values" className="block text-sm font-medium text-gray-700 mb-2">
                            Values (comma-separated)
                          </label>
                          <input
                            type="text"
                            id="option1_values"
                            name="option1_values"
                            value={formData.option1_values}
                            onChange={handleChange}
                            placeholder="e.g., Small, Medium, Large"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Option 2 */}
                    <div className="border-b pb-6">
                      <h3 className="text-md font-semibold text-gray-900 mb-3">Option 2 (Optional)</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="option2_name" className="block text-sm font-medium text-gray-700 mb-2">
                            Option Name
                          </label>
                          <input
                            type="text"
                            id="option2_name"
                            name="option2_name"
                            value={formData.option2_name}
                            onChange={handleChange}
                            placeholder="e.g., Color"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                        <div>
                          <label htmlFor="option2_values" className="block text-sm font-medium text-gray-700 mb-2">
                            Values (comma-separated)
                          </label>
                          <input
                            type="text"
                            id="option2_values"
                            name="option2_values"
                            value={formData.option2_values}
                            onChange={handleChange}
                            placeholder="e.g., Red, Blue, Green"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Option 3 */}
                    <div>
                      <h3 className="text-md font-semibold text-gray-900 mb-3">Option 3 (Optional)</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="option3_name" className="block text-sm font-medium text-gray-700 mb-2">
                            Option Name
                          </label>
                          <input
                            type="text"
                            id="option3_name"
                            name="option3_name"
                            value={formData.option3_name}
                            onChange={handleChange}
                            placeholder="e.g., Material"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                        <div>
                          <label htmlFor="option3_values" className="block text-sm font-medium text-gray-700 mb-2">
                            Values (comma-separated)
                          </label>
                          <input
                            type="text"
                            id="option3_values"
                            name="option3_values"
                            value={formData.option3_values}
                            onChange={handleChange}
                            placeholder="e.g., Cotton, Polyester"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                          />
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {!formData.has_variants && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                    <p className="text-gray-600">
                      This product will have no variants. Enable variants above if you need multiple options like size
                      or color.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Step 5: SEO & Publishing */}
            {currentStep === 5 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">SEO & Publishing</h2>

                {/* Status */}
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
                    Product Status
                  </label>
                  <select
                    id="status"
                    name="status"
                    value={formData.status}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Default status for products created with this template</p>
                </div>

                {/* Published Scope */}
                <div>
                  <label htmlFor="published_scope" className="block text-sm font-medium text-gray-700 mb-2">
                    Sales Channel
                  </label>
                  <select
                    id="published_scope"
                    name="published_scope"
                    value={formData.published_scope}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                  >
                    <option value="web">Online Store</option>
                    <option value="global">All Sales Channels</option>
                  </select>
                </div>

                {/* SEO Title */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Search Engine Optimization</h3>

                  <div>
                    <label htmlFor="seo_title" className="block text-sm font-medium text-gray-700 mb-2">
                      SEO Title
                    </label>
                    <input
                      type="text"
                      id="seo_title"
                      name="seo_title"
                      value={formData.seo_title}
                      onChange={handleChange}
                      placeholder="Leave blank to use product title"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">{formData.seo_title.length}/70 characters recommended</p>
                  </div>

                  <div className="mt-4">
                    <label htmlFor="seo_description" className="block text-sm font-medium text-gray-700 mb-2">
                      SEO Description
                    </label>
                    <textarea
                      id="seo_description"
                      name="seo_description"
                      value={formData.seo_description}
                      onChange={handleChange}
                      rows={3}
                      placeholder="Enter meta description for search engines..."
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      {formData.seo_description.length}/160 characters recommended
                    </p>
                  </div>
                </div>

                {/* Additional Settings */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Settings</h3>

                  <div className="flex items-center mb-4">
                    <input
                      type="checkbox"
                      id="gift_card"
                      name="gift_card"
                      checked={formData.gift_card}
                      onChange={handleChange}
                      className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                    />
                    <label htmlFor="gift_card" className="ml-2 block text-sm text-gray-700">
                      This is a gift card
                    </label>
                  </div>

                  <div>
                    <label htmlFor="template_suffix" className="block text-sm font-medium text-gray-700 mb-2">
                      Theme Template Suffix
                    </label>
                    <input
                      type="text"
                      id="template_suffix"
                      name="template_suffix"
                      value={formData.template_suffix}
                      onChange={handleChange}
                      placeholder="e.g., custom"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">Advanced: Use alternate product page template</p>
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex">
                    <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-green-800">
                      <h4 className="font-medium mb-1">Ready to Create Template</h4>
                      <p className="text-green-700">
                        Your Shopify product template is configured and ready to be saved. You can use this template to
                        quickly create products with consistent settings.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6 border-t mt-8">
              <button
                type="button"
                onClick={handlePrevious}
                disabled={currentStep === 1}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>

              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => navigate('/shopify/products/create')}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>

                {currentStep < 5 ? (
                  <button
                    type="button"
                    onClick={handleNext}
                    className="px-6 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 transition-colors"
                  >
                    Next
                  </button>
                ) : (
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
                )}
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ShopifyTemplateCreator;
