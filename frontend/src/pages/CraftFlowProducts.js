import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import {
  CubeIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  EyeIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline';

const CraftFlowProducts = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [printMethodFilter, setPrintMethodFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/products/`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { page_size: 100 },
      });

      setProducts(response.data.items || []);
    } catch (error) {
      console.error('Error loading products:', error);
      addNotification('error', 'Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async productId => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/ecommerce/admin/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      addNotification('success', 'Product deleted successfully');
      loadProducts();
    } catch (error) {
      console.error('Error deleting product:', error);
      addNotification('error', 'Failed to delete product');
    }
  };

  const handleToggleActive = async (productId, currentStatus) => {
    try {
      await axios.put(
        `${API_BASE_URL}/api/ecommerce/admin/products/${productId}`,
        { is_active: !currentStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      addNotification('success', `Product ${!currentStatus ? 'activated' : 'deactivated'}`);
      loadProducts();
    } catch (error) {
      console.error('Error toggling product status:', error);
      addNotification('error', 'Failed to update product status');
    }
  };

  // Filter products
  const filteredProducts = products.filter(product => {
    const matchesSearch =
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.slug.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesPrintMethod = printMethodFilter === 'all' || product.print_method === printMethodFilter;
    const matchesCategory = categoryFilter === 'all' || product.category === categoryFilter;
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && product.is_active) ||
      (statusFilter === 'inactive' && !product.is_active);

    return matchesSearch && matchesPrintMethod && matchesCategory && matchesStatus;
  });

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
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <CubeIcon className="w-8 h-8 mr-3 text-sage-600" />
              Products
            </h1>
            <p className="text-gray-600">{filteredProducts.length} products</p>
          </div>

          <button
            onClick={() => navigate('/craftflow/products/create')}
            className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Product
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-6 p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
              />
            </div>

            {/* Print Method Filter */}
            <select
              value={printMethodFilter}
              onChange={e => setPrintMethodFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
            >
              <option value="all">All Print Methods</option>
              <option value="uvdtf">UV DTF</option>
              <option value="dtf">DTF</option>
              <option value="sublimation">Sublimation</option>
              <option value="vinyl">Vinyl</option>
              <option value="digital">Digital</option>
            </select>

            {/* Category Filter */}
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
            >
              <option value="all">All Categories</option>
              <option value="cup_wraps">Cup Wraps</option>
              <option value="single_square">Single Square</option>
              <option value="single_rectangle">Single Rectangle</option>
              <option value="other">Other</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        {/* Products Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Print Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Inventory
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredProducts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center">
                    <CubeIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-gray-500">No products found</p>
                    <button
                      onClick={() => navigate('/craftflow/products/create')}
                      className="mt-4 text-sage-600 hover:text-sage-700"
                    >
                      Create your first product →
                    </button>
                  </td>
                </tr>
              ) : (
                filteredProducts.map(product => (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-12 w-12">
                          {product.featured_image ? (
                            <img
                              className="h-12 w-12 rounded-md object-cover"
                              src={product.featured_image}
                              alt={product.name}
                            />
                          ) : (
                            <div className="h-12 w-12 rounded-md bg-gray-200 flex items-center justify-center">
                              <PhotoIcon className="h-6 w-6 text-gray-400" />
                            </div>
                          )}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{product.name}</div>
                          <div className="text-sm text-gray-500">{product.slug}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {product.print_method?.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {product.category?.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${product.price?.toFixed(2)}
                      {product.compare_at_price && (
                        <span className="ml-2 text-gray-400 line-through">${product.compare_at_price?.toFixed(2)}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {product.track_inventory ? product.inventory_quantity : '∞'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleToggleActive(product.id, product.is_active)}
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          product.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {product.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() =>
                            window.open(
                              `${window.location.origin.replace('3000', '3001')}/products/${product.slug}`,
                              '_blank'
                            )
                          }
                          className="text-sage-600 hover:text-sage-900"
                          title="View on storefront"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => navigate(`/craftflow/products/edit/${product.id}`)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit product"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDeleteProduct(product.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete product"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CraftFlowProducts;
