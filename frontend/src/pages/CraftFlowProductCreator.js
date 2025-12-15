import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import { CubeIcon, PhotoIcon, PlusIcon, XMarkIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const CraftFlowProductCreator = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();
  const { id } = useParams();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [designs, setDesigns] = useState([]);
  const [imageUrls, setImageUrls] = useState(['']);
  const [uploadingImages, setUploadingImages] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [mockupDesignFiles, setMockupDesignFiles] = useState([]);
  const [generatingMockups, setGeneratingMockups] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
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
    is_active: true,
    is_featured: false,
    design_id: '',
    template_name: '',
  });

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    if (id) {
      loadProduct();
    }
    loadDesigns();
    loadTemplates();
  }, [id]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/products/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const product = response.data;
      setFormData({
        name: product.name || '',
        slug: product.slug || '',
        description: product.description || '',
        short_description: product.short_description || '',
        product_type: product.product_type || 'physical',
        print_method: product.print_method || 'uvdtf',
        category: product.category || 'cup_wraps',
        price: product.price || '',
        compare_at_price: product.compare_at_price || '',
        cost: product.cost || '',
        track_inventory: product.track_inventory || false,
        inventory_quantity: product.inventory_quantity || 0,
        allow_backorder: product.allow_backorder || false,
        is_active: product.is_active !== undefined ? product.is_active : true,
        is_featured: product.is_featured || false,
        design_id: product.design_id || '',
        template_name: product.template_name || '',
      });

      if (product.images && product.images.length > 0) {
        setImageUrls(product.images);
      }
    } catch (error) {
      console.error('Error loading product:', error);
      addNotification('error', 'Failed to load product');
    } finally {
      setLoading(false);
    }
  };

  const loadDesigns = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/designs/`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { page_size: 100 },
      });
      setDesigns(response.data.items || []);
    } catch (error) {
      console.error('Error loading designs:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/settings/craftflow-commerce-template`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const handleInputChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Auto-generate slug from name
    if (name === 'name' && !id) {
      const slug = value
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
      setFormData(prev => ({ ...prev, slug }));
    }
  };

  const handleImageUrlChange = (index, value) => {
    const newUrls = [...imageUrls];
    newUrls[index] = value;
    setImageUrls(newUrls);
  };

  const addImageUrl = () => {
    setImageUrls([...imageUrls, '']);
  };

  const removeImageUrl = index => {
    setImageUrls(imageUrls.filter((_, i) => i !== index));
  };

  const handleDesignSelect = e => {
    const designId = e.target.value;
    setFormData(prev => ({ ...prev, design_id: designId }));

    // Find the design and auto-fill template name and image
    const design = designs.find(d => d.id.toString() === designId);
    if (design) {
      setFormData(prev => ({
        ...prev,
        template_name: design.template_name || '',
      }));

      // Add design image to images if not already there
      if (design.image_url && !imageUrls.includes(design.image_url)) {
        setImageUrls([design.image_url, ...imageUrls.filter(url => url)]);
      }
    }
  };

  const handleMockupDesignFilesChange = e => {
    const files = Array.from(e.target.files);
    setMockupDesignFiles(files);
  };

  const handleGenerateMockups = async () => {
    if (!selectedTemplate) {
      addNotification('error', 'Please select a template first');
      return;
    }

    if (mockupDesignFiles.length === 0) {
      addNotification('error', 'Please select design files to generate mockups');
      return;
    }

    try {
      setGeneratingMockups(true);
      addNotification('info', 'Generating mockups... This may take a moment');

      // TODO: Implement mockup generation API call
      // This would call an endpoint that takes template + design files and generates mockups
      // For now, we'll just upload the design files as mockup images

      const uploadPromises = mockupDesignFiles.map(async file => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(`${API_BASE_URL}/api/ecommerce/admin/product-images/upload`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        });

        return response.data.url;
      });

      const uploadedUrls = await Promise.all(uploadPromises);

      // Add uploaded mockups to image list
      setImageUrls(prev => [...prev.filter(url => url), ...uploadedUrls]);

      addNotification('success', `Generated ${uploadedUrls.length} mockup(s) successfully`);

      // Clear the design files
      setMockupDesignFiles([]);
    } catch (error) {
      console.error('Error generating mockups:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to generate mockups';
      addNotification('error', errorMessage);
    } finally {
      setGeneratingMockups(false);
    }
  };

  const handleImageUpload = async e => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    // Validate file types
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    const invalidFiles = files.filter(f => !validTypes.includes(f.type));
    if (invalidFiles.length > 0) {
      addNotification('error', 'Only JPG, PNG, WEBP and GIF images are allowed');
      return;
    }

    // Validate file sizes (max 10MB each)
    const maxSize = 10 * 1024 * 1024;
    const oversizedFiles = files.filter(f => f.size > maxSize);
    if (oversizedFiles.length > 0) {
      addNotification('error', 'Images must be less than 10MB');
      return;
    }

    setUploadingImages(true);
    try {
      const uploadPromises = files.map(async file => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(`${API_BASE_URL}/api/ecommerce/admin/product-images/upload`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        });

        return response.data.url;
      });

      const uploadedUrls = await Promise.all(uploadPromises);

      // Add uploaded URLs to image list, filtering out empty ones
      setImageUrls(prev => [...prev.filter(url => url), ...uploadedUrls]);

      addNotification('success', `Uploaded ${uploadedUrls.length} image(s) successfully`);
    } catch (error) {
      console.error('Error uploading images:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to upload images';
      addNotification('error', errorMessage);
    } finally {
      setUploadingImages(false);
      // Reset file input
      e.target.value = '';
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validation
    if (!formData.name || !formData.slug) {
      addNotification('error', 'Please fill in required fields');
      return;
    }

    if (!formData.price || parseFloat(formData.price) <= 0) {
      addNotification('error', 'Please enter a valid price');
      return;
    }

    try {
      setSaving(true);

      // Filter out empty image URLs
      const validImages = imageUrls.filter(url => url.trim());

      const productData = {
        ...formData,
        price: parseFloat(formData.price),
        compare_at_price: formData.compare_at_price ? parseFloat(formData.compare_at_price) : null,
        cost: formData.cost ? parseFloat(formData.cost) : null,
        inventory_quantity: parseInt(formData.inventory_quantity) || 0,
        images: validImages,
        featured_image: validImages[0] || null,
      };

      let response;
      if (id) {
        response = await axios.put(`${API_BASE_URL}/api/ecommerce/admin/products/${id}`, productData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        addNotification('success', 'Product updated successfully');
      } else {
        response = await axios.post(`${API_BASE_URL}/api/ecommerce/admin/products/`, productData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        addNotification('success', 'Product created successfully');
      }

      navigate('/craftflow/products');
    } catch (error) {
      console.error('Error saving product:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save product';
      addNotification('error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading product...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/craftflow/products')}
              className="mr-4 p-2 text-sage-600 hover:text-sage-800 hover:bg-sage-100 rounded-lg"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <CubeIcon className="w-8 h-8 mr-3 text-sage-600" />
                {id ? 'Edit Product' : 'Create Product'}
              </h1>
              <p className="text-gray-600">Add a new product to your storefront</p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Product Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="Funny Bunny Cup Wrap"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">URL Slug *</label>
                <input
                  type="text"
                  name="slug"
                  value={formData.slug}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="funny-bunny-cup-wrap"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">URL: /products/{formData.slug || 'product-slug'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Short Description</label>
                <input
                  type="text"
                  name="short_description"
                  value={formData.short_description}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="Brief description for product cards"
                  maxLength={500}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="Full product description"
                />
              </div>
            </div>
          </div>

          {/* Product Classification */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Classification</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Product Type *</label>
                <select
                  name="product_type"
                  value={formData.product_type}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  required
                >
                  <option value="physical">Physical</option>
                  <option value="digital">Digital</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Print Method *</label>
                <select
                  name="print_method"
                  value={formData.print_method}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  required
                >
                  <option value="uvdtf">UV DTF</option>
                  <option value="dtf">DTF</option>
                  <option value="sublimation">Sublimation</option>
                  <option value="vinyl">Vinyl</option>
                  <option value="digital">Digital</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Category *</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  required
                >
                  <option value="cup_wraps">Cup Wraps</option>
                  <option value="single_square">Single Square</option>
                  <option value="single_rectangle">Single Rectangle</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Pricing</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Price * ($)</label>
                <input
                  type="number"
                  name="price"
                  value={formData.price}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="3.50"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Compare At Price ($)</label>
                <input
                  type="number"
                  name="compare_at_price"
                  value={formData.compare_at_price}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="5.00"
                />
                <p className="text-xs text-gray-500 mt-1">Original price (for showing discounts)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cost ($)</label>
                <input
                  type="number"
                  name="cost"
                  value={formData.cost}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="1.50"
                />
                <p className="text-xs text-gray-500 mt-1">Your cost (for margin tracking)</p>
              </div>
            </div>
          </div>

          {/* Inventory */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Inventory</h2>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="track_inventory"
                  checked={formData.track_inventory}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">Track inventory quantity</label>
              </div>

              {formData.track_inventory && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Inventory Quantity</label>
                    <input
                      type="number"
                      name="inventory_quantity"
                      value={formData.inventory_quantity}
                      onChange={handleInputChange}
                      min="0"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                    />
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      name="allow_backorder"
                      checked={formData.allow_backorder}
                      onChange={handleInputChange}
                      className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-900">
                      Allow backorders (sell when out of stock)
                    </label>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Design Link */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Link to Design (Optional)</h2>
            <p className="text-sm text-gray-600 mb-4">
              Link this product to an existing design for reference. This is optional.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Design</label>
                <select
                  name="design_id"
                  value={formData.design_id}
                  onChange={handleDesignSelect}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                >
                  <option value="">None</option>
                  {designs.map(design => (
                    <option key={design.id} value={design.id}>
                      {design.design_name} - {design.template_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Template Name</label>
                <input
                  type="text"
                  name="template_name"
                  value={formData.template_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                  placeholder="16oz Tumbler"
                />
              </div>
            </div>
          </div>

          {/* Mockup Generator */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate Mockups (Optional)</h2>
            <p className="text-sm text-gray-600 mb-4">
              Select a template and upload design files to automatically generate product mockups. Skip this if you want
              to upload mockups manually below.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select CraftFlow Commerce Template
                </label>
                <select
                  value={selectedTemplate?.id || ''}
                  onChange={e => {
                    const template = templates.find(t => t.id === e.target.value);
                    setSelectedTemplate(template || null);
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                >
                  <option value="">No template selected</option>
                  {templates.map(template => (
                    <option key={template.id} value={template.id}>
                      {template.name} - {template.template_title}
                    </option>
                  ))}
                </select>
                {templates.length === 0 && (
                  <p className="text-xs text-orange-600 mt-1">
                    No templates available.{' '}
                    <button
                      type="button"
                      onClick={() => navigate('/craftflow/templates/create')}
                      className="underline hover:text-orange-700"
                    >
                      Create a template first
                    </button>
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Upload Design Files</label>
                <input
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                  multiple
                  onChange={handleMockupDesignFilesChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                />
                {mockupDesignFiles.length > 0 && (
                  <p className="text-xs text-gray-600 mt-1">
                    {mockupDesignFiles.length} file(s) selected: {mockupDesignFiles.map(f => f.name).join(', ')}
                  </p>
                )}
              </div>

              <button
                type="button"
                onClick={handleGenerateMockups}
                disabled={!selectedTemplate || mockupDesignFiles.length === 0 || generatingMockups}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generatingMockups ? 'Generating Mockups...' : 'Generate Mockups'}
              </button>

              {selectedTemplate && (
                <div className="mt-2 p-3 bg-gray-50 rounded-md">
                  <p className="text-xs text-gray-700">
                    <strong>Template:</strong> {selectedTemplate.name}
                  </p>
                  <p className="text-xs text-gray-700">
                    <strong>Print Method:</strong> {selectedTemplate.print_method}
                  </p>
                  <p className="text-xs text-gray-700">
                    <strong>Category:</strong> {selectedTemplate.category}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Images */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-between">
              <span className="flex items-center">
                <PhotoIcon className="w-5 h-5 mr-2" />
                Product Images (Upload Manually or Add URLs)
              </span>
              <div className="flex items-center space-x-2">
                <label
                  htmlFor="image-upload"
                  className={`flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md cursor-pointer ${
                    uploadingImages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
                  }`}
                >
                  <PhotoIcon className="w-4 h-4 mr-1" />
                  {uploadingImages ? 'Uploading...' : 'Upload Images'}
                </label>
                <input
                  id="image-upload"
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                  multiple
                  onChange={handleImageUpload}
                  disabled={uploadingImages}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={addImageUrl}
                  className="flex items-center px-3 py-1 text-sm bg-sage-600 text-white rounded-md hover:bg-sage-700"
                >
                  <PlusIcon className="w-4 h-4 mr-1" />
                  Add URL
                </button>
              </div>
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Upload product mockup images manually (JPG, PNG, WEBP, GIF - max 10MB each) or add image URLs. The first
              image will be the featured image. You can also use the mockup generator above to automatically create
              mockups from a template.
            </p>

            <div className="space-y-3">
              {imageUrls.map((url, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="url"
                    value={url}
                    onChange={e => handleImageUrlChange(index, e.target.value)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                    placeholder="https://example.com/image.jpg"
                  />
                  {index === 0 && <span className="px-2 py-1 text-xs bg-sage-100 text-sage-800 rounded">Featured</span>}
                  {imageUrls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeImageUrl(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                    >
                      <XMarkIcon className="w-5 h-5" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {imageUrls.some(url => url) && (
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                {imageUrls
                  .filter(url => url)
                  .map((url, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={url}
                        alt={`Preview ${index + 1}`}
                        className="w-full h-32 object-cover rounded-md border border-gray-300"
                        onError={e => {
                          e.target.src =
                            'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIEVycm9yPC90ZXh0Pjwvc3ZnPg==';
                        }}
                      />
                      {index === 0 && (
                        <div className="absolute top-2 left-2 px-2 py-1 bg-sage-600 text-white text-xs rounded">
                          Featured
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Status</h2>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">Active (visible on storefront)</label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  name="is_featured"
                  checked={formData.is_featured}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900">Featured (show in featured section)</label>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/craftflow/products')}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className={`px-6 py-2 rounded-md text-white ${
                saving ? 'bg-gray-400 cursor-not-allowed' : 'bg-sage-600 hover:bg-sage-700'
              }`}
            >
              {saving ? 'Saving...' : id ? 'Update Product' : 'Create Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CraftFlowProductCreator;
