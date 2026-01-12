import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from './NotificationSystem';
import {
  ShoppingBagIcon,
  CubeIcon,
  PhotoIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline';

const ShopifyIntegration = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();

  const [shopifyStore, setShopifyStore] = useState(null);
  const [products, setProducts] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreator, setShowCreator] = useState(false);

  useEffect(() => {
    fetchShopifyData();
  }, [token]);

  const fetchShopifyData = async () => {
    if (!token) return;

    try {
      setLoading(true);

      // Fetch Shopify store info
      const storeResponse = await fetch('/api/shopify/store', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (storeResponse.ok) {
        const storeData = await storeResponse.json();
        setShopifyStore(storeData);

        // Fetch products and templates if store is connected
        await Promise.all([fetchProducts(), fetchTemplates()]);
      }
    } catch (error) {
      console.error('Error fetching Shopify data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/shopify/products/my-products', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setProducts(data.products || []);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/shopify/templates', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const connectShopify = () => {
    const shopDomain = prompt('Enter your Shopify store domain (e.g., mystore.myshopify.com):');
    if (!shopDomain) return;

    // Redirect to Shopify OAuth
    window.location.href = `/api/shopify/connect?shop_domain=${shopDomain}`;
  };

  const testConnection = async () => {
    try {
      const response = await fetch('/api/shopify/test-connection', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        addNotification(`Connected to ${data.shop.name}`, 'success');
      } else {
        throw new Error('Connection test failed');
      }
    } catch (error) {
      addNotification('Connection test failed', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600"></div>
      </div>
    );
  }

  if (!shopifyStore) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <ShoppingBagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Connect Your Shopify Store</h3>
          <p className="text-gray-600 mb-6">
            Connect your Shopify store to create products using your templates and designs
          </p>
          <button
            onClick={connectShopify}
            className="bg-sage-600 hover:bg-sage-700 text-white px-6 py-3 rounded-md font-medium transition-colors"
          >
            Connect Shopify Store
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Store Connection Status */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CheckCircleIcon className="w-6 h-6 text-green-500" />
            <div>
              <h3 className="font-semibold text-gray-900">Shopify Store Connected</h3>
              <p className="text-sm text-gray-600">{shopifyStore.shop_name}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button onClick={testConnection} className="text-sage-600 hover:text-sage-700 text-sm font-medium">
              Test Connection
            </button>
            <button
              onClick={() => window.open(`https://${shopifyStore.shop_domain}/admin`, '_blank')}
              className="flex items-center text-sage-600 hover:text-sage-700 text-sm font-medium"
            >
              Open Admin
              <ArrowTopRightOnSquareIcon className="w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center">
            <CubeIcon className="w-8 h-8 text-sage-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Templates</p>
              <p className="text-2xl font-bold text-gray-900">{templates.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center">
            <ShoppingBagIcon className="w-8 h-8 text-sage-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Products Created</p>
              <p className="text-2xl font-bold text-gray-900">{products.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center">
            <PhotoIcon className="w-8 h-8 text-sage-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Active Products</p>
              <p className="text-2xl font-bold text-gray-900">{products.filter(p => p.status === 'active').length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Product Creation */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Create New Product</h3>
          {templates.length === 0 && (
            <div className="flex items-center text-amber-600">
              <ExclamationTriangleIcon className="w-5 h-5 mr-1" />
              <span className="text-sm">No templates available</span>
            </div>
          )}
        </div>

        {templates.length > 0 ? (
          <div>
            <p className="text-gray-600 mb-4">Use your existing templates to create products with custom designs</p>
            <button
              onClick={() => setShowCreator(!showCreator)}
              className="bg-sage-600 hover:bg-sage-700 text-white px-6 py-3 rounded-md font-medium transition-colors"
            >
              {showCreator ? 'Hide Creator' : 'Create Product'}
            </button>
          </div>
        ) : (
          <div>
            <p className="text-gray-600 mb-4">
              You need to create some product templates first before you can create Shopify products.
            </p>
            <button
              onClick={() => {
                /* Navigate to templates */
              }}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-md font-medium transition-colors"
            >
              Manage Templates
            </button>
          </div>
        )}
      </div>

      {/* Mini Product Creator */}
      {showCreator && templates.length > 0 && (
        <MiniProductCreator
          templates={templates}
          onProductCreated={() => {
            fetchProducts();
            setShowCreator(false);
          }}
        />
      )}

      {/* Recent Products */}
      {products.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Products</h3>
          <div className="space-y-3">
            {products.slice(0, 5).map(product => (
              <div key={product.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                <div>
                  <h4 className="font-medium text-gray-900">{product.title}</h4>
                  <p className="text-sm text-gray-600">Template: {product.template?.name || 'Unknown'}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      product.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {product.status}
                  </span>
                  <button
                    onClick={() =>
                      window.open(
                        `https://${shopifyStore.shop_domain}/admin/products/${product.shopify_product_id}`,
                        '_blank'
                      )
                    }
                    className="text-sage-600 hover:text-sage-700 text-sm"
                  >
                    View in Shopify
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Mini Product Creator Component
const MiniProductCreator = ({ templates, onProductCreated }) => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();

  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [title, setTitle] = useState('');
  const [price, setPrice] = useState(25.0);
  const [designFiles, setDesignFiles] = useState([]);
  const [isCreating, setIsCreating] = useState(false);

  const handleFileChange = e => {
    setDesignFiles(Array.from(e.target.files));
  };

  const createProduct = async () => {
    if (!selectedTemplate || !title || designFiles.length === 0) {
      addNotification('Please fill in all fields and upload at least one design', 'error');
      return;
    }

    try {
      setIsCreating(true);
      const formData = new FormData();

      formData.append('template_id', selectedTemplate);
      formData.append('title', title);
      formData.append('price', price);
      formData.append('description', '');
      formData.append('vendor', 'Custom Design Store');
      formData.append('tags', '');
      formData.append('variants', '[]');

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
        addNotification('Product created successfully!', 'success');
        onProductCreated();

        // Reset form
        setSelectedTemplate('');
        setTitle('');
        setPrice(25.0);
        setDesignFiles([]);
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

  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <h4 className="font-medium text-gray-900 mb-4">Quick Product Creator</h4>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Template</label>
          <select
            value={selectedTemplate}
            onChange={e => setSelectedTemplate(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="">Select a template</option>
            {templates.map(template => (
              <option key={template.id} value={template.id}>
                {template.template_title || template.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product Title</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Enter product title"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={e => setPrice(parseFloat(e.target.value))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Design Files</label>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          />
          {designFiles.length > 0 && (
            <p className="text-sm text-gray-600 mt-1">{designFiles.length} file(s) selected</p>
          )}
        </div>

        <button
          onClick={createProduct}
          disabled={isCreating}
          className={`w-full py-2 rounded-md font-medium transition-colors ${
            isCreating ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-sage-600 hover:bg-sage-700 text-white'
          }`}
        >
          {isCreating ? 'Creating...' : 'Create Product'}
        </button>
      </div>
    </div>
  );
};

export default ShopifyIntegration;
