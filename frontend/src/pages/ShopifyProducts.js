import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import { useNavigate } from 'react-router-dom';
import {
  BuildingStorefrontIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ViewColumnsIcon,
  Squares2X2Icon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  ExclamationTriangleIcon,
  CurrencyDollarIcon,
  TagIcon,
  PhotoIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';

const ShopifyProducts = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [storeConnected, setStoreConnected] = useState(true);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);

      const response = await fetch('/api/shopify/products', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // No store connected
          setStoreConnected(false);
          return;
        }
        throw new Error('Failed to load products');
      }

      const data = await response.json();
      setProducts(data.products || []);
      setStoreConnected(true);
    } catch (error) {
      console.error('Error loading products:', error);
      if (error.message.includes('store')) {
        setStoreConnected(false);
      } else {
        addNotification('Failed to load products', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteProduct = async productId => {
    if (!window.confirm('Are you sure you want to delete this product from Shopify?')) {
      return;
    }

    try {
      const response = await fetch(`/api/shopify/products/${productId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete product');
      }

      addNotification('Product deleted successfully', 'success');
      loadProducts(); // Reload products
    } catch (error) {
      console.error('Error deleting product:', error);
      addNotification('Failed to delete product', 'error');
    }
  };

  const openInShopify = product => {
    if (product.admin_graphql_api_id) {
      // Extract numeric ID from GraphQL ID
      const numericId = product.admin_graphql_api_id.split('/').pop();
      const shopDomain = product.shop_domain || 'your-shop'; // Would need to get this from store info
      window.open(`https://${shopDomain}.myshopify.com/admin/products/${numericId}`, '_blank');
    }
  };

  // Filter products based on search and status
  const filteredProducts = products.filter(product => {
    const matchesSearch =
      product.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.product_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.vendor?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || product.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  if (!storeConnected) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Store Connected</h2>
          <p className="text-gray-600 mb-6">Please connect your Shopify store to view and manage products.</p>
          <button
            onClick={() => navigate('/shopify/connect')}
            className="bg-sage-600 text-white px-6 py-2 rounded-md hover:bg-sage-700"
          >
            Connect Shopify Store
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading products...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Shopify Products</h1>
            <p className="text-gray-600">Manage your Shopify store products</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/shopify/create')}
              className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create Product
            </button>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full focus:ring-sage-500 focus:border-sage-500"
              />
            </div>

            <div className="flex items-center space-x-3">
              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-sage-500 focus:border-sage-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="draft">Draft</option>
                <option value="archived">Archived</option>
              </select>

              {/* View Mode Toggle */}
              <div className="flex border border-gray-300 rounded-md">
                <button
                  onClick={() => setViewMode('table')}
                  className={`p-2 ${viewMode === 'table' ? 'bg-sage-100 text-sage-600' : 'text-gray-600'}`}
                >
                  <ViewColumnsIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-sage-100 text-sage-600' : 'text-gray-600'}`}
                >
                  <Squares2X2Icon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Results Count */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredProducts.length} of {products.length} products
          </div>
        </div>

        {/* Products Display */}
        {filteredProducts.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <BuildingStorefrontIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {products.length === 0 ? 'No products found' : 'No products match your filters'}
            </h3>
            <p className="text-gray-600 mb-4">
              {products.length === 0
                ? 'Start by creating your first product or sync existing products from Shopify.'
                : 'Try adjusting your search criteria or filters.'}
            </p>
            {products.length === 0 && (
              <button
                onClick={() => navigate('/shopify/create')}
                className="bg-sage-600 text-white px-6 py-2 rounded-md hover:bg-sage-700"
              >
                Create Your First Product
              </button>
            )}
          </div>
        ) : viewMode === 'table' ? (
          /* Table View */
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Inventory
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vendor
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredProducts.map(product => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-12 w-12">
                            {product.image ? (
                              <img
                                className="h-12 w-12 rounded-lg object-cover"
                                src={product.image.src}
                                alt={product.title}
                              />
                            ) : (
                              <div className="h-12 w-12 rounded-lg bg-gray-200 flex items-center justify-center">
                                <PhotoIcon className="w-6 h-6 text-gray-400" />
                              </div>
                            )}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 line-clamp-1">{product.title}</div>
                            <div className="text-sm text-gray-500">ID: {product.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            product.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : product.status === 'draft'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {product.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.variants && product.variants[0]
                          ? `${product.variants[0].inventory_quantity || 0} in stock`
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.product_type || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.vendor || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => setSelectedProduct(product)}
                            className="text-blue-600 hover:text-blue-900"
                            title="View Details"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => openInShopify(product)}
                            className="text-green-600 hover:text-green-900"
                            title="Open in Shopify"
                          >
                            <LinkIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => deleteProduct(product.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Delete Product"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* Grid View */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredProducts.map(product => (
              <div
                key={product.id}
                className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
              >
                {/* Product Image */}
                <div className="aspect-w-16 aspect-h-12 bg-gray-200">
                  {product.image ? (
                    <img src={product.image.src} alt={product.title} className="w-full h-48 object-cover" />
                  ) : (
                    <div className="w-full h-48 flex items-center justify-center">
                      <PhotoIcon className="w-12 h-12 text-gray-400" />
                    </div>
                  )}
                </div>

                {/* Product Info */}
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">{product.title}</h3>

                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        product.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : product.status === 'draft'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {product.status}
                    </span>
                    {product.variants && product.variants[0] && (
                      <span className="text-sm text-gray-600">${product.variants[0].price}</span>
                    )}
                  </div>

                  {product.product_type && (
                    <div className="flex items-center text-sm text-gray-600 mb-2">
                      <TagIcon className="w-4 h-4 mr-1" />
                      {product.product_type}
                    </div>
                  )}

                  <div className="text-sm text-gray-500 mb-3">
                    {product.variants && product.variants[0]
                      ? `${product.variants[0].inventory_quantity || 0} in stock`
                      : 'Inventory not tracked'}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedProduct(product)}
                      className="flex-1 flex items-center justify-center px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                    >
                      <EyeIcon className="w-4 h-4 mr-1" />
                      View
                    </button>
                    <button
                      onClick={() => openInShopify(product)}
                      className="flex-1 flex items-center justify-center px-3 py-2 text-sm bg-green-50 text-green-600 rounded hover:bg-green-100"
                    >
                      <LinkIcon className="w-4 h-4 mr-1" />
                      Shopify
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Product Detail Modal */}
        {selectedProduct && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl max-h-full overflow-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h3 className="text-lg font-semibold">{selectedProduct.title}</h3>
                <button onClick={() => setSelectedProduct(null)} className="text-gray-400 hover:text-gray-600">
                  ×
                </button>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Product Image */}
                  <div>
                    {selectedProduct.image ? (
                      <img src={selectedProduct.image.src} alt={selectedProduct.title} className="w-full rounded-lg" />
                    ) : (
                      <div className="w-full h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                        <PhotoIcon className="w-16 h-16 text-gray-400" />
                      </div>
                    )}
                  </div>

                  {/* Product Details */}
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Product Information</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <span
                            className={`font-medium ${
                              selectedProduct.status === 'active'
                                ? 'text-green-600'
                                : selectedProduct.status === 'draft'
                                  ? 'text-yellow-600'
                                  : 'text-gray-600'
                            }`}
                          >
                            {selectedProduct.status}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Product Type:</span>
                          <span className="font-medium">{selectedProduct.product_type || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Vendor:</span>
                          <span className="font-medium">{selectedProduct.vendor || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Created:</span>
                          <span className="font-medium">
                            {new Date(selectedProduct.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    {selectedProduct.body_html && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Description</h4>
                        <div
                          className="text-sm text-gray-700 prose max-w-none"
                          dangerouslySetInnerHTML={{ __html: selectedProduct.body_html }}
                        />
                      </div>
                    )}

                    {selectedProduct.variants && selectedProduct.variants.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Variants</h4>
                        <div className="space-y-2">
                          {selectedProduct.variants.map(variant => (
                            <div key={variant.id} className="flex justify-between text-sm">
                              <span>{variant.title}</span>
                              <span className="font-medium">${variant.price}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex space-x-3 pt-4">
                      <button
                        onClick={() => openInShopify(selectedProduct)}
                        className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        <LinkIcon className="w-4 h-4 mr-2" />
                        Open in Shopify
                      </button>
                      <button
                        onClick={() => deleteProduct(selectedProduct.id)}
                        className="flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        <TrashIcon className="w-4 h-4 mr-2" />
                        Delete Product
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopifyProducts;
