import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import { ChevronRightIcon, PhotoIcon, CubeIcon, SparklesIcon, PlusIcon } from '@heroicons/react/24/outline';

const ShopifyProductCreator = () => {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const { addNotification } = useNotifications();

  const [currentStep, setCurrentStep] = useState(1);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [designFiles, setDesignFiles] = useState([]);
  const [mockupPreview, setMockupPreview] = useState(null);
  const [productDetails, setProductDetails] = useState({
    title: '',
    description: '',
    price: 25.0,
    vendor: 'Custom Design Store',
    tags: '',
    variants: [],
  });
  const [loading, setLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const steps = [
    { id: 1, name: 'Select Template', icon: CubeIcon },
    { id: 2, name: 'Upload Design', icon: PhotoIcon },
    { id: 3, name: 'Preview Mockup', icon: SparklesIcon },
    { id: 4, name: 'Product Details', icon: ChevronRightIcon },
    { id: 5, name: 'Create Product', icon: SparklesIcon },
  ];

  // Fetch available templates
  useEffect(() => {
    const fetchTemplates = async () => {
      if (!token) return;

      try {
        setLoading(true);
        const response = await fetch('/api/shopify/templates', {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          setTemplates(data.templates || []);
        } else {
          throw new Error('Failed to fetch templates');
        }
      } catch (error) {
        console.error('Error fetching templates:', error);
        addNotification('Failed to load templates', 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleTemplateSelect = template => {
    setSelectedTemplate(template);
    setCurrentStep(2);
  };

  const handleFileUpload = files => {
    setDesignFiles(Array.from(files));
    if (files.length > 0) {
      setCurrentStep(3);
    }
  };

  const generatePreview = async () => {
    if (!selectedTemplate || designFiles.length === 0) return;

    try {
      setLoading(true);
      const formData = new FormData();
      designFiles.forEach(file => {
        formData.append('design_files', file);
      });

      const response = await fetch(`/api/shopify/templates/${selectedTemplate.id}/preview`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setMockupPreview(data);
        setCurrentStep(4);
        addNotification('Preview generated successfully!', 'success');
      } else {
        throw new Error('Failed to generate preview');
      }
    } catch (error) {
      console.error('Error generating preview:', error);
      addNotification('Failed to generate preview', 'error');
    } finally {
      setLoading(false);
    }
  };

  const createProduct = async () => {
    if (!selectedTemplate || designFiles.length === 0 || !productDetails.title) {
      addNotification('Please fill in all required fields', 'error');
      return;
    }

    try {
      setIsCreating(true);
      const formData = new FormData();

      // Add product details
      formData.append('template_id', selectedTemplate.id);
      formData.append('title', productDetails.title);
      formData.append('description', productDetails.description);
      formData.append('price', productDetails.price);
      formData.append('vendor', productDetails.vendor);
      formData.append('tags', productDetails.tags);
      formData.append('variants', JSON.stringify(productDetails.variants));

      // Add design files
      designFiles.forEach(file => {
        formData.append('design_files', file);
      });

      const response = await fetch('/api/shopify/products/from-template', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        addNotification('Product created successfully in Shopify!', 'success');
        setCurrentStep(5);

        // Reset form for next product
        setTimeout(() => {
          setCurrentStep(1);
          setSelectedTemplate(null);
          setDesignFiles([]);
          setMockupPreview(null);
          setProductDetails({
            title: '',
            description: '',
            price: 25.0,
            vendor: 'Custom Design Store',
            tags: '',
            variants: [],
          });
        }, 3000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create product');
      }
    } catch (error) {
      console.error('Error creating product:', error);
      addNotification(error.message, 'error');
    } finally {
      setIsCreating(false);
    }
  };

  if (loading && currentStep === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600 mx-auto"></div>
          <p className="mt-4 text-sage-600">Loading templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-sage-800 mb-2">Create Shopify Product</h1>
          <p className="text-sage-600">Design and create products using templates</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;

              return (
                <div key={step.id} className="flex items-center">
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                      isActive
                        ? 'border-sage-600 bg-sage-100 text-sage-600'
                        : isCompleted
                          ? 'border-sage-600 bg-sage-600 text-white'
                          : 'border-gray-300 bg-white text-gray-400'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span
                    className={`ml-2 text-sm font-medium ${
                      isActive || isCompleted ? 'text-sage-600' : 'text-gray-400'
                    }`}
                  >
                    {step.name}
                  </span>
                  {index < steps.length - 1 && (
                    <div className={`ml-4 flex-1 h-0.5 ${isCompleted ? 'bg-sage-600' : 'bg-gray-300'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Step 1: Template Selection */}
          {currentStep === 1 && (
            <TemplateSelection templates={templates} onSelect={handleTemplateSelect} loading={loading} />
          )}

          {/* Step 2: Design Upload */}
          {currentStep === 2 && (
            <DesignUpload selectedTemplate={selectedTemplate} onUpload={handleFileUpload} designFiles={designFiles} />
          )}

          {/* Step 3: Preview Generation */}
          {currentStep === 3 && (
            <PreviewGeneration
              selectedTemplate={selectedTemplate}
              designFiles={designFiles}
              mockupPreview={mockupPreview}
              onGeneratePreview={generatePreview}
              loading={loading}
            />
          )}

          {/* Step 4: Product Details */}
          {currentStep === 4 && (
            <ProductDetailsForm
              productDetails={productDetails}
              setProductDetails={setProductDetails}
              selectedTemplate={selectedTemplate}
              onNext={() => setCurrentStep(5)}
            />
          )}

          {/* Step 5: Create Product */}
          {currentStep === 5 && (
            <ProductCreation
              productDetails={productDetails}
              selectedTemplate={selectedTemplate}
              mockupPreview={mockupPreview}
              onCreateProduct={createProduct}
              isCreating={isCreating}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// Template Selection Component
const TemplateSelection = ({ templates, onSelect, loading }) => {
  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto"></div>
        <p className="mt-4 text-sage-600">Loading templates...</p>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="text-center py-12">
        <CubeIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Templates Available</h3>
        <p className="text-gray-600 mb-6">Create your first product template to get started.</p>
        <button
          onClick={() => navigate('/shopify/templates/create')}
          className="inline-flex items-center px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Create Template
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Select a Template</h2>
        <button
          onClick={() => (window.location.href = '/shopify/templates/create')}
          className="flex items-center px-3 py-2 text-sm bg-sage-600 text-white rounded-lg hover:bg-sage-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4 mr-1" />
          New Template
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map(template => (
          <div
            key={template.id}
            onClick={() => onSelect(template)}
            className="border rounded-lg p-4 hover:border-sage-300 hover:shadow-md transition-all cursor-pointer"
          >
            <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded-lg mb-4">
              <CubeIcon className="w-8 h-8 text-gray-400 mx-auto my-auto" />
            </div>
            <h3 className="font-medium text-gray-900">{template.template_title || template.name}</h3>
            <p className="text-sm text-gray-600 mt-1">{template.description}</p>
            {template.price && <p className="text-sm font-medium text-sage-600 mt-2">${template.price}</p>}
          </div>
        ))}
      </div>
    </div>
  );
};

// Design Upload Component
const DesignUpload = ({ selectedTemplate, onUpload, designFiles }) => {
  const handleFileChange = e => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onUpload(files);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Design Files</h2>
      <div className="mb-4 p-4 bg-sage-50 rounded-lg">
        <p className="text-sm text-sage-700">
          <strong>Selected Template:</strong> {selectedTemplate?.template_title || selectedTemplate?.name}
        </p>
      </div>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <PhotoIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <div className="space-y-2">
          <h3 className="text-lg font-medium text-gray-900">Upload your design files</h3>
          <p className="text-gray-600">Support PNG, JPG, SVG files</p>
          <div className="flex items-center justify-center">
            <label
              htmlFor="design-upload"
              className="cursor-pointer bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-md transition-colors"
            >
              Choose Files
            </label>
            <input
              id="design-upload"
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>
      </div>

      {designFiles.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Selected Files:</h3>
          <div className="space-y-2">
            {designFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                <span className="text-sm text-gray-700">{file.name}</span>
                <span className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Preview Generation Component
const PreviewGeneration = ({ selectedTemplate, designFiles, mockupPreview, onGeneratePreview, loading }) => {
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Generate Mockup Preview</h2>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Template</h3>
            <p className="text-sm text-gray-600">{selectedTemplate?.template_title || selectedTemplate?.name}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Design Files</h3>
            <p className="text-sm text-gray-600">{designFiles.length} file(s) selected</p>
          </div>
        </div>

        {!mockupPreview && (
          <div className="text-center">
            <button
              onClick={onGeneratePreview}
              disabled={loading}
              className={`px-6 py-3 rounded-md font-medium transition-colors ${
                loading ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-sage-600 hover:bg-sage-700 text-white'
              }`}
            >
              {loading ? 'Generating...' : 'Generate Preview'}
            </button>
          </div>
        )}

        {mockupPreview && (
          <div>
            <h3 className="font-medium text-gray-900 mb-4">Preview Generated</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mockupPreview.mockups?.map((mockup, index) => (
                <div key={index} className="border rounded-lg overflow-hidden">
                  <img src={mockup.data} alt={mockup.filename} className="w-full h-48 object-cover" />
                  <div className="p-3">
                    <p className="text-sm font-medium text-gray-900">{mockup.type}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Product Details Form Component
const ProductDetailsForm = ({ productDetails, setProductDetails, selectedTemplate, onNext }) => {
  const updateField = (field, value) => {
    setProductDetails(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const addVariant = () => {
    const newVariant = {
      title: 'Default',
      price: productDetails.price,
      sku: `${selectedTemplate?.name}-${Date.now()}`,
      inventory_quantity: 100,
    };
    setProductDetails(prev => ({
      ...prev,
      variants: [...prev.variants, newVariant],
    }));
  };

  const removeVariant = index => {
    setProductDetails(prev => ({
      ...prev,
      variants: prev.variants.filter((_, i) => i !== index),
    }));
  };

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Product Details</h2>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Product Title*</label>
          <input
            type="text"
            value={productDetails.title}
            onChange={e => updateField('title', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sage-500"
            placeholder="Enter product title"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <textarea
            value={productDetails.description}
            onChange={e => updateField('description', e.target.value)}
            rows={4}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sage-500"
            placeholder="Enter product description"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Price*</label>
            <input
              type="number"
              step="0.01"
              value={productDetails.price}
              onChange={e => updateField('price', parseFloat(e.target.value))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sage-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Vendor</label>
            <input
              type="text"
              value={productDetails.vendor}
              onChange={e => updateField('vendor', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sage-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
          <input
            type="text"
            value={productDetails.tags}
            onChange={e => updateField('tags', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sage-500"
            placeholder="Comma-separated tags"
          />
        </div>

        <div className="text-center">
          <button
            onClick={onNext}
            disabled={!productDetails.title}
            className={`px-6 py-3 rounded-md font-medium transition-colors ${
              !productDetails.title
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-sage-600 hover:bg-sage-700 text-white'
            }`}
          >
            Continue to Create Product
          </button>
        </div>
      </div>
    </div>
  );
};

// Product Creation Component
const ProductCreation = ({ productDetails, selectedTemplate, mockupPreview, onCreateProduct, isCreating }) => {
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Create Product</h2>

      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-medium text-gray-900 mb-4">Product Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Title</p>
              <p className="font-medium">{productDetails.title}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Price</p>
              <p className="font-medium">${productDetails.price}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Template</p>
              <p className="font-medium">{selectedTemplate?.template_title || selectedTemplate?.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Mockups</p>
              <p className="font-medium">{mockupPreview?.mockups?.length || 0} images</p>
            </div>
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={onCreateProduct}
            disabled={isCreating}
            className={`px-8 py-4 rounded-md font-medium text-lg transition-colors ${
              isCreating ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-sage-600 hover:bg-sage-700 text-white'
            }`}
          >
            {isCreating ? 'Creating Product...' : 'Create Shopify Product'}
          </button>
        </div>

        {isCreating && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto"></div>
            <p className="mt-2 text-sage-600">This may take a few minutes...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopifyProductCreator;
